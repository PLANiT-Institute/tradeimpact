"""Extract US passenger-car emissions from the EPA GHG Inventory transcriptions.

Inputs (both hand-checked transcriptions of PDF text; the PDFs themselves are not stored —
their URLs and SHA-256 are in data/auto/raw_files.csv)
    raw/epa_ghg_inventory_2025_table_3_13.csv   main text Table 3-13: CO2 from fossil fuel
        combustion, passenger cars, MMT CO2 eq.; 1990, 2005, 2019-2023 -> series ``car_co2``
    raw/epa_ghg_inventory_2025_table_a_91.csv   Annex 3 Table A-91: total GHG from passenger
        cars by fuel (CO2 plus CH4 and N2O), MMT CO2 eq.; 1990, 2000, 2010, 2013-2023
        -> series ``car_ghg_co2e``
Output  processed/country_emissions_us.csv (long format, ktCO2 / ktCO2e)

``car_co2`` is the level series comparable with the EU inventory CRF 1.A.3.b.i CO2; it has
too few trend-window years for the S1 rule. ``car_ghg_co2e`` carries the annual 2013-2023
series and is within 0.5 % of the CO2 series where both exist, so it is the series for the S1
trend — that choice is recorded in emission_targets when the US rate is derived.

Run from the repository root:
    .venv/bin/python script/auto/country_emissions/extract_epa_inventory.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "country_emissions"
RAW = {
    "car_co2": (DATASET / "raw" / "epa_ghg_inventory_2025_table_3_13.csv", "ktCO2"),
    "car_ghg_co2e": (DATASET / "raw" / "epa_ghg_inventory_2025_table_a_91.csv", "ktCO2e"),
}
OUT = DATASET / "processed" / "country_emissions_us.csv"

KT_PER_MMT = 1000.0
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def main() -> None:
    """Sum the fuel rows per year for each table and write one long-format file."""
    out: list[dict[str, object]] = []
    for series, (path, unit) in RAW.items():
        by_year: dict[int, float] = defaultdict(float)
        source_ids: set[str] = set()
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if row["vehicle_type"] != "passenger_cars":
                    continue
                by_year[int(row["year"])] += float(row["value_mmt_co2e"])
                source_ids.add(row["source_id"])
        if len(source_ids) != 1:
            raise SystemExit(f"{path.name}: expected one source_id, found {source_ids}")
        out.extend(
            {
                "country": "US",
                "series": series,
                "year": year,
                "value": round(value * KT_PER_MMT, 1),
                "unit": unit,
                "source_id": next(iter(source_ids)),
                "source_file": path.name,
            }
            for year, value in sorted(by_year.items())
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    for series in RAW:
        rows = [r for r in out if r["series"] == series]
        latest = rows[-1]
        print(
            f"{series}: {len(rows)} years to {latest['year']}, "
            f"{float(str(latest['value'])) / 1000:,.1f} Mt"
        )
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows")


if __name__ == "__main__":
    main()
