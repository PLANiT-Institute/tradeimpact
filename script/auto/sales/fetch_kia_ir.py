"""Download Kia Corporation's IR retail-sales workbook for a year.

Source of truth: Kia Corporation, Investor Relations > Library > Performance and Plans
(https://worldwide.kia.com/en/company/investor-relations/library/performance-and-plans). The
page is a script shell; its own script lists the files through

    GET https://worldwide.kia.com/api/investors/business-sales-results?year=YYYY&page=0&language=en

which returns one ``type: sales`` node per year carrying four workbook paths, served from
``https://worldwide.kia.com/files/<path>``:

    Retail Sales               retail sales by model and destination country/region
    Sales by Model             worldwide sales by model
    Export Sales by Region     shipments exported from Korea, by region (plant-side)
    Overseas Plant Sale(s)     sales by the overseas plants (plant-side)

The retail workbook's title is not stable — the 2025 edition is titled "Overseas Retail Sales"
though its first market column is Korea — so it is matched on the words it does keep.

Only the retail workbook is downloaded: it is the market-side file the cohort is built from,
and the other three are not read by any extractor. The node is overwritten monthly, so the
edition on the site is the year to date and superseded editions are not retained; the Korean
(``language=ko``) node carries byte-different but cell-identical copies of the same workbooks.

Files land in data/auto/sales/raw/kia_<year>_retail_sales_by_model_market.xlsx; existing files
are kept unless --force. Every download is registered in sources.csv and raw_files.csv.

Run from the repository root:  .venv/bin/python script/auto/sales/fetch_kia_ir.py 2024 2025 2026
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
SOURCE_ID = "kia_ir_retail_sales"
PAGE = "https://worldwide.kia.com/en/company/investor-relations/library/performance-and-plans"
LIST_URL = "https://worldwide.kia.com/api/investors/business-sales-results"
FILE_BASE = "https://worldwide.kia.com/files/"
#: The one workbook of the four the pipeline reads, matched on its English file title; no
#: other title in a node contains these words, and every edition's does.
RETAIL_TITLE = "retail sales"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}


def list_node(year: int, context: ssl.SSLContext) -> dict:
    """Return the ``sales`` node of one year, or raise when the year is not published."""
    query = urllib.parse.urlencode({"year": year, "page": 0, "language": "en"})
    req = urllib.request.Request(f"{LIST_URL}?{query}", headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=60) as r:
        payload = json.load(r)
    nodes = [n for n in payload.get("data", {}).get("list", []) if n.get("type") == "sales"]
    if len(nodes) != 1:
        raise SystemExit(f"{year}: expected one sales node, got {len(nodes)}")
    return nodes[0]


def retail_file(node: dict) -> dict:
    """The retail-sales entry of a node's file list.

    Args:
        node: One ``type: sales`` node of the listing response.

    Returns:
        The file entry carrying ``title`` and ``path``.
    """
    matches = [
        f
        for f in node.get("files", [])
        if RETAIL_TITLE in unicodedata.normalize("NFC", f["title"]).lower()
    ]
    if len(matches) != 1:
        titles = [unicodedata.normalize("NFC", f["title"]) for f in node.get("files", [])]
        raise SystemExit(f"{node.get('year')}: no single retail workbook among {titles}")
    return matches[0]


def download(url: str, dest: Path, context: ssl.SSLContext) -> None:
    """Save one workbook."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=120) as r:
        dest.write_bytes(r.read())


def main() -> None:
    """Fetch the retail workbook for each requested year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "Kia Corporation Investor Relations",
            "title": (
                "Monthly sales results: Retail Sales by Country, one workbook per calendar year "
                "with a Total sheet and twelve monthly sheets; the current year's node is "
                "overwritten monthly, so it holds the year to date"
            ),
            "url": PAGE,
            "how_obtained": (
                f"api: GET {LIST_URL}?year=YYYY&page=0&language=en lists the four workbook "
                f"paths, served from {FILE_BASE}<path>; downloaded by "
                "script/auto/sales/fetch_kia_ir.py"
            ),
            "accessed_date": accessed,
            "license": "company IR publication; no explicit reuse licence stated",
            "used_by": "extract_kia_ir.py",
        }
    )
    for year in args.years:
        node = list_node(year, context)
        entry = retail_file(node)
        url = FILE_BASE + entry["path"]
        dest = RAW / f"kia_{year}_retail_sales_by_model_market.xlsx"
        if dest.exists() and not args.force:
            status = "kept"
        else:
            download(url, dest, context)
            status = "fetched"
        digest = upsert_raw_file(
            "sales",
            dest,
            SOURCE_ID,
            unicodedata.normalize("NFC", entry["title"]),
            f"retail sales by model and country {year}; node published "
            f"{node.get('publicatedAt')}; {status} {accessed} from {url}",
        )
        size = dest.stat().st_size
        print(f"{year} retail: {status} {dest.name} {size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
