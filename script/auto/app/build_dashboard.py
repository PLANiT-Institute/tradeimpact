"""Build the one page for the automotive case: data, database and results over one file.

Output  data/auto/database/dashboard.html

There used to be four pages and two servers — a workbench, a catalogue, a dashboard and a front
door, one of them needing a write endpoint to accept a correction. They read the same database
and said overlapping things about it, so they are one page now, sitting beside the database file
it reads, with nothing behind it:

    데이터 입력 · Data       one grid per dataset x sale year: every value, the year it was
                            observed, how far behind the sale year it is, its status
                            (current / carried forward / stale) and its source. Click a value to
                            queue a correction; the queue downloads as overrides.csv, which
                            model/apply_overrides.py applies on the next run.
    데이터 분석 · Database   the catalogue (overview, structure, tables, sources) and the explorer
                            (lineage, browse, pivot, read-only SQL) over every table in the file.
    결과 분석 · Results      the impact by company and market with the sale year and the benchmark
                            as first-class controls, the reference each result is measured
                            against, the year-by-year and lifetime pivots, and the map.

The page carries no figure of its own: it opens the SQLite file beside it and computes everything
on screen at read time. Served from any static directory it reads that sibling file; opened by
double-click it asks the reader for a file, because every browser blocks the sibling read. Any
other SQLite file can be opened the same way — one that carries the project's catalogue tables is
described from them, one that does not is described from its own structure.

This module also holds the CDN pins for every page in the repository (the report, the deck and
the power report import them), so a library upgrade is one edit.

Run from the repository root:  .venv/bin/python script/auto/app/build_dashboard.py
Then open data/auto/database/dashboard.html, or serve the directory:
    .venv/bin/python script/auto/serve_dashboard.py --open
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
OUT = REPO / "data" / "auto" / "database" / "dashboard.html"
TEMPLATE_FILE = Path(__file__).with_name("dashboard_template.html")
TITLE = "Trade Impact — automotive"

#: The static server that serves data/<sector> for the report pages; the dashboard needs none.
SERVE_PORT = 8765

#: sql.js pinned on cdnjs; ``locateFile`` resolves sql-wasm.wasm inside the same directory.
SQLJS_VERSION = "1.10.3"
SQLJS_DIR = f"https://cdnjs.cloudflare.com/ajax/libs/sql.js/{SQLJS_VERSION}/"
D3_SRC = "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"
D3_SRI = "sha384-CjloA8y00+1SDAUkjs099PVfnY2KmDC2BZnws9kh8D/lX1s46w6EPhpXdqMfjK6i"
TOPOJSON_SRC = "https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"
TOPOJSON_SRI = "sha384-9dCJK6nh7skY14HrcvlLYlFga9/MehJjL9ONWRflmiXNRuf8p2jiF4Y5PR881PTq"
SQLJS_SRI = (
    "sha512-+6Q7hv5pGUBXOuHWw8OdQx3ac7DzM3oJhYqz7SHDku0yl9EBd"
    "MqegoPed4GsHRoNF/VQYK2LTYewAIEBrEf/3w=="
)

#: Pipeline stage order; ``registry`` is the provenance pair and sits outside the flow.
STAGES = ("raw", "method", "processed", "output")

#: Dataset (data type) display order in the lineage view.
DATASET_ORDER = (
    "sales",
    "vehicle_technology",
    "vehicle_usage",
    "country_emissions",
    "emission_targets",
    "model",
    "auto",
)

#: Model step order (whitepaper steps 3, 4, 5), matched on output table-name prefixes.
MODEL_STEPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("3a cohorts", ("cohorts",)),
    ("3 reference", ("destination_parameters", "reference_trajectories")),
    (
        "4 impact",
        ("ti_by_model", "ti_annual_by_model", "ti_annual", "ti_withheld", "ti_exclusions"),
    ),
    ("4b crossover and sensitivity", ("ti_crossover", "ti_sensitivity")),
    (
        "5 aggregates and data quality",
        (
            "ti_country",
            "ti_powertrain",
            "ti_company",
            "ti_annual_country",
            "ti_annual_powertrain",
            "ti_data",
            "ti_coverage",
            "ti_source",
            "ti_global",
        ),
    ),
)

#: The lifetime pivot: results by vehicle model and powertrain (the company roll-up is one click
#: away in the same pivot by removing the row fields).
DEFAULT_PIVOT = {
    "agg": "sum",
    "cols": "scenario",
    "rows": ["market", "company", "powertrain", "model"],
    "table": "ti_by_model",
    "vals": ["ti_tco2e"],
}

#: The year pivot: one column per calendar year of the operating life, and three value rows per
#: company — what the scenario benchmark would have emitted, what the products emit, and the
#: difference that is the annual TI.
YEARLY_PIVOT = {
    "agg": "sum",
    "cols": "calendar_year",
    "rows": ["market", "company", "cohort_year", "scenario"],
    "table": "ti_annual",
    "vals": ["e_ref_tco2e", "e_prod_tco2e", "ti_tco2e"],
}

#: Any ``__NAME__`` token left in the rendered page is an unfilled placeholder.
PLACEHOLDER = re.compile(r"__[A-Z0-9_]+__")


def js(value: Any) -> str:
    """Serialise a build-time constant as a JavaScript literal.

    Keys are sorted and ``<`` is escaped, so the literal is deterministic between runs and can
    never close the surrounding ``<script>`` element early.

    Args:
        value: Any JSON-serialisable constant.

    Returns:
        The JSON text to paste into the page.
    """
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return blob.replace("<", "\\u003c")


def build() -> str:
    """Fill the template's constants; nothing numeric is computed at build time.

    Returns:
        The complete HTML document.

    Raises:
        SystemExit: If a placeholder is left unfilled.
    """
    html = TEMPLATE_FILE.read_text(encoding="utf-8")
    for token, value in {
        "__TITLE__": TITLE,
        "__SQLJS_DIR__": SQLJS_DIR,
        "__SQLJS_SRI__": SQLJS_SRI,
        "__SQLJS_VERSION__": SQLJS_VERSION,
        "__D3_SRC__": D3_SRC,
        "__D3_SRI__": D3_SRI,
        "__TOPOJSON_SRC__": TOPOJSON_SRC,
        "__TOPOJSON_SRI__": TOPOJSON_SRI,
        "__DB_FILE__": DB.name,
        "__DEFAULT_PIVOT__": js(DEFAULT_PIVOT),
        "__YEARLY_PIVOT__": js(YEARLY_PIVOT),
        "__STAGES__": js(list(STAGES)),
        "__DATASET_ORDER__": js(list(DATASET_ORDER)),
        "__MODEL_STEPS__": js([[label, list(prefixes)] for label, prefixes in MODEL_STEPS]),
    }.items():
        html = html.replace(token, value)
    left = PLACEHOLDER.search(html)
    if left is not None:
        raise SystemExit(f"unfilled placeholder in the template: {left.group(0)}")
    return html


def manifest_rows(db: Path) -> int:
    """Count the rows of the database's ``tables`` manifest.

    The page reads that manifest itself; the build only checks it is there, so a page is never
    written against a database the reader cannot navigate.

    Args:
        db: Path to the automotive SQLite database.

    Returns:
        Number of rows in the ``tables`` manifest.

    Raises:
        SystemExit: If the database has no ``tables`` manifest or the manifest is empty.
    """
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        present = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'tables'"
        ).fetchone()
        if present is None:
            raise SystemExit(f"{db} has no 'tables' manifest: run build_database.py first")
        rows: int = conn.execute('SELECT COUNT(*) FROM "tables"').fetchone()[0]
    finally:
        conn.close()
    if not rows:
        raise SystemExit(f"{db} lists no tables: is build_database.py still running?")
    return rows


def main() -> None:
    """Write the page beside the database it reads.

    Raises:
        SystemExit: If the database is missing or carries no ``tables`` manifest.
    """
    if not DB.exists():
        raise SystemExit(f"database not found: {DB}")
    rows = manifest_rows(DB)
    OUT.write_text(build(), encoding="utf-8")
    print(
        f"{DB.relative_to(REPO)}: {DB.stat().st_size / 1e6:.2f} MB, {rows} tables "
        "(read by the page at open, not embedded)"
    )
    print(f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1024:,.0f} KB; open it, or serve with ")
    print(f"  .venv/bin/python script/auto/serve_dashboard.py --open  -> port {SERVE_PORT}")


if __name__ == "__main__":
    main()
