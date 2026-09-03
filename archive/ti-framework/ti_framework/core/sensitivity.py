# SPDX-License-Identifier: GPL-3.0-or-later
"""Sensitivity sweeps and uncertainty propagation (Guideline §5.2 [rule-g5.2-sensitivity], build brief §5).

Mandatory sweeps:
  * vehicle lifetime T ± 3 yr
  * PHEV Utility Factor UF ± 0.15 (central and UF-0.15 lower bound reported side by side)
  * real-world correction range
  * the full S1/S2/S3 scenario spread

Optional switches (default off, NOTES.md §3):
  * sector-split pro-rata correction — corrected vs uncorrected side by side
  * Monte Carlo joint propagation -> confidence band, with Tier-C suppression to a directional
    label when the Tier-C volume share exceeds the configured threshold.
"""

from __future__ import annotations

import copy
from dataclasses import replace

import numpy as np

from ti_framework.core.aggregate import Placement, compute_cohort, direction_label
from ti_framework.models import (
    Country,
    EngineConfig,
    Powertrain,
    Scenario,
    SupportParams,
)


def _total(
    firm: str,
    cohort_year: int,
    scenario: Scenario,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> float:
    cohort, _, _ = compute_cohort(
        firm, cohort_year, scenario, placements, countries, support, config
    )
    return cohort.total


def sweep_lifetime(
    firm: str,
    cohort_year: int,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> dict[str, dict[str, float]]:
    """TI_cohort at T-Δ, T, T+Δ for each scenario."""
    T = support.lifetime_T
    if T is None:
        return {}
    delta = support.lifetime_sens
    out: dict[str, dict[str, float]] = {}
    for label, Tv in (("T_minus", T - delta), ("T_central", T), ("T_plus", T + delta)):
        if Tv < 1:
            continue
        sup = support.with_lifetime(Tv)
        out[label] = {
            sc.value: _total(firm, cohort_year, sc, placements, countries, sup, config)
            for sc in config.scenarios
        }
    return out


def sweep_uf(
    firm: str,
    cohort_year: int,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> dict[str, dict[str, float]]:
    """Central vs UF-band lower bound (UF - support.uf_band) for PHEV-containing cohorts."""
    band = support.uf_band

    def shift(p: Placement, delta: float) -> Placement:
        if p.vehicle.powertrain is Powertrain.PHEV:
            base = p.uf_override if p.uf_override is not None else p.vehicle.uf
            if base is not None:
                return replace(p, uf_override=max(0.0, min(1.0, base + delta)))
        return p

    out: dict[str, dict[str, float]] = {}
    for label, delta in (("UF_central", 0.0), ("UF_lower", -band), ("UF_upper", band)):
        pl = [shift(p, delta) for p in placements]
        out[label] = {
            sc.value: _total(firm, cohort_year, sc, pl, countries, support, config)
            for sc in config.scenarios
        }
    return out


def sweep_realworld(
    firm: str,
    cohort_year: int,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> dict[str, dict[str, float]]:
    """Scale corrected Layer-2 intensities by the real-world correction range (relative)."""
    if support.realworld_range is None:
        return {}
    lo, hi = support.realworld_range

    def scale(p: Placement, f: float) -> Placement:
        v = p.vehicle
        nv = replace(
            v,
            ice_intensity=None if v.ice_intensity is None else v.ice_intensity * f,
            eta_ev=None if v.eta_ev is None else v.eta_ev * f,
            eta_elec=None if v.eta_elec is None else v.eta_elec * f,
            ice_mode_intensity=None if v.ice_mode_intensity is None else v.ice_mode_intensity * f,
        )
        return replace(p, vehicle=nv)

    out: dict[str, dict[str, float]] = {}
    for label, f in (("RW_low", lo), ("RW_central", 1.0), ("RW_high", hi)):
        pl = [scale(p, f) for p in placements]
        out[label] = {
            sc.value: _total(firm, cohort_year, sc, pl, countries, support, config)
            for sc in config.scenarios
        }
    return out


def sector_split_comparison(
    firm: str,
    cohort_year: int,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> dict[str, dict[str, float]]:
    """Pro-rata uncorrected vs sector-split-corrected TI, side by side (Challenge 1)."""
    uncorrected = replace(config, sector_split_enabled=False)
    corrected = replace(config, sector_split_enabled=True)
    return {
        "uncorrected": {
            sc.value: _total(firm, cohort_year, sc, placements, countries, support, uncorrected)
            for sc in config.scenarios
        },
        "corrected": {
            sc.value: _total(firm, cohort_year, sc, placements, countries, support, corrected)
            for sc in config.scenarios
        },
    }


def sweep_s2_ndc_range(
    firm: str,
    cohort_year: int,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> dict[str, float]:
    """Compare unconditional S2 rates with published conditional upper bounds.

    Countries without an upper bound retain their central S2 value. This makes the
    workbook's ``s2_upper`` field an explicit sensitivity input instead of dead data.
    """
    central = _total(
        firm, cohort_year, Scenario.S2, placements, countries, support, config
    )
    upper_countries = copy.deepcopy(countries)
    changed = False
    for country in upper_countries.values():
        for rate in (country.r_fleet, country.r_power):
            if rate.s2_upper is not None:
                rate.s2 = rate.s2_upper
                changed = True
    if not changed:
        return {"S2_unconditional": central}
    return {
        "S2_unconditional": central,
        "S2_conditional_upper": _total(
            firm,
            cohort_year,
            Scenario.S2,
            placements,
            upper_countries,
            support,
            config,
        ),
    }


def monte_carlo(
    firm: str,
    cohort_year: int,
    scenario: Scenario,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> dict[str, object]:
    """Joint Monte Carlo propagation over T, UF and real-world correction (Challenge 3).

    Returns mean, median and a 5–95% confidence band on TI_cohort. When the Tier-C volume
    share exceeds ``config.tier_c_threshold`` only a directional label is emitted.
    """
    rng = np.random.default_rng(config.mc_seed)
    T = support.lifetime_T
    if T is None:
        return {"error": "T missing"}
    band = support.uf_band
    rw = support.realworld_range or (1.0, 1.0)

    tierc_units = sum(
        (p.units or 0.0)
        for p in placements
        if p.vehicle.tier.value == "C"
    )
    total_units = sum((p.units or 0.0) for p in placements)
    tierc_share = tierc_units / total_units if total_units > 0 else 0.0

    draws: list[float] = []
    for _ in range(config.mc_draws):
        Tv = int(rng.integers(max(1, T - support.lifetime_sens), T + support.lifetime_sens + 1))
        uf_delta = float(rng.uniform(-band, band))
        rw_f = float(rng.uniform(rw[0], rw[1]))
        sup = support.with_lifetime(Tv)
        pl = []
        for p in placements:
            v = p.vehicle
            nv = replace(
                v,
                ice_intensity=None if v.ice_intensity is None else v.ice_intensity * rw_f,
                eta_ev=None if v.eta_ev is None else v.eta_ev * rw_f,
                eta_elec=None if v.eta_elec is None else v.eta_elec * rw_f,
                ice_mode_intensity=None if v.ice_mode_intensity is None else v.ice_mode_intensity * rw_f,
            )
            np_ = replace(p, vehicle=nv)
            if v.powertrain is Powertrain.PHEV and v.uf is not None:
                np_ = replace(np_, uf_override=max(0.0, min(1.0, v.uf + uf_delta)))
            pl.append(np_)
        draws.append(_total(firm, cohort_year, scenario, pl, countries, sup, config))

    arr = np.array(draws, dtype=float)
    result: dict[str, object] = {
        "scenario": scenario.value,
        "n_draws": len(draws),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "p05": float(np.percentile(arr, 5)),
        "p95": float(np.percentile(arr, 95)),
        "tier_c_share": tierc_share,
    }
    if tierc_share > config.tier_c_threshold:
        result["suppressed"] = True
        result["directional_label"] = direction_label(float(np.median(arr)))
    else:
        result["suppressed"] = False
    return result


def run_sensitivity(
    firm: str,
    cohort_year: int,
    placements: list[Placement],
    countries: dict[str, Country],
    support: SupportParams,
    config: EngineConfig,
) -> dict[str, object]:
    """Run all mandatory sweeps plus any enabled optional analyses."""
    out: dict[str, object] = {
        "lifetime": sweep_lifetime(firm, cohort_year, placements, countries, support, config),
        "uf": sweep_uf(firm, cohort_year, placements, countries, support, config),
        "realworld": sweep_realworld(firm, cohort_year, placements, countries, support, config),
        "scenario_spread": {
            sc.value: _total(firm, cohort_year, sc, placements, countries, support, config)
            for sc in config.scenarios
        },
        "s2_ndc_range": sweep_s2_ndc_range(
            firm, cohort_year, placements, countries, support, config
        ),
    }
    # sector-split side-by-side is always informative given universal pro-rata
    out["sector_split"] = sector_split_comparison(
        firm, cohort_year, placements, countries, support, copy.copy(config)
    )
    if config.monte_carlo:
        out["monte_carlo"] = {
            sc.value: monte_carlo(firm, cohort_year, sc, placements, countries, support, config)
            for sc in config.scenarios
        }
    return out
