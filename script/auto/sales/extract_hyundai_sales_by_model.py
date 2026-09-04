"""Hyundai IR "Unit Sales by Model" workbooks -> data/auto/sales/processed/sales_hyundai_kr.csv

Input   data/auto/sales/raw/hyundai_<year>_sales_by_model.xlsx (sheet ``Unit Sales by Model``):
        a Domestic block and an Export block, each with PC / RV / CV classes, one row per model
        and trim code ("Avante (CN7 HEV)", "Kona (SX2 EV)"), Jan..Dec and Total.
Output  one row per (company, block, model label, cohort year):
        Domestic -> destination KR (country), basis ``domestic_sales`` (market-side, Korea);
        Export   -> destination ``export`` (level unknown), basis ``export_shipments``
                    (plant-side shipments from Korea, destination not stated; kept for
                    reconciliation with trade statistics, never priced).
        Commercial rows (LCV, HCV) are emitted with their class as the model label so that
        sales/method/kr_labels.csv can route them to the freight benchmark, or withhold them
        with a reason where no certified value exists.

Powertrain is read from the trim code: PHEV, HEV, EV (BEV), NEXO (FCEV); N performance trims
and everything else are ICE. Genesis nameplates carry ``company = genesis``.

Run from the repository root:  .venv/bin/python script/auto/sales/extract_hyundai_sales_by_model.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
OUT = REPO / "data" / "auto" / "sales" / "processed" / "sales_hyundai_kr.csv"
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
GENESIS = re.compile(r"^(G70|G80|G90|GV60|GV70|GV80|Genesis)\b")
BLOCKS = {
    "Domestic": ("KR", "country", "domestic_sales"),
    "Export": ("export", "unknown", "export_shipments"),
}
#: Commercial rows carry the class as their label, so the Korea label map can route them.
CV_LABELS = {"LCV", "HCV"}


def powertrain(label: str) -> str:
    """Powertrain from the trim code in parentheses."""
    code = label[label.find("(") + 1 : label.rfind(")")] if "(" in label else ""
    tokens = set(code.replace("_", " ").upper().split())
    if "PHEV" in tokens:
        return "PHEV"
    if "HEV" in tokens:
        return "HEV"
    if (
        "EV" in tokens
        or label.upper().startswith("IONIQ 5")
        or label.upper().startswith("IONIQ 6")
        or label.upper().startswith("IONIQ 9")
    ):
        return "BEV"
    if label.upper().startswith("NEXO"):
        return "FCEV"
    return "ICE"


def extract(path: Path, year: int) -> list[dict[str, object]]:
    """Rows of one year's workbook."""
    df = pd.read_excel(path, sheet_name="Unit Sales by Model", header=None)
    header_row = df.index[df.iloc[:, 3].astype(str).str.strip().str.startswith("Jan")][0]
    header = df.iloc[header_row].astype(str).str.strip()
    total_col = df.columns[header == "Total"][0]
    rows: list[dict[str, object]] = []
    block = None
    block_total: dict[str, int] = {}
    seen: dict[str, int] = {}
    for i in range(header_row + 1, len(df)):
        col1 = df.iat[i, 1]
        label = df.iat[i, 2]
        if isinstance(col1, str) and col1.strip() in BLOCKS:
            block = col1.strip()
            continue
        if isinstance(col1, str) and col1.strip() == "Total" and block:
            block_total[block] = int(df.iat[i, total_col])
            continue
        # The class column (PC / RV / CV) is not needed any more: the label itself carries the
        # class for commercial rows and the Korea label map routes every label to a segment.
        if block is None or not isinstance(label, str) or label.strip() in {"Sub-total"}:
            continue
        model = label.strip()
        value = pd.to_numeric(df.iat[i, total_col], errors="coerce")
        units = 0 if pd.isna(value) else int(value)
        seen[block] = seen.get(block, 0) + units
        if units == 0:
            continue
        dest, level, basis = BLOCKS[block]
        rows.append(
            {
                "company": "genesis" if GENESIS.match(model) else "hyundai",
                "destination": dest,
                "destination_level": level,
                "origin": "KR",
                "cohort_year": year,
                "period": f"{year}-01..{year}-12",
                "model": model,
                "powertrain": "" if model in CV_LABELS else powertrain(model),
                "units": units,
                "basis": basis,
                "source_id": SOURCE_ID,
                "source_file": path.name,
            }
        )
    for b, total in block_total.items():
        if seen.get(b) != total:
            raise SystemExit(f"{path.name} {b}: rows sum to {seen.get(b)} but Total row is {total}")
    return rows


def main() -> None:
    """Extract every sales_by_model workbook on disk."""
    rows: list[dict[str, object]] = []
    for path in sorted(RAW.glob("hyundai_*_sales_by_model.xlsx")):
        rows.extend(extract(path, int(path.name.split("_")[1])))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    agg: dict[tuple, int] = {}
    for r in rows:
        k = (r["cohort_year"], r["company"], r["destination"])
        agg[k] = agg.get(k, 0) + int(r["units"])
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; "
        + ", ".join(f"{k[1]} {k[2]} {k[0]} {v:,}" for k, v in sorted(agg.items()))
    )


if __name__ == "__main__":
    main()
