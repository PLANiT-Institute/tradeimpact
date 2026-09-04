"""KOTSA TMACS annual distance -> vehicle_usage_kr_traffic.csv (passenger-car vehicle-kilometres).

Input   raw/kotsa_tmacs_annual_vkm_<year>.json   (ALL column: thousand km)
        raw/kotsa_tmacs_daily_km_<year>.json     (ALL column: km per vehicle per day)
Output  processed/vehicle_usage_kr_traffic.csv
        traffic_<segment>   that class's total-row ALL / 1000, million vehicle-km
        daily_km_<segment>  that class's total-row km per vehicle per day

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
#: KOTSA vehicle classes -> the project's segment names.
SEGMENTS = {
    "승용차": "passenger_car",
    "승합차": "bus",
    "화물차": "freight",
    "특수차": "special",
}


def total_rows(path: Path) -> dict[str, float]:
    """{segment: ALL value of that class's total row} for one TMACS file."""
    out: dict[str, float] = {}
    for r in json.loads(path.read_bytes()):
        segment = SEGMENTS.get(str(r.get("CAR_CLS_NM")))
        if segment is None or r.get("FUEL_CLS_NM") not in TOTAL_LABELS:
            continue
        value = r.get("ALL")
        if value not in (None, ""):
            out[segment] = float(value)
    return out


def main() -> None:
    """One row per year and series."""
    rows: list[dict[str, object]] = []
    for kind, prefix, unit, scale in (
        ("annual_vkm", "traffic", "million_vkm", 1 / 1000.0),
        ("daily_km", "daily_km", "km_per_vehicle_day", 1.0),
    ):
        for path in sorted(RAW.glob(f"kotsa_tmacs_{kind}_*.json")):
            year = int(path.stem.rsplit("_", 1)[1])
            values = total_rows(path)
            if not values:
                print(f"note: {path.name} carries no class total row (published later)")
                continue
            for segment, value in sorted(values.items()):
                rows.append(
                    {
                        "country": "KR",
                        "series": f"{prefix}_{segment}",
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
    latest = max(int(str(r["year"])) for r in rows)
    traffic = {
        str(r["series"])[8:]: r["value"]
        for r in rows
        if str(r["series"]).startswith("traffic_") and r["year"] == latest
    }
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; {latest} vehicle-km (million) "
        + ", ".join(f"{k} {v:,.0f}" for k, v in sorted(traffic.items()))
    )


if __name__ == "__main__":
    main()
