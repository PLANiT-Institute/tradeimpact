"""Extract EU27 car CO2, grid intensity and EU aggregate series into the emissions schema.

Reads ``data/auto/vehicle_usage/raw/destination_eu27_inputs.json`` (shared raw file; the
Eurostat inventory series and the Ember-via-OWID grid intensity series were fetched into it
on the recorded ``accessed_date`` — links in method.md) and writes
``data/auto/country_emissions/processed/country_emissions_eu27.csv`` in long format.

Run from the repository root:
    .venv/bin/python script/auto/country_emissions/extract_eu27_snapshot.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "vehicle_usage" / "raw" / "destination_eu27_inputs.json"
OUT = REPO / "data" / "auto" / "country_emissions" / "processed" / "country_emissions_eu27.csv"

# raw key -> (series, unit, source_id); per-country series
COUNTRY_SERIES = {
    "car_co2_kt": ("car_co2", "ktCO2", "eurostat_env_air_gge_crf1a3b1"),
    "grid_intensity_gco2_kwh": ("grid_intensity", "gCO2_per_kWh", "owid_ember_grid_intensity"),
}
# raw key -> (series, unit, source_id); EU27 aggregate series
EU_SERIES = {
    "eu_power_co2_kt": ("power_co2", "ktCO2", "eurostat_env_air_gge_crf1a1a"),
    "eu_transport_ghg_mt": ("transport_ghg", "MtCO2e", "eurostat_env_air_gge_crf1a3"),
}
EU_CODE = "EU27"

FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def main() -> None:
    """Flatten per-country and EU aggregate year series to long rows."""
    snap = json.loads(RAW.read_text())
    raw = snap["raw"]
    out: list[dict[str, object]] = []

    def add(country: str, series: str, year: str, value: object, unit: str, source_id: str) -> None:
        if value is None:
            return
        out.append(
            {
                "country": country,
                "series": series,
                "year": int(year),
                "value": float(value),
                "unit": unit,
                "source_id": source_id,
                "source_file": RAW.name,
            }
        )

    for key, (series, unit, source_id) in COUNTRY_SERIES.items():
        for country, years in raw[key].items():
            for year, value in years.items():
                add(country, series, year, value, unit, source_id)
    for key, (series, unit, source_id) in EU_SERIES.items():
        for year, value in raw[key].items():
            add(EU_CODE, series, year, value, unit, source_id)

    out.sort(key=lambda r: (str(r["country"]), str(r["series"]), int(str(r["year"]))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out)
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows, accessed {snap['accessed_date']}")


if __name__ == "__main__":
    main()
