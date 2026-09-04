"""Download the MOLIT monthly vehicle registration statistics workbook (Korea stock and age).

Source of truth: Ministry of Land, Infrastructure and Transport (MOLIT), Vehicle
Registration Statistics (approved national statistic no. 116015), MOLIT statistics portal
https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=58. The portal's own script downloads
a monthly workbook through

    GET https://stat.molit.go.kr/portal/common/downLoadFile.do?oFileName=<name>&rFileName=<name>&midpath=%2Fstat_file%2F

where <name> is the workbook's own Korean filename for that year and month, which
``NAME_VARIANTS`` below templates. The December workbook of a year is the year-end snapshot:
one sheet gives year-end stock by vehicle class and use from 2007 onward, another gives
stock by model year (vehicle age) x class x use, with the oldest band open-ended. The
passenger-car class is the one defined by the Motor Vehicle Management Act, up to ten
seats.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_usage/fetch_molit_registrations.py 2025 [2024 ...]
"""

from __future__ import annotations

import argparse
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "vehicle_usage" / "raw"
SOURCE_ID = "molit_vehicle_registration"
PAGE = "https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=58"
ENDPOINT = "https://stat.molit.go.kr/portal/common/downLoadFile.do"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)", "Referer": PAGE}
NAME_VARIANTS = (
    # The portal's own filenames for the December workbook, verbatim: "<year> December
    # vehicle registration statistics.xlsx", written with and without a space.
    "{year}년 12월 자동차 등록자료 통계.xlsx",
    "{year}년 12월 자동차등록자료 통계.xlsx",
)


def download(year: int, context: ssl.SSLContext) -> tuple[bytes, str]:
    """Try the known filename variants for the December workbook of one year."""
    last_error = ""
    for pattern in NAME_VARIANTS:
        name = pattern.format(year=year)
        query = urllib.parse.urlencode(
            {"oFileName": name, "rFileName": name, "midpath": "/stat_file/"}
        )
        req = urllib.request.Request(f"{ENDPOINT}?{query}", headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=context, timeout=120) as r:
                data = r.read()
        except urllib.error.HTTPError as e:  # pragma: no cover - network
            last_error = f"{name}: HTTP {e.code}"
            continue
        if data.startswith(b"PK"):
            return data, f"{ENDPOINT}?{query}"
        last_error = f"{name}: not an xlsx ({data[:40]!r})"
    raise SystemExit(f"MOLIT December {year} workbook not found: {last_error}")


def main() -> None:
    """Fetch the December workbook for each requested year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": (
                "Ministry of Land, Infrastructure and Transport (MOLIT), Korea, statistics portal"
            ),
            "title": (
                "Vehicle Registration Statistics (monthly workbook): year-end stock by "
                "vehicle class and use 2007 onward; stock by model year (age) x class x use; "
                "fuel mix"
            ),
            "url": PAGE,
            "how_obtained": (
                f"api: GET {ENDPOINT}?oFileName=<the workbook's own filename for that "
                "year and month>&rFileName=<same>&midpath=/stat_file/ (endpoint from the "
                "portal's own script); downloaded by "
                "script/auto/vehicle_usage/fetch_molit_registrations.py"
            ),
            "accessed_date": accessed,
            "license": (
                "MOLIT official statistics; mirrored on data.go.kr (dataset 15024777) with "
                "no restriction on use"
            ),
            "used_by": "extract_molit_registrations.py",
        }
    )
    for year in args.years:
        dest = RAW / f"molit_vehicle_registration_{year}_12.xlsx"
        if dest.exists() and not args.force:
            status, url = "kept", ENDPOINT
        else:
            data, url = download(year, context)
            dest.write_bytes(data)
            status = "fetched"
        digest = upsert_raw_file(
            "vehicle_usage",
            dest,
            SOURCE_ID,
            NAME_VARIANTS[0].format(year=year),
            f"December {year} workbook (year-end snapshot); {status} {accessed} from {url}",
        )
        print(f"{year}: {status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
