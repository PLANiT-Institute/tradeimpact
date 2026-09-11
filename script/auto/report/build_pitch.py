"""Build the five-slide pitch deck for the automotive result, as a page that reads the database.

Output  data/auto/report/ti_automotive_pitch.html

The full report (``build_report.py``) is for a reader who wants to interrogate the analysis. This
is for the ten minutes before that: five slides, one idea each, ending on what the result does
not say. It is the same kind of artefact as the report and obeys the same rule — the page carries
no figure of its own. It opens ``tradeimpact_auto.sqlite`` and computes every number on screen at
read time, so the deck cannot drift from the tables under it.

    1  The question      what TI measures, and the one comparison that carries the pitch
    2  By company        the four companies under both benchmarks, per vehicle and in total
    3  Where it comes from   the powertrain decomposition, and the hybrid swing
    4  By destination    the same cars scored against four different national trajectories
    5  What it does not say  coverage, the pro-rata benchmark, and what moves the answer

Libraries: sql.js and d3 from cdnjs, the dashboard's pins and integrity hashes.

Run from the repository root:  .venv/bin/python script/auto/report/build_pitch.py
Then:  .venv/bin/python script/auto/serve_dashboard.py  and open
       http://127.0.0.1:8765/report/ti_automotive_pitch.html
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
)

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "data" / "auto" / "report" / "ti_automotive_pitch.html"
DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
#: The database relative to the page when both are served from data/auto.
DB_RELATIVE = f"../{DB.parent.name}/{DB.name}"
SERVED_DB = f"http://127.0.0.1:{SERVE_PORT}/{DB.parent.name}/{DB.name}"
TITLE = "Trade Impact — the automotive result in five slides"
TEMPLATE_FILE = Path(__file__).with_name("pitch_template.html")


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
        "__SERVE_URL__": f"http://127.0.0.1:{SERVE_PORT}/{OUT.parent.name}/{OUT.name}",
    }.items():
        html = html.replace(key, value)
    leftover = [k for k in ("__TITLE__", "__SQLJS_", "__D3_", "__DB_", "__SERVE") if k in html]
    if leftover:
        raise SystemExit(f"unfilled template keys: {leftover}")
    return html


def main() -> None:
    """Write the deck."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(
        f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1024:,.0f} KB; reads {DB_RELATIVE} at "
        f"open; serve with .venv/bin/python script/auto/serve_dashboard.py -> "
        f"http://127.0.0.1:{SERVE_PORT}/{OUT.parent.name}/{OUT.name}"
    )


if __name__ == "__main__":
    main()
