"""Extract EU27 car CO2, grid intensity and EU aggregate series from their direct sources.

Inputs
    country_emissions/raw/eurostat_env_air_gge_car_co2.json      CO2 CRF 1.A.3.b.i per country
    country_emissions/raw/eurostat_env_air_gge_eu_power_co2.json  CO2 CRF 1.A.1.a, EU27 aggregate
    country_emissions/raw/eurostat_env_air_gge_eu_transport.json  GHG CRF 1.A.3, EU27 aggregate
    (JSON-stat responses fetched directly by vehicle_usage/fetch_eurostat.py)
    country_emissions/raw/owid_carbon_intensity_electricity.csv   Ember grid intensity via OWID
Output  country_emissions/processed/country_emissions_eu27.csv — long format; ``EU27`` is the
        aggregate code; Eurostat ``EL`` is recoded to ``GR``.

Run from the repository root:
    .venv/bin/python script/auto/country_emissions/extract_eu27_snapshot.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "country_emissions"
OUT = DATASET / "processed" / "country_emissions_eu27.csv"
OWID = DATASET / "raw" / "owid_carbon_intensity_electricity.csv"

EU = "EU27"
EU_AGGREGATE = "EU27_2020"
GEO_RECODE = {"EL": "GR"}
ISO3_TO_ALPHA2 = {
    "AUT": "AT",
    "BEL": "BE",
    "BGR": "BG",
    "HRV": "HR",
    "CYP": "CY",
    "CZE": "CZ",
    "DNK": "DK",
    "EST": "EE",
    "FIN": "FI",
    "FRA": "FR",
    "DEU": "DE",
    "GRC": "GR",
    "HUN": "HU",
    "IRL": "IE",
    "ITA": "IT",
    "LVA": "LV",
    "LTU": "LT",
    "LUX": "LU",
    "MLT": "MT",
    "NLD": "NL",
    "POL": "PL",
    "PRT": "PT",
    "ROU": "RO",
    "SVK": "SK",
    "SVN": "SI",
    "ESP": "ES",
    "SWE": "SE",
}
EU27 = set(ISO3_TO_ALPHA2.values())
# raw file -> (series, unit, source_id suffix, aggregate only?)
CUBES = {
    "eurostat_env_air_gge_car_co2.json": (
        "car_co2",
        "ktCO2",
        "eurostat_env_air_gge_crf1a3b1",
        False,
    ),
    "eurostat_env_air_gge_eu_power_co2.json": (
        "power_co2",
        "ktCO2",
        "eurostat_env_air_gge_crf1a1a",
        True,
    ),
    "eurostat_env_air_gge_eu_transport.json": (
        "transport_ghg",
        "MtCO2e",
        "eurostat_env_air_gge_crf1a3",
        True,
    ),
}
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def flatten(payload: dict) -> list[tuple[dict[str, str], float]]:
    """JSON-stat 2.0 cube -> [({dimension: category}, value)]."""
    ids: list[str] = payload["id"]
    sizes: list[int] = payload["size"]
    lookup = [
        {pos: key for key, pos in payload["dimension"][name]["category"]["index"].items()}
        for name in ids
    ]
    out = []
    for position, value in payload["value"].items():
        remainder = int(position)
        cats: list[str] = []
        for size, table in zip(reversed(sizes), reversed(lookup), strict=True):
            cats.append(table[remainder % size])
            remainder //= size
        out.append((dict(zip(ids, reversed(cats), strict=True)), float(value)))
    return out


def main() -> None:
    """Flatten the inventory cubes and filter the OWID export to the member states."""
    out: list[dict[str, object]] = []
    for name, (series, unit, source_id, aggregate) in CUBES.items():
        snap = json.loads((DATASET / "raw" / name).read_text())
        for cats, value in flatten(snap["response"]):
            geo = cats["geo"]
            if aggregate:
                if geo != EU_AGGREGATE:
                    continue
                country = EU
            else:
                country = GEO_RECODE.get(geo, geo)
                if country not in EU27:
                    continue
            out.append(
                {
                    "country": country,
                    "series": series,
                    "year": int(cats["time"]),
                    "value": value,
                    "unit": unit,
                    "source_id": source_id,
                    "source_file": name,
                }
            )
    with OWID.open(newline="") as f:
        for row in csv.DictReader(f):
            country = ISO3_TO_ALPHA2.get(row["Code"])
            if country is None or row["Carbon intensity"] == "":
                continue
            out.append(
                {
                    "country": country,
                    "series": "grid_intensity",
                    "year": int(row["Year"]),
                    "value": float(row["Carbon intensity"]),
                    "unit": "gCO2_per_kWh",
                    "source_id": "owid_ember_grid_intensity",
                    "source_file": OWID.name,
                }
            )
    out.sort(key=lambda r: (str(r["country"]), str(r["series"]), int(str(r["year"]))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows")


if __name__ == "__main__":
    main()
