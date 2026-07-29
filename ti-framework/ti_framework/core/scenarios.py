# SPDX-License-Identifier: GPL-3.0-or-later
"""Three-scenario runner (Guideline §4.7 [rule-g4.7-three-scenarios]) and the high-level engine entry point.

Runs the full Layer 1->2->3 computation under S1/S2/S3 and assembles a ``RunResult`` with
the required outputs and a data-quality declaration. Never reports S2 alone.
"""

from __future__ import annotations

from ti_framework.core.aggregate import Placement, compute_cohort
from ti_framework.core.portfolio import rolling_portfolio
from ti_framework.models import (
    CohortResult,
    Country,
    DataQuality,
    DataTier,
    EngineConfig,
    RunResult,
    Scenario,
    SupportParams,
    Vehicle,
    VehicleResult,
    Volume,
)

_SCENARIO_SOURCE_DEFAULT = {
    Scenario.S1: "IEA WEO STEPS (transport & electricity)",
    Scenario.S2: "UNFCCC NDC unconditional (pro-rata, economy-wide)",
    Scenario.S3: "IEA NZE (transport & electricity)",
}


def _portfolio_rampup(annual: list[float], cohort_year: int) -> list[float]:
    """Rolling-portfolio ramp-up for identical repeated cohorts (WP §3.8).

    Assumes a cohort identical to this one is sold every year from ``cohort_year``
    onward and evaluates ``core.portfolio.rolling_portfolio`` — the general
    multi-cohort form — over the first T calendar years. The series builds up to
    the steady-state value (= TI_cohort) as cohorts accumulate.
    """
    T = len(annual)
    if T == 0:
        return []
    cohorts = {cohort_year + i: annual for i in range(T)}
    series = rolling_portfolio(cohorts, range(cohort_year, cohort_year + T))
    return [series[tau] for tau in range(cohort_year, cohort_year + T)]


def run(
    firm: str,
    cohort_year: int,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig | None = None,
    analysis_level: str = "Level 1",
    layer1_method: str = "B",
) -> RunResult:
    """Run the engine across the configured scenarios and assemble all required outputs."""
    config = config or EngineConfig()
    cohorts: dict[Scenario, CohortResult] = {}
    all_vehicle_results: list[VehicleResult] = []
    missing: list[str] = []
    portfolio: dict[Scenario, list[float]] = {}

    for scenario in config.scenarios:
        cohort, vrs, miss = compute_cohort(
            firm, cohort_year, scenario, placements, countries, support, config
        )
        cohorts[scenario] = cohort
        all_vehicle_results.extend(vrs)
        missing.extend(miss)
        portfolio[scenario] = _portfolio_rampup(cohort.annual, cohort_year)

    # De-duplicate missing while preserving order.
    missing_unique = list(dict.fromkeys(missing))

    # --- Data-quality declaration (Guideline §5.3) ---
    benchmark_tiers = {c.code: c.tier.value for c in countries.values()}
    flag_markets: dict[str, str] = {}
    for sc in cohorts.values():
        flag_markets.update(sc.excluded_flag_markets)
    layer2_tiers: dict[str, str] = {}
    volume_tier_values: dict[str, DataTier] = {}
    warnings: list[str] = []
    for p in placements:
        key = f"{p.vehicle.brand} {p.vehicle.model or ''}".strip()
        layer2_tiers[key] = p.vehicle.tier.value
        current = volume_tier_values.get(p.country_code, DataTier.A)
        if p.volume_tier.rank >= current.rank:
            volume_tier_values[p.country_code] = p.volume_tier
    for c in countries.values():
        warnings.extend(c.warnings)
    for sc in cohorts.values():
        warnings.extend(w for w in sc.warnings if w not in warnings)

    scenario_sources = {sc.value: _SCENARIO_SOURCE_DEFAULT[sc] for sc in config.scenarios}

    dq = DataQuality(
        firm=firm,
        cohort_year=cohort_year,
        analysis_level=analysis_level,
        layer1_method=layer1_method,
        benchmark_tiers=benchmark_tiers,
        layer2_tiers=layer2_tiers,
        volume_tiers={code: tier.value for code, tier in volume_tier_values.items()},
        lifetime_T=support.lifetime_T,
        lifetime_sens=support.lifetime_sens,
        scenario_sources=scenario_sources,
        missing_inputs=missing_unique,
        warnings=list(dict.fromkeys(warnings)),
        flag_markets=flag_markets,
    )

    return RunResult(
        firm=firm,
        cohort_year=cohort_year,
        cohorts=cohorts,
        vehicle_results=all_vehicle_results,
        data_quality=dq,
        config=config,
        portfolio=portfolio,
    )


def placements_from_volumes(volumes: list[Volume], vehicles: list[Vehicle]) -> list[Placement]:
    """Assemble placements by matching registration volumes to vehicle parameter rows.

    Matches on (brand, model, powertrain), falling back to (brand, powertrain). Volumes with
    no matching parameter row are still emitted (with an empty Vehicle) so the missing-input
    machinery records them rather than dropping them silently.
    """
    index: dict[tuple, Vehicle] = {}
    for v in vehicles:
        if v.powertrain is None:
            continue
        index[(v.brand, v.model, v.powertrain)] = v
        index.setdefault((v.brand, None, v.powertrain), v)

    out: list[Placement] = []
    for vol in volumes:
        if vol.powertrain is None:
            continue
        veh = index.get((vol.brand, vol.model, vol.powertrain)) or index.get(
            (vol.brand, None, vol.powertrain)
        )
        if veh is None:
            veh = Vehicle(
                brand=vol.brand or "",
                model=vol.model,
                powertrain=vol.powertrain,
                tier=DataTier.UNKNOWN,
            )
        out.append(
            Placement(
                country_code=vol.country_code,
                vehicle=veh,
                units=vol.units,
                volume_tier=vol.tier,
                volume_source=vol.source,
            )
        )
    return out
