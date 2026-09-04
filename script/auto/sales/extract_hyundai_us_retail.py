"""Hyundai IR "US Retail Sales by Model" workbooks -> data/auto/sales/processed/sales_hyundai_us.csv

Input   data/auto/sales/raw/hyundai_<year>_us_retail_sales.xlsx (sheet ``US``): one row per
        nameplate with Jan..Dec and Total, Hyundai and Genesis together, PC and RV blocks.
Output  one row per (company, model, cohort year) with the calendar-year total.

Basis. The sheet is titled "US Retail Sales" but its 2024 total (911,805) equals Hyundai Motor
America's reported total sales (836,802, fleet included) plus Genesis Motor America (75,003).
The rows are therefore brand total sales including fleet, not retail; ``basis`` records this as
``brand_total_sales``. US-built and imported cars are both inside (market-side count).

Company. Genesis nameplates (G70, G80, G90, GV60, GV70, GV80) are written with
``company = genesis`` so that companies.csv decides their scope; Hyundai rows carry ``hyundai``.

Powertrain is set only where the nameplate states it (IONIQ 5/6/9 and the EV variants: BEV;
Nexo: FCEV). Nameplates sold with several powertrains (Tucson, Santa Fe, ...) are left blank and
split downstream with the EPA Automotive Trends production shares.

Run from the repository root:  .venv/bin/python script/auto/sales/extract_hyundai_us_retail.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
OUT = REPO / "data" / "auto" / "sales" / "processed" / "sales_hyundai_us.csv"
SOURCE_ID = "hyundai_ir_sales_results"
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
GENESIS = re.compile(r"^(G70|G80|G90|GV60|GV70|GV80)\b")
BEV = re.compile(r"^(IONIQ 5|IONIQ 6|IONIQ 9|IONIQ$)|\bEV\b", re.IGNORECASE)
SKIP = {"Sub-total", "Total", "US Total Industry", "HMC Market Share"}


def powertrain(model: str) -> str:
    """Powertrain stated by the nameplate itself, else blank."""
    if model.lower() == "nexo":
        return "FCEV"
    if model == "IONIQ":
        return ""  # the first-generation Ioniq came as HEV, PHEV and EV
    if BEV.search(model):
        return "BEV"
    return ""


def extract(path: Path, year: int) -> list[dict[str, object]]:
    """Rows of one year's workbook."""
    df = pd.read_excel(path, sheet_name="US", header=None)
    header_row = df.index[df.iloc[:, 3].astype(str).str.strip() == "Jan"][0]
    total_col = df.columns[df.iloc[header_row].astype(str).str.strip() == "Total"][0]
    month_cols = list(df.columns[3:total_col])
    rows: list[dict[str, object]] = []
    grand_total = None
    for i in range(header_row + 1, len(df)):
        label = df.iat[i, 2]
        block = str(df.iat[i, 1]).strip()
        if block == "Total":
            grand_total = int(df.iat[i, total_col])
            continue
        if not isinstance(label, str) or label.strip() in SKIP:
            continue
        model = label.strip()
        total = int(df.iat[i, total_col])
        months = int(pd.to_numeric(df.iloc[i, month_cols], errors="coerce").fillna(0).sum())
        if months != total:
            raise SystemExit(f"{path.name} {model}: months {months} != total {total}")
        if total == 0:
            continue
        rows.append(
            {
                "company": "genesis" if GENESIS.match(model) else "hyundai",
                "destination": "US",
                "destination_level": "country",
                "origin": "",
                "cohort_year": year,
                "period": f"{year}-01..{year}-12",
                "model": model,
                "powertrain": powertrain(model),
                "units": total,
                "basis": "brand_total_sales",
                "source_id": SOURCE_ID,
                "source_file": path.name,
            }
        )
    if grand_total is None or sum(int(r["units"]) for r in rows) != grand_total:
        raise SystemExit(f"{path.name}: model rows do not sum to the Total row {grand_total}")
    return rows


def main() -> None:
    """Extract every us_retail_sales workbook on disk."""
    rows: list[dict[str, object]] = []
    for path in sorted(RAW.glob("hyundai_*_us_retail_sales.xlsx")):
        year = int(path.name.split("_")[1])
        rows.extend(extract(path, year))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    by_year = {}
    for r in rows:
        key = (r["cohort_year"], r["company"])
        by_year[key] = by_year.get(key, 0) + int(r["units"])
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; "
        + ", ".join(f"{k[1]} {k[0]} {v:,}" for k, v in sorted(by_year.items()))
    )


if __name__ == "__main__":
    main()
