"""Extract Australian passenger-vehicle distance from the ABS Survey of Motor Vehicle Use.

Input   data/auto/vehicle_usage/raw/abs_survey_motor_vehicle_use_2020.xls (ABS 9208.0 data
        cube 92080DO001_202006, Table 1: summary of motor vehicle use by type of vehicle for
        the survey years 2012, 2014, 2016, 2018 and 2020 — the final edition of the survey)
Output  data/auto/vehicle_usage/processed/vehicle_usage_au_smvu.csv (long format)

Series (country AU, passenger vehicles): ``car_traffic`` total kilometres (million vkm),
``car_stock_smvu`` vehicles in the survey frame, ``car_vkt_avg`` average kilometres per
vehicle (km, published in thousands). The 2020 survey year covers the twelve months to
30 June 2020 and includes the first pandemic restrictions; the survey was discontinued after
it, so 2018 is the last unaffected observation.

Run from the repository root:  .venv/bin/python script/auto/vehicle_usage/extract_abs_smvu.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import xlrd

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "vehicle_usage"
RAW = DATASET / "raw" / "abs_survey_motor_vehicle_use_2020.xls"
OUT = DATASET / "processed" / "vehicle_usage_au_smvu.csv"

SOURCE_ID = "abs_survey_motor_vehicle_use_2020"
SHEET, HEADER_ROW, BLOCK = "Table_1", 4, "Passenger vehicles"
COLUMNS = {
    # header label -> (series, unit, multiplier)
    "Total kilometres travelled": ("car_traffic", "million_vkm", 1.0),
    "Number of vehicles": ("car_stock_smvu", "vehicles", 1.0),
    "Average kilometres travelled": ("car_vkt_avg", "km", 1000.0),
}
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def main() -> None:
    """Read the passenger-vehicle block of Table 1."""
    sh = xlrd.open_workbook(RAW).sheet_by_name(SHEET)
    cols: dict[str, int] = {}
    for c in range(sh.ncols):
        label = str(sh.cell_value(HEADER_ROW, c)).strip()
        if label in COLUMNS and label not in cols:
            cols[label] = c
    if len(cols) != len(COLUMNS):
        raise SystemExit(f"{SHEET}: expected columns {list(COLUMNS)}, found {list(cols)}")

    out: list[dict[str, object]] = []
    started = False
    for r in range(HEADER_ROW + 1, sh.nrows):
        first = str(sh.cell_value(r, 0)).strip()
        if first == BLOCK:
            started = True
            continue
        if not started:
            continue
        if not first.replace(".0", "").isdigit():
            break
        for label, (series, unit, mult) in COLUMNS.items():
            out.append(
                {
                    "country": "AU",
                    "series": series,
                    "year": int(float(first)),
                    "value": float(sh.cell_value(r, cols[label])) * mult,
                    "unit": unit,
                    "source_id": SOURCE_ID,
                    "source_file": RAW.name,
                }
            )
    if not out:
        raise SystemExit("no passenger-vehicle rows found; the workbook layout has changed")
    out.sort(key=lambda r: (str(r["series"]), int(str(r["year"]))))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    avg = {int(str(r["year"])): r["value"] for r in out if r["series"] == "car_vkt_avg"}
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows; AU average km per passenger vehicle {avg}")


if __name__ == "__main__":
    main()
