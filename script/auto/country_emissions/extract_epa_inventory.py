"""Extract US passenger-car CO2 from the EPA GHG Inventory Table 3-13 transcription.

Input   data/auto/country_emissions/raw/epa_ghg_inventory_2025_table_3_13.csv — the passenger-car
        rows of Table 3-13 (CO2 from fossil fuel combustion in the transportation end-use sector,
        MMT CO2 eq.) as extracted from the inventory PDF text; the PDF itself (18 MB) is not
        stored — its URL and SHA-256 are in data/auto/raw_files.csv.
Output  data/auto/country_emissions/processed/country_emissions_us.csv — series ``car_co2`` in
        ktCO2 (gasoline + diesel passenger cars), one row per reported year.

The main-text table reports 1990, 2005 and the last five years only. That is too few points
in the 2015-2024 trend window for the S1 log-linear rule (which needs four, and excludes
2020-2021), so a US S1 rate needs the inventory annex time series before it can be derived.

Run from the repository root:
    .venv/bin/python script/auto/country_emissions/extract_epa_inventory.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "country_emissions"
RAW = DATASET / "raw" / "epa_ghg_inventory_2025_table_3_13.csv"
OUT = DATASET / "processed" / "country_emissions_us.csv"

KT_PER_MMT = 1000.0
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def main() -> None:
    """Sum the fuel rows per year and write the long-format series."""
    by_year: dict[int, float] = defaultdict(float)
    source_ids: set[str] = set()
    with RAW.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["vehicle_type"] != "passenger_cars":
                continue
            by_year[int(row["year"])] += float(row["value_mmt_co2e"])
            source_ids.add(row["source_id"])
    if len(source_ids) != 1:
        raise SystemExit(f"expected one source_id in the transcription, found {source_ids}")
    out = [
        {
            "country": "US",
            "series": "car_co2",
            "year": year,
            "value": round(value * KT_PER_MMT, 1),
            "unit": "ktCO2",
            "source_id": next(iter(source_ids)),
            "source_file": RAW.name,
        }
        for year, value in sorted(by_year.items())
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    latest = out[-1]
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} years; US passenger-car CO2 {latest['year']}: "
        f"{float(str(latest['value'])) / 1000:,.1f} MtCO2"
    )


if __name__ == "__main__":
    main()
