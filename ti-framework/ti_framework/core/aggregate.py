# SPDX-License-Identifier: GPL-3.0-or-later
"""Single-cohort firm-level aggregation with mandatory decomposition
(Whitepaper §3.6 [eq-3.6-cohort], §3.7 [eq-3.7-annual-flow], Guideline §4.4).

    TI_cohort,F,Y0,S = sum_v sum_c [ V_c,v * TI_vehicle,v,c,S ]   [tCO2e]
    decomposition:  TI_cohort = sum_c TI_country,c = sum_v TI_powertrain,v   (mandatory)

A ``Placement`` is one (operating country, vehicle model, powertrain) cell with its volume.
This module builds Layer-1/Layer-2 objects per placement per scenario and aggregates them,
applying the confirmed FLAG-market rule (D3) and the optional sector-split / S-curve switches.
"""

from __future__ import annotations

from dataclasses import dataclass

from ti_framework.core.crossover import crossover_bev, crossover_ice, crossover_numeric
from ti_framework.core.cumulative import ti_cumulative
from ti_framework.core.gap import ti_gap_series
from ti_framework.io.schema import FLAG_REASONS
from ti_framework.layer1.automotive import MethodBBenchmark
from ti_framework.layer2.automotive import BEVEmissions, GridTrajectory, ICEEmissions, PHEVEmissions
from ti_framework.layer2.base import ProductEmissions
from ti_framework.models import (
    CohortResult,
    Country,
    DataTier,
    EngineConfig,
    Powertrain,
    Scenario,
    SupportParams,
    Vehicle,
    VehicleResult,
)


@dataclass
class Placement:
    """One (country, vehicle, volume) cell of the cohort."""

    country_code: str
    vehicle: Vehicle
    units: float | None
    uf_override: float | None = None  # used by sensitivity sweeps (PHEV)


@dataclass
class _CellOutput:
    vehicle_result: VehicleResult
    ti_tco2e: float
    annual_tco2e: list[float]
    tier: DataTier


def _effective_rate(base: float | None, factor: float, enabled: bool) -> float | None:
    if base is None:
        return None
    return base * factor if enabled else base


def _scenario_rates(
    country: Country, scenario: Scenario, config: EngineConfig
) -> tuple[float | None, float | None, str | None]:
    """Resolve (r_fleet, r_power) for a scenario, applying the FLAG rule (D3) for S2.

    Returns (r_fleet, r_power, exclusion_reason). When exclusion_reason is not None the
    placement should be excluded from this scenario's headline.
    """
    if scenario is Scenario.S2 and country.is_flag:
        reason = FLAG_REASONS.get(country.status, "benchmark not derivable from NDC")
        if config.flag_market_rule == "exclude":
            return None, None, reason
        # iea_proxy: substitute the S1 (STEPS) sector trajectory as the S2 proxy
        rf, rp = country.r_fleet.s1, country.r_power.s1
        if rf is None:
            return None, None, f"{reason}; IEA proxy unavailable (S1 rate missing)"
        return rf, rp, None

    rf = country.r_fleet.get(scenario)
    rp = country.r_power.get(scenario)
    rf = _effective_rate(rf, config.sector_split_fleet, config.sector_split_enabled)
    rp = _effective_rate(rp, config.sector_split_power, config.sector_split_enabled)
    return rf, rp, None


def _compute_cell(
    placement: Placement,
    country: Country,
    scenario: Scenario,
    distance: float,
    T: int,
    config: EngineConfig,
    missing: list[str],
) -> _CellOutput | None:
    v = placement.vehicle
    pt = v.powertrain
    r_fleet, r_power, _ = _scenario_rates(country, scenario, config)

    if country.fleet_intensity_base is None:
        missing.append(f"[{country.code}] fleet_intensity_base (I_fleet,seg,c(0)) missing")
        return None
    if r_fleet is None:
        missing.append(f"[{country.code}/{scenario.value}] r_fleet missing")
        return None

    benchmark = MethodBBenchmark(
        intensity_base=country.fleet_intensity_base,
        r_fleet=r_fleet,
        distance=distance,
        s_curve=config.s_curve,
        s_curve_k=config.s_curve_k,
        horizon=T,
    )

    uf = placement.uf_override if placement.uf_override is not None else v.uf

    # Build the Layer-2 product for the powertrain.
    if pt is None:
        missing.append(f"[{country.code}] vehicle '{v.brand} {v.model}' powertrain missing")
        return None

    grid = None
    if pt in (Powertrain.BEV, Powertrain.PHEV):
        if country.grid_intensity is None or r_power is None:
            missing.append(f"[{country.code}/{scenario.value}] grid G0 or r_power missing for {pt.value}")
            return None
        grid = GridTrajectory(g0=country.grid_intensity, r_power=r_power)

    product: ProductEmissions
    if pt.is_fixed:
        if v.ice_intensity is None:
            missing.append(f"[{country.code}] ICE intensity missing for '{v.brand} {v.model}'")
            return None
        product = ICEEmissions(ice_intensity=v.ice_intensity, distance=distance)
    elif pt is Powertrain.BEV:
        if v.eta_ev is None:
            missing.append(f"[{country.code}] eta_EV missing for BEV '{v.brand} {v.model}'")
            return None
        assert grid is not None
        product = BEVEmissions(eta_ev=v.eta_ev, grid=grid, distance=distance)
    else:  # PHEV
        if uf is None or v.eta_elec is None or v.ice_mode_intensity is None:
            missing.append(f"[{country.code}] PHEV params (UF/eta_elec/I_ICE_mode) missing for '{v.brand} {v.model}'")
            return None
        assert grid is not None
        product = PHEVEmissions(
            uf=uf, eta_elec=v.eta_elec, ice_mode_intensity=v.ice_mode_intensity,
            grid=grid, distance=distance,
        )

    gap = ti_gap_series(benchmark, product, T)
    cumulative = ti_cumulative(gap)

    # Crossover: closed form for ICE/BEV (exponential benchmark), numeric otherwise.
    if config.s_curve:
        t_star, reason = crossover_numeric(gap)
    elif pt.is_fixed:
        t_star, reason = crossover_ice(country.fleet_intensity_base, r_fleet, distance, product.emissions(0))
    elif pt is Powertrain.BEV:
        assert grid is not None
        t_star, reason = crossover_bev(country.fleet_intensity_base, r_fleet, v.eta_ev, grid.g0, r_power)  # type: ignore[arg-type]
    else:
        t_star, reason = crossover_numeric(gap)

    vr = VehicleResult(
        country_code=country.code,
        powertrain=pt,
        scenario=scenario,
        gap_series=gap.tolist(),
        cumulative=cumulative,
        crossover_year=t_star,
        crossover_reason=reason,
    )

    units = placement.units or 0.0
    ti_tco2e = cumulative * units / 1000.0
    annual = [(g * units / 1000.0) for g in gap.tolist()]
    # cell data tier = worse of vehicle tier and country tier
    cell_tier = v.tier if v.tier.rank >= country.tier.rank else country.tier
    return _CellOutput(vehicle_result=vr, ti_tco2e=ti_tco2e, annual_tco2e=annual, tier=cell_tier)


