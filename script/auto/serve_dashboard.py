"""Serve data/auto over HTTP so dashboard.html can read the database beside it.

``data/auto/database/dashboard.html`` carries no data: it fetches ``tradeimpact_auto.sqlite`` from
its
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
import errno
import functools
import mimetypes
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
#: Sector directory under data/ -> the page the server announces.
SECTOR_PAGES = {"auto": "database/dashboard.html", "power": "report/ti_power_report.html"}
ROOT = REPO / "data" / "auto"
PAGE = SECTOR_PAGES["auto"]
HOST = "127.0.0.1"
PORT = 8765
#: Origins allowed to read this server: a page opened from disk, and the server itself.
ALLOWED_ORIGINS = frozenset({"null", f"http://{HOST}:{PORT}", f"http://localhost:{PORT}"})


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
        """Add the no-store and loopback CORS headers before the header block is closed."""
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            # A dashboard.html opened by double-click has the opaque origin "null" and cannot
            # read the database beside it; letting that one origin read this loopback server
            # is what makes the page connect itself with no click.
            self.send_header("Access-Control-Allow-Origin", origin)
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Log one line per request without the date prefix the base class adds."""
        print(f"  {self.address_string()} {format % args}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    Args:
        argv: Argument list to parse; ``None`` reads ``sys.argv``.

    Returns:
        Namespace with the integer ``port`` to bind and the ``open`` flag.
    """
    parser = argparse.ArgumentParser(description=f"Serve {ROOT.name} for {PAGE} on {HOST}.")
    parser.add_argument("--port", type=int, default=PORT, help=f"TCP port to bind (default {PORT})")
    parser.add_argument(
        "--open", action="store_true", help="open the dashboard in the default browser once serving"
    )
    parser.add_argument(
        "--root",
        choices=sorted(SECTOR_PAGES),
        default="auto",
        help="sector directory under data/ to serve (default auto)",
    )
    return parser.parse_args(argv)


def bind(handler: object, port: int) -> ThreadingHTTPServer:
    """Bind the first free port at or after ``port``.

    A busy port usually means this server is already running (or another one is), which is not
    a reason to fail: the next free port serves the same directory just as well.

    Args:
        handler: Request-handler factory.
        port: First port to try.

    Returns:
        The bound server.

    Raises:
        SystemExit: If no port in the next ten is free.
    """
    for candidate in range(port, port + 10):
        try:
            return ThreadingHTTPServer((HOST, candidate), handler)  # type: ignore[arg-type]
        except OSError as exc:
            if exc.errno not in (errno.EADDRINUSE, errno.EACCES):
                raise
            print(f"port {candidate} is in use, trying {candidate + 1}", flush=True)
    raise SystemExit(f"no free port between {port} and {port + 9}")


def serve(port: int = PORT, open_browser: bool = False, sector: str = "auto") -> None:
    """Serve ``data/<sector>`` on the loopback interface until interrupted.

    Args:
        port: TCP port to bind.
        open_browser: Open the dashboard URL in the default browser once the server is bound.
        sector: Directory under ``data/`` to serve; decides the page announced.

    Raises:
        SystemExit: If the directory or the dashboard page is missing.
    """
    root, page = REPO / "data" / sector, SECTOR_PAGES[sector]
    if not root.is_dir():
        raise SystemExit(f"directory not found: {root}")
    if not (root / page).exists():
        raise SystemExit(f"{page} not found: run the sector pipeline first")
    handler = functools.partial(NoStoreHandler, directory=str(root))
    with bind(handler, port) as httpd:
        port = httpd.server_address[1]
        print(f"serving {root.relative_to(REPO)} at http://{HOST}:{port}/{page}", flush=True)
        print("Ctrl-C to stop", flush=True)
        if open_browser:
            threading.Timer(0.5, webbrowser.open, [f"http://{HOST}:{port}/{page}"]).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


def main() -> None:
    """Parse the command line and serve."""
    args = parse_args()
    serve(args.port, args.open, args.root)


if __name__ == "__main__":
    main()
