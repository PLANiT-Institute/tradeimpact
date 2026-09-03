"""Step 5 — aggregate the per-cell lifetime TI to importer country and exporter company.

Input   data/auto/output/ti_by_model_eu27.csv
Outputs data/auto/output/ti_country_eu27.csv     company x destination x scenario
        data/auto/output/ti_powertrain_eu27.csv  company x powertrain x scenario
        data/auto/output/ti_company_eu27.csv     company x scenario, with the decomposition check

Algorithm (whitepaper §3.6-3.7):
    $$ TI_{firm,S} = \\sum_{c}\\sum_{p} TI_{c,p,S},\\qquad
       \\sum_c TI_{c,S} = \\sum_p TI_{p,S} = TI_{firm,S} $$
    ASCII: total = sum over destinations = sum over powertrains (identity checked to 1e-6 rel).
    Per-vehicle values are units-weighted means (kgCO2e per covered vehicle).

Run from the repository root:  .venv/bin/python script/auto/model/aggregate_country.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "data" / "auto" / "output"
CELLS = OUT_DIR / "ti_by_model_eu27.csv"
WITHHELD = OUT_DIR / "ti_withheld_eu27.csv"
OUT_COUNTRY = OUT_DIR / "ti_country_eu27.csv"
OUT_POWERTRAIN = OUT_DIR / "ti_powertrain_eu27.csv"
OUT_COMPANY = OUT_DIR / "ti_company_eu27.csv"

# Summands are 4-dp-rounded values summed in different orders; the true float error is
# ~1e-10 relative, so anything looser than this would let a dropped small cell through.
IDENTITY_TOL = 1e-9
ANNUAL = OUT_DIR / "ti_annual_eu27.csv"

GROUP_FIELDS = [
    "company",
    "key",
    "scenario",
    "units",
    "ti_tco2e",
    "ti_per_vehicle_kgco2e",
    "direction",
]
COMPANY_FIELDS = [
    "company",
    "scenario",
    "cohort_year",
    "covered_units",
    "withheld_units",
    "covered_share",
    "ti_tco2e",
    "ti_per_vehicle_kgco2e",
    "direction",
    "decomposition_identity_holds",
]


def direction(value: float) -> str:
    """Sign label used in every published table."""
    return "contribution" if value > 0 else ("liability" if value < 0 else "neutral")


def group(cells: list[dict[str, str]], by: str) -> list[dict[str, object]]:
    """Sum TI and units over ``by`` (destination or powertrain) per company x scenario."""
    ti: dict[tuple[str, str, str], float] = defaultdict(float)
    units: dict[tuple[str, str, str], int] = defaultdict(int)
    for c in cells:
        k = (c["company"], c[by], c["scenario"])
        ti[k] += float(c["ti_tco2e"])
        units[k] += int(c["units"])
    return [
        {
            "company": k[0],
            "key": k[1],
            "scenario": k[2],
            "units": units[k],
            "ti_tco2e": round(ti[k], 4),
            "ti_per_vehicle_kgco2e": round(ti[k] * 1000.0 / units[k], 4) if units[k] else None,
            "direction": direction(ti[k]),
        }
        for k in sorted(ti)
    ]


def write(path: Path, fields: list[str], rows: list[dict[str, object]], key_name: str) -> None:
    """Write rows, renaming the generic ``key`` column to its meaning."""
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[key_name if x == "key" else x for x in fields])
        w.writeheader()
        for r in rows:
            w.writerow({(key_name if k == "key" else k): v for k, v in r.items()})


def main() -> None:
    """Aggregate and verify the decomposition identity for every company x scenario."""
    with CELLS.open(newline="") as f:
        cells = list(csv.DictReader(f))
    with WITHHELD.open(newline="") as f:
        withheld_units: dict[str, int] = defaultdict(int)
        for r in csv.DictReader(f):
            withheld_units[r["company"]] += int(r["units"])
    # Independent recomputation: the annual flow (eq 3.7) summed over years must equal the
    # cell totals (eq 3.5-3.6) — a different aggregation path, not a re-ordering of the same one.
    with ANNUAL.open(newline="") as f:
        annual_total: dict[tuple[str, str], float] = defaultdict(float)
        for r in csv.DictReader(f):
            annual_total[(r["company"], r["scenario"])] += float(r["ti_tco2e"])

    by_country = group(cells, "destination")
    by_powertrain = group(cells, "powertrain")
    write(OUT_COUNTRY, GROUP_FIELDS, by_country, "destination")
    write(OUT_POWERTRAIN, GROUP_FIELDS, by_powertrain, "powertrain")

    company_rows: list[dict[str, object]] = []
    for company in sorted({c["company"] for c in cells}):
        for scenario in sorted({c["scenario"] for c in cells}):
            mine = [c for c in cells if c["company"] == company and c["scenario"] == scenario]
            total = sum(float(c["ti_tco2e"]) for c in mine)
            covered = sum(int(c["units"]) for c in mine)
            row_sum = sum(
                float(r["ti_tco2e"])
                for r in by_country
                if r["company"] == company and r["scenario"] == scenario
            )
            col_sum = sum(
                float(r["ti_tco2e"])
                for r in by_powertrain
                if r["company"] == company and r["scenario"] == scenario
            )
            scale = max(1.0, abs(total))
            holds = (
                abs(row_sum - total) <= IDENTITY_TOL * scale
                and abs(col_sum - total) <= IDENTITY_TOL * scale
                and abs(annual_total[(company, scenario)] - total) <= 1e-6 * scale
            )
            held = withheld_units[company]
            company_rows.append(
                {
                    "company": company,
                    "scenario": scenario,
                    "cohort_year": mine[0]["cohort_year"],
                    "covered_units": covered,
                    "withheld_units": held,
                    "covered_share": round(covered / (covered + held), 6)
                    if covered + held
                    else None,
                    "ti_tco2e": round(total, 4),
                    "ti_per_vehicle_kgco2e": round(total * 1000.0 / covered, 4)
                    if covered
                    else None,
                    "direction": direction(total),
                    "decomposition_identity_holds": holds,
                }
            )
            if not holds:
                raise SystemExit(f"decomposition identity fails for {company} {scenario}")
    with OUT_COMPANY.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COMPANY_FIELDS)
        w.writeheader()
        w.writerows(company_rows)

    for r in company_rows:
        print(
            f"{r['company']} {r['scenario']}: {float(r['ti_tco2e']):>14,.0f} tCO2e  "
            f"({r['ti_per_vehicle_kgco2e']} kg/vehicle, {r['direction']}, "
            f"covered {r['covered_share']:.1%})"
        )
    print(
        f"{OUT_COUNTRY.name}: {len(by_country)} rows; {OUT_POWERTRAIN.name}: {len(by_powertrain)}; "
        f"{OUT_COMPANY.name}: {len(company_rows)}; identity holds for all"
    )


if __name__ == "__main__":
    main()
