"""Download the companies' published worldwide sales, the denominator for global coverage.

    toyota   Toyota Motor Corporation, "Sales, Production and Export Results", detailed data
             workbook. Sheet ``Sales`` carries worldwide sales for Toyota (including Lexus),
             Daihatsu, Hino and the group, one column per calendar year; sheet
             ``Sales of Lexus`` carries Lexus on its own; ``Sales by country・region`` gives
             23 named countries. Downloaded as published (xlsx).
    nissan   Nissan Motor Corporation, monthly "Production, sales and exports results". The
             release is a web page, so its tables are written out as CSV exactly as printed,
             with the release URL recorded beside the file.

Hyundai publishes no worldwide-total file: its investor-relations page offers exactly five
workbooks (sales by model, global plant sales, export by region, US retail, Europe retail), so
its global figure is derived in extract_global_sales.py from the files it does publish. Kia's
worldwide figure for the half year in scope comes from the retail workbook already held.

Run from the repository root:  .venv/bin/python script/auto/sales/fetch_global_sales.py
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
}
TOYOTA_PAGE = "https://global.toyota/en/company/profile/production-sales-figures/202512.html"
TOYOTA_FILE = (
    "https://global.toyota/pages/global_toyota/company/profile/production-sales-figures/"
    "production_sales_figures_en_202512.xlsx"
)
TOYOTA_DEST = RAW / "toyota_global_sales_202512.xlsx"
NISSAN_PAGE = "https://global.nissannews.com/en/releases/nissan-production-sales-exports-dec-2025"
NISSAN_DEST = RAW / "nissan_global_sales_2025.csv"
NISSAN_FIELDS = ["table", "row", "label", "month", "units_cy", "units_cy_prior"]
CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
TABLE = re.compile(r"<table[^>]*>(.*?)</table>", re.S)


def get(url: str, context: ssl.SSLContext) -> bytes:
    """One request with a browser user agent."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=180) as r:
        return r.read()


def cell_text(fragment: str) -> str:
    """Tag-free, entity-decoded cell text."""
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\xa0", " ").strip()


def number(value: str) -> int | None:
    """A published count, or None for a percentage or a blank."""
    text = value.replace(",", "").strip()
    if not text or "%" in text or text.startswith(("+", "-", "*")):
        return None
    try:
        return int(text)
    except ValueError:
        return None


def nissan_rows(page: str) -> list[dict[str, object]]:
    """Nissan's release tables: the label and the counts, whatever column they sit in.

    The release merges cells, so the label is the first non-empty cell of a row and the counts
    are the cells that parse as a number: the month, then the calendar year, then the year
    before it.
    """
    out: list[dict[str, object]] = []
    for ti, table in enumerate(TABLE.findall(page)):
        for ri, tr in enumerate(ROW.findall(table)):
            cells = [cell_text(c) for c in CELL.findall(tr)]
            if not any(cells):
                continue
            labels = [c for c in cells if c and number(c) is None and "%" not in c]
            counts = [number(c) for c in cells if number(c) is not None]
            if not labels or not counts:
                continue
            out.append(
                {
                    "table": ti,
                    "row": ri,
                    "label": labels[0],
                    "month": counts[0],
                    "units_cy": counts[1] if len(counts) > 1 else "",
                    "units_cy_prior": counts[2] if len(counts) > 2 else "",
                }
            )
    return out


def main() -> None:
    """Fetch both publishers' worldwide figures."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()

    if TOYOTA_DEST.exists() and not args.force:
        toyota_status = "kept"
    else:
        TOYOTA_DEST.write_bytes(get(TOYOTA_FILE, context))
        toyota_status = "fetched"
    upsert_source(
        {
            "source_id": "toyota_global_sales",
            "publisher": "Toyota Motor Corporation",
            "title": (
                "Sales, Production and Export Results, detailed data workbook: worldwide sales "
                "for Toyota (including Lexus), Daihatsu, Hino and the group by calendar year, "
                "Lexus on its own sheet, and sales for 23 named countries"
            ),
            "url": TOYOTA_PAGE,
            "how_obtained": (
                f"downloaded from {TOYOTA_FILE} by script/auto/sales/fetch_global_sales.py"
            ),
            "accessed_date": accessed,
            "license": "company investor publication; no explicit reuse licence stated",
            "used_by": "extract_global_sales.py",
        }
    )
    d1 = upsert_raw_file(
        "sales",
        TOYOTA_DEST,
        "toyota_global_sales",
        "production_sales_figures_en_202512.xlsx",
        f"December 2025 edition, calendar years 2016 onward; {toyota_status} {accessed} "
        f"from {TOYOTA_FILE}",
    )
    print(f"toyota: {toyota_status} {TOYOTA_DEST.name} {TOYOTA_DEST.stat().st_size:,} B {d1[:12]}")

    if NISSAN_DEST.exists() and not args.force:
        nissan_status = "kept"
    else:
        rows = nissan_rows(get(NISSAN_PAGE, context).decode("utf-8", "replace"))
        if not rows:
            raise SystemExit(f"{NISSAN_PAGE}: no tables found")
        with NISSAN_DEST.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=NISSAN_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        nissan_status = "fetched"
    upsert_source(
        {
            "source_id": "nissan_global_sales",
            "publisher": "Nissan Motor Corporation",
            "title": (
                "Production, sales and exports results for December and calendar year 2025: "
                "global sales and sales for Japan, the US, Canada, Mexico, Europe, China and "
                "the rest, with the prior year beside each"
            ),
            "url": NISSAN_PAGE,
            "how_obtained": (
                "the release is a web page, so its tables were written to CSV by "
                "script/auto/sales/fetch_global_sales.py"
            ),
            "accessed_date": accessed,
            "license": "company press release; redistribution of the table is a licence question",
            "used_by": "extract_global_sales.py",
        }
    )
    d2 = upsert_raw_file(
        "sales",
        NISSAN_DEST,
        "nissan_global_sales",
        "tables of the December 2025 global results release",
        f"calendar years 2025 and 2024; {nissan_status} {accessed} from {NISSAN_PAGE}",
    )
    print(f"nissan: {nissan_status} {NISSAN_DEST.name} {NISSAN_DEST.stat().st_size:,} B {d2[:12]}")


if __name__ == "__main__":
    main()
