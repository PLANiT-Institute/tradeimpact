"""Extract Australian passenger-vehicle stock, age and fuel mix from the ABS Motor Vehicle Census.

Input   data/auto/vehicle_usage/raw/abs_motor_vehicle_census_2021.xls (ABS 9309.0 data cube
        93090DO001_2021; census dates 31 January 2016, 2020 and 2021 — the final edition of
        the series)
Output  data/auto/vehicle_usage/processed/vehicle_usage_au.csv (long format)

Series (country AU, national totals):
    car_stock             passenger vehicles on register (Table 1, Australia column)
    car_mean_age_years    estimated average age of passenger vehicles (Table 3, Australia)
    car_stock_petrol / car_stock_diesel / car_stock_other_fuel   passenger vehicles by fuel
                          (Table 4; ``other`` includes electric, hybrid, LPG and unknown)

Run from the repository root:  .venv/bin/python script/auto/vehicle_usage/extract_abs_mvc.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import xlrd

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "vehicle_usage"
RAW = DATASET / "raw" / "abs_motor_vehicle_census_2021.xls"
OUT = DATASET / "processed" / "vehicle_usage_au.csv"

SOURCE_ID = "abs_motor_vehicle_census_2021"
BLOCK = "PASSENGER VEHICLES"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def block_rows(sheet: xlrd.sheet.Sheet, header_row: int) -> list[list[object]]:
    """Rows of the PASSENGER VEHICLES block: the year rows that follow its label."""
    rows: list[list[object]] = []
    started = False
    for r in range(header_row, sheet.nrows):
        first = str(sheet.cell_value(r, 0)).strip()
        if first == BLOCK:
            started = True
            continue
        if started:
            if first == "" or not first.replace(".0", "").isdigit():
                break
            rows.append([sheet.cell_value(r, c) for c in range(sheet.ncols)])
    return rows


def column(sheet: xlrd.sheet.Sheet, header_row: int, label: str) -> int:
    """Index of the column whose header equals ``label``."""
    for c in range(sheet.ncols):
        if str(sheet.cell_value(header_row, c)).strip() == label:
            return c
    raise SystemExit(f"{sheet.name}: no column {label!r}")


def main() -> None:
    """Read the national passenger-vehicle series from Tables 1, 3 and 4."""
    wb = xlrd.open_workbook(RAW)
    out: list[dict[str, object]] = []

    def add(series: str, year: float, value: float, unit: str) -> None:
        out.append(
            {
                "country": "AU",
                "series": series,
                "year": int(year),
                "value": value,
                "unit": unit,
                "source_id": SOURCE_ID,
                "source_file": RAW.name,
            }
        )

    for table, series, unit in (
        ("Table_1", "car_stock", "vehicles"),
        ("Table_3", "car_mean_age_years", "years"),
    ):
        sh = wb.sheet_by_name(table)
        col = column(sh, 4, "Australia")
        for row in block_rows(sh, 4):
            add(series, float(str(row[0])), float(str(row[col])), unit)

    sh = wb.sheet_by_name("Table_4")
    fuel_cols = {
        "car_stock_petrol": column(sh, 5, "Total"),
        "car_stock_diesel": column(sh, 5, "Diesel"),
        "car_stock_other_fuel": column(sh, 5, "Other"),
    }
    for row in block_rows(sh, 5):
        for series, col in fuel_cols.items():
            add(series, float(str(row[0])), float(str(row[col])), "vehicles")

    if not out:
        raise SystemExit("no passenger-vehicle rows found; the workbook layout has changed")
    out.sort(key=lambda r: (str(r["series"]), int(str(r["year"]))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    latest = max(int(str(r["year"])) for r in out)
    stock = next(r["value"] for r in out if r["series"] == "car_stock" and r["year"] == latest)
    age = next(
        r["value"] for r in out if r["series"] == "car_mean_age_years" and r["year"] == latest
    )
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rows; AU {latest}: {stock:,.0f} passenger "
        f"vehicles, mean age {age} y"
    )


if __name__ == "__main__":
    main()
