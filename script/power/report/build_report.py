"""Build the power case study's interactive report: a tabbed page that reads the sector database.

Output  data/power/report/ti_power_report.html

Same construction as the automotive report: the page carries no data of its own, loads sql.js,
d3 and topojson from cdnjs (pins and integrity hashes imported from the automotive dashboard
builder so the two sectors move together), opens ``data/power/database/tradeimpact_power.sqlite``
beside it and computes every sentence, tile, chart, table and map point with SQL at read time.
``template.html`` beside this script is the page; this script fills its build-time constants.

Tabs, in the order the analysis is built: companies and their projects; the map of generating
units by company; coverage and roles; destination benchmarks (grid, S1/S2, the NDC anchor);
other inputs; annual impact; total impact by company and role; sources.

Run from the repository root:  .venv/bin/python script/power/report/build_report.py
Then:  .venv/bin/python script/auto/serve_dashboard.py --root power --port 8766  and open
       http://127.0.0.1:8766/report/ti_power_report.html
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "auto" / "model"))
from build_dashboard import (  # noqa: E402
    D3_SRC,
    D3_SRI,
    SQLJS_DIR,
    SQLJS_SRI,
    SQLJS_VERSION,
    TOPOJSON_SRC,
    TOPOJSON_SRI,
)

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "data" / "power" / "report" / "ti_power_report.html"
DB = REPO / "data" / "power" / "database" / "tradeimpact_power.sqlite"
DB_RELATIVE = f"../{DB.parent.name}/{DB.name}"
SERVE_PORT = 8766
SERVED_DB = f"http://127.0.0.1:{SERVE_PORT}/{DB.parent.name}/{DB.name}"
TITLE = "Trade Impact of the power trade"
TEMPLATE_FILE = Path(__file__).with_name("template.html")
SERVE_CMD = "script/auto/serve_dashboard.py --root power --port 8766"


def build() -> str:
    """Fill the template's constants; nothing else is computed at build time."""
    html = TEMPLATE_FILE.read_text(encoding="utf-8")
    for key, value in {
        "__TITLE__": TITLE,
        "__SQLJS_DIR__": SQLJS_DIR,
        "__SQLJS_SRI__": SQLJS_SRI,
        "__SQLJS_VERSION__": SQLJS_VERSION,
        "__D3_SRC__": D3_SRC,
        "__D3_SRI__": D3_SRI,
        "__TOPOJSON_SRC__": TOPOJSON_SRC,
        "__TOPOJSON_SRI__": TOPOJSON_SRI,
        "__DB_RELATIVE__": DB_RELATIVE,
        "__SERVED_DB__": SERVED_DB,
        "__DB_FILE__": DB.name,
        "__SERVE_PORT__": str(SERVE_PORT),
        "__SERVE_CMD__": f".venv/bin/python {SERVE_CMD}",
        "__SERVE_URL__": f"http://127.0.0.1:{SERVE_PORT}/{OUT.parent.name}/{OUT.name}",
    }.items():
        html = html.replace(key, value)
    markers = ("__TITLE__", "__SQLJS_", "__D3_", "__TOPOJSON_", "__DB_", "__SERVE")
    leftover = [k for k in markers if k in html]
    if leftover:
        raise SystemExit(f"unfilled template keys: {leftover}")
    return html


def main() -> None:
    """Write the page."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(
        f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1024:,.0f} KB; reads {DB_RELATIVE} at "
        f"open; serve with .venv/bin/python {SERVE_CMD} -> "
        f"http://127.0.0.1:{SERVE_PORT}/{OUT.parent.name}/{OUT.name}"
    )


if __name__ == "__main__":
    main()
