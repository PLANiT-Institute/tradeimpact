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
        Placement(
            "KR", Vehicle("H", "ICE1", Powertrain.ICE, ice_intensity=0.16, tier=DataTier.A), 1000
        ),
    ]
    cohort, _, _ = compute_cohort(
        "F", 2024, Scenario.S2, placements, {"KR": _kr()}, _support(), _cfg()
    )
    assert decomposition_identity_holds(cohort)
    assert sum(cohort.by_country.values()) == pytest.approx(cohort.total)
    assert sum(cohort.by_powertrain.values()) == pytest.approx(cohort.total)


def _us() -> Country:
    return Country(
        name="United States",
        code="US",
        grid_intensity=0.37,
        fleet_intensity_base=0.22,
        r_fleet=ScenarioRate(s1=0.015, s2=0.03, s3=0.06),
        r_power=ScenarioRate(s1=0.02, s2=0.04, s3=0.08),
        status=BenchmarkStatus.COMPUTED,
        tier=DataTier.A,
    )


def _two_market_placements() -> list[Placement]:
    """Two markets, two powertrains, and two models sharing one cell."""
    return [
        Placement("KR", Vehicle("H", "BEV1", Powertrain.BEV, eta_ev=0.18, tier=DataTier.A), 1000),
        Placement(
            "KR", Vehicle("H", "ICE1", Powertrain.ICE, ice_intensity=0.16, tier=DataTier.A), 1500
        ),
        Placement(
            "KR", Vehicle("H", "ICE2", Powertrain.ICE, ice_intensity=0.21, tier=DataTier.A), 500
        ),
        Placement("US", Vehicle("H", "BEV1", Powertrain.BEV, eta_ev=0.18, tier=DataTier.A), 800),
    ]


def test_cell_decomposition_reconstructs_both_margins():
    cohort, _, _ = compute_cohort(
        "F",
        2024,
        Scenario.S2,
        _two_market_placements(),
        {"KR": _kr(), "US": _us()},
        _support(),
        _cfg(),
    )

    # Two models in the same market and powertrain collapse into one cell carrying both volumes.
    assert [(c.country_code, c.powertrain.value) for c in cohort.by_cell] == [
        ("KR", "BEV"),
        ("KR", "ICE"),
        ("US", "BEV"),
    ]
    kr_ice = next(c for c in cohort.by_cell if (c.country_code, c.powertrain) == ("KR", Powertrain.ICE))
    assert kr_ice.units == pytest.approx(2000)
    assert kr_ice.ti_per_vehicle_kg == pytest.approx(kr_ice.ti_tco2e * 1000 / 2000)

    assert sum(c.ti_tco2e for c in cohort.by_cell) == pytest.approx(cohort.total)
    for code, value in cohort.by_country.items():
        row = sum(c.ti_tco2e for c in cohort.by_cell if c.country_code == code)
        assert row == pytest.approx(value)
    for key, value in cohort.by_powertrain.items():
        column = sum(c.ti_tco2e for c in cohort.by_cell if c.powertrain.value == key)
        assert column == pytest.approx(value)


def test_identity_rejects_a_joint_that_disagrees_with_a_margin():
    """Two margins can both sum to the total while the joint moves weight between them."""
    cohort, _, _ = compute_cohort(
        "F",
        2024,
        Scenario.S2,
        _two_market_placements(),
        {"KR": _kr(), "US": _us()},
        _support(),
        _cfg(),
    )
    assert decomposition_identity_holds(cohort)

    kr_bev = next(c for c in cohort.by_cell if (c.country_code, c.powertrain) == ("KR", Powertrain.BEV))
    us_bev = next(c for c in cohort.by_cell if (c.country_code, c.powertrain) == ("US", Powertrain.BEV))
    shift = 1.0
    kr_bev.ti_tco2e += shift
    us_bev.ti_tco2e -= shift
    # Total and the powertrain margin still reconcile; the country margin no longer does.
    assert sum(c.ti_tco2e for c in cohort.by_cell) == pytest.approx(cohort.total)
    assert not decomposition_identity_holds(cohort)


def test_zero_volume_contributes_nothing():
    placements = [
        Placement("KR", Vehicle("H", "BEV1", Powertrain.BEV, eta_ev=0.18, tier=DataTier.A), 0),
    ]
    cohort, vrs, _ = compute_cohort(
        "F", 2024, Scenario.S2, placements, {"KR": _kr()}, _support(), _cfg()
    )
    assert cohort.total == pytest.approx(0.0)
    # the per-vehicle result is still computed (independent of volume)
    assert vrs and vrs[0].cumulative != 0.0


def test_flag_market_excluded_from_s2():
    us = Country(
        name="United States",
        code="US",
        grid_intensity=0.38,
        fleet_intensity_base=0.2,
        status=BenchmarkStatus.FLAG_NO_BENCHMARK,
    )
    placements = [
        Placement("US", Vehicle("X", "BEV", Powertrain.BEV, eta_ev=0.2, tier=DataTier.A), 1000),
    ]
    cohort, _, _ = compute_cohort(
        "F", 2024, Scenario.S2, placements, {"US": us}, _support(), _cfg()
    )
    assert "US" in cohort.excluded_flag_markets
    assert cohort.total == pytest.approx(0.0)


def test_flag_market_iea_proxy_uses_s1():
    us = Country(
        name="United States",
        code="US",
        grid_intensity=0.38,
        fleet_intensity_base=0.2,
        r_fleet=ScenarioRate(s1=0.02),
        r_power=ScenarioRate(s1=0.03),
        status=BenchmarkStatus.FLAG_NO_BENCHMARK,
    )
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
    cohort, _, missing = compute_cohort(
        "F", 2024, Scenario.S2, placements, {"KR": kr}, _support(), _cfg()
    )
    assert any("r_fleet missing" in m for m in missing)
    assert cohort.total == pytest.approx(0.0)


def test_missing_T_returns_empty():
    sup = SupportParams(lifetime_T=None, vkt={"KR": 13000})
    placements = [Placement("KR", Vehicle("H", "ICE", Powertrain.ICE, ice_intensity=0.16), 1000)]
    cohort, vrs, missing = compute_cohort(
        "F", 2024, Scenario.S2, placements, {"KR": _kr()}, sup, _cfg()
    )
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


def test_tier_c_volume_alone_triggers_directional_suppression():
    kr = _kr()
    placements = [
        Placement(
            "KR",
            Vehicle("H", "BEV", Powertrain.BEV, eta_ev=0.18, tier=DataTier.A),
            1000,
            volume_tier=DataTier.C,
        )
    ]
    cohort, _, _ = compute_cohort(
        "F", 2024, Scenario.S2, placements, {"KR": kr}, _support(), _cfg()
    )
    assert cohort.directional_only is True


def test_unknown_vehicle_tier_is_suppressed_as_low_confidence():
    placements = [
        Placement(
            "KR",
            Vehicle("H", "BEV", Powertrain.BEV, eta_ev=0.18),
            1000,
            volume_tier=DataTier.A,
        )
    ]
    cohort, _, _ = compute_cohort(
        "F", 2024, Scenario.S2, placements, {"KR": _kr()}, _support(), _cfg()
    )
    assert cohort.directional_only is True
    assert any("Tier-C/unknown affected-unit share" in warning for warning in cohort.warnings)


def test_direction_label():
    assert direction_label(5) == "contribution"
    assert direction_label(-5) == "liability"
    assert direction_label(0) == "neutral"
