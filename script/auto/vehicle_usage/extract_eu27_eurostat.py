"""Extract EU27 passenger-car stock, traffic and age-band series into the usage schema.

Reads ``data/auto/vehicle_usage/raw/destination_eu27_inputs.json`` — a hash-pinned copy
of four Eurostat datasets (see method.md for the links) fetched on the recorded
``accessed_date`` — and writes ``data/auto/vehicle_usage/processed/vehicle_usage_eu27.csv``
in long format: one row per country x series x year.

Run from the repository root:  .venv/bin/python script/auto/vehicle_usage/extract_eu27_eurostat.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "vehicle_usage"
RAW = DATASET / "raw" / "destination_eu27_inputs.json"
OUT = DATASET / "processed" / "vehicle_usage_eu27.csv"

# raw key -> (series name, unit, source_id); source_id resolves in method/method.md
SERIES = {
    "car_stock": ("car_stock", "vehicles", "eurostat_road_eqs_carpda"),
    "car_traffic_mio_vkm": ("car_traffic", "million_vkm", "eurostat_road_tf_veh"),
    "car_traffic_fallback_mio_vkm": (
        "car_traffic_fallback",
        "million_vkm",
        "eurostat_road_tf_vehmov",
    ),
}
AGE_BANDS = ("car_age_bands", "vehicles", "eurostat_road_eqs_carage")

FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def main() -> None:
    """Flatten the nested country -> year (-> band) dictionaries to long rows."""
    snap = json.loads(RAW.read_text())
    raw = snap["raw"]
    out: list[dict[str, object]] = []

    def add(country: str, series: str, year: str, value: object, unit: str, source_id: str) -> None:
        if value is None:
            return
        out.append(
            {
                "country": country,
                "series": series,
                "year": int(year),
                "value": float(value),
                "unit": unit,
                "source_id": source_id,
                "source_file": RAW.name,
            }
        )

    for key, (series, unit, source_id) in SERIES.items():
        for country, years in raw[key].items():
            for year, value in years.items():
                add(country, series, year, value, unit, source_id)

    key, unit, source_id = AGE_BANDS
    for country, years in raw[key].items():
        for year, bands in years.items():
            for band, value in bands.items():
                add(country, f"car_stock_age_{band.lower()}", year, value, unit, source_id)

    out.sort(key=lambda r: (str(r["country"]), str(r["series"]), int(str(r["year"]))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out)
    countries = {r["country"] for r in out}
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rows, {len(countries)} countries, "
        f"accessed {snap['accessed_date']}"
    )


if __name__ == "__main__":
    main()
