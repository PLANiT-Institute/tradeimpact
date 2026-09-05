"""Download AIRIA's mean-vehicle-age and mean-years-of-use releases for Japan.

Source of truth: Automobile Inspection and Registration Information Association (AIRIA),
Wagakuni no Jidosha Hoyu Doko / Vehicle Ownership Trends in Japan
(https://www.airia.or.jp/publish/statistics/trend.html). Two of its annual releases carry what
the benchmark needs, both as of 31 March of the stated year:

    mean vehicle age     mean years since first registration of the vehicles on the road
    mean years of use    mean years from first registration to deregistration — a published
                         expected vehicle life, which neither the EU27 nor the Korean build
                         can source directly

Both exclude kei vehicles, which is the same population as the JADA registration statistics the
Japanese cohorts are built from, so the life applies to the cohort without a kei correction.
AIRIA asks to be named as the source; the licence field records that.

The URLs are minted per year and are not derivable from the year (2023 sits under a hashed
directory, 2024 under a hashed filename, 2025 under a readable one), so they are read off the
page's own year dropdowns and pinned here.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_usage/fetch_airia_vehicle_age.py
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
SOURCE_ID = "airia_vehicle_age"
PAGE = "https://www.airia.or.jp/publish/statistics/trend.html"
BASE = "https://www.airia.or.jp/publish/file/"
#: local name -> (remote file, what the release reports)
FILES = {
    "airia_mean_use_years_2025.pdf": (
        "shiyounensuu_2025.pdf",
        "mean years of use as of 2025-03-31",
    ),
    "airia_mean_age_2025.pdf": ("syarei_2025.pdf", "mean vehicle age as of 2025-03-31"),
}
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}


def main() -> None:
    """Fetch both releases."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()

    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": (
                "Automobile Inspection and Registration Information Association (AIRIA), Japan"
            ),
            "title": (
                "Vehicle Ownership Trends in Japan: the mean-vehicle-age and "
                "mean-years-of-use tables by vehicle type, as of 31 March each year, excluding "
                "kei vehicles"
            ),
            "url": PAGE,
            "how_obtained": (
                f"PDFs downloaded from {BASE}<file> by "
                "script/auto/vehicle_usage/fetch_airia_vehicle_age.py; the per-year filenames are "
                "pinned in that script, having been read off the page's year dropdowns"
            ),
            "accessed_date": accessed,
            "license": (
                "free to use with attribution; AIRIA requires the source line to name the "
                "Automobile Inspection and Registration Information Association"
            ),
            "used_by": "extract_airia_vehicle_age.py",
        }
    )

    for local, (remote, what) in sorted(FILES.items()):
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
            "vehicle_usage",
            dest,
            SOURCE_ID,
            remote,
            f"{what}; kei vehicles excluded; {status} {accessed} from {url}",
        )
        print(f"{status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
