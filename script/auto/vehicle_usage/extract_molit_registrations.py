"""MOLIT registration workbooks -> vehicle_usage_kr.csv (passenger-car stock and mean age).

Input   raw/molit_vehicle_registration_<year>_12.xlsx (December workbooks)
        sheet 19.연도별 자동차 등록현황: year-end stock by 차종 x 용도, 2007 onward (latest file)
        sheet 15.차령별_차종별_용도별 등록현황: stock by model year x 차종 x 용도 (one per file)
Output  processed/vehicle_usage_kr.csv
        car_stock            승용 계 (all uses) at year end, vehicles
        car_mean_age_years   sum(w_m (Y - m)) / sum(w_m) over model years m of the December
                             snapshot of year Y, with the open-ended oldest band counted at its
                             nominal age (2005 = "2005 and earlier"), so the mean is biased low;
                             the bias is recorded as a warning downstream (tier C)
        car_stock_age_le2 / _2_5 / _5_10 / _10_20 / _gt20   vehicles by age band (Y - m)

승용 is the 자동차관리법 passenger-car class (up to 10 seats); it excludes the Carnival/Staria
9- and 11-seaters (승합) and light trucks (화물).

Run from the repository root:
    .venv/bin/python script/auto/vehicle_usage/extract_molit_registrations.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "vehicle_usage"
RAW = DATA / "raw"
OUT = DATA / "processed" / "vehicle_usage_kr.csv"
SOURCE_ID = "molit_vehicle_registration"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]
SHEET_YEARLY = "19.연도별 자동차 등록현황"
SHEET_AGE = "15.차령별_차종별_용도별 등록현황"
BANDS = (("le2", 0, 2), ("2_5", 2, 5), ("5_10", 5, 10), ("10_20", 10, 20), ("gt20", 20, 200))
#: MOLIT vehicle classes -> the project's segment names.
SEGMENTS = {"승용": "passenger_car", "승합": "bus", "화물": "freight", "특수": "special"}


def total_columns(df: pd.DataFrame) -> dict[str, int]:
    """{segment: column index of that vehicle class's '계' (all uses) block}."""
    classes = df.iloc[2].astype(str).str.replace(" ", "")
    uses = df.iloc[3].astype(str).str.strip()
    starts = {v: i for i, v in enumerate(classes) if v in SEGMENTS}
    out: dict[str, int] = {}
    for korean, start in starts.items():
        for i in range(start, len(uses)):
            if uses.iloc[i] == "계":
                out[SEGMENTS[korean]] = i
                break
    missing = set(SEGMENTS.values()) - set(out)
    if missing:
        raise SystemExit(f"no 계 column for {sorted(missing)}")
    return out


def yearly_stock(path: Path) -> list[dict[str, object]]:
    """Year-end stock per vehicle class from the yearly sheet of one workbook."""
    df = pd.read_excel(path, sheet_name=SHEET_YEARLY, header=None)
    columns = total_columns(df)
    rows = []
    for i in range(4, len(df)):
        year = pd.to_numeric(df.iat[i, 0], errors="coerce")
        if pd.isna(year):
            continue
        for segment, col in columns.items():
            rows.append(
                {
                    "country": "KR",
                    "series": f"stock_{segment}",
                    "year": int(year),
                    "value": int(df.iat[i, col]),
                    "unit": "vehicles",
                    "source_id": SOURCE_ID,
                    "source_file": path.name,
                }
            )
    return rows


def age_rows(path: Path, snapshot_year: int) -> list[dict[str, object]]:
    """Mean age per class, and the age bands of the passenger-car class, from one workbook."""
    df = pd.read_excel(path, sheet_name=SHEET_AGE, header=None)
    columns = total_columns(df)
    rows: list[dict[str, object]] = []
    for segment, col in columns.items():
        weights: dict[int, int] = {}
        total = None
        for i in range(4, len(df)):
            label = str(df.iat[i, 0]).strip()
            if label == "총계":
                total = int(df.iat[i, col])
                continue
            my = pd.to_numeric(label, errors="coerce")
            if pd.isna(my):
                continue
            weights[int(my)] = int(df.iat[i, col])
        if total is None or sum(weights.values()) != total:
            raise SystemExit(f"{path.name} {segment}: model-year rows do not sum to 총계")
        ages = {snapshot_year - my: w for my, w in weights.items()}
        rows.append(
            {
                "country": "KR",
                "series": f"mean_age_{segment}",
                "year": snapshot_year,
                "value": round(sum(a * w for a, w in ages.items()) / total, 4),
                "unit": "years",
                "source_id": SOURCE_ID,
                "source_file": path.name,
            }
        )
        if segment != "passenger_car":
            continue
        for name, lo, hi in BANDS:
            rows.append(
                {
                    "country": "KR",
                    "series": f"stock_age_{segment}_{name}",
                    "year": snapshot_year,
                    "value": sum(w for a, w in ages.items() if lo <= a < hi),
                    "unit": "vehicles",
                    "source_id": SOURCE_ID,
                    "source_file": path.name,
                }
            )
    return rows


def main() -> None:
    """Stock from the latest workbook, age from every December workbook."""
    files = sorted(RAW.glob("molit_vehicle_registration_*_12.xlsx"))
    if not files:
        raise SystemExit("no MOLIT workbook in raw/")
    rows = yearly_stock(files[-1])
    for path in files:
        rows += age_rows(path, int(path.name.split("_")[3]))
    rows.sort(key=lambda r: (str(r["series"]), int(str(r["year"]))))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    latest = max(int(str(r["year"])) for r in rows if str(r["series"]).startswith("stock_"))
    stock = {
        str(r["series"])[6:]: r["value"]
        for r in rows
        if str(r["series"]).startswith("stock_")
        and r["year"] == latest
        and "age" not in str(r["series"])
    }
    ages = {
        str(r["series"])[9:]: r["value"]
        for r in rows
        if str(r["series"]).startswith("mean_age_")
        and r["year"]
        == max(int(str(x["year"])) for x in rows if str(x["series"]).startswith("mean_age_"))
    }
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; {latest} stock "
        + ", ".join(f"{k} {v:,}" for k, v in sorted(stock.items()))
        + "; mean age "
        + ", ".join(f"{k} {v}" for k, v in sorted(ages.items()))
    )


if __name__ == "__main__":
    main()
