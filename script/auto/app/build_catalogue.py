"""Build the Trade data catalogue: the whole database on one page, structure and health.

Output  data/auto/catalogue.html

A hundred and fifteen tables and no map of them. This page is that map, in four views:

    Overview    every dataset as a card — how many tables, how many rows, what years it covers,
                its tier mix and its health, so a bad patch is visible without opening anything
    Structure   the join graph drawn as a diagram, laid out left to right by pipeline layer
                (input, catalogue, processed, result); a box is a table family, a line is a real
                join, and clicking either opens the detail
    Tables      all 115, filterable by dataset, layer and health, with rows, columns, data years,
                tier mix and licence
    Sources     the provider and licence catalogue, and what each licence permits

Clicking any table anywhere opens its detail: description, grain, every column with its type,
role, blank share, distinct count, range and an example, the relations in and out, the licence it
inherits and the health verdict with its reason.

Like every other page here the file carries no figure of its own. It opens
tradeimpact_auto.sqlite and computes the catalogue at read time, so it cannot describe a database
that no longer exists.

Run from the repository root:  .venv/bin/python script/auto/app/build_catalogue.py
Then:  .venv/bin/python script/auto/app/serve_app.py  and open
       http://127.0.0.1:8770/catalogue.html
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from build_dashboard import (  # noqa: E402
    SQLJS_DIR,
    SQLJS_SRI,
    SQLJS_VERSION,
)

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "data" / "auto" / "catalogue.html"
DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
DB_RELATIVE = f"{DB.parent.name}/{DB.name}"
SERVE_PORT = 8770
SERVED_DB = f"http://127.0.0.1:{SERVE_PORT}/{DB.parent.name}/{DB.name}"
TITLE = "Trade — data catalogue"
TEMPLATE_FILE = Path(__file__).with_name("catalogue_template.html")


def build() -> str:
    """Fill the template's constants; nothing numeric is computed at build time."""
    html = TEMPLATE_FILE.read_text(encoding="utf-8")
    for key, value in {
        "__TITLE__": TITLE,
        "__SQLJS_DIR__": SQLJS_DIR,
        "__SQLJS_SRI__": SQLJS_SRI,
        "__SQLJS_VERSION__": SQLJS_VERSION,
        "__DB_RELATIVE__": DB_RELATIVE,
        "__SERVED_DB__": SERVED_DB,
        "__DB_FILE__": DB.name,
        "__SERVE_PORT__": str(SERVE_PORT),
        "__SERVE_URL__": f"http://127.0.0.1:{SERVE_PORT}/{OUT.name}",
    }.items():
        html = html.replace(key, value)
    leftover = [k for k in ("__TITLE__", "__SQLJS_", "__DB_", "__SERVE") if k in html]
    if leftover:
        raise SystemExit(f"unfilled template keys: {leftover}")
    return html


def main() -> None:
    """Write the catalogue page."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(
        f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1024:,.0f} KB; reads {DB_RELATIVE} at "
        f"open; serve with .venv/bin/python script/auto/app/serve_app.py -> "
        f"http://127.0.0.1:{SERVE_PORT}/{OUT.name}"
    )


if __name__ == "__main__":
    main()
