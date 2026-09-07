"""Download Ember's yearly electricity release and keep the fuel-level capacity and generation.

Source of truth: Ember, Yearly Electricity Data (full release, long format), the same release
whose carbon-intensity series this project already uses for the grid benchmark. It states, per
country and year, installed capacity in GW and electricity generation in TWh by fuel, which is
what a country-level capacity factor is computed from.

Output  utilisation/raw/ember/ember_yearly_fuel.csv   the rows of that release with Category in
                                                      {Capacity, Electricity generation},
                                                      Subcategory Fuel, Area type "Country or
                                                      economy"
        utilisation/raw/ember/index.csv               the original URL, its bytes and SHA-256, the
                                                      filter applied, and the subset's own SHA-256

The published file is ~49 MB and 99 % of it is aggregates and shares this model never reads, so
the raw copy on disk is a **filtered subset**: the filter is one expression, it is recorded in
``index.csv`` beside the original file's own SHA-256, and re-running this script from the URL
reproduces the subset exactly. Nothing in the kept rows is altered. It sits in its own raw
sub-directory so that the database loads the index rather than 140,000 rows of source data the
report never queries.

Run from the repository root:
    .venv/bin/python script/power/utilisation/fetch_ember_yearly.py [--refresh]
"""

from __future__ import annotations

import csv
import hashlib
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, write_csv  # noqa: E402
from registry import upsert_raw_file, upsert_source  # noqa: E402

URL = (
    "https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/"
    "yearly_full_release_long_format.csv"
)
LANDING = "https://ember-energy.org/data/yearly-electricity-data/"
RAW_DIR = DATA / "utilisation" / "raw" / "ember"
SUBSET = RAW_DIR / "ember_yearly_fuel.csv"
INDEX = RAW_DIR / "index.csv"
SOURCE_ID = "ember_yearly_electricity"
#: The one filter that produces the subset on disk.
CATEGORIES = ("Capacity", "Electricity generation")
SUBCATEGORY = "Fuel"
AREA_TYPE = "Country or economy"
KEEP = ["Area", "ISO 3 code", "Year", "Category", "Subcategory", "Variable", "Unit", "Value"]
INDEX_FIELDS = [
    "file",
    "url",
    "landing_page",
    "publisher",
    "original_bytes",
    "original_sha256",
    "filter",
    "rows_kept",
    "subset_sha256",
    "fetched",
    "what_it_states",
]


def main() -> None:
    """Download the release, write the filtered subset and record both hashes."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if SUBSET.exists() and "--refresh" not in sys.argv[1:]:
        print(f"{SUBSET.relative_to(REPO)} already on disk; --refresh to download again")
        return
    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(URL, headers={"User-Agent": "tradeimpact/1.0 (research)"})
    with urllib.request.urlopen(request, context=context, timeout=600) as response:
        body = response.read()
    rows = list(csv.DictReader(body.decode("utf-8-sig").splitlines()))
    kept = [
        {k: r[k] for k in KEEP}
        for r in rows
        if r["Category"] in CATEGORIES
        and r["Subcategory"] == SUBCATEGORY
        and r["Area type"] == AREA_TYPE
    ]
    write_csv(SUBSET, KEEP, kept)
    filter_text = (
        f"Category in {CATEGORIES}, Subcategory == {SUBCATEGORY!r}, Area type == {AREA_TYPE!r}; "
        f"columns kept: {', '.join(KEEP)}"
    )
    write_csv(
        INDEX,
        INDEX_FIELDS,
        [
            {
                "file": SUBSET.name,
                "url": URL,
                "landing_page": LANDING,
                "publisher": "Ember",
                "original_bytes": len(body),
                "original_sha256": hashlib.sha256(body).hexdigest(),
                "filter": filter_text,
                "rows_kept": len(kept),
                "subset_sha256": hashlib.sha256(SUBSET.read_bytes()).hexdigest(),
                "fetched": date.today().isoformat(),
                "what_it_states": "installed capacity in GW and electricity generation in TWh per "
                "country, fuel and year, from which the country-level capacity factor is computed",
            }
        ],
    )
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "Ember",
            "title": "Yearly Electricity Data (full release, long format): capacity and "
            "generation by country, fuel and year",
            "url": LANDING,
            "how_obtained": f"downloaded from {URL} by "
            "script/power/utilisation/fetch_ember_yearly.py, filtered to the fuel-level capacity "
            "and generation rows for countries and economies, and stored under "
            "data/power/utilisation/raw/ with the original file's bytes and SHA-256 and the "
            "filter expression in index.csv",
            "accessed_date": date.today().isoformat(),
            "license": "CC BY 4.0 (Ember)",
            "used_by": "utilisation",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "utilisation",
        SUBSET,
        SOURCE_ID,
        "yearly_full_release_long_format.csv (filtered to fuel-level capacity and generation)",
        f"{len(kept)} rows kept of {len(rows)}; the original's SHA-256 and the filter are in "
        "raw/ember/index.csv",
        data_root=DATA,
    )
    print(
        f"{SUBSET.relative_to(REPO)}: {len(kept)} rows kept of {len(rows)} "
        f"({len(body) / 1e6:.0f} MB downloaded); subset sha256 {digest[:16]}"
    )


if __name__ == "__main__":
    main()
