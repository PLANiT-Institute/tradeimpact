"""Step 4b — crossover year per cell and the mandatory sensitivities (guideline §3.3, §5).

Inputs   output/cohorts.csv, output/destination_parameters_*.csv,
         output/reference_trajectories_*.csv (rates),
         vehicle_technology/method/real_world_correction.csv
Outputs  output/ti_crossover.csv     per market x company x destination x model x powertrain
                                     x scenario
         output/ti_sensitivity.csv   per company x market x scenario x dimension x variant

Algorithm:
    Crossover t* is the year the annual gap changes sign (closed form, whitepaper §3.3 note,
    guideline §3.3):
    $$ t^*_{ICE} = \\frac{\\ln\\big(E_{prod}/E_{ref}(0)\\big)}{\\ln(1-r_{fleet})} $$
    $$ t^*_{BEV} = \\frac{\\ln\\big(\\eta G_0 / I_0\\big)}
                        {\\ln\\big((1-r_{fleet})/(1-r_{power})\\big)} $$
    ASCII: t_ice = ln(E_prod/E_ref0)/ln(1-r_fleet)
           t_bev = ln(eta*G0/I0)/ln((1-r_fleet)/(1-r_power))
    Negative t* means the product is already above (ICE) or below (BEV) the benchmark at sale.
    Sensitivities recompute the cohort total with one input moved at a time:
      lifetime       T_c -/+ 3 years (guideline §5.2; each market's own T, floor 1)
      realworld      the factor of each (test cycle, powertrain) set to the low and the high end
                     of its published band; the factor REPLACES the central one, it is never
                     applied on top of it. EPA label values have no band (1.0 at both ends).
      vkt_proxy      proxied (tier C) markets moved to the lower/upper quartile of measured
                     distances; the benchmark per vehicle is unchanged because distance cancels
                     in CO2 per car. Only markets whose parameters publish the quartiles move.
      powertrain_mix cohort rows whose sales source does not split the powertrain
                     (``powertrain_rule = epa_share_my2024``) are repriced with the hybrid
                     technology of the same base model; the central case prices them as ICE.
    Symbols: E in kgCO2e per vehicle-year, I0 fleet intensity (kg/km), G0 grid (kg/kWh), eta
    consumption (kWh/km), r in 1/year, T in years.

Run from the repository root:  .venv/bin/python script/auto/model/build_sensitivity.py
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from model_io import (
    ALL_HEV,
    OUT_DIR,
    REPO,
    certified,
    load_cohorts,
    load_params,
    load_rates,
    load_real_world,
    scenarios_by_market,
    write_csv,
)

OUT_CROSS = OUT_DIR / "ti_crossover.csv"
OUT_SENS = OUT_DIR / "ti_sensitivity.csv"

LIFETIME_DELTA_Y = 3
MIXED_RULE = "epa_share_my2024"
MIXED_PREFIXES = (MIXED_RULE, "kr_unsplit_central_ice")

CROSS_FIELDS = [
    "market",
    "company",
    "destination",
    "model",
    "powertrain",
    "scenario",
    "units",
    "ti_per_vehicle_kgco2e",
    "crossover_year",
    "crossover_calendar_year",
    "reason",
]
SENS_FIELDS = [
    "company",
    "market",
    "cohort_year",
    "scenario",
    "dimension",
    "variant",
    "parameter",
    "ti_tco2e",
]


@dataclass(frozen=True)
class Cell:
    """One priced cohort cell, with everything the sensitivity needs to reprice it.

    Attributes:
        market: Market key, e.g. `EU27` or `US`.
        company: Exporter.
        destination: Importing country (ISO 3166-1 alpha-2).
        segment: Vehicle segment, which decides the benchmark the cell is priced against.
        model: Commercial model name as the sales source reports it.
        powertrain: ICE / HEV / BEV.
        cohort_year: Sale year.
        units: Vehicles in the cell.
        cert: Certified parameter — gCO2/km for ICE and HEV, Wh/km for BEV.
        test_cycle: Cycle the certified value is measured on (WLTP or EPA).
        rule: Powertrain rule from the cohort table.
    """

    market: str
    company: str
    destination: str
    segment: str
    model: str
    powertrain: str
    cohort_year: int
    units: int
    cert: float
    test_cycle: str
    rule: str


def to_cell(row: dict[str, str]) -> Cell:
    """Build a :class:`Cell` from a cohort row."""
    return Cell(
        market=row["market"],
        company=row["company"],
        destination=row["destination"],
        segment=row["segment"],
        model=row["model"],
        powertrain=row["powertrain"],
        cohort_year=int(row["cohort_year"]),
        units=int(row["units"]),
        cert=certified(row),
        test_cycle=row["test_cycle"],
        rule=row["powertrain_rule"],
    )


def crossover(
    pt: str, i0: float, rf: float, rp: float, e_prod0: float, eta_g0: float
) -> tuple[float | None, str | None]:
    """Closed-form t* (years after sale) or (None, reason).

    Args:
        pt: Powertrain.
        i0: Fleet benchmark intensity at t=0 (kgCO2e/km).
        rf: Annual fractional decline of the fleet benchmark (1/year).
        rp: Annual fractional decline of the grid (1/year).
        e_prod0: For ICE/HEV, the ratio E_prod / E_ref(0) (-); unused for BEV.
        eta_g0: For BEV, the product intensity at t=0 (kgCO2e/km); unused otherwise.

    Returns:
        (t*, None) when a finite non-negative crossover exists, else (None, reason).
    """
    if pt == "BEV":
        a, b = 1.0 - rf, 1.0 - rp
        if eta_g0 <= 0 or i0 <= 0:
            return None, "non-positive intensity"
        if abs(a - b) < 1e-12:
            return None, "r_fleet == r_power: parallel trajectories, no finite crossover"
        t = math.log(eta_g0 / i0) / math.log(a / b)
        if t >= 0:
            return t, None
        # t* < 0 has two different meanings for a BEV, so name the right one.
        if eta_g0 > i0:
            return None, "crossover before sale year (product already above benchmark at t=0)"
        return None, (
            "never crosses: below benchmark at sale and the grid decarbonises at least as fast "
            "as the fleet benchmark"
        )
    if rf <= 0:
        return None, "r_fleet <= 0: benchmark non-declining, no crossover"
    if e_prod0 <= 0:
        return None, "non-positive emissions ratio"
    t = math.log(e_prod0) / math.log(1.0 - rf)  # e_prod0 is already the ratio E_prod/E_ref(0)
    return (
        (t, None)
        if t >= 0
        else (None, "crossover before sale year (product already above benchmark at t=0)")
    )


def priced_cells(
    cohorts: list[dict[str, str]], params: dict[tuple[str, str, str], dict[str, str]]
) -> list[Cell]:
    """Cohort rows that carry a published result — the same rule step 4 applies."""
    out: list[Cell] = []
    for row in cohorts:
        p = params.get((row["market"], row["destination"], row["segment"]))
        if p is None or "FLEET_INTENSITY_IMPLAUSIBLE" in p["warnings"]:
            continue
        out.append(to_cell(row))
    return out


def all_hev_cells(
    cells: list[Cell], overrides: dict[tuple[str, str, str, str, str], Cell]
) -> list[Cell]:
    """The cohort with every share-split nameplate repriced as a hybrid.

    A share-split nameplate appears as several central cells (one per powertrain); the
    all-hybrid bound replaces the whole group with the single ``all_hev`` cell once.
    """
    out: list[Cell] = []
    done: set[tuple[str, str, str, str, str]] = set()
    for c in cells:
        key = (c.market, c.company, c.destination, str(c.cohort_year), c.model)
        if c.rule.startswith(MIXED_PREFIXES) and key in overrides:
            if key not in done:
                out.append(overrides[key])
                done.add(key)
            continue
        out.append(c)
    return out


def cohort_total(
    cells: list[Cell],
    params: dict[tuple[str, str], dict[str, str]],
    rates: dict[tuple[str, str, str], tuple[float, float]],
    market: str,
    scenario: str,
    factors: dict[tuple[str, str], dict[str, float]],
    life_delta: int = 0,
    rw_key: str = "factor",
    vkt_key: str | None = None,
) -> dict[tuple[str, int], float]:
    """Cohort total (tCO2e) per company x cohort year for one market x scenario, one input moved.

    Args:
        cells: Priced cells of every market; those outside ``market`` are ignored.
        params: (market, country) -> destination parameters.
        rates: (market, country, scenario) -> (r_fleet, r_power).
        market: Market to total.
        scenario: Scenario to total.
        factors: (test cycle, powertrain) -> real-world factor variants.
        life_delta: Years added to each market's operating life (floored at 1).
        rw_key: Which real-world factor column to use (`factor`, `factor_low`, `factor_high`).
        vkt_key: Parameter column to substitute for the distance in tier-C markets.

    Returns:
        (company, cohort_year) -> lifetime TI of the cohort (tCO2e).
    """
    out: dict[tuple[str, int], float] = defaultdict(float)
    for c in cells:
        if c.market != market:
            continue
        p = params[(c.market, c.destination, c.segment)]
        vkt = float(p["vkt_km"])
        if vkt_key and p["vkt_tier"] == "C" and p[vkt_key]:
            vkt = float(p[vkt_key])
        i0 = float(p["fleet_intensity_gco2_km"]) / 1000.0
        e_ref0 = i0 * float(p["vkt_km"])  # benchmark per car: distance cancels
        life = max(1, int(p["lifetime_years"]) + life_delta)
        rf, rp = rates[(c.market, c.destination, c.segment, scenario)]
        rw = factors[(c.test_cycle, c.powertrain)][rw_key]
        g0 = float(p["grid_gco2_kwh"]) / 1000.0
        cumulative = 0.0
        for t in range(life):
            e_ref = e_ref0 * (1 - rf) ** t
            e_prod = (
                (c.cert / 1000.0 * rw * g0 * (1 - rp) ** t * vkt)
                if c.powertrain == "BEV"
                else (c.cert * rw / 1000.0 * vkt)
            )
            cumulative += e_ref - e_prod
        out[(c.company, c.cohort_year)] += cumulative * c.units / 1000.0
    return dict(out)


def factor_label(
    cells: list[Cell], market: str, factors: dict[tuple[str, str], dict[str, float]], key: str
) -> str:
    """The real-world factors actually in play in one market, as a readable parameter string."""
    used = sorted({(c.test_cycle, c.powertrain) for c in cells if c.market == market})
    return ", ".join(f"{cycle} {pt} {factors[(cycle, pt)][key]}" for cycle, pt in used)


def build_crossovers(
    cells: list[Cell],
    params: dict[tuple[str, str], dict[str, str]],
    rates: dict[tuple[str, str, str], tuple[float, float]],
    factors: dict[tuple[str, str], dict[str, float]],
    scenarios: dict[str, list[str]],
) -> list[dict[str, object]]:
    """Closed-form crossover year and lifetime gap for every priced cell x scenario."""
    rows: list[dict[str, object]] = []
    for c in cells:
        p = params[(c.market, c.destination, c.segment)]
        vkt = float(p["vkt_km"])
        i0 = float(p["fleet_intensity_gco2_km"]) / 1000.0
        g0 = float(p["grid_gco2_kwh"]) / 1000.0
        life = int(p["lifetime_years"])
        rw = factors[(c.test_cycle, c.powertrain)]["factor"]
        for scenario in scenarios[c.market]:
            rf, rp = rates[(c.market, c.destination, c.segment, scenario)]
            e_prod_const = c.cert * rw / 1000.0 * vkt
            eta_g0 = c.cert / 1000.0 * rw * g0
            ratio = e_prod_const / (i0 * vkt) if c.powertrain != "BEV" else 0.0
            t_star, reason = crossover(c.powertrain, i0, rf, rp, ratio, eta_g0)
            cumulative = sum(
                i0 * vkt * (1 - rf) ** t
                - ((eta_g0 * (1 - rp) ** t * vkt) if c.powertrain == "BEV" else e_prod_const)
                for t in range(life)
            )
            rows.append(
                {
                    "market": c.market,
                    "company": c.company,
                    "destination": c.destination,
                    "model": c.model,
                    "powertrain": c.powertrain,
                    "scenario": scenario,
                    "units": c.units,
                    "ti_per_vehicle_kgco2e": round(cumulative, 4),
                    "crossover_year": None if t_star is None else round(t_star, 3),
                    "crossover_calendar_year": None
                    if t_star is None
                    else round(c.cohort_year + t_star, 1),
                    "reason": reason or ("within lifetime" if t_star < life else "after lifetime"),  # type: ignore[operator]
                }
            )
    rows.sort(
        key=lambda r: tuple(
            str(r[k])
            for k in ("market", "company", "scenario", "destination", "model", "powertrain")
        )
    )
    return rows


def main() -> None:
    """Write crossover years per cell and one-at-a-time sensitivities per company x market."""
    params = load_params()
    rates = load_rates()
    factors = load_real_world()
    scenarios = scenarios_by_market(rates)

    cells = priced_cells(load_cohorts(), params)
    overrides = {
        (c.market, c.company, c.destination, str(c.cohort_year), c.model): c
        for c in priced_cells(load_cohorts(ALL_HEV), params)
    }
    hev_cells = all_hev_cells(cells, overrides)

    cross_rows = build_crossovers(cells, params, rates, factors, scenarios)
    write_csv(OUT_CROSS, CROSS_FIELDS, cross_rows)

    sens_rows: list[dict[str, object]] = []
    for market in sorted(scenarios):
        variants: list[tuple[str, str, str, list[Cell], dict[str, object]]] = [
            ("lifetime", "central", "T_c", cells, {}),
            (
                "lifetime",
                "minus",
                f"T_c - {LIFETIME_DELTA_Y}",
                cells,
                {"life_delta": -LIFETIME_DELTA_Y},
            ),
            (
                "lifetime",
                "plus",
                f"T_c + {LIFETIME_DELTA_Y}",
                cells,
                {"life_delta": LIFETIME_DELTA_Y},
            ),
            ("realworld", "central", factor_label(cells, market, factors, "factor"), cells, {}),
            (
                "realworld",
                "low",
                factor_label(cells, market, factors, "factor_low"),
                cells,
                {"rw_key": "factor_low"},
            ),
            (
                "realworld",
                "high",
                factor_label(cells, market, factors, "factor_high"),
                cells,
                {"rw_key": "factor_high"},
            ),
            ("vkt_proxy", "central", "market distance as published for tier-C markets", cells, {}),
            (
                "vkt_proxy",
                "low",
                "lower quartile of measured distances",
                cells,
                {"vkt_key": "vkt_low_km"},
            ),
            (
                "vkt_proxy",
                "high",
                "upper quartile of measured distances",
                cells,
                {"vkt_key": "vkt_high_km"},
            ),
            (
                "powertrain_mix",
                "central",
                f"{MIXED_RULE} cohort rows priced as the rule states",
                cells,
                {},
            ),
            (
                "powertrain_mix",
                ALL_HEV,
                f"{MIXED_RULE} cohort rows repriced with the hybrid of the same base model",
                hev_cells,
                {},
            ),
        ]
        for dimension, variant, parameter, variant_cells, kwargs in variants:
            for scenario in scenarios[market]:
                totals = cohort_total(
                    variant_cells,
                    params,
                    rates,
                    market,
                    scenario,
                    factors,
                    **kwargs,  # type: ignore[arg-type]
                )
                for (company, cohort_year), value in sorted(totals.items()):
                    sens_rows.append(
                        {
                            "company": company,
                            "market": market,
                            "cohort_year": cohort_year,
                            "scenario": scenario,
                            "dimension": dimension,
                            "variant": variant,
                            "parameter": parameter,
                            "ti_tco2e": round(value, 1),
                        }
                    )
    sens_rows.sort(
        key=lambda r: tuple(
            str(r[k])
            for k in ("company", "market", "cohort_year", "scenario", "dimension", "variant")
        )
    )
    write_csv(OUT_SENS, SENS_FIELDS, sens_rows)

    within = sum(1 for r in cross_rows if r["reason"] == "within lifetime")
    print(f"{OUT_CROSS.relative_to(REPO)}: {len(cross_rows)} cells, {within} cross within lifetime")
    for market in sorted(scenarios):
        headline = scenarios[market][-1]
        grains = sorted(
            {
                (str(r["company"]), int(str(r["cohort_year"])))
                for r in sens_rows
                if r["market"] == market
            }
        )
        for company, cohort_year in grains:
            for dimension in ("lifetime", "realworld", "vkt_proxy", "powertrain_mix"):
                values = {
                    r["variant"]: r["ti_tco2e"]
                    for r in sens_rows
                    if r["company"] == company
                    and r["cohort_year"] == cohort_year
                    and r["market"] == market
                    and r["scenario"] == headline
                    and r["dimension"] == dimension
                }
                print(
                    f"  {market} {company} {headline} {dimension}: "
                    + ", ".join(f"{k} {float(str(v)):,.0f}" for k, v in values.items())
                )
    print(f"{OUT_SENS.relative_to(REPO)}: {len(sens_rows)} rows")


if __name__ == "__main__":
    main()