def compute_cohort(
    firm: str,
    cohort_year: int,
    scenario: Scenario,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> tuple[CohortResult, list[VehicleResult], list[str]]:
    """Compute single-cohort firm TI for one scenario, with mandatory decomposition."""
    missing: list[str] = []
    T = support.lifetime_T
    if T is None or T < 1:
        missing.append("Support_params: vehicle lifetime T missing — cohort not computable")
        empty = CohortResult(firm=firm, cohort_year=cohort_year, scenario=scenario, total=0.0,
                             by_country={}, by_powertrain={}, annual=[], warnings=list(missing))
        return empty, [], missing

    by_country: dict[str, float] = {}
    by_powertrain: dict[str, float] = {}
    annual = [0.0] * T
    total = 0.0
    excluded: dict[str, str] = {}
    vehicle_results: list[VehicleResult] = []
    warnings: list[str] = []

    tierc_units = 0.0
    total_units = 0.0

    for p in placements:
        country = countries.get(p.country_code)
        if country is None:
            missing.append(f"[{p.country_code}] country not in inputs")
            continue
        distance = support.vkt_for(p.country_code)
        if distance is None:
            missing.append(f"[{p.country_code}] VKT (D_c) missing")
            continue

        # FLAG exclusion for S2 headline (D3)
        _, _, excl = _scenario_rates(country, scenario, config)
        if excl is not None:
            excluded[p.country_code] = excl
            continue

        cell = _compute_cell(p, country, scenario, distance, T, config, missing)
        if cell is None:
            continue

        vehicle_results.append(cell.vehicle_result)
        total += cell.ti_tco2e
        by_country[p.country_code] = by_country.get(p.country_code, 0.0) + cell.ti_tco2e
        ptkey = cell.vehicle_result.powertrain.value
        by_powertrain[ptkey] = by_powertrain.get(ptkey, 0.0) + cell.ti_tco2e
        for t in range(T):
            annual[t] += cell.annual_tco2e[t]

        u = p.units or 0.0
        total_units += u
        if cell.tier is DataTier.C:
            tierc_units += u
        warnings.extend(w for w in country.warnings if w not in warnings)

    directional_only = total_units > 0 and (tierc_units / total_units) > config.tier_c_threshold
    if directional_only:
        warnings.append(
            f"TIER_C_SUPPRESSION: Tier-C volume share {tierc_units/total_units:.0%} exceeds "
            f"threshold {config.tier_c_threshold:.0%}; emit directional label only."
        )

    result = CohortResult(
        firm=firm,
        cohort_year=cohort_year,
        scenario=scenario,
        total=total,
        by_country=by_country,
        by_powertrain=by_powertrain,
        annual=annual,
        excluded_flag_markets=excluded,
        warnings=warnings,
        directional_only=directional_only,
    )
    return result, vehicle_results, missing


def decomposition_identity_holds(result: CohortResult, tol: float = 1e-6) -> bool:
    """Verify the mandatory identity TI_cohort = sum_c = sum_v (Guideline §4.4)."""
    s_country = sum(result.by_country.values())
    s_pt = sum(result.by_powertrain.values())
    return abs(s_country - result.total) <= tol * max(1.0, abs(result.total)) and abs(
        s_pt - result.total
    ) <= tol * max(1.0, abs(result.total))


def direction_label(value: float) -> str:
    """Directional label for a TI value (used when Tier-C suppression triggers)."""
    if value > 0:
        return "contribution"
    if value < 0:
        return "liability"
    return "neutral"
