"""Step 4 — lifetime trade impact per market x company x destination x model x powertrain.

Market-neutral: the cohort table carries the volumes and the certified product parameters for
every market, and every ``destination_parameters_*.csv`` / ``reference_trajectories_*.csv``
pair on disk is read. EU27 and US results live in the same tables, keyed by ``market``, and
are never summed together.

Inputs
    output/cohorts.csv, output/cohorts_withheld.csv       volumes + certified values (step 3a)
    output/destination_parameters_*.csv                   distance, lifetime per market
    output/reference_trajectories_*.csv                   E_ref(t), G(t) per market x scenario
    vehicle_technology/method/real_world_correction.csv   factor per test cycle x powertrain
Outputs (data/auto/output/)
    ti_by_model.csv    one row per cell x scenario: units, per-vehicle and total TI
    ti_annual.csv      annual TI flow per company x market x scenario over the cohort horizon
    ti_withheld.csv    units that carry no result and why (from step 3a, plus benchmark holds)
    ti_exclusions.csv  market x scenario combinations with no benchmark, and the units affected

Algorithm (whitepaper §3.2-3.5, guideline §3.3-3.4, §4):
    $$ E_{prod}(t) = \\begin{cases} I_{cert}\\,f_{rw}\\,D_c & \\text{ICE, HEV}\\\\
       \\eta_{cert}\\,f_{rw}\\, G_c(t)\\, D_c & \\text{BEV} \\end{cases},\\qquad
       TI_{v} = \\sum_{t=0}^{T_c-1}\\big(E_{ref,c}(t)-E_{prod}(t)\\big),\\qquad
       TI_{cell} = TI_v \\cdot N / 1000 $$
    ASCII: E_prod = tailpipe_gco2_km*factor/1000*vkt [kgCO2e/vehicle-yr] for ICE/HEV;
           E_prod(t) = energy_wh_km/1000 * factor * G(t) * vkt for BEV (G in kgCO2e/kWh);
           TI_v = sum_{t=0}^{T-1} (E_ref(t) - E_prod(t)) [kgCO2e/vehicle]; TI = TI_v*units/1000 [t]
    I_cert  certified tailpipe intensity (gCO2/km), eta_cert certified consumption (Wh/km),
    f_rw    real-world factor (-) looked up on (test cycle, powertrain): WLTP values carry the
            published OBFCM gap, EPA label values are already 5-cycle adjusted (factor 1.0),
    D_c     annual distance (km/yr), T_c operating life (years).
    Positive TI = contribution below the destination benchmark; negative = lock-in liability.

Run from the repository root:  .venv/bin/python script/auto/model/build_ti.py
"""

from __future__ import annotations

from collections import defaultdict

from model_io import (
    COHORTS_WITHHELD,
    OUT_DIR,
    REPO,
    certified,
    load_cohorts,
    load_params,
    load_real_world,
    load_reference,
    read_csv,
    scenarios_by_market,
    write_csv,
)

OUT_CELLS = OUT_DIR / "ti_by_model.csv"
OUT_ANNUAL = OUT_DIR / "ti_annual.csv"
OUT_WITHHELD = OUT_DIR / "ti_withheld.csv"
OUT_EXCLUSIONS = OUT_DIR / "ti_exclusions.csv"

IMPLAUSIBLE_BENCHMARK = (
    "destination benchmark withheld: the national car CO2 inventory and the registered stock "
    "cover different driving populations (FLEET_INTENSITY_IMPLAUSIBLE), so no defensible "
    "benchmark exists; market reported separately"
)
NO_PARAMETERS = (
    "no destination parameters for this market and country: the reference step publishes no "
    "distance, benchmark or lifetime for it"
)

