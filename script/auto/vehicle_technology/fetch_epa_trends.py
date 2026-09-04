"""Download EPA Automotive Trends model-year fuel economy and technology data (carline level).

Source of truth: US EPA, Explore the Automotive Trends Data
(https://www.epa.gov/automotive-trends/explore-automotive-trends-data), file
"Model Year 2024 Fuel Economy and Technology Data (csv)". One row per model-type
configuration with the certification production volume (Model_Type_Actual_Prod_Vol), hybrid
flag, fuel usage, label CO2 and MPG. Public domain (US government work).

The file supplies what the company sales releases withhold: the powertrain split of a nameplate
(Tucson vs Tucson Hybrid vs Tucson Plug-in Hybrid) on a production-for-US-sale basis.

Run from the repository root:  .venv/bin/python script/auto/vehicle_technology/fetch_epa_trends.py
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
RAW = REPO / "data" / "auto" / "vehicle_technology" / "raw"
SOURCE_ID = "epa_automotive_trends_my2024"
PAGE = "https://www.epa.gov/automotive-trends/explore-automotive-trends-data"
URL = (
    "https://www.epa.gov/system/files/other-files/2026-05/"
    "model-year-2024-fuel-economy-and-technology-data.csv"
)
DEST = RAW / "epa_automotive_trends_my2024.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}


def main() -> None:
    """Fetch the MY2024 carline file."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    if DEST.exists() and not args.force:
        status = "kept"
    else:
        req = urllib.request.Request(URL, headers=HEADERS)
        with urllib.request.urlopen(req, context=context, timeout=300) as r:
            DEST.write_bytes(r.read())
        status = "fetched"
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "US Environmental Protection Agency",
            "title": (
                "Automotive Trends: Model Year 2024 Fuel Economy and Technology Data (csv); one "
                "row per model-type configuration with certification production volume, hybrid "
                "flag, fuel usage and label CO2"
            ),
            "url": PAGE,
            "how_obtained": f"downloaded directly from {URL} by "
            "script/auto/vehicle_technology/fetch_epa_trends.py",
            "accessed_date": accessed,
            "license": "US government work, public domain",
            "used_by": "extract_epa_trends.py",
        }
    )
    digest = upsert_raw_file(
        "vehicle_technology",
        DEST,
        SOURCE_ID,
        "model-year-2024-fuel-economy-and-technology-data.csv",
        f"MY2024 carline file (1978 rows); {status} {accessed} from {URL}",
    )
    print(f"{status} {DEST.name} {DEST.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
