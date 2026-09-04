"""Download the world geometry and the ISO country-code list the dashboard map view reads.

Sources of truth
    world-atlas 2.0.2 (topojson/world-atlas, ISC licence), countries-110m.json: Natural Earth
    1:110m admin-0 countries (public domain) as TopoJSON, feature ids = ISO 3166-1 numeric.
        https://github.com/topojson/world-atlas   file via https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json
    world-countries 5.1.0 (mledoze/world-countries, ODbL 1.0), countries.json: ISO 3166-1
    alpha-2 (cca2), alpha-3 (cca3) and numeric (ccn3) codes with names.
        https://github.com/mledoze/world-countries   file via https://cdn.jsdelivr.net/npm/world-countries@5.1.0/countries.json

Outputs
    data/auto/dashboard/raw/countries-110m.json          geometry, loaded into the database
    data/auto/dashboard/raw/world_countries.json         code list as published
    data/auto/dashboard/method/country_codes.csv         iso_numeric, alpha2, alpha3, name (lookup)

Run from the repository root:  .venv/bin/python script/auto/dashboard/fetch_map_assets.py
"""

from __future__ import annotations

import argparse
import csv
import json
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "dashboard"
RAW = DATA / "raw"
METHOD = DATA / "method"
GEOMETRY = RAW / "countries-110m.json"
CODES_RAW = RAW / "world_countries.json"
CODES = METHOD / "country_codes.csv"
GEOMETRY_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json"
CODES_URL = "https://cdn.jsdelivr.net/npm/world-countries@5.1.0/countries.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (tradeimpact fetcher)"}


def download(url: str, dest: Path, context: ssl.SSLContext, force: bool) -> str:
    """Fetch one file unless present."""
    if dest.exists() and not force:
        return "kept"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=120) as r:
        data = r.read()
    json.loads(data)
    dest.write_bytes(data)
    return "fetched"


def main() -> None:
    """Fetch geometry and codes, write the code lookup, register everything."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    METHOD.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()

    status = download(GEOMETRY_URL, GEOMETRY, context, args.force)
    upsert_source(
        {
            "source_id": "world_atlas_110m",
            "publisher": (
                "topojson/world-atlas (Mike Bostock), from Natural Earth 1:110m admin-0 countries"
            ),
            "title": (
                "countries-110m.json: world country polygons as TopoJSON, feature id = ISO "
                "3166-1 numeric, name property"
            ),
            "url": "https://github.com/topojson/world-atlas",
            "how_obtained": (
                f"downloaded from {GEOMETRY_URL} by script/auto/dashboard/fetch_map_assets.py"
            ),
            "accessed_date": accessed,
            "license": "ISC (world-atlas); Natural Earth data public domain",
            "used_by": "build_database.py (table map_geometry); dashboard map view",
        }
    )
    d1 = upsert_raw_file(
        "dashboard", GEOMETRY, "world_atlas_110m", "countries-110m.json", f"{status} {accessed}"
    )

    status2 = download(CODES_URL, CODES_RAW, context, args.force)
    upsert_source(
        {
            "source_id": "world_countries_codes",
            "publisher": "mledoze/world-countries",
            "title": (
                "countries.json: ISO 3166-1 alpha-2, alpha-3 and numeric codes with country names"
            ),
            "url": "https://github.com/mledoze/world-countries",
            "how_obtained": (
                f"downloaded from {CODES_URL} by script/auto/dashboard/fetch_map_assets.py; "
                "reduced to method/country_codes.csv"
            ),
            "accessed_date": accessed,
            "license": "Open Data Commons Open Database License (ODbL) 1.0",
            "used_by": "dashboard.html map view (code lookup); build_database.py",
        }
    )
    d2 = upsert_raw_file(
        "dashboard", CODES_RAW, "world_countries_codes", "countries.json", f"{status2} {accessed}"
    )

    countries = json.loads(CODES_RAW.read_bytes())
    rows = sorted(
        (
            {
                "iso_numeric": c["ccn3"],
                "alpha2": c["cca2"],
                "alpha3": c["cca3"],
                "name": c["name"]["common"],
            }
            for c in countries
            if c.get("ccn3")
        ),
        key=lambda r: r["alpha2"],
    )
    with CODES.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["iso_numeric", "alpha2", "alpha3", "name"])
        w.writeheader()
        w.writerows(rows)
    print(
        f"{GEOMETRY.name} {status} {d1[:12]}; {CODES_RAW.name} {status2} {d2[:12]}; "
        f"{CODES.relative_to(REPO)}: {len(rows)} codes"
    )


if __name__ == "__main__":
    main()
