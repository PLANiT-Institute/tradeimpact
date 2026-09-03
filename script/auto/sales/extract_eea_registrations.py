"""Extract EEA 2024 EU27 first registrations (Toyota, Hyundai) into the sales schema.

Reads the two hash-pinned EEA CO2-monitoring API snapshots in ``data/auto/sales/raw/``
(``eea_toyota_2024_final.json``, ``eea_hyundai_2024_final.json``). The API response is an
aggregation: country -> commercial name -> powertrain, with the summed registrations per
bucket. Writes ``data/auto/sales/processed/sales_eea_eu27_2024.csv``.

Run from the repository root:  .venv/bin/python script/auto/sales/extract_eea_registrations.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "sales"
SCOPE = DATASET / "method" / "companies.csv"
IN_SCOPE = {r["company"] for r in csv.DictReader(SCOPE.open(newline="")) if r["in_scope"] == "yes"}
# Every pinned brand snapshot whose company is in scope (EEA make Mk, lower case).
RAW = {
    brand: p
    for p in sorted((DATASET / "raw").glob("eea_*_final.json"))
    for brand in [json.loads(p.read_text())["brand_filter"].split("=", 1)[1].lower()]
    if brand in IN_SCOPE
}
OUT = DATASET / "processed" / "sales_eea_eu27_2024.csv"

BASIS = "registrations"
POWERTRAIN = {"BEV": "BEV", "FCEV": "FCEV", "HEV": "HEV", "PHEV": "PHEV", "ICE_OTHER": "ICE"}

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
    "source_file",
]


def rows_from_snapshot(company: str, path: Path) -> list[dict[str, object]]:
    """One row per country x model x powertrain bucket with registrations > 0."""
    snap = json.loads(path.read_text())
    year = int(snap["dataset_year"])
    out: list[dict[str, object]] = []
    for country in snap["response"]["aggregations"]["countries"]["buckets"]:
        for model in country["models"]["buckets"]:
            for key, bucket in model["powertrains"]["buckets"].items():
                units = int(bucket["registrations"]["value"])
                if units <= 0:
                    continue
                if key not in POWERTRAIN:
                    raise SystemExit(f"{path.name}: unknown powertrain bucket {key!r}")
                out.append(
                    {
                        "company": company,
                        "destination": country["key"],
                        "destination_level": "country",
                        "origin": "",
                        "cohort_year": year,
                        "period": f"{year}-01..{year}-12",
                        "model": model["key"],
                        "powertrain": POWERTRAIN[key],
                        "units": units,
                        "basis": BASIS,
                        "source_file": path.name,
                    }
                )
    expected = int(snap["response"]["aggregations"]["registrations"]["value"])
    got = sum(int(r["units"]) for r in out)
    if got != expected:
        raise SystemExit(f"{path.name}: buckets sum to {got}, snapshot total is {expected}")
    return out


def main() -> None:
    """Write both brands to one CSV, sorted for a byte-stable output."""
    out: list[dict[str, object]] = []
    for company, path in RAW.items():
        rows = rows_from_snapshot(company, path)
        print(f"{path.name}: {len(rows)} rows, {sum(int(r['units']) for r in rows):,} units")
        out.extend(rows)
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
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows")


if __name__ == "__main__":
    main()
