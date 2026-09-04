"""Extract Australian passenger-car and power-sector emissions from the ANGA inventory.

Input   data/auto/country_emissions/raw/anga_paris_inventory_australia.json (ANGA OData
        entity set AR5_ParisInventory_AUSTRALIA, fetched by fetch_anga_odata.py)
Output  data/auto/country_emissions/processed/country_emissions_au.csv (long format)

Series (country AU; Gg in the source = kt here):
    car_co2        CO2 from Energy > Fuel Combustion > Transport > Road Transportation > Cars
    car_ghg_co2e   CO2-e (AR5) from the same category, CO2 + CH4 + N2O components summed
    power_co2      CO2 from Energy Industries > Public Electricity and Heat Production
    transport_ghg  CO2-e (AR5) from Transport (all sub-categories summed)

Run from the repository root:
    .venv/bin/python script/auto/country_emissions/extract_anga_inventory.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "country_emissions"
RAW = DATASET / "raw" / "anga_paris_inventory_australia.json"
OUT = DATASET / "processed" / "country_emissions_au.csv"

CO2E = "CO2-e - AR5"
CARS = ("Energy", "Fuel Combustion", "Transport", "Road Transportation", "Cars")
POWER = ("Energy", "Fuel Combustion", "Energy Industries", "Public Electricity and Heat Production")
# series -> (category path prefix on UNFCCC_Level_1.., gas level 0, unit)
SERIES = {
    "car_co2": (
        ("Energy", "Fuel Combustion", "Transport", "Road Transportation", "Cars"),
        "CO2",
        "ktCO2",
    ),
    "car_ghg_co2e": (
        ("Energy", "Fuel Combustion", "Transport", "Road Transportation", "Cars"),
        CO2E,
        "ktCO2e",
    ),
    "power_co2": (
        (
            "Energy",
            "Fuel Combustion",
            "Energy Industries",
            "Public Electricity and Heat Production",
        ),
        "CO2",
        "ktCO2",
    ),
    "transport_ghg": (("Energy", "Fuel Combustion", "Transport"), CO2E, "ktCO2e"),
}
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def path_of(row: dict) -> tuple[str, ...]:
    """The non-empty UNFCCC category labels of a row, level 1 downward."""
    labels = []
    for i in range(1, 11):
        v = row.get(f"UNFCCC_Level_{i}")
        if v in (None, ""):
            break
        labels.append(v)
    return tuple(labels)


def main() -> None:
    """Sum every row under each series' category prefix and gas, per year."""
    snap = json.loads(RAW.read_text())
    rows = snap["response"]["value"]
    parents = {path_of(r)[:-1] for r in rows if path_of(r)}
    totals: dict[tuple[str, int], float] = defaultdict(float)
    for r in rows:
        p = path_of(r)
        if p in parents:
            continue  # a parent category: its value is the sum of its leaves
        for series, (prefix, gas, _unit) in SERIES.items():
            if p[: len(prefix)] == prefix and r["Gas_Level_0"] == gas and r["Gg"] is not None:
                # For CO2-e the leaf rows are the gas components (Gas_Level_1 set); for a
                # plain gas the leaf rows have Gas_Level_1 empty. Sum leaves only.
                if gas == CO2E and not r.get("Gas_Level_1"):
                    continue
                if gas != CO2E and r.get("Gas_Level_1"):
                    continue
                totals[(series, int(r["InventoryYear_ID"]))] += float(r["Gg"])
    out = [
        {
            "country": "AU",
            "series": series,
            "year": year,
            "value": round(value, 3),
            "unit": SERIES[series][2],
            "source_id": snap["source_id"],
            "source_file": RAW.name,
        }
        for (series, year), value in sorted(totals.items())
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    for series in SERIES:
        mine = [r for r in out if r["series"] == series]
        latest = mine[-1]
        mt = float(str(latest["value"])) / 1000
        print(f"{series}: {len(mine)} years to {latest['year']}, {mt:,.1f} Mt")
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows")


if __name__ == "__main__":
    main()
