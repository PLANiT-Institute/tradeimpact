"""Extract EU27 passenger-car stock, traffic and age-band series from the Eurostat cubes.

Inputs  data/auto/vehicle_usage/raw/eurostat_<dataset>.json — JSON-stat 2.0 responses fetched
        directly from the Eurostat API by ``fetch_eurostat.py`` (request URL, dataset page and
        response hash inside each file): road_eqs_carpda (stock), road_tf_veh (traffic by cars
        registered in the country), road_tf_vehmov (traffic on the territory, fallback only),
        road_eqs_carage (stock by age class).
Output  data/auto/vehicle_usage/processed/vehicle_usage_eu27.csv — long format, one row per
        country x series x year, EU27 member states only (Eurostat ``EL`` recoded to ``GR``).

Run from the repository root:  .venv/bin/python script/auto/vehicle_usage/extract_eu27_eurostat.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "vehicle_usage"
OUT = DATASET / "processed" / "vehicle_usage_eu27.csv"

EU27 = {
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
}
GEO_RECODE = {"EL": "GR"}
# raw file -> (series, unit, extra dimension used as a series suffix or None)
CUBES = {
    "eurostat_road_eqs_carpda.json": ("car_stock", "vehicles", None),
    "eurostat_road_tf_veh.json": ("car_traffic", "million_vkm", None),
    "eurostat_road_tf_vehmov.json": ("car_traffic_fallback", "million_vkm", None),
    "eurostat_road_eqs_carage.json": ("car_stock_age", "vehicles", "age"),
}
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def flatten(payload: dict) -> list[tuple[dict[str, str], float]]:
    """JSON-stat 2.0 cube -> [({dimension: category}, value)]."""
    ids: list[str] = payload["id"]
    sizes: list[int] = payload["size"]
    lookup = [
        {pos: key for key, pos in payload["dimension"][name]["category"]["index"].items()}
        for name in ids
    ]
    out = []
    for position, value in payload["value"].items():
        remainder = int(position)
        cats: list[str] = []
        for size, table in zip(reversed(sizes), reversed(lookup), strict=True):
            cats.append(table[remainder % size])
            remainder //= size
        out.append((dict(zip(ids, reversed(cats), strict=True)), float(value)))
    return out


def main() -> None:
    """Flatten the four cubes to long rows for the 27 member states."""
    out: list[dict[str, object]] = []
    for name, (series, unit, suffix_dim) in CUBES.items():
        path = DATASET / "raw" / name
        snap = json.loads(path.read_text())
        for cats, value in flatten(snap["response"]):
            country = GEO_RECODE.get(cats["geo"], cats["geo"])
            if country not in EU27:
                continue
            label = series if suffix_dim is None else f"{series}_{cats[suffix_dim].lower()}"
            out.append(
                {
                    "country": country,
                    "series": label,
                    "year": int(cats["time"]),
                    "value": value,
                    "unit": unit,
                    "source_id": snap["source_id"],
                    "source_file": name,
                }
            )
    out.sort(key=lambda r: (str(r["country"]), str(r["series"]), int(str(r["year"]))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    countries = {r["country"] for r in out}
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows, {len(countries)} countries")


if __name__ == "__main__":
    main()
