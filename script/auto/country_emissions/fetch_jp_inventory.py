"""Download Japan's national greenhouse gas inventory workbook (CO2 by sector).

Source of truth: Greenhouse Gas Inventory Office of Japan (GIO) at the National Institute for
Environmental Studies (NIES), for the Ministry of the Environment: National Greenhouse Gas
Inventory Data of Japan (https://www.nies.go.jp/gio/archive/ghgdata/). One workbook carries
the whole series, fiscal 1990 to the latest fiscal year, and sheet
``3.Allocated_CO2-sector`` is the only place the road fleet is split by vehicle type, each
row labelled in Japanese and in English:

    Road Transportation   passenger road transport
    Passenger Vehicle     cars
    Bus                   buses
    Truck and Lorry       goods vehicles

The sheet is the electricity-and-heat-allocated presentation, but its road rows are identical
to the unallocated sheet because a vehicle's own fuel is direct combustion and the electricity
an electric car charges with is accounted in the power sector, not here. That separation is
what the project relies on: the transport target moves the benchmark and the power target moves
the battery-electric product, with no double counting.

Run from the repository root:  .venv/bin/python script/auto/country_emissions/fetch_jp_inventory.py
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
RAW = REPO / "data" / "auto" / "country_emissions" / "raw"
SOURCE_ID = "gio_nies_inventory"
PAGE = "https://www.nies.go.jp/gio/archive/ghgdata/"
URL = (
    "https://www.nies.go.jp/gio/archive/ghgdata/k6efli000007q2e2-att/"
    "L5-7gas_2026_gioweb_ver1.0.xlsx"
)
DEST = RAW / "gio_nies_inventory_co2_by_sector.xlsx"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}


def main() -> None:
    """Fetch the inventory workbook."""
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
            "publisher": (
                "Greenhouse Gas Inventory Office of Japan (GIO), National Institute for "
                "Environmental Studies (NIES), for the Ministry of the Environment of Japan"
            ),
            "title": (
                "National Greenhouse Gas Inventory Data of Japan: national CO2 by sector, "
                "fiscal 1990 onward. "
                "Sheet 3.Allocated_CO2-sector splits road transport into cars, buses and goods "
                "vehicles"
            ),
            "url": PAGE,
            "how_obtained": (
                f"downloaded directly from {URL} by "
                "script/auto/country_emissions/fetch_jp_inventory.py"
            ),
            "accessed_date": accessed,
            "license": (
                "government publication; NIES and Ministry of the Environment terms, attribution"
            ),
            "used_by": "extract_jp_inventory.py",
        }
    )
    digest = upsert_raw_file(
        "country_emissions",
        DEST,
        SOURCE_ID,
        "L5-7gas_2026_gioweb_ver1.0.xlsx",
        "fiscal years; sheet 3.Allocated_CO2-sector rows Passenger Vehicle / Bus / Truck "
        f"and Lorry; "
        f"{status} {accessed} from {URL}",
    )
    print(f"{status} {DEST.name} {DEST.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
