"""Japan's inventory workbook -> country_emissions_jp.csv (road CO2 by vehicle segment).

Input   raw/gio_nies_inventory_co2_by_sector.xlsx, sheet ``3.Allocated_CO2-sector``
Output  processed/country_emissions_jp.csv
        co2_passenger_car   　乗用車 Passenger Vehicle, ktCO2, fiscal years
        co2_bus             　バス Bus
        co2_freight         貨物自動車/トラック Truck and Lorry
        road_co2_passenger  自動車（旅客）Road Transportation, the parent of cars and buses

Japan publishes the vehicle-type split directly, which Korea does not: there the split had to
be borrowed from a bottom-up local inventory. These rows are therefore tier A.

Two things the table does not say in its cells. The years are **fiscal** (April to March), not
calendar, so a fiscal 2024 figure covers April 2024 to March 2025. And the sheet lays its data
out from column Q onward, with the label in two columns (Japanese, then English), so the reader
locates both by content rather than by position.

Run from the repository root:
    .venv/bin/python script/auto/country_emissions/extract_jp_inventory.py
"""

from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "country_emissions"
RAW = DATA / "raw" / "gio_nies_inventory_co2_by_sector.xlsx"
OUT = DATA / "processed" / "country_emissions_jp.csv"
SHEET = "3.Allocated_CO2-sector"
SOURCE_ID = "gio_nies_inventory"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]
#: The English label of each row we take -> the series name. English is used as the key because
#: the Japanese labels carry furigana and leading spaces that differ between editions.
ROWS = {
    "Passenger Vehicle": "co2_passenger_car",
    "Bus": "co2_bus",
    "Truck and Lorry": "co2_freight",
    "Road Transportation": "road_co2_passenger",
}


def clean(value: object) -> str:
    """Comparable label text."""
    return unicodedata.normalize("NFKC", str(value)).replace("　", " ").strip()


def main() -> None:
    """Write one row per segment and fiscal year."""
    df = pd.read_excel(RAW, sheet_name=SHEET, header=None)
    years: dict[int, int] = {}
    for i in range(len(df)):
        found = {
            j: int(v)
            for j, v in enumerate(df.iloc[i])
            if isinstance(v, (int, float))
            and not pd.isna(v)
            and 1990 <= float(v) <= 2100
            and float(v).is_integer()
        }
        if len(found) >= 20:
            years = found
            break
    if not years:
        raise SystemExit(f"{RAW.name} {SHEET}: no year header row with 20 or more years")

    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for i in range(len(df)):
        labels = {clean(v) for v in df.iloc[i, :40].tolist()}
        for label, series in ROWS.items():
            if label not in labels or series in seen:
                continue
            seen.add(series)
            for col, year in sorted(years.items()):
                value = pd.to_numeric(df.iat[i, col], errors="coerce")
                if pd.isna(value):
                    continue
                rows.append(
                    {
                        "country": "JP",
                        "series": series,
                        "year": year,
                        "value": round(float(value), 3),
                        "unit": "ktCO2",
                        "source_id": SOURCE_ID,
                        "source_file": RAW.name,
                    }
                )
    missing = set(ROWS.values()) - seen
    if missing:
        raise SystemExit(f"{RAW.name} {SHEET}: rows not found for {sorted(missing)}")
    rows.sort(key=lambda r: (str(r["series"]), int(str(r["year"]))))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    latest = max(int(str(r["year"])) for r in rows)
    summary = {
        str(r["series"]): float(str(r["value"])) for r in rows if int(str(r["year"])) == latest
    }
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; fiscal {latest} "
        + ", ".join(f"{k} {v:,.0f} kt" for k, v in sorted(summary.items()))
    )


if __name__ == "__main__":
    main()
