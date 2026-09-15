"""Open any SQLite file in the data catalogue, in a browser, with one command.

The catalogue page normally sits beside the automotive database and reads it. This serves the
same page against *any* SQLite file — the power database, an export from somewhere else, a
colleague's file — by putting the chosen file at one fixed URL the page always asks for:

    /            the catalogue page
    /db.sqlite   the file being reviewed, whatever and wherever it is

A file that carries the project's own catalogue tables (``schema_tables`` and the rest) is
described from them. A file that does not — most files — is described on the fly: the page reads
its ``sqlite_master``, counts its rows, infers its joins from declared foreign keys and from
columns that carry another table's primary key, and computes a column's statistics when that
table is opened.

With no argument it opens the automotive database. Pass a path to open something else, or use
``--list`` to see the SQLite files in the repository.

    .venv/bin/python script/dbreview.py
    .venv/bin/python script/dbreview.py data/power/database/tradeimpact_power.sqlite
    .venv/bin/python script/dbreview.py ~/somewhere/else/EXPORT.sqlite

The server is loopback only, read only, and serves exactly two things: the page and the file.
Stop it with Ctrl-C.
"""

from __future__ import annotations

import argparse
import errno
import http.server
import re
import socketserver
import threading
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAGE = REPO / "data" / "auto" / "catalogue.html"
DEFAULT_DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
HOST = "127.0.0.1"
PORT = 8780
#: The one URL the page asks for, whatever file is behind it.
DB_ROUTE = "/db.sqlite"
CHUNK = 1 << 20


def find_databases() -> list[Path]:
    """Every SQLite file in the repository's data directories, largest last."""
    found = sorted((REPO / "data").rglob("*.sqlite"))
    return sorted(found, key=lambda p: p.stat().st_size)


def page_html(db: Path) -> bytes:
    """The catalogue page, pointed at the fixed database route and told which file it is."""
    html = PAGE.read_text(encoding="utf-8")
    # The page resolves its database from three constants declared on one line; the two route
    # constants become the served route and the name becomes the file being reviewed.
    for name, value in (("DB_RELATIVE", DB_ROUTE), ("SERVED_DB", DB_ROUTE), ("DB_FILE", db.name)):
        html, n = re.subn(rf"\b{name}='[^']*'", f"{name}='{value}'", html, count=1)
        if n != 1:
            raise SystemExit(f"catalogue.html: could not find the {name} constant to rewrite")
    return html.encode("utf-8")


class Handler(http.server.BaseHTTPRequestHandler):
    """Serves the catalogue page and the one database being reviewed. Nothing else."""

    protocol_version = "HTTP/1.1"
    db: Path = DEFAULT_DB

    def _head(self, status: int, ctype: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        """Serve the page at / and the database at /db.sqlite."""
        path = self.path.split("?")[0]
        if path in ("/", "/catalogue.html", "/index.html"):
            body = page_html(self.db)
            self._head(200, "text/html; charset=utf-8", len(body))
            self.wfile.write(body)
            return
        if path == DB_ROUTE:
            size = self.db.stat().st_size
            self._head(200, "application/vnd.sqlite3", size)
            with self.db.open("rb") as f:
                while chunk := f.read(CHUNK):
                    self.wfile.write(chunk)
            return
        self.send_error(404, "this server serves the catalogue page and one database")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """One terse line per request."""
        print(f"  {format % args}")


def bind(port: int) -> socketserver.TCPServer:
    """Bind the first free port at or after ``port``."""
    for candidate in range(port, port + 10):
        try:
            server = socketserver.ThreadingTCPServer((HOST, candidate), Handler)
        except OSError as exc:
            if exc.errno not in (errno.EADDRINUSE, errno.EACCES):
                raise
            print(f"port {candidate} is in use, trying {candidate + 1}")
            continue
        server.allow_reuse_address = True
        return server
    raise SystemExit(f"no free port between {port} and {port + 9}")


def main() -> None:
    """Parse the command line, serve the chosen database and open a browser at it."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("database", nargs="?", help="SQLite file to review (default: automotive)")
    parser.add_argument("--port", type=int, default=PORT, help=f"TCP port (default {PORT})")
    parser.add_argument("--list", action="store_true", help="list the repository's SQLite files")
    parser.add_argument("--no-open", action="store_true", help="do not open a browser")
    args = parser.parse_args()

    if args.list:
        for path in find_databases():
            print(f"  {path.stat().st_size / 1e6:8.1f} MB  {path.relative_to(REPO)}")
        return

    db = Path(args.database).expanduser().resolve() if args.database else DEFAULT_DB
    if not db.exists():
        raise SystemExit(f"not found: {db}")
    if not PAGE.exists():
        raise SystemExit("catalogue.html not found: run script/auto/app/build_catalogue.py first")

    Handler.db = db
    with bind(args.port) as server:
        port = server.server_address[1]
        url = f"http://{HOST}:{port}/"
        print(f"reviewing {db}")
        print(f"  {db.stat().st_size / 1e6:,.1f} MB  ->  {url}")
        print("Ctrl-C to stop")
        if not args.no_open:
            threading.Timer(0.6, webbrowser.open, [url]).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
