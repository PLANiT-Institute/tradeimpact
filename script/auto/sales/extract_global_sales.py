"""Worldwide sales per company and year: the denominator for global coverage.

Output  data/auto/sales/processed/global_sales_totals.csv
        company, cohort_year, units, basis, brands_covered, derived, derivation, source_id,
        source_file

Where each figure comes from, and what it counts.

    toyota   the group workbook's ``Sales`` sheet, row "Worldwide sales" of the Toyota (incl.
             Lexus) block, calendar-year column. Counts the Toyota and Lexus brands; Daihatsu
             and Hino are separate blocks and are not included.
    nissan   the global release's "Global sales" row. Counts Nissan and Infiniti.
    hyundai  derived, because Hyundai publishes no worldwide total: Korea domestic sales plus
             shipments exported from Korea plus sales by the overseas plants, each from its own
             Hyundai workbook. Counts the Hyundai and Genesis brands. The export leg is
             shipments rather than sales, so the figure is approximate and marked derived.
    kia      the retail workbook's every-destination total for the half year in scope. Counts
             the Kia brand.

Run from the repository root:  .venv/bin/python script/auto/sales/extract_global_sales.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "sales"
RAW = DATASET / "raw"
PROCESSED = DATASET / "processed"
OUT = PROCESSED / "global_sales_totals.csv"

FIELDS = [
    "company",
    "cohort_year",
    "units",
    "basis",
    "brands_covered",
    "derived",
    "derivation",
    "source_id",
    "source_file",
]
TOYOTA_FILE = RAW / "toyota_global_sales_202512.xlsx"
NISSAN_FILE = RAW / "nissan_global_sales_2025.csv"
KIA_FILE = PROCESSED / "sales_kia_ir_2026.csv"
HYUNDAI_KR = PROCESSED / "sales_hyundai_kr.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def toyota_rows() -> list[dict[str, object]]:
    """Toyota (including Lexus) worldwide sales for every calendar year the workbook closes."""
    df = pd.read_excel(TOYOTA_FILE, sheet_name="Sales", header=None)
    header = df.iloc[2].tolist()
    block = df.index[df.iloc[:, 1].astype(str).str.strip() == "Toyota (incl. Lexus)"]
    if not len(block):
        raise SystemExit(f"{TOYOTA_FILE.name}: no 'Toyota (incl. Lexus)' block")
    row = int(block[0]) + 1
    if "Worldwide sales" not in str(df.iat[row, 2]):
        raise SystemExit(f"{TOYOTA_FILE.name}: row after the block is not 'Worldwide sales'")
    out: list[dict[str, object]] = []
    for i, label in enumerate(header):
        text = str(label).strip()
        year = None
        if text.endswith(".0") and text[:4].isdigit():
            year = int(text[:4])
        elif "Cumulative Total" in text and text[:4].isdigit():
            year = int(text[:4])
        if year is None:
            continue
        value = pd.to_numeric(df.iat[row, i], errors="coerce")
        if pd.isna(value):
            continue
        out.append(
            {
                "company": "toyota",
                "cohort_year": year,
                "units": int(value),
                "basis": "worldwide_sales",
                "brands_covered": "toyota;lexus",
                "derived": "no",
                "derivation": (
                    f"sheet Sales, Toyota (incl. Lexus) block, row Worldwide sales, column {text}"
                ),
                "source_id": "toyota_global_sales",
                "source_file": TOYOTA_FILE.name,
            }
        )
    return out


def nissan_rows() -> list[dict[str, object]]:
    """Nissan's global sales for the release year and the year before it."""
    rows = [r for r in read_csv(NISSAN_FILE) if r["label"].strip() == "Global sales"]
    if not rows:
        raise SystemExit(f"{NISSAN_FILE.name}: no 'Global sales' row")
    r = rows[0]
    out: list[dict[str, object]] = []
    for year, column in ((2025, "units_cy"), (2024, "units_cy_prior")):
        if not r[column]:
            continue
        out.append(
            {
                "company": "nissan",
                "cohort_year": year,
                "units": int(r[column]),
                "basis": "worldwide_sales",
                "brands_covered": "nissan;infiniti",
                "derived": "no",
                "derivation": f"release row 'Global sales', column {column}",
                "source_id": "nissan_global_sales",
                "source_file": NISSAN_FILE.name,
            }
        )
    return out


