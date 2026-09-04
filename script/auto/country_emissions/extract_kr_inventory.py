"""Korea: road-transport CO2 (GIR inventory) and the passenger-car share (KOTSA) ->
country_emissions_kr.csv

Inputs
    raw/gir_inventory_co2_1990_2023.csv      national CO2 by IPCC category, ktCO2, 1990-2023
    raw/kotsa_road_ghg_by_vehicle_type.csv   road GHG by vehicle type x province, ktCO2e, 2012-2024
Output
    processed/country_emissions_kr.csv (long format: country, series, year, value, unit, ...)
        road_co2           GIR 1.A.3.b 도로수송, ktCO2 (fuel-sales basis, national inventory)
        kotsa_car_ghg      KOTSA 승용 national sum, ktCO2e (bottom-up; level not comparable)
        kotsa_road_ghg     KOTSA all classes national sum, ktCO2e
        car_share_road     KOTSA 승용 / KOTSA all classes (fraction)
        car_co2            road_co2 x car_share_road, ktCO2 — the benchmark numerator, TIER C

Why the share and not the level. The national inventory publishes no vehicle-type split; the
KOTSA local inventory does, but its national total sits 13-26 % below the GIR road total (2018:
82,663 vs 95,307 ktCO2e; 2023: 69,646 vs 94,414) because it is built bottom-up from registered
vehicles x inspection distance x factors. The two are handed to reconciliation as a recorded
disagreement; here only the KOTSA share is used, on the GIR level.

Run from the repository root:
    .venv/bin/python script/auto/country_emissions/extract_kr_inventory.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "country_emissions"
GIR = DATA / "raw" / "gir_inventory_co2_1990_2023.csv"
KOTSA = DATA / "raw" / "kotsa_road_ghg_by_vehicle_type.csv"
OUT = DATA / "processed" / "country_emissions_kr.csv"
ROAD_ROW = "A 연료연소_3 수송_b 도로수송"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def main() -> None:
    """Write the Korean emission series."""
    gir = pd.read_csv(GIR, encoding="utf-8-sig")
    label_col = gir.columns[0]
    road = gir[gir[label_col].astype(str).str.strip() == ROAD_ROW]
    if len(road) != 1:
        raise SystemExit(f"{GIR.name}: expected one row {ROAD_ROW!r}, found {len(road)}")
    rows: list[dict[str, object]] = []
    road_co2: dict[int, float] = {}
    for col in gir.columns[1:]:
        value = pd.to_numeric(road.iloc[0][col], errors="coerce")
        if pd.isna(value):
            continue
        road_co2[int(col)] = float(value)
        rows.append(
            {
                "country": "KR",
                "series": "road_co2",
                "year": int(col),
                "value": round(float(value), 3),
                "unit": "ktCO2",
                "source_id": "gir_inventory_co2",
                "source_file": GIR.name,
            }
        )

    kotsa = pd.read_csv(KOTSA, encoding="cp949")
    kotsa.columns = [c.replace(" ", "") for c in kotsa.columns]
    kotsa["구분"] = kotsa["구분"].astype(str).str.replace(" ", "")
    national = kotsa.groupby("년도")[["승용", "승합", "화물", "특수"]].sum()
    for year, r in national.iterrows():
        total = float(r.sum())
        car = float(r["승용"])
        share = car / total
        y = int(year)
        rows += [
            {
                "country": "KR",
                "series": "kotsa_car_ghg",
                "year": y,
                "value": round(car, 3),
                "unit": "ktCO2e",
                "source_id": "kotsa_road_ghg_vehicle_type",
                "source_file": KOTSA.name,
            },
            {
                "country": "KR",
                "series": "kotsa_road_ghg",
                "year": y,
                "value": round(total, 3),
                "unit": "ktCO2e",
                "source_id": "kotsa_road_ghg_vehicle_type",
                "source_file": KOTSA.name,
            },
            {
                "country": "KR",
                "series": "car_share_road",
                "year": y,
                "value": round(share, 6),
                "unit": "fraction",
                "source_id": "kotsa_road_ghg_vehicle_type",
                "source_file": KOTSA.name,
            },
        ]
        if y in road_co2:
            rows.append(
                {
                    "country": "KR",
                    "series": "car_co2",
                    "year": y,
                    "value": round(road_co2[y] * share, 3),
                    "unit": "ktCO2",
                    "source_id": "gir_inventory_co2;kotsa_road_ghg_vehicle_type",
                    "source_file": f"{GIR.name};{KOTSA.name}",
                }
            )
    rows.sort(key=lambda r: (str(r["series"]), int(str(r["year"]))))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    latest = max(y for y in road_co2 if y in national.index)
    gap = national.loc[latest].sum() / road_co2[latest] - 1
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; road CO2 {latest} {road_co2[latest]:,.0f} kt, "
        f"car share {national.loc[latest, '승용'] / national.loc[latest].sum():.3f}, "
        f"KOTSA level vs GIR {gap:+.1%}"
    )


if __name__ == "__main__":
    main()
