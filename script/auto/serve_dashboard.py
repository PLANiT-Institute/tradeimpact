"""Serve data/auto over HTTP so dashboard.html can read the database beside it.

``data/auto/dashboard.html`` carries no data: it fetches ``tradeimpact_auto.sqlite`` from its
own directory, which the browser only allows over HTTP (a page opened from ``file://`` is
refused and falls back to its file picker). This starts a stdlib server on the loopback
interface, prints the URL and serves that one directory.

Every response is sent ``Cache-Control: no-store``, so re-running the pipeline and reloading
the page always shows the rebuilt database rather than a cached copy of the previous one.

Run from the repository root:  .venv/bin/python script/auto/serve_dashboard.py
Stop it with Ctrl-C. Nothing is written: the handler serves GET and HEAD only.
"""

from __future__ import annotations

import argparse
import functools
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "data" / "auto"
PAGE = "dashboard.html"
HOST = "127.0.0.1"
PORT = 8765


class NoStoreHandler(SimpleHTTPRequestHandler):
    """Static handler that never lets the browser cache a response.

    The database is rewritten by every pipeline run and keeps its name, so a cached copy is
    the difference between reading today's results and yesterday's.
    """

    #: Keep-alive: the database is one 24 MB response and the page asks for it on every load.
    protocol_version = "HTTP/1.1"

    #: SimpleHTTPRequestHandler guesses by extension; .sqlite is not in the stdlib table.
    extensions_map = {
        **mimetypes.types_map,
        "": "application/octet-stream",
        ".db": "application/vnd.sqlite3",
        ".json": "application/json",
        ".sqlite": "application/vnd.sqlite3",
    }

    def end_headers(self) -> None:
        """Add the no-store headers before the header block is closed."""
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Log one line per request without the date prefix the base class adds."""
        print(f"  {self.address_string()} {format % args}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    Args:
        argv: Argument list to parse; ``None`` reads ``sys.argv``.

    Returns:
        Namespace with the integer ``port`` to bind.
    """
    parser = argparse.ArgumentParser(description=f"Serve {ROOT.name} for {PAGE} on {HOST}.")
    parser.add_argument("--port", type=int, default=PORT, help=f"TCP port to bind (default {PORT})")
    return parser.parse_args(argv)


def serve(port: int = PORT) -> None:
    """Serve ``data/auto`` on the loopback interface until interrupted.

    Args:
        port: TCP port to bind.

    Raises:
        SystemExit: If the directory or the dashboard page is missing.
    """
    if not ROOT.is_dir():
        raise SystemExit(f"directory not found: {ROOT}")
    if not (ROOT / PAGE).exists():
        raise SystemExit(f"{PAGE} not found: run script/auto/model/build_dashboard.py first")
    handler = functools.partial(NoStoreHandler, directory=str(ROOT))
    with ThreadingHTTPServer((HOST, port), handler) as httpd:
        print(f"serving {ROOT.relative_to(REPO)} at http://{HOST}:{port}/{PAGE}")
        print("Ctrl-C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


def main() -> None:
    """Parse the command line and serve."""
    serve(parse_args().port)


if __name__ == "__main__":
    main()
