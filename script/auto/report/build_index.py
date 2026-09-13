"""Build the front door for the automotive result, as a page that reads the database.

Output  data/auto/index.html

Three artefacts already existed and none of them knew about the others: a dashboard for someone
who wants to filter, a report for someone who wants to interrogate, and a five-slide deck for the
ten minutes before either. All three start at full depth. This is the page in front of them —
what Trade Impact measures, what the current result says, what it can and cannot be used for,
and where every other artefact lives.

It is organised by use rather than by pipeline stage, because a reader arrives with a question
and not with a data flow. And it obeys the same rule as the report and the deck: the page carries
no figure of its own. It opens ``tradeimpact_auto.sqlite`` and computes everything on screen at
read time, so the front door can never describe a result the tables no longer hold.

Library: sql.js from cdnjs, the dashboard's pin and integrity hash. No chart library: this page
has no charts, on purpose — the artefacts it points at do.

Run from the repository root:  .venv/bin/python script/auto/report/build_index.py
Then:  .venv/bin/python script/auto/serve_dashboard.py  and open
       http://127.0.0.1:8765/index.html
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from build_dashboard import (  # noqa: E402
    SERVE_PORT,
    SQLJS_DIR,
    SQLJS_SRI,
    SQLJS_VERSION,
)

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "data" / "auto" / "index.html"
DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
#: The database relative to the page, which sits one level above the report and the database.
DB_RELATIVE = f"{DB.parent.name}/{DB.name}"
SERVED_DB = f"http://127.0.0.1:{SERVE_PORT}/{DB.parent.name}/{DB.name}"
TITLE = "Trade Impact — the automotive result"
TEMPLATE_FILE = Path(__file__).with_name("index_template.html")
#: The page sits at the sector root, so its links to the other artefacts lose a level.
LINK_FIXES = {
    '"../database/dashboard.html"': '"database/dashboard.html"',
    '"ti_automotive_report.html': '"report/ti_automotive_report.html',
    '"ti_automotive_pitch.html"': '"report/ti_automotive_pitch.html"',
    '"../output/method.md"': '"output/method.md"',
    '"../../../reference/': '"../../reference/',
}


def build() -> str:
    """Fill the template's constants; nothing numeric is computed at build time."""
    html = TEMPLATE_FILE.read_text(encoding="utf-8")
    for key, value in LINK_FIXES.items():
        html = html.replace(key, value)
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
    """Write the front door."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(
        f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1024:,.0f} KB; reads {DB_RELATIVE} at "
        f"open; serve with .venv/bin/python script/auto/serve_dashboard.py -> "
        f"http://127.0.0.1:{SERVE_PORT}/{OUT.name}"
    )


if __name__ == "__main__":
    main()
