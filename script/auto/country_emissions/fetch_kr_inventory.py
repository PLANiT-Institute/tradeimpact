"""Download Korea's national GHG inventory (CO2 by category) and the KOTSA road GHG by vehicle type.

Sources of truth (both open data on data.go.kr, keyless file downloads, licence 제한 없음):

    GIR 가스별 국가 온실가스 인벤토리 배출량(CO2)  https://www.data.go.kr/data/15070396/fileData.do
        CO2 by IPCC category, national, 1990-2023 (edition 2025-12-29), ktCO2. Row
        "A 연료연소_3 수송_b 도로수송" is 1.A.3.b road transport. Fuel-sales (top-down) basis.
        No vehicle-type split exists in the national inventory.
    KOTSA 지역별 차종별 도로부문 온실가스 배출량      https://www.data.go.kr/data/15106288/fileData.do
        Road GHG by vehicle type (승용/승합/화물/특수) x province, 2012-2024, ktCO2e, bottom-up
        (registered vehicles x KOTSA distance x emission factor). Used only for the passenger-car
        SHARE of road emissions: its level sits 13-26 % below the national inventory.

The primary GIR publication (workbooks by IPCC guideline) is at
https://www.gir.go.kr/home/board/read.do?menuId=36&boardId=88&boardMasterId=2.

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
                "온실가스종합정보센터 GIR (Greenhouse Gas Inventory and Research Center of "
                "Korea), via "
                "공공데이터포털 data.go.kr"
            ),
            "title": (
                "가스별 국가 온실가스 인벤토리 배출량(CO2): national CO2 by IPCC category "
                "1990-2023, ktCO2 "
                "(2025-12-29 edition, 2006 IPCC guidelines)"
            ),
            "url": "https://www.data.go.kr/data/15070396/fileData.do",
            "license": "공공데이터포털 이용허락범위 제한 없음 (KOGL type 1 equivalent)",
            "used_by": "extract_kr_inventory.py",
        },
        "note": (
            "CSV UTF-8 BOM; header says kt CO2-eq, CO2 sheet so ktCO2; row 'A 연료연소_3 "
            "수송_b 도로수송' = "
            "1.A.3.b"
        ),
    },
    "kotsa_road_ghg_by_vehicle_type.csv": {
        "file_id": "FILE_000000003654294",
        "source": {
            "source_id": "kotsa_road_ghg_vehicle_type",
            "publisher": (
                "한국교통안전공단 KOTSA (Korea Transportation Safety Authority), via data.go.kr"
            ),
            "title": (
                "지역별 차종별 도로부문 온실가스 배출량: road-sector GHG by vehicle type "
                "(승용, 승합, 화물, 특수) and "
                "province, 2012-2024, ktCO2e, bottom-up local inventory"
            ),
            "url": "https://www.data.go.kr/data/15106288/fileData.do",
            "license": "공공데이터포털 이용허락범위 제한 없음 (KOGL type 1 equivalent)",
            "used_by": "extract_kr_inventory.py (passenger-car share only)",
        },
        "note": (
            "CSV cp949; level disagrees with GIR 1.A.3.b by 13-26 %, used for the 승용 share only"
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
