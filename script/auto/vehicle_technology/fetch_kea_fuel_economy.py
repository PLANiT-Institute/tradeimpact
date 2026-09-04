"""Download Korea's certified label fuel economy by model and trim (KEA) and the NIER fleet CO2
table.

Sources of truth (data.go.kr keyless file downloads, licence 제한 없음):

    한국에너지공단 자동차 표시연비 정보  https://www.data.go.kr/data/15083023/fileData.do
        One row per trim certified for sale: 모델명, 제조(수입사), 차종, 유형, 복합_연비 (km/L, or
        km/kWh for BEV/PHEV in the same column), 1회충전주행거리 (km, BEV/PHEV only), 도심/고속도로
        연비, 등급. The label value is 5-cycle corrected (Korea adopted the US 5-cycle method in
        2012), so it is the sibling of the EPA label value, not of WLTP. No CO2 and no fuel column.
    국립환경과학원 제작사별 연도별 판매자동차 온실가스 배출기준 및 실적  https://www.data.go.kr/data/15042041/fileData.do
        Per-manufacturer sales-weighted new-car CO2 (g/km, 2-cycle regulatory basis) and fuel
        economy, standard vs achieved, 2012-2020. Context and cross-check only.

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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
            "publisher": "한국에너지공단 KEA (Korea Energy Agency), via data.go.kr",
            "title": (
                "자동차 표시연비 정보: certified label fuel economy by model and trim for "
                "vehicles on sale "
                "(km/L; km/kWh and range for BEV/PHEV), 5-cycle corrected, edition 2026-04-24"
            ),
            "url": "https://www.data.go.kr/data/15083023/fileData.do",
            "license": "공공데이터포털 이용허락범위 제한 없음 (KOGL type 1 equivalent)",
            "used_by": "extract_kea_fuel_economy.py",
        },
        "note": (
            "CSV UTF-8 BOM, 4,203 rows; 복합_연비 is km/L or km/kWh in one column (BEV/PHEV rows "
            "carry 1회충전주행거리)"
        ),
    },
    "nier_manufacturer_fleet_co2_2012_2020.csv": {
        "file_id": "FILE_000000003553964",
        "source": {
            "source_id": "nier_manufacturer_fleet_co2",
            "publisher": (
                "국립환경과학원 NIER (National Institute of Environmental Research), via data.go.kr"
            ),
            "title": (
                "제작사별 연도별 판매자동차 온실가스 배출기준 및 실적: per-manufacturer "
                "sales-weighted new-car CO2 "
                "(g/km, 2-cycle regulatory basis) and fuel economy, standard vs achieved, 2012-2020"
            ),
            "url": "https://www.data.go.kr/data/15042041/fileData.do",
            "license": "공공데이터포털 이용허락범위 제한 없음 (KOGL type 1 equivalent)",
            "used_by": "method note cross-check only",
        },
        "note": "CSV cp949; ends 2020; 실적(100) vs 실적(비율) are different bases",
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
