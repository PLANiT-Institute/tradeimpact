"""Download the ISO 3166-1 country-code table the power sector joins names and codes with.

Source of truth: mledoze/world-countries (https://github.com/mledoze/world-countries), read from
its npm distribution on jsDelivr, version pinned. The table gives alpha-2, alpha-3 and numeric
codes with common and official names, which is what the Global Energy Monitor country names and
the Our World in Data ISO-3 codes are mapped through.

Run from the repository root:  .venv/bin/python script/power/geography/fetch_country_codes.py
"""

from __future__ import annotations

import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "power"
RAW = DATA / "geography" / "raw" / "world_countries.json"
VERSION = "5.1.0"
URL = f"https://cdn.jsdelivr.net/npm/world-countries@{VERSION}/countries.json"
SOURCE_ID = "world_countries_codes"


def main() -> None:
    """Download the JSON and register it."""
    RAW.parent.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(URL, context=context, timeout=60) as response:
        RAW.write_bytes(response.read())
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "mledoze/world-countries",
            "title": "countries.json: ISO 3166-1 alpha-2, alpha-3 and numeric codes with names",
            "url": "https://github.com/mledoze/world-countries",
            "how_obtained": f"downloaded from {URL} by "
            "script/power/geography/fetch_country_codes.py",
            "accessed_date": date.today().isoformat(),
            "license": "Open Data Commons Open Database License (ODbL) 1.0",
            "used_by": "geography;grid;projects",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "geography", RAW, SOURCE_ID, "countries.json", f"world-countries {VERSION}", data_root=DATA
    )
    print(f"{RAW.relative_to(REPO)}: {RAW.stat().st_size:,} bytes, sha256 {digest[:16]}")


if __name__ == "__main__":
    main()
