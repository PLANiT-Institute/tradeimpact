"""Download Korea's national CO2 inventory and the road GHG split by vehicle type.

Sources of truth (both open data on data.go.kr, keyless file downloads, licence: no restriction
on use):

    National Greenhouse Gas Inventory Emissions by Gas (CO2), Greenhouse Gas Inventory and
    Research Center of Korea (GIR)      https://www.data.go.kr/data/15070396/fileData.do
        National CO2 by IPCC category, 1990-2023, ktCO2, 2006 IPCC guidelines. The row for fuel
        combustion / transport / road transport is category 1.A.3.b. Fuel-sales (top-down) basis.

    Road-Sector Greenhouse Gas Emissions by Region and Vehicle Type, Korea Transportation Safety
    Authority (KOTSA)                   https://www.data.go.kr/data/15106288/fileData.do
        Road GHG by vehicle type (passenger car, bus, goods, special) x province, 2012-2024,
        ktCO2e, a bottom-up local inventory. Its national level sits 13-26 % below the GIR road
        total, so only its passenger-car share is used, never its level.

Run from the repository root:  .venv/bin/python script/auto/country_emissions/fetch_kr_inventory.py
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
RAW = REPO / "data" / "auto" / "country_emissions" / "raw"
DOWNLOAD = "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId={file_id}&fileDetailSn=1&insertDataPrcus=N"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}

FILES = {
    "gir_inventory_co2_1990_2023.csv": {
        "file_id": "FILE_000000003573902",
        "source": {
            "source_id": "gir_inventory_co2",
            "publisher": (
                "Greenhouse Gas Inventory and Research Center of Korea (GIR), via the "
                "public data portal data.go.kr"
            ),
            "title": (
                "National Greenhouse Gas Inventory Emissions by Gas (CO2): national CO2 "
                "by IPCC category 1990-2023, ktCO2 (2025-12-29 edition, 2006 IPCC guidelines)"
            ),
            "url": "https://www.data.go.kr/data/15070396/fileData.do",
            "license": ("public data portal, no restriction on use (equivalent to KOGL type 1)"),
            "used_by": "extract_kr_inventory.py",
        },
        "note": (
            "CSV UTF-8 BOM; the header says kt CO2-eq but the sheet is CO2, so ktCO2; the "
            "row for fuel combustion / transport / road transport is category 1.A.3.b"
        ),
    },
    "kotsa_road_ghg_by_vehicle_type.csv": {
        "file_id": "FILE_000000003654294",
        "source": {
            "source_id": "kotsa_road_ghg_vehicle_type",
            "publisher": ("Korea Transportation Safety Authority (KOTSA), via data.go.kr"),
            "title": (
                "Road-Sector Greenhouse Gas Emissions by Region and Vehicle Type: road GHG "
                "by vehicle type (passenger car, bus, goods, special) and province, 2012-2024, "
                "ktCO2e, a bottom-up local inventory"
            ),
            "url": "https://www.data.go.kr/data/15106288/fileData.do",
            "license": ("public data portal, no restriction on use (equivalent to KOGL type 1)"),
            "used_by": "extract_kr_inventory.py (passenger-car share only)",
        },
        "note": (
            "CSV cp949; the level disagrees with GIR 1.A.3.b by 13-26 %, so only the "
            "passenger-car share is used"
        ),
    },
}


def main() -> None:
    """Fetch both files (kept if present unless --force) and register them."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    for name, spec in FILES.items():
        dest = RAW / name
        url = DOWNLOAD.format(file_id=spec["file_id"])
        if dest.exists() and not args.force:
            status = "kept"
        else:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=context, timeout=120) as r:
                dest.write_bytes(r.read())
            status = "fetched"
        upsert_source(
            {
                **spec["source"],
                "how_obtained": f"downloaded directly from {url} by "
                "script/auto/country_emissions/fetch_kr_inventory.py",
                "accessed_date": accessed,
            }
        )
        digest = upsert_raw_file(
            "country_emissions",
            dest,
            spec["source"]["source_id"],
            f"data.go.kr {spec['file_id']}",
            f"{spec['note']}; {status} {accessed} from {url}",
        )
        print(f"{status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
