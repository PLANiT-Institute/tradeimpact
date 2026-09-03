"""Fetch one brand's EU27 first registrations from the EEA CO2-monitoring API.

Reuses the exact aggregation query stored in the committed Toyota snapshot, with only the
brand term (``Mk``) swapped, so every brand snapshot has the same structure and filters:
dataset year, status Final, EU27, country x commercial name x powertrain buckets with the
registrations-weighted certified WLTP CO2 and electric consumption.

Writes ``data/auto/sales/raw/eea_<brand>_<year>_final.json`` with the query, its hash, the
response and its hash, and the access date — never overwriting an existing snapshot unless
``--force`` is given (raw files are pinned once obtained).

Run from the repository root:
    .venv/bin/python script/auto/sales/fetch_eea_registrations.py KIA
    .venv/bin/python script/auto/sales/fetch_eea_registrations.py HONDA
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RAW_DIR = REPO / "data" / "auto" / "sales" / "raw"
TEMPLATE = RAW_DIR / "eea_toyota_2024_final.json"
API = "https://co2cars.apps.eea.europa.eu/tools/api"
SOURCE_PAGE = "https://co2cars.apps.eea.europa.eu/"
USER_AGENT = "tradeimpact/0.2 source acquisition"


def sha256(value: object) -> str:
    """Hash of the canonical JSON encoding."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def swap_brand(node: object, old: str, new: str) -> int:
    """Replace every ``{"term": {"Mk": old}}`` in place; return how many were swapped."""
    count = 0
    if isinstance(node, dict):
        term = node.get("term")
        if isinstance(term, dict) and term.get("Mk") == old:
            term["Mk"] = new
            return 1
        for v in node.values():
            count += swap_brand(v, old, new)
    elif isinstance(node, list):
        for v in node:
            count += swap_brand(v, old, new)
    return count


def main() -> None:
    """Fetch and pin one brand snapshot."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("brand", help="EEA make (Mk) value, e.g. KIA or HONDA")
    parser.add_argument("--force", action="store_true", help="overwrite an existing snapshot")
    args = parser.parse_args()
    brand = args.brand.upper()

    template = json.loads(TEMPLATE.read_text())
    year = int(template["dataset_year"])
    out = RAW_DIR / f"eea_{brand.lower()}_{year}_final.json"
    if out.exists() and not args.force:
        raise SystemExit(f"{out.relative_to(REPO)} exists; raw files are pinned (use --force)")

    query = copy.deepcopy(template["query"])
    template_brand = template["brand_filter"].split("=", 1)[1]
    swapped = swap_brand(query, template_brand, brand)
    if swapped != 1:
        raise SystemExit(f"expected one Mk term in the template query, found {swapped}")

    url = f"{API}?source={urllib.parse.quote(json.dumps(query, separators=(',', ':')))}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310
        payload = json.loads(response.read().decode())

    total = payload["aggregations"]["registrations"]["value"]
    snapshot = {
        "accessed_date": date.today().isoformat(),
        "adapter_version": f"eea-{brand.lower()}-eu27-v2",
        "api_endpoint": API,
        "brand_filter": f"Mk={brand}",
        "dataset_status": template["dataset_status"],
        "dataset_year": year,
        "geography": template["geography"],
        "query": query,
        "query_sha256": sha256(query),
        "response": payload,
        "response_sha256": sha256(payload),
        "source_page": SOURCE_PAGE,
    }
    out.write_text(json.dumps(snapshot, indent=1, sort_keys=True) + "\n")
    countries = len(payload["aggregations"]["countries"]["buckets"])
    print(f"{out.relative_to(REPO)}: {int(total):,} registrations, {countries} countries")


if __name__ == "__main__":
    main()
