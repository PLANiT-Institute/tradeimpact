"""Extract certified WLTP values per model x powertrain from the EEA snapshots.

Reads the two EEA CO2-monitoring API snapshots in ``data/auto/sales/raw/`` (the raw file
is shared with the sales dataset — it is not copied). Each country x model x powertrain
bucket carries a registrations-weighted mean of the certified WLTP tailpipe CO2
(``Ewltp__g_km_``) and, where reported, electric energy consumption. This script pools the
countries into one registrations-weighted value per company x model x powertrain and writes
``data/auto/vehicle_technology/processed/vehicle_technology_eea_2024.csv``.

Certified values only: no real-world correction and no utility factor is applied here.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_technology/extract_eea_certified.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
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
    "model",
    "powertrain",
    "tailpipe_gco2_km",
    "tailpipe_units",
    "energy_wh_km",
    "energy_units",
    "units",
    "test_cycle",
    "source_id",
    "source_file",
]


def weighted(sums: dict[str, float]) -> float | None:
    """Registrations-weighted mean, or None when no bucket reported the value."""
    return round(sums["num"] / sums["den"], 3) if sums["den"] else None


def main() -> None:
    """Pool EEA buckets across countries into one technology row per model x powertrain."""
    acc: dict[tuple[str, str, str], dict[str, dict[str, float]]] = defaultdict(
        lambda: {
            "co2": {"num": 0.0, "den": 0.0},
            "energy": {"num": 0.0, "den": 0.0},
            "units": {"num": 0.0, "den": 0.0},
        }
    )
    source_files: dict[str, str] = {}
    for company, path in RAW.items():
        snap = json.loads(path.read_text())
        source_files[company] = path.name
        for country in snap["response"]["aggregations"]["countries"]["buckets"]:
            for model in country["models"]["buckets"]:
                for key, bucket in model["powertrains"]["buckets"].items():
                    units = bucket["registrations"]["value"]
                    if not units:
                        continue
                    cell = acc[(company, model["key"], POWERTRAIN[key])]
                    cell["units"]["num"] += units
                    for field, agg in (("co2", "co2_mapped"), ("energy", "energy_mapped")):
                        n = bucket[agg]["registrations"]["value"]
                        mean = bucket[agg]["weighted_average"]["value"]
                        if n and mean is not None:
                            cell[field]["num"] += mean * n
                            cell[field]["den"] += n

    out: list[dict[str, object]] = []
    for (company, model, powertrain), cell in sorted(acc.items()):
        out.append(
            {
                "company": company,
                "model": model,
                "powertrain": powertrain,
                "tailpipe_gco2_km": weighted(cell["co2"]),
                "tailpipe_units": int(cell["co2"]["den"]),
                "energy_wh_km": weighted(cell["energy"]),
                "energy_units": int(cell["energy"]["den"]),
                "units": int(cell["units"]["num"]),
                "test_cycle": TEST_CYCLE,
                "source_id": SOURCE_ID,
                "source_file": source_files[company],
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out)
    no_co2 = sum(1 for r in out if r["tailpipe_gco2_km"] is None)
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} model x powertrain rows, "
        f"{no_co2} without a certified CO2 value"
    )


if __name__ == "__main__":
    main()
