"""Download Japan's Motor Vehicle Fuel Consumption Survey, Table 1 (vehicle-kilometres).

Source of truth: Ministry of Land, Infrastructure, Transport and Tourism (MLIT), Jidosha Nenryo
Shohiryo Chosa / Motor Vehicle Fuel Consumption Survey, published through e-Stat under survey
code 00600370 (https://www.e-stat.go.jp/stat-search/files?toukei=00600370). Table 1, the summary
by fuel and vehicle type, is the only table that carries all three quantities the benchmark needs
in one place, per fuel x operation (commercial or private) x use (goods or passenger) x vehicle
type:

    vehicle-kilometres            thousand km per fiscal year
    kilometres per vehicle-day    km per vehicle per calendar day
    working-day rate              working days as a share of calendar days

so annual distance per vehicle is the second times 365, and the implied stock is the first
divided by that — no separate registration series has to be joined to a distance series at a
possibly different date. Fiscal years (April to March).

One e-Stat quirk: a table is addressed by ``statInfId``, which is minted per release, so the id
differs for every fiscal year and cannot be derived from the year. The ids below were read off
the survey's own annual file list and are pinned here with the year they belong to.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_usage/fetch_mlit_fuel_survey.py
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
RAW = REPO / "data" / "auto" / "vehicle_usage" / "raw"
SOURCE_ID = "mlit_fuel_consumption_survey"
PAGE = "https://www.e-stat.go.jp/stat-search/files?toukei=00600370"
DOWNLOAD = "https://www.e-stat.go.jp/stat-search/file-download?statInfId={stat_inf_id}&fileKind=4"
#: fiscal year -> the e-Stat statInfId of that year's Table 1.
TABLES = {
    2024: "000040284813",
    2025: "000040468862",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}


def main() -> None:
    """Fetch one workbook per pinned fiscal year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()

    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": (
                "Ministry of Land, Infrastructure, Transport and Tourism (MLIT), Japan, via e-Stat"
            ),
            "title": (
                "Motor Vehicle Fuel Consumption Survey, Table 1 (summary by fuel and "
                "vehicle type): fuel consumption, vehicle-kilometres, kilometres per vehicle-day "
                "and the working-day rate, by fuel, commercial or private operation, goods or "
                "passenger use and vehicle type, fiscal years"
            ),
            "url": PAGE,
            "how_obtained": (
                "downloaded from the e-Stat file endpoint "
                f"{DOWNLOAD.format(stat_inf_id='<statInfId>')} by "
                "script/auto/vehicle_usage/fetch_mlit_fuel_survey.py; the statInfId per fiscal "
                "year is pinned in that script"
            ),
            "accessed_date": accessed,
            "license": (
                "government statistics; e-Stat terms of use (free use with attribution; e-Stat "
                "is the portal of official statistics of Japan)"
            ),
            "used_by": "extract_mlit_fuel_survey.py",
        }
    )

    for year, stat_inf_id in sorted(TABLES.items()):
        dest = RAW / f"mlit_fuel_survey_fy{year}.xlsx"
        url = DOWNLOAD.format(stat_inf_id=stat_inf_id)
        if dest.exists() and not args.force:
            status = "kept"
        else:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, context=context, timeout=300) as response:
                dest.write_bytes(response.read())
            status = "fetched"
        digest = upsert_raw_file(
            "vehicle_usage",
            dest,
            SOURCE_ID,
            f"Table 1, summary by fuel and vehicle type (statInfId {stat_inf_id})",
            f"fiscal {year} (April {year} to March {year + 1}); {status} {accessed} from {url}",
        )
        print(f"{status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
