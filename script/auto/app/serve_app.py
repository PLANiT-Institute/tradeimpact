"""Serve data/auto for the workbench, and accept queued edits over one write endpoint.

The workbench (``app.html``) reads ``tradeimpact_auto.sqlite`` the same way every other page
does, so serving is the same static, no-store, loopback-only handler the dashboard uses. What
this server adds is the one thing a static page cannot do: persist a correction.

    GET  /edits   the queued edits so far, as JSON
    POST /edit    append one override (JSON body) to data/auto/overrides.csv, return the full list

An edit never touches a raw source. It is a staged instruction — sale year, dataset, country,
parameter, old value, new value, and a mandatory source id and note — written to
data/auto/overrides.csv, which the pipeline applies on the next run
(script/auto/model/apply_overrides.py) with the value, its source and its note. Raw data stays
immutable and every change carries who said so and why, the same discipline the registries keep.

The server is loopback only and writes exactly one file, ``data/auto/overrides.csv``. It refuses a
body without both a source and a note, so a value can never enter the queue unattributed.

Run from the repository root:  .venv/bin/python script/auto/app/serve_app.py
Then open  http://127.0.0.1:8770/app.html   ·  Ctrl-C to stop.
"""

from __future__ import annotations

import argparse
import csv
import errno
import functools
import io
import json
import mimetypes
import threading
import webbrowser
from datetime import UTC, datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "data" / "auto"
PAGE = "app.html"
EDITS = ROOT / "overrides.csv"
HOST = "127.0.0.1"
PORT = 8770
EDIT_FIELDS = [
    "queued_at",
    "cohort_year",
    "dataset",
    "country",
    "parameter",
    "old_value",
    "new_value",
    "source_id",
    "note",
]
#: The body keys a POST /edit must carry, and the two that may not be blank.
REQUIRED = ("cohort_year", "dataset", "country", "parameter", "new_value", "source_id", "note")
NON_EMPTY = ("source_id", "note")
MAX_BODY = 64 * 1024


def read_edits() -> list[dict[str, str]]:
    """Every queued edit, oldest first; an empty list when none has been queued."""
    if not EDITS.exists():
        return []
    with EDITS.open(newline="") as f:
        return list(csv.DictReader(f))


def append_edit(body: dict[str, object]) -> list[dict[str, str]]:
    """Validate one edit and append it to the queue.

    Args:
        body: The decoded JSON body of a POST /edit.

    Returns:
        The full queue after appending.

    Raises:
        ValueError: If a required key is missing or a source or note is blank.
    """
    missing = [k for k in REQUIRED if k not in body]
    if missing:
        raise ValueError(f"missing {missing}")
    if any(not str(body.get(k, "")).strip() for k in NON_EMPTY):
        raise ValueError("source_id and note are both required")
    row = {
        "queued_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "cohort_year": str(body["cohort_year"]),
        "dataset": str(body["dataset"]),
        "country": str(body["country"]),
        "parameter": str(body["parameter"]),
        "old_value": str(body.get("old", body.get("old_value", ""))),
        "new_value": str(body["new_value"]),
        "source_id": str(body["source_id"]).strip(),
        "note": str(body["note"]).strip(),
    }
    rows = read_edits()
    rows.append(row)
    with EDITS.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EDIT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


class WorkbenchHandler(SimpleHTTPRequestHandler):
    """Static no-store handler for data/auto, plus /edits and /edit."""

    protocol_version = "HTTP/1.1"
    extensions_map = {
        **mimetypes.types_map,
        "": "application/octet-stream",
        ".sqlite": "application/vnd.sqlite3",
        ".json": "application/json",
    }

    def _json(self, status: int, payload: dict[str, object]) -> None:
        """Write one JSON response with the no-store and loopback headers."""
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        """Serve /edits as JSON; everything else is a static file."""
        if self.path.split("?")[0] == "/edits":
            self._json(200, {"edits": read_edits()})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        """Accept one queued edit at /edit."""
        if self.path.split("?")[0] != "/edit":
            self._json(404, {"error": "unknown endpoint"})
            return
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_BODY:
            self._json(413, {"error": "empty or oversized body"})
            return
        try:
            body = json.load(io.BytesIO(self.rfile.read(length)))
            rows = append_edit(body)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
            return
        print(
            f"  queued edit: {body.get('dataset')}/{body.get('country')} "
            f"{body.get('parameter')} ({body.get('cohort_year')})"
        )
        self._json(200, {"edits": rows})

    def end_headers(self) -> None:
        """Never let the browser cache a response; the database is rewritten every run."""
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """One terse line per request."""
        print(f"  {self.address_string()} {format % args}")


def bind(handler: object, port: int) -> ThreadingHTTPServer:
    """Bind the first free port at or after ``port`` (a busy port just means try the next)."""
    for candidate in range(port, port + 10):
        try:
            return ThreadingHTTPServer((HOST, candidate), handler)  # type: ignore[arg-type]
        except OSError as exc:
            if exc.errno not in (errno.EADDRINUSE, errno.EACCES):
                raise
            print(f"port {candidate} is in use, trying {candidate + 1}", flush=True)
    raise SystemExit(f"no free port between {port} and {port + 9}")


def serve(port: int = PORT, open_browser: bool = False) -> None:
    """Serve the workbench on the loopback interface until interrupted."""
    if not (ROOT / PAGE).exists():
        raise SystemExit(f"{PAGE} not found: run script/auto/app/build_app.py first")
    handler = functools.partial(WorkbenchHandler, directory=str(ROOT))
    with bind(handler, port) as httpd:
        port = httpd.server_address[1]
        print(f"serving {ROOT.relative_to(REPO)} at http://{HOST}:{port}/{PAGE}", flush=True)
        print(f"overrides → {EDITS.relative_to(REPO)}", flush=True)
        print("Ctrl-C to stop", flush=True)
        if open_browser:
            threading.Timer(0.5, webbrowser.open, [f"http://{HOST}:{port}/{PAGE}"]).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


def main() -> None:
    """Parse the command line and serve."""
    parser = argparse.ArgumentParser(description=f"Serve the workbench and queue edits on {HOST}.")
    parser.add_argument("--port", type=int, default=PORT, help=f"TCP port (default {PORT})")
    parser.add_argument("--open", action="store_true", help="open the workbench in the browser")
    args = parser.parse_args()
    serve(args.port, args.open)


if __name__ == "__main__":
    main()
