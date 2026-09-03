"""Extract grid carbon intensity for the non-EU importers from the OWID/Ember CSV.

Input   data/auto/country_emissions/raw/owid_carbon_intensity_electricity.csv
        (Our World in Data grapher export of Ember Yearly Electricity Data; all entities)
Output  data/auto/country_emissions/processed/country_emissions_owid_grid.csv
        long format, series ``grid_intensity``, for the importers not covered by the EU27
        snapshot (United States, Australia).

Run from the repository root:  .venv/bin/python script/auto/country_emissions/extract_owid_grid.py
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "country_emissions"
RAW = DATASET / "raw" / "owid_carbon_intensity_electricity.csv"
OUT = DATASET / "processed" / "country_emissions_owid_grid.csv"

# Importers in scope that the EU27 snapshot does not cover: OWID ISO3 -> repo alpha-2.
IMPORTERS = {"USA": "US", "AUS": "AU"}
SOURCE_ID = "owid_ember_grid_intensity"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def main() -> None:
    """Filter the OWID export to the in-scope importers, one row per year."""
    out: list[dict[str, object]] = []
    with RAW.open(newline="") as f:
        for row in csv.DictReader(f):
            code = IMPORTERS.get(row["Code"])
            if code is None or row["Carbon intensity"] == "":
                continue
            out.append({
                "country": code, "series": "grid_intensity", "year": int(row["Year"]),
                "value": float(row["Carbon intensity"]), "unit": "gCO2_per_kWh",
                "source_id": SOURCE_ID, "source_file": RAW.name,
            })
    out.sort(key=lambda r: (str(r["country"]), int(str(r["year"]))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    for code in IMPORTERS.values():
        years = [int(str(r["year"])) for r in out if r["country"] == code]
        print(f"{code}: {len(years)} years, {min(years)}-{max(years)}" if years else f"{code}: none")
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows")


if __name__ == "__main__":
    main()
