# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from ti_framework.core.aggregate import (
    Placement,
    compute_cohort,
    decomposition_identity_holds,
    direction_label,
)
from ti_framework.models import (
    BenchmarkStatus,
    Country,
    DataTier,
    EngineConfig,
    Powertrain,
    Scenario,
    ScenarioRate,
    SupportParams,
    Vehicle,
)


def _kr() -> Country:
    return Country(
        name="South Korea",
        code="KR",
        grid_intensity=0.4,
        fleet_intensity_base=0.18,
        r_fleet=ScenarioRate(s1=0.025, s2=0.045, s3=0.07),
        r_power=ScenarioRate(s1=0.03, s2=0.05, s3=0.09),
        status=BenchmarkStatus.COMPUTED,
        tier=DataTier.A,
    )


def _support() -> SupportParams:
    return SupportParams(lifetime_T=15, vkt={"KR": 13000, "US": 19000})


def _cfg() -> EngineConfig:
    return EngineConfig()


def test_decomposition_identity_holds():
    placements = [
        Placement("KR", Vehicle("H", "BEV1", Powertrain.BEV, eta_ev=0.18, tier=DataTier.A), 1000),
        Placement("KR", Vehicle("H", "ICE1", Powertrain.ICE, ice_intensity=0.16, tier=DataTier.A), 1000),
    ]
    cohort, _, _ = compute_cohort("F", 2024, Scenario.S2, placements, {"KR": _kr()}, _support(), _cfg())
    assert decomposition_identity_holds(cohort)
    assert sum(cohort.by_country.values()) == pytest.approx(cohort.total)
    assert sum(cohort.by_powertrain.values()) == pytest.approx(cohort.total)


def test_zero_volume_contributes_nothing():
    placements = [
        Placement("KR", Vehicle("H", "BEV1", Powertrain.BEV, eta_ev=0.18, tier=DataTier.A), 0),
    ]
    cohort, vrs, _ = compute_cohort("F", 2024, Scenario.S2, placements, {"KR": _kr()}, _support(), _cfg())
    assert cohort.total == pytest.approx(0.0)
    # the per-vehicle result is still computed (independent of volume)
    assert vrs and vrs[0].cumulative != 0.0


def test_flag_market_excluded_from_s2():
    us = Country(name="United States", code="US", grid_intensity=0.38,
                 fleet_intensity_base=0.2, status=BenchmarkStatus.FLAG_NO_BENCHMARK)
    placements = [
        Placement("US", Vehicle("X", "BEV", Powertrain.BEV, eta_ev=0.2, tier=DataTier.A), 1000),
    ]
    cohort, _, _ = compute_cohort("F", 2024, Scenario.S2, placements, {"US": us}, _support(), _cfg())
    assert "US" in cohort.excluded_flag_markets
    assert cohort.total == pytest.approx(0.0)


def test_flag_market_iea_proxy_uses_s1():
    us = Country(name="United States", code="US", grid_intensity=0.38, fleet_intensity_base=0.2,
                 r_fleet=ScenarioRate(s1=0.02), r_power=ScenarioRate(s1=0.03),
                 status=BenchmarkStatus.FLAG_NO_BENCHMARK)
    cfg = EngineConfig(flag_market_rule="iea_proxy")
    placements = [
        Placement("US", Vehicle("X", "BEV", Powertrain.BEV, eta_ev=0.2, tier=DataTier.A), 1000),
    ]
    cohort, _, _ = compute_cohort("F", 2024, Scenario.S2, placements, {"US": us}, _support(), cfg)
    assert "US" not in cohort.excluded_flag_markets
    assert cohort.total != 0.0


def test_missing_ndc_rate_recorded():
    kr = _kr()
    kr.r_fleet = ScenarioRate()  # all None -> S2 missing
    placements = [Placement("KR", Vehicle("H", "ICE", Powertrain.ICE, ice_intensity=0.16), 1000)]
    cohort, _, missing = compute_cohort("F", 2024, Scenario.S2, placements, {"KR": kr}, _support(), _cfg())
    assert any("r_fleet missing" in m for m in missing)
    assert cohort.total == pytest.approx(0.0)


def test_missing_T_returns_empty():
    sup = SupportParams(lifetime_T=None, vkt={"KR": 13000})
    placements = [Placement("KR", Vehicle("H", "ICE", Powertrain.ICE, ice_intensity=0.16), 1000)]
    cohort, vrs, missing = compute_cohort("F", 2024, Scenario.S2, placements, {"KR": _kr()}, sup, _cfg())
    assert cohort.total == 0.0
    assert any("lifetime T" in m for m in missing)


def test_tier_c_directional_suppression():
    kr = _kr()
    placements = [
        Placement("KR", Vehicle("H", "BEVc", Powertrain.BEV, eta_ev=0.18, tier=DataTier.C), 9000),
        Placement("KR", Vehicle("H", "BEVa", Powertrain.BEV, eta_ev=0.18, tier=DataTier.A), 1000),
    ]
    cfg = EngineConfig(tier_c_threshold=0.5)
    cohort, _, _ = compute_cohort("F", 2024, Scenario.S2, placements, {"KR": kr}, _support(), cfg)
    assert cohort.directional_only is True
    assert any("TIER_C_SUPPRESSION" in w for w in cohort.warnings)


def test_direction_label():
    assert direction_label(5) == "contribution"
    assert direction_label(-5) == "liability"
    assert direction_label(0) == "neutral"