CELL_FIELDS = [
    "market",
    "company",
    "destination",
    "model",
    "powertrain",
    "scenario",
    "cohort_year",
    "units",
    "lifetime_years",
    "vkt_km",
    "vkt_tier",
    "test_cycle",
    "real_world_factor",
    "e_prod_year0_kgco2e",
    "e_ref_year0_kgco2e",
    "ti_per_vehicle_kgco2e",
    "ti_tco2e",
]
ANNUAL_FIELDS = [
    "market",
    "company",
    "scenario",
    "t",
    "calendar_year",
    "surviving_vehicles",
    "ti_tco2e",
]
WITHHELD_FIELDS = [
    "market",
    "company",
    "destination",
    "cohort_year",
    "model",
    "powertrain",
    "units",
    "reason",
    "coverage_note",
]
EXCLUSION_FIELDS = [
    "market",
    "company",
    "scenario",
    "cohort_year",
    "units_affected",
    "reason",
]


def main() -> None:
    """Compute the per-cell lifetime TI and the cohort annual flow for every market."""
    cohorts = load_cohorts()
    withheld: list[dict[str, object]] = [dict(r) for r in read_csv(COHORTS_WITHHELD)]
    params = load_params()
    reference = load_reference()
    factors = load_real_world()
    scenarios = scenarios_by_market(reference)

    cells: list[dict[str, object]] = []
    annual: dict[tuple[str, str, str], dict[int, float]] = defaultdict(lambda: defaultdict(float))
    surviving: dict[tuple[str, str], dict[int, float]] = defaultdict(lambda: defaultdict(float))

    for c in cohorts:
        market, country = c["market"], c["destination"]
        units, powertrain = int(c["units"]), c["powertrain"]
        cohort_year = int(c["cohort_year"])
        identity = {
            "market": market,
            "company": c["company"],
            "destination": country,
            "cohort_year": cohort_year,
            "model": c["model"],
            "powertrain": powertrain,
        }
        p = params.get((market, country))
        if p is None:
            withheld.append(
                {
                    **identity,
                    "units": units,
                    "reason": NO_PARAMETERS,
                    "coverage_note": c["coverage_note"],
                }
            )
            continue
        if "FLEET_INTENSITY_IMPLAUSIBLE" in p["warnings"]:
            withheld.append(
                {
                    **identity,
                    "units": units,
                    "reason": IMPLAUSIBLE_BENCHMARK,
                    "coverage_note": c["coverage_note"],
                }
            )
            continue
        vkt, life = float(p["vkt_km"]), int(p["lifetime_years"])
        cert = certified(c)
        rw = factors[(c["test_cycle"], powertrain)]["factor"]
        for t in range(life):
            surviving[(market, c["company"])][cohort_year + t] += units
        for scenario in scenarios[market]:
            trajectory = reference[(market, country, scenario)]
            cumulative = 0.0
            e_prod0 = 0.0
            for t in range(life):
                e_ref, grid = trajectory[t]
                if powertrain == "BEV":
                    e_prod = cert / 1000.0 * rw * grid * vkt
                else:
                    e_prod = cert * rw / 1000.0 * vkt
                if t == 0:
                    e_prod0 = e_prod
                gap = e_ref - e_prod
                cumulative += gap
                annual[(market, c["company"], scenario)][cohort_year + t] += gap * units / 1000.0
            cells.append(
                {
                    **identity,
                    "scenario": scenario,
                    "units": units,
                    "lifetime_years": life,
                    "vkt_km": round(vkt, 3),
                    "vkt_tier": p["vkt_tier"],
                    "test_cycle": c["test_cycle"],
                    "real_world_factor": rw,
                    "e_prod_year0_kgco2e": round(e_prod0, 4),
                    "e_ref_year0_kgco2e": round(trajectory[0][0], 4),
                    "ti_per_vehicle_kgco2e": round(cumulative, 4),
                    "ti_tco2e": round(cumulative * units / 1000.0, 4),
                }
            )

    cells.sort(
        key=lambda r: tuple(
            str(r[k])
            for k in ("market", "company", "scenario", "destination", "model", "powertrain")
        )
    )
    write_csv(OUT_CELLS, CELL_FIELDS, cells)

    annual_rows: list[dict[str, object]] = []
    for (market, company, scenario), series in sorted(annual.items()):
        year0 = min(series)
        for calendar_year, value in sorted(series.items()):
            annual_rows.append(
                {
                    "market": market,
                    "company": company,
                    "scenario": scenario,
                    "t": calendar_year - year0,
                    "calendar_year": calendar_year,
                    "surviving_vehicles": int(surviving[(market, company)][calendar_year]),
                    "ti_tco2e": round(value, 4),
                }
            )
    write_csv(OUT_ANNUAL, ANNUAL_FIELDS, annual_rows)

    withheld.sort(
        key=lambda r: tuple(
            str(r[k]) for k in ("market", "company", "powertrain", "destination", "model")
        )
    )
    write_csv(OUT_WITHHELD, WITHHELD_FIELDS, withheld)

    exclusions = build_exclusions(params, cells)
    write_csv(OUT_EXCLUSIONS, EXCLUSION_FIELDS, exclusions)

    report(cells, withheld, exclusions, scenarios)


