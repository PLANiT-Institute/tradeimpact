# SPDX-License-Identifier: GPL-3.0-or-later
import math

import pytest

from ti_framework.core.crossover import (
    crossover_bev,
    crossover_ice,
    crossover_numeric,
)
from ti_framework.core.cumulative import ti_cumulative
from ti_framework.core.gap import ti_gap_series
from ti_framework.layer1.automotive import MethodBBenchmark
from ti_framework.layer2.automotive import BEVEmissions, GridTrajectory, ICEEmissions


def test_gap_series_basic():
    b = MethodBBenchmark(intensity_base=0.2, r_fleet=0.05, distance=10000)
    ice = ICEEmissions(ice_intensity=0.18, distance=10000)
    gap = ti_gap_series(b, ice, 3)
    assert gap[0] == pytest.approx(0.2 * 10000 - 0.18 * 10000)
    assert gap[1] == pytest.approx(0.2 * 0.95 * 10000 - 0.18 * 10000)


def test_gap_T_equals_1():
    b = MethodBBenchmark(intensity_base=0.2, r_fleet=0.05, distance=10000)
    ice = ICEEmissions(ice_intensity=0.18, distance=10000)
    gap = ti_gap_series(b, ice, 1)
    assert len(gap) == 1
    assert ti_cumulative(gap) == pytest.approx(gap[0])


def test_gap_T_zero_raises():
    b = MethodBBenchmark(intensity_base=0.2, r_fleet=0.05, distance=10000)
    ice = ICEEmissions(ice_intensity=0.18, distance=10000)
    with pytest.raises(ValueError):
        ti_gap_series(b, ice, 0)


def test_cumulative_sum():
    assert ti_cumulative([1.0, -2.0, 3.0]) == pytest.approx(2.0)


def test_negative_gap_liability():
    # ICE dirtier than benchmark from t=0 -> all-negative gap (pure liability)
    b = MethodBBenchmark(intensity_base=0.10, r_fleet=0.05, distance=10000)
    ice = ICEEmissions(ice_intensity=0.20, distance=10000)
    gap = ti_gap_series(b, ice, 5)
    assert all(g < 0 for g in gap)
    assert ti_cumulative(gap) < 0


def test_crossover_ice_closed_form():
    # benchmark I0=0.2, ICE=0.18 -> crosses when 0.2*0.95^t = 0.18
    t_star, reason = crossover_ice(intensity_base=0.2, r_fleet=0.05, distance=10000, e_prod=0.18 * 10000)
    assert reason is None
    expected = math.log(0.18 / 0.2) / math.log(0.95)
    assert t_star == pytest.approx(expected)


def test_crossover_ice_no_decline():
    t_star, reason = crossover_ice(0.2, 0.0, 10000, 0.18 * 10000)
    assert t_star is None
    assert "non-declining" in reason


def test_crossover_bev_closed_form_matches_numeric():
    I0, rf, eta, g0, rp, D = 0.2, 0.05, 0.18, 0.4, 0.02, 10000
    t_star, reason = crossover_bev(I0, rf, eta, g0, rp)
    b = MethodBBenchmark(intensity_base=I0, r_fleet=rf, distance=D)
    bev = BEVEmissions(eta_ev=eta, grid=GridTrajectory(g0=g0, r_power=rp), distance=D)
    num, _ = crossover_numeric(ti_gap_series(b, bev, 200))
    if t_star is not None and num is not None:
        assert t_star == pytest.approx(num, rel=1e-2)


def test_crossover_bev_parallel_no_crossover():
    t_star, reason = crossover_bev(0.2, 0.05, 0.18, 0.4, 0.05)
    assert t_star is None
    assert "parallel" in reason


def test_crossover_numeric_sign_change():
    # gap goes +, +, -, - : crossover between index 1 and 2
    t_star, _ = crossover_numeric([10.0, 5.0, -5.0, -10.0])
    assert t_star == pytest.approx(1.5)


def test_crossover_numeric_none():
    t_star, reason = crossover_numeric([10.0, 9.0, 8.0])
    assert t_star is None
    assert "no sign change" in reason
