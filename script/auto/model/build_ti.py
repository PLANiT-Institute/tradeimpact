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
    ti_annual.csv      per company x market x cohort year x scenario x calendar year: the
                       surviving fleet, what the benchmark would have emitted, what the
                       products emit, their difference (the annual TI), the running total,
                       and all three per surviving vehicle
    ti_annual_by_model.csv  the same flow at cell grain: per market x company x destination x
                       model x powertrain x scenario x year (benchmark, product, gap, TI)
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
    DATA,
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
OUT_ANNUAL_CELLS = OUT_DIR / "ti_annual_by_model.csv"
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
    "segment",
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
    "fleet_intensity_tier",
    "grid_tier",
    "lifetime_tier",
    "rate_tier",
    "layer1_tier",
    "technology_tier",
    "powertrain_tier",
    "layer2_tier",
    "tier",
]
ANNUAL_FIELDS = [
    "market",
    "company",
    "cohort_year",
    "scenario",
    "t",
    "calendar_year",
    "surviving_vehicles",
    "e_ref_tco2e",
    "e_prod_tco2e",
    "ti_tco2e",
    "cumulative_ti_tco2e",
    "e_ref_kgco2e_per_vehicle",
    "e_prod_kgco2e_per_vehicle",
    "gap_kgco2e_per_vehicle",
]
ANNUAL_CELL_FIELDS = [
    "market",
    "company",
    "destination",
    "cohort_year",
    "segment",
    "model",
    "powertrain",
    "scenario",
    "t",
    "calendar_year",
    "units",
    "e_ref_kgco2e_per_vehicle",
    "e_prod_kgco2e_per_vehicle",
    "gap_kgco2e_per_vehicle",
    "e_ref_tco2e",
    "e_prod_tco2e",
    "ti_tco2e",
    "tier",
]
WITHHELD_FIELDS = [
    "market",
    "company",
    "destination",
    "cohort_year",
    "segment",
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


TIER_ORDER = {"A": 0, "B": 1, "C": 2}
#: Whitepaper §5.1 tier of a scenario rate by how it was derived (emission_targets target_level).
RATE_TIER = {
    "observed_trend": "A",
    "ndc_prorata": "B",
    "ndc_prorata_s1_floor": "B",
    "1p5c_prorata": "B",
    "world_prorata": "C",
}
#: Tier of the certified product value by the test cycle it comes from.
TECHNOLOGY_TIER = {"WLTP": "A", "EPA": "A", "KR_5CYCLE": "B"}


def worst(*tiers: str) -> str:
    """The lowest data-quality tier among the given ones (C is worse than B is worse than A)."""
    ranked = [t for t in tiers if t in TIER_ORDER]
    return max(ranked, key=lambda t: TIER_ORDER[t]) if ranked else ""


def powertrain_tier(rule: str) -> str:
    """Tier of the volume-to-powertrain step from the cohort's powertrain rule."""
    if rule.startswith(("explicit", "stated")):
        return "A"
    if rule.startswith("epa_share"):
        return "B"
    return "C"


def load_rate_tiers() -> dict[tuple[str, str], str]:
    """(country, scenario) -> worst tier of its two rates, from the processed target tables."""
    out: dict[tuple[str, str], str] = {}
    for path in sorted((DATA / "emission_targets" / "processed").glob("emission_targets_*.csv")):
        for r in read_csv(path):
            key = (r["country"], r["scenario"])
            out[key] = worst(out.get(key, ""), RATE_TIER.get(r["target_level"], "C"))
    return out


def main() -> None:
    """Compute the per-cell lifetime TI and the cohort annual flow for every market."""
    rate_tiers = load_rate_tiers()
    cohorts = load_cohorts()
    withheld: list[dict[str, object]] = [dict(r) for r in read_csv(COHORTS_WITHHELD)]
    params = load_params()
    reference = load_reference()
    factors = load_real_world()
    scenarios = scenarios_by_market(reference)

    cells: list[dict[str, object]] = []

    annual_cells: list[dict[str, object]] = []
    #: (market, company, cohort year, scenario) -> calendar year -> {benchmark, product}
    #: emissions in tCO2e. The annual TI is their difference, so the table carries the
    #: comparison and not only its result.
    annual: dict[tuple[str, str, int, str], dict[int, dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: {"e_ref": 0.0, "e_prod": 0.0})
    )
    surviving: dict[tuple[str, str, int], dict[int, float]] = defaultdict(
        lambda: defaultdict(float)
    )

    for c in cohorts:
        market, country, segment = c["market"], c["destination"], c["segment"]
        units, powertrain = int(c["units"]), c["powertrain"]
        cohort_year = int(c["cohort_year"])
        identity = {
            "market": market,
            "segment": segment,
            "company": c["company"],
            "destination": country,
            "cohort_year": cohort_year,
            "model": c["model"],
            "powertrain": powertrain,
        }
        p = params.get((market, country, segment))
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
            surviving[(market, c["company"], cohort_year)][cohort_year + t] += units
        for scenario in scenarios[market]:
            trajectory = reference[(market, country, segment, scenario)]
            tier_flags = tiers(p, c, country, scenario, rate_tiers)
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
                bucket = annual[(market, c["company"], cohort_year, scenario)][cohort_year + t]
                bucket["e_ref"] += e_ref * units / 1000.0
                bucket["e_prod"] += e_prod * units / 1000.0
                annual_cells.append(
                    {
                        **identity,
                        "scenario": scenario,
                        "t": t,
                        "calendar_year": cohort_year + t,
                        "units": units,
                        "e_ref_kgco2e_per_vehicle": round(e_ref, 4),
                        "e_prod_kgco2e_per_vehicle": round(e_prod, 4),
                        "gap_kgco2e_per_vehicle": round(gap, 4),
                        "e_ref_tco2e": round(e_ref * units / 1000.0, 4),
                        "e_prod_tco2e": round(e_prod * units / 1000.0, 4),
                        "ti_tco2e": round(gap * units / 1000.0, 4),
                        "tier": tier_flags["tier"],
                    }
                )
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
                    **tier_flags,
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
    for (market, company, cohort_year, scenario), series in sorted(annual.items()):
        cumulative = 0.0
        for calendar_year, side in sorted(series.items()):
            fleet = surviving[(market, company, cohort_year)][calendar_year]
            flow = side["e_ref"] - side["e_prod"]
            cumulative += flow
            annual_rows.append(
                {
                    "market": market,
                    "company": company,
                    "cohort_year": cohort_year,
                    "scenario": scenario,
                    "t": calendar_year - cohort_year,
                    "calendar_year": calendar_year,
                    "surviving_vehicles": int(fleet),
                    "e_ref_tco2e": round(side["e_ref"], 4),
                    "e_prod_tco2e": round(side["e_prod"], 4),
                    "ti_tco2e": round(flow, 4),
                    "cumulative_ti_tco2e": round(cumulative, 4),
                    "e_ref_kgco2e_per_vehicle": round(side["e_ref"] * 1000.0 / fleet, 4),
                    "e_prod_kgco2e_per_vehicle": round(side["e_prod"] * 1000.0 / fleet, 4),
                    "gap_kgco2e_per_vehicle": round(flow * 1000.0 / fleet, 4),
                }
            )
    write_csv(OUT_ANNUAL, ANNUAL_FIELDS, annual_rows)
    annual_cells.sort(
        key=lambda r: (
            str(r["market"]),
            str(r["company"]),
            str(r["scenario"]),
            str(r["destination"]),
            str(r["model"]),
            str(r["powertrain"]),
            int(str(r["t"])),
        )
    )
    write_csv(OUT_ANNUAL_CELLS, ANNUAL_CELL_FIELDS, annual_cells)

    withheld.sort(
        key=lambda r: tuple(
            str(r[k]) for k in ("market", "company", "powertrain", "destination", "model")
        )
    )
    write_csv(OUT_WITHHELD, WITHHELD_FIELDS, withheld)

    exclusions = build_exclusions(params, cells)
    write_csv(OUT_EXCLUSIONS, EXCLUSION_FIELDS, exclusions)

    report(cells, withheld, exclusions, scenarios)


def tiers(
    p: dict[str, str],
    c: dict[str, str],
    country: str,
    scenario: str,
    rate_tiers: dict[tuple[str, str], str],
) -> dict[str, str]:
    """Whitepaper §5.2 tier declaration of one cell: Layer 1 (benchmark) and Layer 2 (product).

    Layer 1 is the worst of the destination's distance, fleet-intensity, grid and lifetime tiers
    and of the scenario's rate tier; Layer 2 is the worst of the certified-value tier (by test
    cycle) and the powertrain-attribution tier (by rule). ``tier`` is the worst of both layers.
    """
    rate = rate_tiers.get((country, scenario), "")
    layer1 = worst(
        p["vkt_tier"], p["fleet_intensity_tier"], p["grid_tier"], p["lifetime_tier"], rate
    )
    tech = TECHNOLOGY_TIER.get(c["test_cycle"], "C")
    pt = powertrain_tier(c["powertrain_rule"])
    layer2 = worst(tech, pt)
    return {
        "fleet_intensity_tier": p["fleet_intensity_tier"],
        "grid_tier": p["grid_tier"],
        "lifetime_tier": p["lifetime_tier"],
        "rate_tier": rate,
        "layer1_tier": layer1,
        "technology_tier": tech,
        "powertrain_tier": pt,
        "layer2_tier": layer2,
        "tier": worst(layer1, layer2),
    }


def build_exclusions(
    params: dict[tuple[str, str], dict[str, str]], cells: list[dict[str, object]]
) -> list[dict[str, object]]:
    """One row per company x market x scenario that the market publishes no benchmark for.

    The reference step records the excluded scenarios on the destination parameters; this turns
    that flag into an explicit published row carrying the units it affects, so a missing
    scenario is never a silent gap in the result tables.

    Args:
        params: (market, country) -> destination parameters.
        cells: Assessed cells, used for the affected unit counts and cohort years.

    Returns:
        Exclusion rows sorted by market, company, scenario.
    """
    reasons: dict[str, dict[str, str]] = defaultdict(dict)
    for (market, _country, _segment), p in params.items():
        for entry in filter(None, p["scenario_exclusion_reason"].split(" | ")):
            scenario, _, reason = entry.partition(": ")
            reasons[market][scenario] = reason
        for scenario in filter(None, p["scenarios_excluded"].split(";")):
            reasons[market].setdefault(scenario, "no rate published for this scenario")
    rows: list[dict[str, object]] = []
    for market, per_scenario in reasons.items():
        assessed = [c for c in cells if c["market"] == market]
        companies = sorted({str(c["company"]) for c in assessed})
        first = sorted({str(c["scenario"]) for c in assessed})[:1]
        for company in companies:
            mine = [c for c in assessed if c["company"] == company and c["scenario"] in first]
            for cohort_year in sorted({int(str(c["cohort_year"])) for c in mine}):
                year_cells = [c for c in mine if int(str(c["cohort_year"])) == cohort_year]
                for scenario, reason in sorted(per_scenario.items()):
                    rows.append(
                        {
                            "market": market,
                            "company": company,
                            "scenario": scenario,
                            "cohort_year": cohort_year,
                            "units_affected": sum(int(str(c["units"])) for c in year_cells),
                            "reason": reason,
                        }
                    )
    rows.sort(
        key=lambda r: (
            str(r["market"]),
            str(r["company"]),
            str(r["cohort_year"]),
            str(r["scenario"]),
        )
    )
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
