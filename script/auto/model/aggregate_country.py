"""Step 5 — aggregate the per-cell lifetime TI to importer country and exporter company.

Every roll-up is per company **x market**: EU27 and US cohorts rest on different sales bases,
different test cycles and different benchmarks, so they are never summed into one figure.

Input   data/auto/output/ti_by_model.csv, ti_annual.csv, ti_withheld.csv, ti_exclusions.csv
Outputs data/auto/output/ti_country.csv     company x market x destination x scenario
        data/auto/output/ti_powertrain.csv  company x market x powertrain x scenario
        data/auto/output/ti_company.csv     company x market x scenario, with the decomposition
                                            check and one explicit row per excluded scenario

Algorithm (whitepaper §3.6-3.7):
    $$ TI_{firm,m,S} = \\sum_{c}\\sum_{p} TI_{m,c,p,S},\\qquad
       \\sum_c TI_{m,c,S} = \\sum_p TI_{m,p,S} = TI_{firm,m,S} $$
    ASCII: total = sum over destinations = sum over powertrains, within one market
           (identity checked to 1e-9 relative, and against the annual flow to 1e-6).
    Per-vehicle values are units-weighted means (kgCO2e per covered vehicle).

Run from the repository root:  .venv/bin/python script/auto/model/aggregate_country.py
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from model_io import OUT_DIR, read_csv, write_csv

CELLS = OUT_DIR / "ti_by_model.csv"
WITHHELD = OUT_DIR / "ti_withheld.csv"
ANNUAL = OUT_DIR / "ti_annual.csv"
EXCLUSIONS = OUT_DIR / "ti_exclusions.csv"
OUT_COUNTRY = OUT_DIR / "ti_country.csv"
OUT_POWERTRAIN = OUT_DIR / "ti_powertrain.csv"
OUT_COMPANY = OUT_DIR / "ti_company.csv"

# Summands are 4-dp-rounded values summed in different orders; the true float error is
# ~1e-10 relative, so anything looser than this would let a dropped small cell through.
IDENTITY_TOL = 1e-9
ANNUAL_TOL = 1e-6

REPORTED, EXCLUDED = "reported", "excluded"

GROUP_FIELDS = [
    "company",
    "market",
    "key",
    "scenario",
    "units",
    "ti_tco2e",
    "ti_per_vehicle_kgco2e",
    "direction",
]
COMPANY_FIELDS = [
    "company",
    "market",
    "scenario",
    "cohort_year",
    "status",
    "covered_units",
    "withheld_units",
    "covered_share",
    "ti_tco2e",
    "ti_per_vehicle_kgco2e",
    "direction",
    "decomposition_identity_holds",
    "exclusion_reason",
]


def direction(value: float) -> str:
    """Sign label used in every published table."""
    return "contribution" if value > 0 else ("liability" if value < 0 else "neutral")


def group(cells: list[dict[str, str]], by: str) -> list[dict[str, object]]:
    """Sum TI and units over ``by`` (destination or powertrain) per company x market x scenario."""
    ti: dict[tuple[str, str, str, str], float] = defaultdict(float)
    units: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for c in cells:
        k = (c["company"], c["market"], c[by], c["scenario"])
        ti[k] += float(c["ti_tco2e"])
        units[k] += int(c["units"])
    return [
        {
            "company": k[0],
            "market": k[1],
            "key": k[2],
            "scenario": k[3],
            "units": units[k],
            "ti_tco2e": round(ti[k], 4),
            "ti_per_vehicle_kgco2e": round(ti[k] * 1000.0 / units[k], 4) if units[k] else None,
            "direction": direction(ti[k]),
        }
        for k in sorted(ti)
    ]


def write_group(path: Path, rows: list[dict[str, object]], key_name: str) -> None:
    """Write a grouped table, renaming the generic ``key`` column to its meaning."""
    fields = [key_name if x == "key" else x for x in GROUP_FIELDS]
    write_csv(
        path, fields, [{(key_name if k == "key" else k): v for k, v in r.items()} for r in rows]
    )


def main() -> None:
    """Aggregate and verify the decomposition identity for every company x market x scenario."""
    cells = read_csv(CELLS)
    withheld_units: dict[tuple[str, str], int] = defaultdict(int)
    for r in read_csv(WITHHELD):
        withheld_units[(r["company"], r["market"])] += int(r["units"])
    # Independent recomputation: the annual flow (eq 3.7) summed over years must equal the
    # cell totals (eq 3.5-3.6) — a different aggregation path, not a re-ordering of the same one.
    annual_total: dict[tuple[str, str, str], float] = defaultdict(float)
    for r in read_csv(ANNUAL):
        annual_total[(r["company"], r["market"], r["scenario"])] += float(r["ti_tco2e"])
    exclusions = read_csv(EXCLUSIONS)

    by_country = group(cells, "destination")
    by_powertrain = group(cells, "powertrain")
    write_group(OUT_COUNTRY, by_country, "destination")
    write_group(OUT_POWERTRAIN, by_powertrain, "powertrain")

    company_rows: list[dict[str, object]] = []
    for company, market in sorted({(c["company"], c["market"]) for c in cells}):
        theirs = [c for c in cells if c["company"] == company and c["market"] == market]
        held = withheld_units[(company, market)]
        for scenario in sorted({c["scenario"] for c in theirs}):
            mine = [c for c in theirs if c["scenario"] == scenario]
            total = sum(float(c["ti_tco2e"]) for c in mine)
            covered = sum(int(c["units"]) for c in mine)
            row_sum = sum(
                float(str(r["ti_tco2e"]))
                for r in by_country
                if (r["company"], r["market"], r["scenario"]) == (company, market, scenario)
            )
            col_sum = sum(
                float(str(r["ti_tco2e"]))
                for r in by_powertrain
                if (r["company"], r["market"], r["scenario"]) == (company, market, scenario)
            )
            scale = max(1.0, abs(total))
            holds = (
                abs(row_sum - total) <= IDENTITY_TOL * scale
                and abs(col_sum - total) <= IDENTITY_TOL * scale
                and abs(annual_total[(company, market, scenario)] - total) <= ANNUAL_TOL * scale
            )
            company_rows.append(
                {
                    "company": company,
                    "market": market,
                    "scenario": scenario,
                    "cohort_year": min(int(c["cohort_year"]) for c in mine),
                    "status": REPORTED,
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
                    "exclusion_reason": "",
                }
            )
            if not holds:
                raise SystemExit(f"decomposition identity fails for {company} {market} {scenario}")
        # An excluded scenario is published as its own row so the gap is never silent.
        for e in exclusions:
            if (e["company"], e["market"]) != (company, market):
                continue
            company_rows.append(
                {
                    "company": company,
                    "market": market,
                    "scenario": e["scenario"],
                    "cohort_year": e["cohort_year"],
                    "status": EXCLUDED,
                    "covered_units": int(e["units_affected"]),
                    "withheld_units": held,
                    "covered_share": None,
                    "ti_tco2e": None,
                    "ti_per_vehicle_kgco2e": None,
                    "direction": None,
                    "decomposition_identity_holds": None,
                    "exclusion_reason": e["reason"],
                }
            )
    company_rows.sort(key=lambda r: (str(r["company"]), str(r["market"]), str(r["scenario"])))
    write_csv(OUT_COMPANY, COMPANY_FIELDS, company_rows)

    for published in company_rows:
        label = f"{published['company']} {published['market']} {published['scenario']}"
        if published["status"] == EXCLUDED:
            print(f"{label}: excluded (no benchmark)")
            continue
        print(
            f"{label}: {float(str(published['ti_tco2e'])):>14,.0f} tCO2e  "
            f"({published['ti_per_vehicle_kgco2e']} kg/vehicle, {published['direction']}, "
            f"covered {float(str(published['covered_share'])):.1%})"
        )
    print(
        f"{OUT_COUNTRY.name}: {len(by_country)} rows; {OUT_POWERTRAIN.name}: {len(by_powertrain)}; "
        f"{OUT_COMPANY.name}: {len(company_rows)}; identity holds for all"
    )


if __name__ == "__main__":
    main()
