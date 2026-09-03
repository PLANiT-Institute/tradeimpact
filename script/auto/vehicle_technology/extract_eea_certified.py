"""Extract certified WLTP values per destination x model x powertrain from the EEA snapshots.

Reads the two EEA CO2-monitoring API snapshots in ``data/auto/sales/raw/`` (the raw file
is shared with the sales dataset — it is not copied). Each country x model x powertrain
bucket carries a registrations-weighted mean of the certified WLTP tailpipe CO2
(``Ewltp__g_km_``) and, where reported, electric energy consumption (``z__Wh_km_``). The
values are kept per destination because the same commercial name is a different mix of
variants in each market. Writes
``data/auto/vehicle_technology/processed/vehicle_technology_eea_2024.csv``.

Certified values only: no real-world correction and no utility factor is applied here.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_technology/extract_eea_certified.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RAW = {
    "toyota": REPO / "data" / "auto" / "sales" / "raw" / "eea_toyota_2024_final.json",
    "hyundai": REPO / "data" / "auto" / "sales" / "raw" / "eea_hyundai_2024_final.json",
}
OUT = (
    REPO / "data" / "auto" / "vehicle_technology" / "processed" / "vehicle_technology_eea_2024.csv"
)

POWERTRAIN = {"BEV": "BEV", "FCEV": "FCEV", "HEV": "HEV", "PHEV": "PHEV", "ICE_OTHER": "ICE"}
TEST_CYCLE = "WLTP"
SOURCE_ID = "eea_co2_monitoring_2024"

FIELDS = [
    "company",
    "destination",
    "model",
    "powertrain",
    "cohort_year",
    "tailpipe_gco2_km",
    "tailpipe_units",
    "energy_wh_km",
    "energy_units",
    "units",
    "test_cycle",
    "source_id",
    "source_file",
]


def mapped(bucket: dict, agg: str) -> tuple[float | None, int]:
    """(weighted mean, registrations behind it) for a ``*_mapped`` sub-aggregation."""
    n = int(bucket[agg]["registrations"]["value"])
    mean = bucket[agg]["weighted_average"]["value"]
    return (round(mean, 4) if n and mean is not None else None), n


def main() -> None:
    """One technology row per country x model x powertrain bucket with registrations."""
    out: list[dict[str, object]] = []
    for company, path in RAW.items():
        snap = json.loads(path.read_text())
        year = int(snap["dataset_year"])
        for country in snap["response"]["aggregations"]["countries"]["buckets"]:
            for model in country["models"]["buckets"]:
                for key, bucket in model["powertrains"]["buckets"].items():
                    units = int(bucket["registrations"]["value"])
                    if units <= 0:
                        continue
                    co2, co2_n = mapped(bucket, "co2_mapped")
                    energy, energy_n = mapped(bucket, "energy_mapped")
                    out.append(
                        {
                            "company": company,
                            "destination": country["key"],
                            "model": model["key"],
                            "powertrain": POWERTRAIN[key],
                            "cohort_year": year,
                            "tailpipe_gco2_km": co2,
                            "tailpipe_units": co2_n,
                            "energy_wh_km": energy,
                            "energy_units": energy_n,
                            "units": units,
                            "test_cycle": TEST_CYCLE,
                            "source_id": SOURCE_ID,
                            "source_file": path.name,
                        }
                    )

    out.sort(
        key=lambda r: (
            str(r["company"]),
            str(r["destination"]),
            str(r["model"]),
            str(r["powertrain"]),
        )
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out)
    no_co2 = sum(1 for r in out if r["tailpipe_gco2_km"] is None)
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows, {no_co2} without a certified CO2 value")


if __name__ == "__main__":
    main()
