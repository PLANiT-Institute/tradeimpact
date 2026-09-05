"""Download Korea's annual vehicle-kilometres by vehicle class from KOTSA TMACS.

Source of truth: Korea Transportation Safety Authority (KOTSA), Motor Vehicle Travel
Distance Statistics (odometer readings at the periodic vehicle
inspection, grossed up to the registered fleet), TMACS
https://tmacs.kotsa.or.kr/web/TG/TG200/TG2200/Tg1700_02.jsp?mid=S3080. The page's own data call is

    POST https://tmacs.kotsa.or.kr/web/TG/TG200/TG2200/Tg2119_AJAX.jsp
         gubun=Tg1700_04 (annual total, thousand km) | Tg1700_03 (km per vehicle per day)
         year=YYYY  carUse=<all | commercial | private>, sent as the portal's own values

returning JSON rows (YEAR, CAR_USE_NM, CAR_CLS_NM, FUEL_CLS_NM, ALL, 16 provinces). The same
statistic is mirrored on data.go.kr (datasets 15072343, 15088454) with no restriction on
use.

Known traps recorded in the method note: 2015 returns no rows; the total-row label changes from
from a mean to a sum in 2021 and the per-vehicle distance breaks by about 11 % in that
year; the annual ALL
column is in thousand km although the page does not say so.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_usage/fetch_kotsa_tmacs.py 2016 2024
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "vehicle_usage" / "raw"
SOURCE_ID = "kotsa_tmacs_vkm"
PAGE = "https://tmacs.kotsa.or.kr/web/TG/TG200/TG2200/Tg1700_02.jsp?mid=S3080"
ENDPOINT = "https://tmacs.kotsa.or.kr/web/TG/TG200/TG2200/Tg2119_AJAX.jsp"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}
KINDS = {"Tg1700_04": "annual_vkm", "Tg1700_03": "daily_km"}


def post(gubun: str, year: int, context: ssl.SSLContext) -> bytes:
    """One TMACS query."""
    body = urllib.parse.urlencode({"gubun": gubun, "year": year, "carUse": "전체"}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=60) as r:
        data = r.read()
    json.loads(data)  # fail loudly on a non-JSON reply
    return data


def main() -> None:
    """Fetch annual and daily tables for every year in [first, last]."""
    ap = argparse.ArgumentParser()
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": (
                "Korea Transportation Safety Authority (KOTSA), TMACS traffic and vehicle "
                "statistics"
            ),
            "title": (
                "Motor Vehicle Travel Distance Statistics: annual vehicle-kilometres "
                "(thousand km) and km per "
                "vehicle per day by "
                "vehicle class, fuel and province, from inspection odometer readings, 2012 onward"
            ),
            "url": PAGE,
            "how_obtained": (
                f"api: POST {ENDPOINT} gubun=Tg1700_04|Tg1700_03&year=YYYY&carUse=전체 (the page's "
                "own data call, JSON); downloaded by script/auto/vehicle_usage/fetch_kotsa_tmacs.py"
            ),
            "accessed_date": accessed,
            "license": (
                "KOTSA statistics; mirrored on data.go.kr (15072343, 15088454) with "
                "no restriction on use"
            ),
            "used_by": "extract_kotsa_tmacs.py",
        }
    )
    for year in range(args.first, args.last + 1):
        for gubun, kind in KINDS.items():
            dest = RAW / f"kotsa_tmacs_{kind}_{year}.json"
            if dest.exists() and not args.force:
                status = "kept"
            else:
                dest.write_bytes(post(gubun, year, context))
                status = "fetched"
            rows = len(json.loads(dest.read_bytes()))
            digest = upsert_raw_file(
                "vehicle_usage",
                dest,
                SOURCE_ID,
                f"Tg2119_AJAX.jsp gubun={gubun} year={year} carUse=전체",
                f"{kind} {year}, {rows} rows; {status} {accessed} from {ENDPOINT}",
            )
            print(f"{year} {kind}: {status} {rows} rows {digest[:12]}")


if __name__ == "__main__":
    main()
