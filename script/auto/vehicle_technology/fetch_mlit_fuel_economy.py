"""Download MLIT's 自動車燃費一覧 (certified fuel economy and CO2 per grade, WLTC mode).

Source of truth: 国土交通省 物流・自動車局, 自動車燃費一覧（令和８年３月）
(https://www.mlit.go.jp/jidosha/jidosha_tk10_000050.html). The workbooks list, per maker sheet
and per 型式, the WLTC 燃費値 in km/L **and 1km走行におけるCO2排出量 in gCO2/km**, so the product
side needs no fuel-carbon conversion at all — unlike Korea, where the label publishes km/L only.

Two workbooks carry the vehicles the Japanese cohorts contain:

    ガソリン乗用車（普通・小型自動車, WLTCモード）   petrol and petrol-hybrid cars
    ディーゼル乗用車（WLTCモード）                 diesel cars, maker sheets suffixed _WLTC

軽自動車 are not fetched: the JADA nameplate ranking the cohorts are built from excludes kei
vehicles by construction (its own note says 軽自動車及び海外ブランド車を除く), so no kei unit can
enter a cohort. Battery-electric vehicles are absent from 燃費一覧 altogether — it is a
fuel-consumption publication — which is why Japanese battery-electric units are withheld rather
than priced.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_technology/fetch_mlit_fuel_economy.py
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
SOURCE_ID = "mlit_fuel_economy_list"
PAGE = "https://www.mlit.go.jp/jidosha/jidosha_tk10_000050.html"
BASE = "https://www.mlit.go.jp/jidosha/content/"
#: local name -> (remote file, edition year, what the workbook covers). Two editions are kept:
#: 燃費一覧 lists only what is type-approved on the edition date, so a nameplate withdrawn during
#: the cohort year is in the older edition and gone from the newer one.
FILES = {
    "mlit_fuel_economy_petrol_car_wltc_2026.xlsx": (
        "001986923.xlsx",
        2026,
        "ガソリン乗用車（普通・小型自動車）WLTCモード; petrol and petrol-hybrid cars",
    ),
    "mlit_fuel_economy_diesel_car_wltc_2026.xlsx": (
        "001986958.xlsx",
        2026,
        "ディーゼル乗用車; maker sheets suffixed _WLTC and _JC08",
    ),
    "mlit_fuel_economy_petrol_car_wltc_2025.xlsx": (
        "3.1.G_LD_WLTC.xlsx",
        2025,
        "ガソリン乗用車（普通・小型自動車）WLTCモード, 令和7年3月 edition",
    ),
    "mlit_fuel_economy_diesel_car_wltc_2025.xlsx": (
        "4.1.D_LD_WLTC.xlsx",
        2025,
        "ディーゼル乗用車（普通・小型自動車）WLTCモード, 令和7年3月 edition",
    ),
}
#: edition year -> the page it is published on.
PAGES = {
    2026: "https://www.mlit.go.jp/jidosha/jidosha_tk10_000050.html",
    2025: "https://www.mlit.go.jp/jidosha/jidosha_tk10_000048.html",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}


def main() -> None:
    """Fetch both workbooks."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()

    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": (
                "国土交通省 物流・自動車局 Ministry of Land, Infrastructure, Transport and Tourism"
            ),
            "title": (
                "自動車燃費一覧 令和7年3月 and 令和8年3月 editions: certified WLTC fuel economy "
                "(km/L) and CO2 emissions (gCO2/km) per 型式 and 類別, by maker, for cars "
                "type-approved as of the edition date"
            ),
            "url": PAGE,
            "how_obtained": (
                f"workbooks downloaded from {BASE}<file> by "
                "script/auto/vehicle_technology/fetch_mlit_fuel_economy.py; the content ids are "
                "pinned in that script and are re-minted with every edition"
            ),
            "accessed_date": accessed,
            "license": (
                "government publication; MLIT terms of use (free use with attribution, "
                "https://www.mlit.go.jp/link.html)"
            ),
            "used_by": "extract_mlit_fuel_economy.py",
        }
    )

    for local, (remote, edition, what) in sorted(FILES.items()):
        dest = RAW / local
        url = BASE + remote
        if dest.exists() and not args.force:
            status = "kept"
        else:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, context=context, timeout=300) as response:
                dest.write_bytes(response.read())
            status = "fetched"
        digest = upsert_raw_file(
            "vehicle_technology",
            dest,
            SOURCE_ID,
            remote,
            f"edition {edition} ({PAGES[edition]}); {what}; {status} {accessed} from {url}. "
            "The 2025 edition is served under a readable filename that a future edition could "
            "overwrite, so the digest recorded here is what pins the content.",
        )
        print(f"{status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
