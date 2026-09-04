"""Step 5 — aggregate the per-cell lifetime TI to importer country and exporter company.

Every roll-up is per company **x market**: EU27 and US cohorts rest on different sales bases,
different test cycles and different benchmarks, so they are never summed into one figure.

Input   data/auto/output/ti_by_model.csv, ti_annual.csv, ti_annual_by_model.csv,
        ti_withheld.csv, ti_exclusions.csv
Outputs data/auto/output/ti_country.csv     company x market x destination x scenario
        data/auto/output/ti_powertrain.csv  company x market x powertrain x scenario
        data/auto/output/ti_company.csv     company x market x scenario, with the decomposition
                                            check and one explicit row per excluded scenario
        data/auto/output/ti_annual_country.csv     the same two roll-ups by calendar year, each
        data/auto/output/ti_annual_powertrain.csv  carrying the benchmark and the product side
                                            as well as their difference, so a reader can see
                                            what is being compared in every year and not only
                                            the lifetime total

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
ANNUAL_CELLS = OUT_DIR / "ti_annual_by_model.csv"
EXCLUSIONS = OUT_DIR / "ti_exclusions.csv"
OUT_COUNTRY = OUT_DIR / "ti_country.csv"
OUT_POWERTRAIN = OUT_DIR / "ti_powertrain.csv"
OUT_COMPANY = OUT_DIR / "ti_company.csv"
OUT_ANNUAL_COUNTRY = OUT_DIR / "ti_annual_country.csv"
OUT_ANNUAL_POWERTRAIN = OUT_DIR / "ti_annual_powertrain.csv"

# Summands are 4-dp-rounded values summed in different orders; the true float error is
# ~1e-10 relative, so anything looser than this would let a dropped small cell through.
IDENTITY_TOL = 1e-9
ANNUAL_TOL = 1e-6
# Cell values are published rounded to 4 dp of tCO2e, so a roll-up over n cells can differ from
# the unrounded flow by up to half a step per cell.
CELL_ROUNDING = 5e-5

REPORTED, EXCLUDED = "reported", "excluded"

GROUP_FIELDS = [
    "company",
    "market",
    "cohort_year",
    "key",
    "scenario",
    "units",
    "ti_tco2e",
    "ti_per_vehicle_kgco2e",
    "direction",
]
ANNUAL_GROUP_FIELDS = [
    "company",
    "market",
    "cohort_year",
    "key",
    "scenario",
    "t",
    "calendar_year",
    "units",
    "e_ref_tco2e",
    "e_prod_tco2e",
    "ti_tco2e",
    "cumulative_ti_tco2e",
    "e_ref_kgco2e_per_vehicle",
    "e_prod_kgco2e_per_vehicle",
    "gap_kgco2e_per_vehicle",
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
    """Sign label used in every published table.

    TI is the product's emissions minus the benchmark's, so a positive figure is emissions the
    destination is locked into and a negative figure is emissions avoided. The words stay
    attached to the meaning, not to the sign.
    """
    return "liability" if value > 0 else ("contribution" if value < 0 else "neutral")


def group(cells: list[dict[str, str]], by: str) -> list[dict[str, object]]:
    """Sum TI and units over ``by`` (destination or powertrain) per company x market x scenario."""
    ti: dict[tuple[str, str, int, str, str], float] = defaultdict(float)
    units: dict[tuple[str, str, int, str, str], int] = defaultdict(int)
    for c in cells:
        k = (c["company"], c["market"], int(c["cohort_year"]), c[by], c["scenario"])
        ti[k] += float(c["ti_tco2e"])
        units[k] += int(c["units"])
    return [
        {
            "company": k[0],
            "market": k[1],
            "cohort_year": k[2],
            "key": k[3],
            "scenario": k[4],
            "units": units[k],
            "ti_tco2e": round(ti[k], 4),
            "ti_per_vehicle_kgco2e": round(ti[k] * 1000.0 / units[k], 4) if units[k] else None,
            "direction": direction(ti[k]),
        }
        for k in sorted(ti)
    ]


def group_annual(cells: list[dict[str, str]], by: str) -> list[dict[str, object]]:
    """Roll the per-cell annual flow up over ``by``, keeping both sides of the comparison.

    The benchmark and the product are summed separately and their difference is the annual TI,
    so every row states what a surviving vehicle of that group would have emitted under the
    scenario benchmark, what it actually emits, and the gap — in that calendar year, not over
    the lifetime. The summands are the cell values as published, rounded to 4 dp of tCO2e, so a
    group total inherits at most 5e-5 tCO2e of rounding per cell; that is the bound the identity
    check below allows for.

    Args:
        cells: Rows of ``ti_annual_by_model.csv``.
        by: Column to group on, ``destination`` or ``powertrain``.

    Returns:
        One row per company x market x cohort year x group x scenario x calendar year,
        ordered so the running total reads down the table.
    """
    sums: dict[tuple[str, str, int, str, str, int], dict[str, float]] = defaultdict(
        lambda: {"e_ref": 0.0, "e_prod": 0.0, "units": 0.0, "cells": 0.0}
    )
    for c in cells:
        key = (
            c["company"],
            c["market"],
            int(c["cohort_year"]),
            c[by],
            c["scenario"],
            int(c["calendar_year"]),
        )
        units = int(c["units"])
        bucket = sums[key]
        bucket["e_ref"] += float(c["e_ref_tco2e"])
        bucket["e_prod"] += float(c["e_prod_tco2e"])
        bucket["units"] += units
        bucket["cells"] += 1

    rows: list[dict[str, object]] = []
    cumulative: dict[tuple[str, str, int, str, str], float] = defaultdict(float)
    for key in sorted(sums):
        company, market, cohort_year, group_key, scenario, calendar_year = key
        bucket = sums[key]
        units, flow = bucket["units"], bucket["e_prod"] - bucket["e_ref"]
        running = cumulative[(company, market, cohort_year, group_key, scenario)] + flow
        cumulative[(company, market, cohort_year, group_key, scenario)] = running
        rows.append(
            {
                "company": company,
                "market": market,
                "cohort_year": cohort_year,
                "key": group_key,
                "scenario": scenario,
                "t": calendar_year - cohort_year,
                "calendar_year": calendar_year,
                "units": int(units),
                "e_ref_tco2e": round(bucket["e_ref"], 4),
                "e_prod_tco2e": round(bucket["e_prod"], 4),
                "ti_tco2e": round(flow, 4),
                "cumulative_ti_tco2e": round(running, 4),
                "e_ref_kgco2e_per_vehicle": round(bucket["e_ref"] * 1000.0 / units, 4),
                "e_prod_kgco2e_per_vehicle": round(bucket["e_prod"] * 1000.0 / units, 4),
                "gap_kgco2e_per_vehicle": round(flow * 1000.0 / units, 4),
                "direction": direction(flow),
            }
        )
    return rows


def write_group(path: Path, rows: list[dict[str, object]], key_name: str) -> None:
    """Write a grouped table, renaming the generic ``key`` column to its meaning."""
    template = ANNUAL_GROUP_FIELDS if "calendar_year" in rows[0] else GROUP_FIELDS
    fields = [key_name if x == "key" else x for x in template]
    write_csv(
        path, fields, [{(key_name if k == "key" else k): v for k, v in r.items()} for r in rows]
    )


def main() -> None:
    """Aggregate and verify the decomposition identity for every company x market x scenario."""
    cells = read_csv(CELLS)
    withheld_units: dict[tuple[str, str, int], int] = defaultdict(int)
    for r in read_csv(WITHHELD):
        withheld_units[(r["company"], r["market"], int(r["cohort_year"]))] += int(r["units"])
    # Independent recomputation: the annual flow (eq 3.7) summed over years must equal the
    # cell totals (eq 3.5-3.6) — a different aggregation path, not a re-ordering of the same one.
    annual_total: dict[tuple[str, str, int, str], float] = defaultdict(float)
    annual_flow: dict[tuple[str, str, int, str, int], float] = {}
    for r in read_csv(ANNUAL):
        key = (r["company"], r["market"], int(r["cohort_year"]), r["scenario"])
        annual_total[key] += float(r["ti_tco2e"])
        annual_flow[(*key, int(r["calendar_year"]))] = float(r["ti_tco2e"])
    exclusions = read_csv(EXCLUSIONS)

    by_country = group(cells, "destination")
    by_powertrain = group(cells, "powertrain")
    write_group(OUT_COUNTRY, by_country, "destination")
    write_group(OUT_POWERTRAIN, by_powertrain, "powertrain")

    annual_cells = read_csv(ANNUAL_CELLS)
    annual_by_country = group_annual(annual_cells, "destination")
    annual_by_powertrain = group_annual(annual_cells, "powertrain")
    write_group(OUT_ANNUAL_COUNTRY, annual_by_country, "destination")
    write_group(OUT_ANNUAL_POWERTRAIN, annual_by_powertrain, "powertrain")
    # The same identity as the lifetime tables, held year by year: the two annual roll-ups must
    # each reproduce the company annual flow.
    cell_counts: dict[tuple[str, str, int, str, int], int] = defaultdict(int)
    for c in annual_cells:
        cell_counts[
            (
                c["company"],
                c["market"],
                int(c["cohort_year"]),
                c["scenario"],
                int(c["calendar_year"]),
            )
        ] += 1
    for label, rows in (("destination", annual_by_country), ("powertrain", annual_by_powertrain)):
        totals: dict[tuple[str, str, int, str, int], float] = defaultdict(float)
        for r in rows:
            key = (
                str(r["company"]),
                str(r["market"]),
                int(str(r["cohort_year"])),
                str(r["scenario"]),
                int(str(r["calendar_year"])),
            )
            totals[key] += float(str(r["ti_tco2e"]))
        for key, value in totals.items():
            published = annual_flow.get(key)
            if published is None:
                raise SystemExit(f"annual {label} roll-up has no company row for {key}")
            bound = ANNUAL_TOL * max(1.0, abs(published)) + CELL_ROUNDING * cell_counts[key]
            if abs(value - published) > bound:
                raise SystemExit(
                    f"annual {label} roll-up {value:,.4f} != company annual flow "
                    f"{published:,.4f} for {key} (bound {bound:,.6f})"
                )

    company_rows: list[dict[str, object]] = []
    grains = sorted({(c["company"], c["market"], int(c["cohort_year"])) for c in cells})
    for company, market, cohort_year in grains:
        theirs = [
            c
            for c in cells
            if c["company"] == company
            and c["market"] == market
            and int(c["cohort_year"]) == cohort_year
        ]
        held = withheld_units[(company, market, cohort_year)]
        grain = (company, market, cohort_year)
        for scenario in sorted({c["scenario"] for c in theirs}):
            mine = [c for c in theirs if c["scenario"] == scenario]
            total = sum(float(c["ti_tco2e"]) for c in mine)
            covered = sum(int(c["units"]) for c in mine)
            row_sum = sum(
                float(str(r["ti_tco2e"]))
                for r in by_country
                if (r["company"], r["market"], r["cohort_year"], r["scenario"])
                == (*grain, scenario)
            )
            col_sum = sum(
                float(str(r["ti_tco2e"]))
                for r in by_powertrain
                if (r["company"], r["market"], r["cohort_year"], r["scenario"])
                == (*grain, scenario)
            )
            scale = max(1.0, abs(total))
            holds = (
                abs(row_sum - total) <= IDENTITY_TOL * scale
                and abs(col_sum - total) <= IDENTITY_TOL * scale
                and abs(annual_total[(*grain, scenario)] - total) <= ANNUAL_TOL * scale
            )
            company_rows.append(
                {
                    "company": company,
                    "market": market,
                    "scenario": scenario,
                    "cohort_year": cohort_year,
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
                raise SystemExit(
                    f"decomposition identity fails for {company} {market} {cohort_year} {scenario}"
                )
        # An excluded scenario is published as its own row so the gap is never silent.
        for e in exclusions:
            if (e["company"], e["market"], int(e["cohort_year"])) != grain:
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
    company_rows.sort(
        key=lambda r: (
            str(r["company"]),
            str(r["market"]),
            str(r["cohort_year"]),
            str(r["scenario"]),
        )
    )
    write_csv(OUT_COMPANY, COMPANY_FIELDS, company_rows)

    for published in company_rows:
        label = (
            f"{published['company']} {published['market']} {published['cohort_year']} "
            f"{published['scenario']}"
        )
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
        f"{OUT_COMPANY.name}: {len(company_rows)}; {OUT_ANNUAL_COUNTRY.name}: "
        f"{len(annual_by_country)}; {OUT_ANNUAL_POWERTRAIN.name}: {len(annual_by_powertrain)}; "
        "identity holds for all, year by year"
    )


if __name__ == "__main__":
    main()
