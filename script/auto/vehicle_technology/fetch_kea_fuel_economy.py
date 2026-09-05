"""Download Korea's certified label fuel economy by model and trim (KEA) and the NIER fleet CO2
table.

Sources of truth (data.go.kr keyless file downloads, no restriction on use):

    Korea Energy Agency (KEA), Vehicle Label Fuel Economy Information
    https://www.data.go.kr/data/15083023/fileData.do
        One row per trim certified for sale, with the model name, the maker or importer, the
        vehicle class, the body type, the combined fuel economy (km/L, or km/kWh for BEV and
        PHEV in the same column), the single-charge range (km, BEV and PHEV only), the city and
        highway values and the efficiency grade. The label value is 5-cycle corrected (Korea
        adopted the US 5-cycle method in 2012), so it is the sibling of the EPA label value, not
        of WLTP. No CO2 column and no fuel column.

    National Institute of Environmental Research (NIER), Greenhouse Gas Emission Standards and
    Performance of Vehicles Sold, by Manufacturer and Year
    https://www.data.go.kr/data/15042041/fileData.do
        Per-manufacturer sales-weighted new-car CO2 (g/km, 2-cycle regulatory basis) and fuel
        economy, standard against achieved, 2012-2020. Context and cross-check only.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_technology/fetch_kea_fuel_economy.py
"""

from __future__ import annotations

import argparse
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "vehicle_technology" / "raw"
DOWNLOAD = "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId={file_id}&fileDetailSn=1&insertDataPrcus=N"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}

FILES = {
    "kea_vehicle_fuel_economy_labels.csv": {
        "file_id": "FILE_000000003644543",
        "source": {
            "source_id": "kea_fuel_economy_labels",
            "publisher": "Korea Energy Agency (KEA), via data.go.kr",
            "title": (
                "Vehicle Label Fuel Economy Information: certified label fuel economy by "
                "model and trim for vehicles on sale (km/L; km/kWh and range for BEV and PHEV), "
                "5-cycle corrected, edition 2026-04-24"
            ),
            "url": "https://www.data.go.kr/data/15083023/fileData.do",
            "license": ("public data portal, no restriction on use (equivalent to KOGL type 1)"),
            "used_by": "extract_kea_fuel_economy.py",
        },
        "note": (
            "CSV UTF-8 BOM, 4,203 rows; the combined-fuel-economy column is km/L or km/kWh "
            "in one column, and BEV and PHEV rows also carry a single-charge range"
        ),
    },
    "nier_manufacturer_fleet_co2_2012_2020.csv": {
        "file_id": "FILE_000000003553964",
        "source": {
            "source_id": "nier_manufacturer_fleet_co2",
            "publisher": (
                "National Institute of Environmental Research (NIER), Korea, via data.go.kr"
            ),
            "title": (
                "Greenhouse Gas Emission Standards and Performance of Vehicles Sold, by "
                "Manufacturer and Year: per-manufacturer sales-weighted new-car CO2 (g/km, "
                "2-cycle regulatory basis) and fuel economy, standard against achieved, "
                "2012-2020"
            ),
            "url": "https://www.data.go.kr/data/15042041/fileData.do",
            "license": ("public data portal, no restriction on use (equivalent to KOGL type 1)"),
            "used_by": "method note cross-check only",
        },
        "note": (
            "CSV cp949; ends 2020; the two achievement columns (indexed to 100 and as a ratio) "
            "are different bases"
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
                "script/auto/vehicle_technology/fetch_kea_fuel_economy.py",
                "accessed_date": accessed,
            }
        )
        digest = upsert_raw_file(
            "vehicle_technology",
            dest,
            spec["source"]["source_id"],
            f"data.go.kr {spec['file_id']}",
            f"{spec['note']}; {status} {accessed} from {url}",
        )
        print(f"{status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
