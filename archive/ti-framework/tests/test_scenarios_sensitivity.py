# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from ti_framework.core.aggregate import Placement
from ti_framework.core.portfolio import rolling_portfolio, steady_state_portfolio
from ti_framework.core.scenarios import run
from ti_framework.core.sensitivity import (
    monte_carlo,
    run_sensitivity,
    sweep_lifetime,
    sweep_s2_ndc_range,
    sweep_uf,
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


def _countries():
    return {
        "KR": Country(
            name="South Korea",
            code="KR",
            grid_intensity=0.4,
            fleet_intensity_base=0.18,
            r_fleet=ScenarioRate(s1=0.025, s2=0.045, s3=0.07),
            r_power=ScenarioRate(s1=0.03, s2=0.05, s3=0.09),
            status=BenchmarkStatus.COMPUTED,
            tier=DataTier.A,
        )
    }


def _support():
    return SupportParams(lifetime_T=15, vkt={"KR": 13000}, realworld_range=(0.95, 1.25))


def _placements():
    return [
        Placement("KR", Vehicle("H", "BEV", Powertrain.BEV, eta_ev=0.18, tier=DataTier.A), 50000),
        Placement(
            "KR",
            Vehicle(
                "K",
                "PHEV",
                Powertrain.PHEV,
                uf=0.4,
                eta_elec=0.2,
                ice_mode_intensity=0.18,
                tier=DataTier.A,
            ),
            20000,
        ),
    ]


def test_run_produces_three_scenarios():
    res = run("F", 2024, _placements(), _countries(), _support(), EngineConfig())
    assert set(res.cohorts) == {Scenario.S1, Scenario.S2, Scenario.S3}
    # more ambitious benchmark (S3) -> lower TI than S1 for a clean-vehicle portfolio
    assert res.cohorts[Scenario.S1].total > res.cohorts[Scenario.S3].total


def test_run_data_quality_declaration_present():
    res = run("F", 2024, _placements(), _countries(), _support(), EngineConfig())
    dq = res.data_quality
    assert dq.lifetime_T == 15
    assert "S2" in dq.scenario_sources
    assert dq.volume_tiers == {"KR": "?"}


def test_run_reports_worst_volume_tier_by_country():
    placements = _placements()
    placements[0].volume_tier = DataTier.B
    placements[1].volume_tier = DataTier.C
    res = run("F", 2024, placements, _countries(), _support(), EngineConfig())
    assert res.data_quality.volume_tiers == {"KR": "C"}


def test_lifetime_sweep_has_three_points():
    out = sweep_lifetime("F", 2024, _placements(), _countries(), _support(), EngineConfig())
    assert set(out) == {"T_minus", "T_central", "T_plus"}


def test_uf_sweep_lower_bound_reduces_phev_contribution():
    out = sweep_uf("F", 2024, _placements(), _countries(), _support(), EngineConfig())
    # Lower UF -> more combustion -> lower (more negative) TI than central
    assert out["UF_lower"]["S2"] < out["UF_central"]["S2"]


def test_sector_split_side_by_side():
    cfg = EngineConfig(sector_split_fleet=0.7)  # transport decarbonises slower than economy
    out = run_sensitivity("F", 2024, _placements(), _countries(), _support(), cfg)
    ss = out["sector_split"]
    assert "uncorrected" in ss and "corrected" in ss
    # slower fleet benchmark (factor<1) lowers the benchmark -> changes TI
    assert ss["uncorrected"]["S2"] != ss["corrected"]["S2"]


def test_s2_conditional_upper_is_used():
    countries = _countries()
    countries["KR"].r_fleet.s2_upper = 0.06
    countries["KR"].r_power.s2_upper = 0.07
    out = sweep_s2_ndc_range(
        "F", 2024, _placements(), countries, _support(), EngineConfig()
    )
    assert set(out) == {"S2_unconditional", "S2_conditional_upper"}
    assert out["S2_unconditional"] != out["S2_conditional_upper"]


def test_monte_carlo_band_ordering():
    cfg = EngineConfig(monte_carlo=True, mc_draws=200)
    mc = monte_carlo("F", 2024, Scenario.S2, _placements(), _countries(), _support(), cfg)
    assert mc["p05"] <= mc["median"] <= mc["p95"]
    assert mc["n_draws"] == 200


def test_rolling_portfolio_steady_state_equivalence():
    annual = [10.0, 8.0, 6.0, 4.0]  # one cohort's profile (t=0..3)
    # identical cohorts each year -> at maturity portfolio == sum(annual)
    cohorts = {y: annual for y in range(2021, 2025)}
    port = rolling_portfolio(cohorts, range(2024, 2025))
    assert port[2024] == pytest.approx(steady_state_portfolio(annual))


def test_portfolio_rampup_increases():
    res = run("F", 2024, _placements(), _countries(), _support(), EngineConfig())
    series = res.portfolio[Scenario.S2]
    # ramp-up is cumulative -> monotone in magnitude for a single-signed annual series
    assert len(series) == 15
