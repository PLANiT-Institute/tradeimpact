"""Fetch Australia's Paris Agreement inventory from the ANGA OData API (source of truth).

Australia's National Greenhouse Accounts publish the inventory as an OData v4 feed at
https://greenhouseaccounts.climatechange.gov.au/OData. The entity set
``AR5_ParisInventory_AUSTRALIA`` holds every UNFCCC category x gas x inventory year since
1990 (Gg). The server refuses $top and $filter on category columns, so the whole set is
fetched and saved verbatim as data/auto/country_emissions/raw/anga_paris_inventory_australia.json
(with request URL, access date and row count) and registered in data/auto/registry/raw_files.csv.

Run from the repository root:  .venv/bin/python script/auto/country_emissions/fetch_anga_odata.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import ssl
import urllib.request
from datetime import date
from pathlib import Path

import certifi

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
OUT = DATA / "country_emissions" / "raw" / "anga_paris_inventory_australia.json"
SERVICE = "https://greenhouseaccounts.climatechange.gov.au/OData"
ENTITY = "AR5_ParisInventory_AUSTRALIA"
SOURCE_ID = "anga_odata_paris_inventory"
USER_AGENT = "tradeimpact/0.2 source acquisition"


def main() -> None:
    """Download the entity set once; raw files are pinned unless --force."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="overwrite the pinned raw file")
    args = parser.parse_args()
    if OUT.exists() and not args.force:
        print(f"{OUT.relative_to(REPO)}: pinned, skipped")
        return
    url = f"{SERVICE}/{ENTITY}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=900, context=context) as response:  # noqa: S310
        payload = json.loads(response.read().decode())
    rows = payload.get("value", [])
    if not rows or payload.get("@odata.nextLink"):
        raise SystemExit("unexpected ANGA response: empty or paged")
    accessed = date.today().isoformat()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "accessed_date": accessed,
                "source_id": SOURCE_ID,
                "service_document": SERVICE,
                "entity_set": ENTITY,
                "request_url": url,
                "rows": len(rows),
                "response": payload,
            },
            sort_keys=True,
        )
        + "\n"
    )
    registry = DATA / "registry" / "raw_files.csv"
    entries = list(csv.DictReader(registry.open(newline="")))
    entries = [
        e for e in entries if not (e["dataset"] == "country_emissions" and e["file"] == OUT.name)
    ]
    entries.append(
        {
            "dataset": "country_emissions",
            "file": OUT.name,
            "source_id": SOURCE_ID,
            "original_name": f"{ENTITY} (OData v4 JSON)",
            "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
            "note": (
                f"Australia Paris Agreement inventory by UNFCCC category x gas x year (Gg; "
                f"{len(rows)} rows; 1990 onward) fetched {accessed} from {url}"
            ),
        }
    )
    with registry.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(entries[0]))
        w.writeheader()
        w.writerows(entries)
    print(f"{OUT.relative_to(REPO)}: {len(rows):,} rows")


if __name__ == "__main__":
    main()
