"""Download Hyundai Motor Company's IR sales-results workbooks for a year.

Source of truth: Hyundai Motor Company, IR Resources > Sales Results
(https://www.hyundai.com/worldwide/en/company/ir/ir-resources/sales-results). The page is a
script shell; its own script lists the files through

    POST https://www.hyundai.com/wsvc/ww/salesPerformance.list.do   lang=en&year=YYYY

which returns one node per year with five DAM xlsx paths (the node is overwritten monthly, so
the December edition is the full calendar year and superseded editions are not retained):

    attrSalesModelValue     sales by model: Korea domestic and export, with powertrain trim codes
    attrGlobalPlantValue    global plant sales (plant-side, overseas plants)
    attrExportRegionValue   exports from Korea by destination region (plant-side)
    attrUSRetailValue       US sales by model, Hyundai + Genesis (labelled retail; brand total)
    attrEuropeRetailValue   Europe subsidiaries retail sales by model

Files land in data/auto/sales/raw/hyundai_<year>_<family>.xlsx; existing files are kept unless
--force. Every download is registered in sources.csv and raw_files.csv.

Run from the repository root:  .venv/bin/python script/auto/sales/fetch_hyundai_ir.py 2024 2025
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
SOURCE_ID = "hyundai_ir_sales_results"
PAGE = "https://www.hyundai.com/worldwide/en/company/ir/ir-resources/sales-results"
LIST_URL = "https://www.hyundai.com/wsvc/ww/salesPerformance.list.do"
HOST = "https://www.hyundai.com"
FAMILIES = {
    "attrSalesModelValue": "sales_by_model",
    "attrGlobalPlantValue": "global_plant_sales",
    "attrExportRegionValue": "export_by_region",
    "attrUSRetailValue": "us_retail_sales",
    "attrEuropeRetailValue": "eu_retail_sales",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}


def post_list(year: int, context: ssl.SSLContext) -> dict:
    """Return the sales-results node for one year."""
    body = urllib.parse.urlencode({"lang": "en", "year": year}).encode()
    req = urllib.request.Request(LIST_URL, data=body, headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=60) as r:
        payload = json.load(r)
    nodes = payload.get("data", {}).get("list", [])
    if not nodes:
        raise SystemExit(f"no sales-results node for {year}: {payload}")
    return nodes[0]


def download(url: str, dest: Path, context: ssl.SSLContext) -> None:
    """Save one DAM file."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=120) as r:
        dest.write_bytes(r.read())


def main() -> None:
    """Fetch the five workbooks for each requested year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "Hyundai Motor Company Investor Relations",
            "title": (
                "Monthly sales results workbooks: sales by model (Korea domestic and export), "
                "global plant sales, export by region, US sales by model (Hyundai and Genesis), "
                "Europe subsidiaries retail sales by model; one node per year overwritten "
                "monthly (December edition = full calendar year)"
            ),
            "url": PAGE,
            "how_obtained": (
                f"api: POST {LIST_URL} (lang=en&year=YYYY) lists the five xlsx paths; "
                "downloaded by script/auto/sales/fetch_hyundai_ir.py"
            ),
            "accessed_date": accessed,
            "license": "company IR publication; no explicit reuse licence stated",
            "used_by": (
                "extract_hyundai_ir.py, extract_hyundai_us_retail.py, "
                "extract_hyundai_sales_by_model.py, extract_hyundai_eu_retail.py"
            ),
        }
    )
    for year in args.years:
        node = post_list(year, context)
        for attr, family in FAMILIES.items():
            dam_path = node.get(attr)
            if not dam_path:
                print(f"{year} {family}: not published")
                continue
            url = HOST + dam_path
            dest = RAW / f"hyundai_{year}_{family}.xlsx"
            if dest.exists() and not args.force:
                status = "kept"
            else:
                download(url, dest, context)
                status = "fetched"
            digest = upsert_raw_file(
                "sales",
                dest,
                SOURCE_ID,
                Path(dam_path).name,
                f"{family} {year}; node updateDate {node.get('updateDate')}; "
                f"{status} {accessed} from {url}",
            )
            size = dest.stat().st_size
            print(f"{year} {family}: {status} {dest.name} {size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
