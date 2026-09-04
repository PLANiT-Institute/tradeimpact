"""Download Kia America's sales-by-model workbook for December of a year (full-year YTD column).

Source of truth: Kia America Newsroom > Sales (https://www.kiamedia.com/us/en/sales). The page
offers an xlsx export per month:

    https://www.kiamedia.com/us/en/sales/salesbymonthexport?month=12&year=YYYY&yeartocompare=YYYY-1

The sheet SalesByMonth carries one row per model with the month and the year-to-date volume for
both years; the December export therefore holds two full calendar years. Volumes are total US
sales as reported by Kia America (retail and fleet are not split in the table). A Referer header
is required. Files land in data/auto/sales/raw/kia_america_<year>_sales_by_month.xlsx.

Run from the repository root:  .venv/bin/python script/auto/sales/fetch_kia_america.py 2024 2025
"""

from __future__ import annotations

import argparse
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
SOURCE_ID = "kia_america_sales_by_month"
PAGE = "https://www.kiamedia.com/us/en/sales"
EXPORT = PAGE + "/salesbymonthexport?month=12&year={year}&yeartocompare={prev}"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)", "Referer": PAGE}


def main() -> None:
    """Fetch the December export for each requested year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "Kia America (kiamedia.com newsroom)",
            "title": (
                "Sales by month export: US sales by model, month and year-to-date for the "
                "selected year and the comparison year (total volume; retail and fleet not split)"
            ),
            "url": PAGE,
            "how_obtained": (
                "api: xlsx endpoint salesbymonthexport?month=12&year=YYYY&yeartocompare=YYYY-1 "
                "(Referer required); downloaded by script/auto/sales/fetch_kia_america.py"
            ),
            "accessed_date": accessed,
            "license": "press information; kiamedia.com terms of use",
            "used_by": "extract_kia_america.py",
        }
    )
    for year in args.years:
        url = EXPORT.format(year=year, prev=year - 1)
        dest = RAW / f"kia_america_{year}_sales_by_month.xlsx"
        if dest.exists() and not args.force:
            status = "kept"
        else:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=context, timeout=60) as r:
                data = r.read()
            if not data.startswith(b"PK"):
                raise SystemExit(f"{url}: response is not an xlsx ({data[:60]!r})")
            dest.write_bytes(data)
            status = "fetched"
        digest = upsert_raw_file(
            "sales",
            dest,
            SOURCE_ID,
            f"salesbymonthexport month=12 year={year} yeartocompare={year - 1}",
            f"December {year} export: {year} and {year - 1} full-year YTD; "
            f"{status} {accessed} from {url}",
        )
        print(f"{year}: {status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
