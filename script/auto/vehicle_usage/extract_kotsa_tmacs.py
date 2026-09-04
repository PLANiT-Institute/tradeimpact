"""KOTSA TMACS annual distance -> vehicle_usage_kr_traffic.csv (passenger-car vehicle-kilometres).

Input   raw/kotsa_tmacs_annual_vkm_<year>.json   (ALL column: thousand km)
        raw/kotsa_tmacs_daily_km_<year>.json     (ALL column: km per vehicle per day)
Output  processed/vehicle_usage_kr_traffic.csv
        car_traffic        승용차 total-row ALL / 1000, million vehicle-km
        car_daily_km       승용차 total-row km per vehicle per day

The total row is labelled 평균 up to 2020 and 계 from 2021; both are read. The 2021 value
carries an 11 % discontinuity in per-vehicle distance with no fleet event behind it; the
reference builder reads the latest year and the rate derivation excludes 2020-2021 anyway.

Run from the repository root:  .venv/bin/python script/auto/vehicle_usage/extract_kotsa_tmacs.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "vehicle_usage"
RAW = DATA / "raw"
OUT = DATA / "processed" / "vehicle_usage_kr_traffic.csv"
SOURCE_ID = "kotsa_tmacs_vkm"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]
TOTAL_LABELS = {"평균", "계"}


def total_row(path: Path) -> float | None:
    """ALL value of the 승용차 total row, or None when the file carries no such row."""
    for r in json.loads(path.read_bytes()):
        if r.get("CAR_CLS_NM") == "승용차" and r.get("FUEL_CLS_NM") in TOTAL_LABELS:
            value = r.get("ALL")
            return None if value in (None, "") else float(value)
    return None


def main() -> None:
    """One row per year and series."""
    rows: list[dict[str, object]] = []
    for kind, series, unit, scale in (
        ("annual_vkm", "car_traffic", "million_vkm", 1 / 1000.0),
        ("daily_km", "car_daily_km", "km_per_vehicle_day", 1.0),
    ):
        for path in sorted(RAW.glob(f"kotsa_tmacs_{kind}_*.json")):
            year = int(path.stem.rsplit("_", 1)[1])
            value = total_row(path)
            if value is None:
                print(f"note: {path.name} has no 승용차 total row (published later)")
                continue
            rows.append(
                {
                    "country": "KR",
                    "series": series,
                    "year": year,
                    "value": round(value * scale, 3),
                    "unit": unit,
                    "source_id": SOURCE_ID,
                    "source_file": path.name,
                }
            )
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    traffic = {r["year"]: r["value"] for r in rows if r["series"] == "car_traffic"}
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; car traffic (million vkm) "
        + ", ".join(f"{y} {v:,.0f}" for y, v in sorted(traffic.items()))
    )


if __name__ == "__main__":
    main()