def hyundai_rows() -> list[dict[str, object]]:
    """Hyundai worldwide sales, derived from the three workbooks it does publish."""
    korea = read_csv(HYUNDAI_KR)
    out: list[dict[str, object]] = []
    for path in sorted(RAW.glob("hyundai_*_global_plant_sales.xlsx")):
        year = int(path.name.split("_")[1])
        df = pd.read_excel(path, sheet_name=0, header=None)
        head = df.index[df.iloc[:, 3].astype(str).str.strip().str.startswith("Jan")]
        if not len(head):
            continue
        total_col = df.columns[df.iloc[int(head[0])].astype(str).str.strip() == "Total"][0]
        grand = df[df.iloc[:, 1].astype(str).str.strip() == "Grand Total"]
        if not len(grand):
            raise SystemExit(f"{path.name}: no Grand Total row")
        overseas = int(grand.iloc[0][total_col])
        domestic = sum(
            int(r["units"])
            for r in korea
            if int(r["cohort_year"]) == year and r["basis"] == "domestic_sales"
        )
        exports = sum(
            int(r["units"])
            for r in korea
            if int(r["cohort_year"]) == year and r["basis"] == "export_shipments"
        )
        if not domestic or not exports:
            continue
        out.append(
            {
                "company": "hyundai",
                "cohort_year": year,
                "units": domestic + exports + overseas,
                "basis": "worldwide_sales_derived",
                "brands_covered": "hyundai;genesis",
                "derived": "yes",
                "derivation": (
                    f"Korea domestic {domestic:,} plus shipments exported from Korea "
                    f"{exports:,} plus overseas plant sales {overseas:,}; the export leg is "
                    "shipments rather than sales, so the total is approximate"
                ),
                "source_id": "hyundai_ir_sales_results",
                "source_file": f"{HYUNDAI_KR.name};{path.name}",
            }
        )
    return out


def kia_rows() -> list[dict[str, object]]:
    """Kia worldwide retail for the period its retail workbook covers."""
    rows = read_csv(KIA_FILE)
    years = {int(r["cohort_year"]) for r in rows}
    out: list[dict[str, object]] = []
    for year in sorted(years):
        mine = [r for r in rows if int(r["cohort_year"]) == year]
        period = mine[0]["period"]
        out.append(
            {
                "company": "kia",
                "cohort_year": year,
                "units": sum(int(r["units"]) for r in mine),
                "basis": "worldwide_retail",
                "brands_covered": "kia",
                "derived": "yes",
                "derivation": (
                    f"every destination in the retail workbook summed, period {period}; the "
                    "workbook is the company's own every-market release, so the sum is its "
                    "worldwide retail for that period"
                ),
                "source_id": "kia_ir_retail_sales",
                "source_file": KIA_FILE.name,
            }
        )
    return out


def main() -> None:
    """Write the worldwide totals table."""
    rows = toyota_rows() + nissan_rows() + hyundai_rows() + kia_rows()
    rows.sort(key=lambda r: (str(r["company"]), int(str(r["cohort_year"]))))
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    recent = [r for r in rows if int(str(r["cohort_year"])) >= 2024]
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; "
        + ", ".join(
            f"{r['company']} {r['cohort_year']} {int(str(r['units'])):,}"
            for r in sorted(recent, key=lambda r: (str(r["company"]), r["cohort_year"]))
        )
    )


if __name__ == "__main__":
    main()
