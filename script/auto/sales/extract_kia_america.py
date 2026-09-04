"""Kia America sales-by-month exports -> data/auto/sales/processed/sales_kia_us.csv

Input   data/auto/sales/raw/kia_america_<year>_sales_by_month.xlsx (sheet ``SalesByMonth``):
        MODEL, December of <year> and <year-1>, YEAR-TO-DATE of <year> and <year-1>.
Output  one row per (model, cohort year) with the full-year (December YTD) volume of <year>,
        taken from the export whose primary year it is. The comparison-year column of the next
        year's export is checked against it and any restatement is reported, not absorbed.

Basis: total US sales as reported by Kia America (``brand_total_sales``; retail and fleet not
split in the table). Powertrain is set only where the nameplate states it (EV6, EV9: BEV); the
rest are split downstream with EPA Automotive Trends production shares.

Run from the repository root:  .venv/bin/python script/auto/sales/extract_kia_america.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
OUT = REPO / "data" / "auto" / "sales" / "processed" / "sales_kia_us.csv"
SOURCE_ID = "kia_america_sales_by_month"
FIELDS = [
    "company",
    "destination",
    "destination_level",
    "origin",
    "cohort_year",
    "period",
    "model",
    "powertrain",
    "units",
    "basis",
    "source_id",
    "source_file",
]
BEV = {"EV6", "EV9", "Niro EV", "EV5", "EV3", "EV4"}


def to_int(value: object) -> int:
    """'12,933' -> 12933; '-' -> 0."""
    s = str(value).strip().replace(",", "")
    return 0 if s in {"-", "nan", ""} else int(s)


def read_export(path: Path) -> tuple[int, dict[str, int], dict[str, int], int, int]:
    """(year, ytd of year by model, ytd of year-1 by model, total year, total year-1)."""
    df = pd.read_excel(path, sheet_name="SalesByMonth", header=None)
    header = df.iloc[1].tolist()
    if str(header[0]).strip() != "MODEL" or str(df.iat[0, 4]).strip() != "YEAR-TO-DATE":
        raise SystemExit(f"{path.name}: unexpected layout {header}")
    year = int(header[4])
    cur: dict[str, int] = {}
    old: dict[str, int] = {}
    totals = (0, 0)
    for i in range(2, len(df)):
        model = str(df.iat[i, 0]).strip()
        if model == "TOTAL":
            totals = (to_int(df.iat[i, 4]), to_int(df.iat[i, 5]))
            continue
        cur[model] = to_int(df.iat[i, 4])
        old[model] = to_int(df.iat[i, 5])
    if sum(cur.values()) != totals[0] or sum(old.values()) != totals[1]:
        raise SystemExit(f"{path.name}: model rows do not sum to TOTAL")
    return year, cur, old, totals[0], totals[1]


def main() -> None:
    """Extract every Kia America export on disk and cross-check overlapping years."""
    exports = {}
    for path in sorted(RAW.glob("kia_america_*_sales_by_month.xlsx")):
        year, cur, old, tot, tot_prev = read_export(path)
        exports[year] = (path.name, cur, old, tot, tot_prev)
    rows: list[dict[str, object]] = []
    for year, (name, cur, _old, _tot, tot_prev) in sorted(exports.items()):
        if year - 1 in exports:
            restated = exports[year - 1][3] - tot_prev
            if restated:
                print(
                    f"note: {year - 1} total in {name} differs from its own export by {restated:+,}"
                )
        for model, units in cur.items():
            if units == 0:
                continue
            rows.append(
                {
                    "company": "kia",
                    "destination": "US",
                    "destination_level": "country",
                    "origin": "",
                    "cohort_year": year,
                    "period": f"{year}-01..{year}-12",
                    "model": model,
                    "powertrain": "BEV" if model in BEV else "",
                    "units": units,
                    "basis": "brand_total_sales",
                    "source_id": SOURCE_ID,
                    "source_file": name,
                }
            )
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    totals = {y: e[3] for y, e in exports.items()}
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; totals "
        + ", ".join(f"{y} {t:,}" for y, t in sorted(totals.items()))
    )


if __name__ == "__main__":
    main()
