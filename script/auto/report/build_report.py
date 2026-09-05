"""Build the Trade Impact analysis report as an interactive, tabbed page that reads the database.

Output  data/auto/report/ti_automotive_report.html

The page carries no data of its own. It loads sql.js (WebAssembly, version-pinned on cdnjs with
subresource integrity), opens ``data/auto/database/tradeimpact_auto.sqlite`` — the sibling
directory when served, the loopback server or a file the reader picks when opened from disk —
and computes every figure in every sentence, table and chart at read time with SQL.

The story runs left to right across the main tabs, in the order the analysis is built:

    1 Sales             what each company sold, into which market, of what kind
    2 Coverage          which of those units carry a result, and why the rest do not
    3 Benchmarks        each destination's emissions, fleet and the two scenario pathways
    4 Other inputs      distance, lifetime, product intensities, real-world correction
    5 Annual impact     the year-by-year comparison, company x market
    6 Total impact      the lifetime result per cohort, and what moves it
    7 Sources           the tables behind the page and where every input came from

Each main tab opens sub-tabs (one per company, per market, or per view). A filter bar (scenario,
company, market, cohort year) redraws the tab in view; the story text on each tab is stated on the
whole result set so the argument stays whole while the reader explores.

This script and ``template.html`` beside it are the report's source the way an extractor is a
CSV's source: the published HTML is regenerated from them and never edited by hand. Nothing
numeric is written into the file at build time, and a test asserts that.

Libraries: sql.js 1.10.3, d3 7.9.0 and topojson 3.0.2 from cdnjs, the same pins and integrity
hashes as the dashboard. The map geometry is a row in the database (``map_geometry``).

Run from the repository root:  .venv/bin/python script/auto/report/build_report.py
Then:  .venv/bin/python script/auto/serve_dashboard.py  and open
       http://127.0.0.1:8765/report/ti_automotive_report.html
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from build_dashboard import (  # noqa: E402
    D3_SRC,
    D3_SRI,
    SERVE_PORT,
    SQLJS_DIR,
    SQLJS_SRI,
    SQLJS_VERSION,
    TOPOJSON_SRC,
    TOPOJSON_SRI,
)

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "data" / "auto" / "report" / "ti_automotive_report.html"
DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
#: The database relative to the page when both are served from data/auto.
DB_RELATIVE = f"../{DB.parent.name}/{DB.name}"
SERVED_DB = f"http://127.0.0.1:{SERVE_PORT}/{DB.parent.name}/{DB.name}"
TITLE = "Trade Impact of the automotive trade"

#: The page itself: markup, styles and the reader script, with build-time placeholders.
TEMPLATE_FILE = Path(__file__).with_name("template.html")


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
        "__SERVE_CMD__": ".venv/bin/python script/auto/serve_dashboard.py",
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
        f"open; serve with .venv/bin/python script/auto/serve_dashboard.py -> "
        f"http://127.0.0.1:{SERVE_PORT}/{OUT.parent.name}/{OUT.name}"
    )


if __name__ == "__main__":
    main()
