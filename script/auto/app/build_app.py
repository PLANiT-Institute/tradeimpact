"""Build the one workbench for the automotive case, a page that reads the database.

Output  data/auto/app.html

Three modes, one file, and the sale year runs through all of them because it is the axis the
data actually turns on: a 2024 cohort is measured against what its destinations had published by
2024, a 2025 cohort against 2025, and the two are different numbers.

    Data input     one grid per dataset x sale year: every value, the year it was observed, how
                   far behind the sale year it is, its status (current / carried forward / stale)
                   and its source. This is where you see what each year actually received, and
                   queue a correction.
    Database       every table in the file, grouped by dataset, browsable like a workbook.
    Results        the impact by company and country, with the sale year AND the scenario as
                   first-class controls, and the reference path each result is measured against
                   drawn out so it is never a mystery which benchmark, of which vintage, applied.

Like every other page in this repository the file carries no figure of its own: it opens
tradeimpact_auto.sqlite and computes everything on screen at read time. Edits do not touch the
raw sources — they are queued through the write server into an auditable edits table, each with a
mandatory source and note, for the pipeline to ingest.

Libraries: sql.js and d3 from cdnjs, the dashboard's pins and integrity hashes.

Run from the repository root:  .venv/bin/python script/auto/app/build_app.py
Then:  .venv/bin/python script/auto/app/serve_app.py  and open http://127.0.0.1:8770/app.html
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from build_dashboard import (  # noqa: E402
    D3_SRC,
    D3_SRI,
    SQLJS_DIR,
    SQLJS_SRI,
    SQLJS_VERSION,
)

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "data" / "auto" / "app.html"
DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
DB_RELATIVE = f"{DB.parent.name}/{DB.name}"
SERVE_PORT = 8770
SERVED_DB = f"http://127.0.0.1:{SERVE_PORT}/{DB.parent.name}/{DB.name}"
TITLE = "Trade Impact — automotive workbench"
TEMPLATE_FILE = Path(__file__).with_name("app_template.html")


def build() -> str:
    """Fill the template's constants; nothing numeric is computed at build time."""
    html = TEMPLATE_FILE.read_text(encoding="utf-8")
    for key, value in {
        "__TITLE__": TITLE,
        "__SQLJS_DIR__": SQLJS_DIR,
        "__SQLJS_SRI__": SQLJS_SRI,
        "__SQLJS_VERSION__": SQLJS_VERSION,
        "__D3_SRC__": D3_SRC,
        "__D3_SRI__": D3_SRI,
        "__DB_RELATIVE__": DB_RELATIVE,
        "__SERVED_DB__": SERVED_DB,
        "__DB_FILE__": DB.name,
        "__SERVE_PORT__": str(SERVE_PORT),
        "__SERVE_URL__": f"http://127.0.0.1:{SERVE_PORT}/{OUT.name}",
    }.items():
        html = html.replace(key, value)
    leftover = [k for k in ("__TITLE__", "__SQLJS_", "__D3_", "__DB_", "__SERVE") if k in html]
    if leftover:
        raise SystemExit(f"unfilled template keys: {leftover}")
    return html


def main() -> None:
    """Write the workbench page."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(
        f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1024:,.0f} KB; reads {DB_RELATIVE} at "
        f"open; serve with .venv/bin/python script/auto/app/serve_app.py -> "
        f"http://127.0.0.1:{SERVE_PORT}/{OUT.name}"
    )


if __name__ == "__main__":
    main()
