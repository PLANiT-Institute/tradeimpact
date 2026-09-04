"""Extract US certified technology values per model x powertrain from the EPA fuel-economy data.

Input   data/auto/vehicle_technology/raw/epa_fueleconomy_vehicles.csv — the complete EPA/DOE
        fueleconomy.gov vehicle dataset (one row per model-year trim, 1984 onward), downloaded
        verbatim from the source of truth (link and hash in data/auto/registry/raw_files.csv).
Output  data/auto/vehicle_technology/processed/vehicle_technology_us_epa.csv — one row per
        company x model-year x model x powertrain for the companies in scope
        (sales/method/companies.csv): unweighted mean over trims of certified tailpipe CO2
        (g/mile -> g/km) and electric consumption (kWh/100 miles -> Wh/km), with the trim count.

Algorithm:
    $$ I_{km} = I_{mile} / 1.609344 $$
    $$ E_{Wh/km} = E_{kWh/100mi} \\cdot 1000 / (100 \\cdot 1.609344) $$
    ASCII: g/km = g/mile / 1.609344; Wh/km = kWh per 100 miles * 10 / 1.609344
    EPA combined-cycle values; no sales weighting is available in this file, so the model
    value is the plain mean of its trims (the trim count is kept for the reader).

Run from the repository root:
    .venv/bin/python script/auto/vehicle_technology/extract_epa_fueleconomy.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
RAW = DATA / "vehicle_technology" / "raw" / "epa_fueleconomy_vehicles.csv"
SCOPE = DATA / "sales" / "method" / "companies.csv"
OUT = DATA / "vehicle_technology" / "processed" / "vehicle_technology_us_epa.csv"

SOURCE_ID = "epa_fueleconomy_vehicles"
TEST_CYCLE = "EPA"
KM_PER_MILE = 1.609344
MODEL_YEARS = {"2024", "2025"}
# EPA alternative-technology label -> repo powertrain
POWERTRAIN = {
    "": "ICE",
    "Diesel": "ICE",
    "Bifuel (CNG)": "ICE",
    "Bifuel (LPG)": "ICE",
    "CNG": "ICE",
    "FFV": "ICE",
    "Hybrid": "HEV",
    "Plug-in Hybrid": "PHEV",
    "EV": "BEV",
    "FCV": "FCEV",
    "eFCV": "FCEV",  # plug-in fuel cell (Honda CR-V e:FCEV); withheld like every FCEV
}
FIELDS = [
    "company",
    "model_year",
    "model",
    "base_model",
    "powertrain",
    "tailpipe_gco2_km",
    "energy_wh_km",
    "n_trims",
    "test_cycle",
    "source_id",
    "source_file",
]


def main() -> None:
    """Group in-scope 2024-2025 trims by model and powertrain."""
    in_scope = {
        r["company"] for r in csv.DictReader(SCOPE.open(newline="")) if r["in_scope"] == "yes"
    }
    acc: dict[tuple[str, str, str, str, str], dict[str, list[float]]] = defaultdict(
        lambda: {"co2": [], "energy": []}
    )
    with RAW.open(newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            company = r["make"].lower()
            if company not in in_scope or r["year"] not in MODEL_YEARS:
                continue
            pt = POWERTRAIN.get(r["atvType"])
            if pt is None:
                raise SystemExit(
                    f"unmapped EPA atvType {r['atvType']!r} for {r['make']} {r['model']}"
                )
            cell = acc[(company, r["year"], r["model"], r["baseModel"], pt)]
            co2 = float(r["co2TailpipeGpm"] or 0)
            if co2 > 0 and pt != "BEV":
                cell["co2"].append(co2 / KM_PER_MILE)
            energy = float(r["combE"] or 0)
            if energy > 0:
                cell["energy"].append(energy * 10.0 / KM_PER_MILE)
    out: list[dict[str, object]] = []
    for (company, year, model, base, pt), cell in sorted(acc.items()):
        n = max(len(cell["co2"]), len(cell["energy"]), 1)
        out.append(
            {
                "company": company,
                "model_year": int(year),
                "model": model,
                "base_model": base,
                "powertrain": pt,
                "tailpipe_gco2_km": round(sum(cell["co2"]) / len(cell["co2"]), 2)
                if cell["co2"]
                else None,
                "energy_wh_km": round(sum(cell["energy"]) / len(cell["energy"]), 2)
                if cell["energy"]
                else None,
                "n_trims": n,
                "test_cycle": TEST_CYCLE,
                "source_id": SOURCE_ID,
                "source_file": RAW.name,
            }
        )
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    by_pt = defaultdict(int)
    for r in out:
        by_pt[str(r["powertrain"])] += 1
    print(f"{OUT.relative_to(REPO)}: {len(out)} model x powertrain rows; {dict(by_pt)}")


if __name__ == "__main__":
    main()
