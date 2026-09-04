"""Fetch the Eurostat cubes behind the EU27 usage and emissions datasets, straight from the API.

Each cube is the API's JSON-stat 2.0 response saved verbatim as a raw file (the source of
truth publishes JSON); the
request URL, dataset page, access date and file hash are recorded in
data/auto/registry/raw_files.csv
on every fetch:
    vehicle_usage/raw/eurostat_road_eqs_carpda.json    passenger-car stock by motor energy
    vehicle_usage/raw/eurostat_road_tf_veh.json        traffic by cars registered in the country
    vehicle_usage/raw/eurostat_road_tf_vehmov.json     traffic on the territory (fallback only)
    vehicle_usage/raw/eurostat_road_eqs_carage.json    passenger cars by age class
    country_emissions/raw/eurostat_env_air_gge_car_co2.json      CO2, CRF 1.A.3.b.i, all countries
    country_emissions/raw/eurostat_env_air_gge_eu_power_co2.json CO2, CRF 1.A.1.a, EU27
    country_emissions/raw/eurostat_env_air_gge_eu_transport.json GHG, CRF 1.A.3, EU27

Existing raw files are never overwritten unless --force is given: raw data is pinned once
obtained.

Run from the repository root:  .venv/bin/python script/auto/vehicle_usage/fetch_eurostat.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import ssl
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
BROWSER = "https://ec.europa.eu/eurostat/databrowser/view/{dataset}/default/table?lang=en"
USER_AGENT = "tradeimpact/0.2 source acquisition"
SINCE = "2015"

# (output path, dataset, filters, description)
CUBES: list[tuple[Path, str, dict[str, str], str]] = [
    (
        DATA / "vehicle_usage" / "raw" / "eurostat_road_eqs_carpda.json",
        "road_eqs_carpda",
        {"unit": "NR", "mot_nrg": "TOTAL", "leg_form": "TOTAL", "sinceTimePeriod": SINCE},
        "passenger cars by motor energy, stock, all legal forms",
    ),
    (
        DATA / "vehicle_usage" / "raw" / "eurostat_road_tf_veh.json",
        "road_tf_veh",
        {
            "vehicle": "CAR",
            "mot_nrg": "TOTAL",
            "regisveh": "TER_REGNAT",
            "unit": "MIO_VKM",
            "sinceTimePeriod": SINCE,
        },
        "road traffic by cars registered in the reporting country, million vehicle-km",
    ),
    (
        DATA / "vehicle_usage" / "raw" / "eurostat_road_tf_vehmov.json",
        "road_tf_vehmov",
        {"vehicle": "CAR", "regisveh": "TERNAT_REG", "unit": "MIO_VKM", "sinceTimePeriod": SINCE},
        "road traffic on the national territory by cars, million vehicle-km (fallback only)",
    ),
    (
        DATA / "vehicle_usage" / "raw" / "eurostat_road_eqs_carage.json",
        "road_eqs_carage",
        {"unit": "NR", "sinceTimePeriod": SINCE},
        "passenger cars by age class",
    ),
    (
        DATA / "country_emissions" / "raw" / "eurostat_env_air_gge_car_co2.json",
        "env_air_gge",
        {"airpol": "CO2", "src_crf": "CRF1A3B1", "unit": "THS_T", "sinceTimePeriod": SINCE},
        "GHG inventory: CO2 from passenger cars (CRF 1.A.3.b.i), thousand tonnes",
    ),
    (
        DATA / "country_emissions" / "raw" / "eurostat_env_air_gge_eu_power_co2.json",
        "env_air_gge",
        {
            "airpol": "CO2",
            "src_crf": "CRF1A1A",
            "unit": "THS_T",
            "geo": "EU27_2020",
            "sinceTimePeriod": "1990",
        },
        "GHG inventory: CO2 from public electricity and heat (CRF 1.A.1.a), EU27, thousand tonnes",
    ),
    (
        DATA / "country_emissions" / "raw" / "eurostat_env_air_gge_eu_transport.json",
        "env_air_gge",
        {
            "airpol": "GHG",
            "src_crf": "CRF1A3",
            "unit": "MIO_T",
            "geo": "EU27_2020",
            "sinceTimePeriod": "1990",
        },
        "GHG inventory: all GHG from transport (CRF 1.A.3), EU27, million tonnes CO2e",
    ),
]


def fetch(dataset: str, filters: dict[str, str]) -> tuple[str, dict]:
    """GET one cube as JSON-stat 2.0; return (url, payload)."""
    url = f"{API}{dataset}?format=JSON&lang=EN&{urllib.parse.urlencode(filters)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=300, context=context) as response:  # noqa: S310
        payload = json.loads(response.read().decode())
    if "value" not in payload or "dimension" not in payload:
        raise SystemExit(f"eurostat {dataset}: unexpected payload")
    return url, payload


def register(path: Path, dataset: str, url: str, description: str, accessed: str) -> None:
    """Upsert this file's row in data/auto/registry/raw_files.csv (link, hash, access date)."""
    registry = DATA / "registry" / "raw_files.csv"
    rows = list(csv.DictReader(registry.open(newline="")))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    row = {
        "dataset": path.parent.parent.name,
        "file": path.name,
        "source_id": f"eurostat_{dataset}",
        "original_name": f"{dataset} (JSON-stat 2.0)",
        "sha256": digest,
        "note": (
            f"{description}; fetched {accessed} from {url} ; dataset page "
            f"{BROWSER.format(dataset=dataset)}"
        ),
    }
    rows = [r for r in rows if not (r["dataset"] == row["dataset"] and r["file"] == row["file"])]
    rows.append(row)
    with registry.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    """Fetch every cube not yet on disk and register it."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="overwrite existing raw files")
    args = parser.parse_args()
    accessed = date.today().isoformat()
    for out, dataset, filters, description in CUBES:
        if out.exists() and not args.force:
            print(f"{out.relative_to(REPO)}: pinned, skipped")
            continue
        url, payload = fetch(dataset, filters)
        snapshot = {
            "accessed_date": accessed,
            "source_id": f"eurostat_{dataset}",
            "dataset": dataset,
            "description": description,
            "dataset_page": BROWSER.format(dataset=dataset),
            "request_url": url,
            "filters": filters,
            "response": payload,
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(snapshot, indent=1, sort_keys=True) + "\n")
        register(out, dataset, url, description, accessed)
        print(
            f"{out.relative_to(REPO)}: {len(payload['value']):,} values; "
            f"updated {payload.get('updated', '')}"
        )


if __name__ == "__main__":
    main()