def build_exclusions(
    params: dict[tuple[str, str], dict[str, str]], cells: list[dict[str, object]]
) -> list[dict[str, object]]:
    """One row per company x market x scenario that the market publishes no benchmark for.

    The reference step records the excluded scenarios on the destination parameters; this turns
    that flag into an explicit published row carrying the units it affects, so a missing
    scenario is never a silent gap in the result tables.

    Args:
        params: (market, country) -> destination parameters.
        cells: Priced cells, used for the affected unit counts and cohort years.

    Returns:
        Exclusion rows sorted by market, company, scenario.
    """
    reasons: dict[str, dict[str, str]] = defaultdict(dict)
    for (market, _country), p in params.items():
        for entry in filter(None, p["scenario_exclusion_reason"].split(" | ")):
            scenario, _, reason = entry.partition(": ")
            reasons[market][scenario] = reason
        for scenario in filter(None, p["scenarios_excluded"].split(";")):
            reasons[market].setdefault(scenario, "no rate published for this scenario")
    rows: list[dict[str, object]] = []
    for market, per_scenario in reasons.items():
        priced = [c for c in cells if c["market"] == market]
        companies = sorted({str(c["company"]) for c in priced})
        first = sorted({str(c["scenario"]) for c in priced})[:1]
        for company in companies:
            mine = [c for c in priced if c["company"] == company and c["scenario"] in first]
            for scenario, reason in sorted(per_scenario.items()):
                rows.append(
                    {
                        "market": market,
                        "company": company,
                        "scenario": scenario,
                        "cohort_year": min(int(str(c["cohort_year"])) for c in mine)
                        if mine
                        else None,
                        "units_affected": sum(int(str(c["units"])) for c in mine),
                        "reason": reason,
                    }
                )
    rows.sort(key=lambda r: (str(r["market"]), str(r["company"]), str(r["scenario"])))
    return rows


def report(
    cells: list[dict[str, object]],
    withheld: list[dict[str, object]],
    exclusions: list[dict[str, object]],
    scenarios: dict[str, list[str]],
) -> None:
    """Print one line per company x market plus the file sizes."""
    for market in sorted(scenarios):
        for company in sorted({str(c["company"]) for c in cells if c["market"] == market}):
            mine = [c for c in cells if c["market"] == market and c["company"] == company]
            totals = {
                s: sum(float(str(c["ti_tco2e"])) for c in mine if c["scenario"] == s)
                for s in scenarios[market]
            }
            covered = sum(
                int(str(c["units"])) for c in mine if c["scenario"] == scenarios[market][0]
            )
            held = sum(
                int(str(w["units"]))
                for w in withheld
                if w["market"] == market and w["company"] == company
            )
            print(
                f"{market} {company}: covered {covered:,} units, withheld {held:,}; TI tCO2e "
                + ", ".join(f"{s} {v:,.0f}" for s, v in totals.items())
            )
    for e in exclusions:
        print(
            f"{e['market']} {e['company']} {e['scenario']}: excluded, "
            f"{int(str(e['units_affected'])):,} units affected"
        )
    print(
        f"{OUT_CELLS.relative_to(REPO)}: {len(cells)} rows; {OUT_WITHHELD.name}: "
        f"{len(withheld)}; {OUT_EXCLUSIONS.name}: {len(exclusions)}"
    )


if __name__ == "__main__":
    main()
