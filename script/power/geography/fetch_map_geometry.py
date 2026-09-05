"""Download the world geometry the power report's unit map is drawn on.

Source of truth: topojson/world-atlas (https://github.com/topojson/world-atlas), Natural Earth
1:110m admin-0 countries as TopoJSON with ISO 3166-1 numeric ids, read from its npm distribution
on jsDelivr, version pinned. The file is loaded into the sector database as one row
(``map_geometry``) so the page needs no second fetch.

Run from the repository root:  .venv/bin/python script/power/geography/fetch_map_geometry.py
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
RAW = DATA / "geography" / "raw" / "countries-110m.json"
VERSION = "2.0.2"
URL = f"https://cdn.jsdelivr.net/npm/world-atlas@{VERSION}/countries-110m.json"
SOURCE_ID = "world_atlas_110m"


def main() -> None:
    """Download the TopoJSON and register it."""
    RAW.parent.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(URL, context=context, timeout=120) as response:
        RAW.write_bytes(response.read())
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "topojson/world-atlas (Mike Bostock), from Natural Earth 1:110m admin-0",
            "title": "countries-110m.json: world country polygons as TopoJSON, id = ISO numeric",
            "url": "https://github.com/topojson/world-atlas",
            "how_obtained": f"downloaded from {URL} by "
            "script/power/geography/fetch_map_geometry.py",
            "accessed_date": date.today().isoformat(),
            "license": "ISC (world-atlas); Natural Earth data public domain",
            "used_by": "database (map_geometry); report map",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "geography",
        RAW,
        SOURCE_ID,
        "countries-110m.json",
        f"world-atlas {VERSION}",
        data_root=DATA,
    )
    print(f"{RAW.relative_to(REPO)}: {RAW.stat().st_size:,} bytes, sha256 {digest[:16]}")


if __name__ == "__main__":
    main()
