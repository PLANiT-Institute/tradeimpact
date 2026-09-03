# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from ti_framework.layer1.automotive import (
    MethodABenchmark,
    MethodBBenchmark,
    MethodCBenchmark,
    bc_divergence,
)


def test_method_b_exponential_decline():
    b = MethodBBenchmark(intensity_base=0.2, r_fleet=0.05, distance=10000)
    assert b.intensity(0) == pytest.approx(0.2)
    assert b.intensity(1) == pytest.approx(0.2 * 0.95)
    assert b.intensity(10) == pytest.approx(0.2 * 0.95**10)
    # e_ref = intensity * distance
    assert b.e_ref(0) == pytest.approx(0.2 * 10000)


def test_method_b_zero_rate_is_flat():
    b = MethodBBenchmark(intensity_base=0.18, r_fleet=0.0, distance=12000)
    assert b.intensity(0) == pytest.approx(b.intensity(20))


def test_method_b_series_length():
    b = MethodBBenchmark(intensity_base=0.2, r_fleet=0.04, distance=10000)
    s = b.e_ref_series(5)
    assert len(s) == 5
    assert s[0] == pytest.approx(2000)


def test_method_b_s_curve_endpoints_match_exponential():
    exp = MethodBBenchmark(intensity_base=0.2, r_fleet=0.05, distance=1, horizon=15)
    s = MethodBBenchmark(intensity_base=0.2, r_fleet=0.05, distance=1, s_curve=True, horizon=15)
    # S-curve passes through I0 at t=0 and the exponential endpoint at the horizon.
    assert s.intensity(0) == pytest.approx(0.2)
    assert s.intensity(15) == pytest.approx(exp.intensity(15), rel=1e-9)


def test_method_a_fleet_stock_average():
    # 3 vintages, flat survival params; fleet average must lie within the new-entrant range
    a = MethodABenchmark(
        vintages=[2020, 2021, 2022],
        n_new=[100, 100, 100],
        i_new=[0.25, 0.22, 0.20],
        alpha=14.0,
        beta=4.0,
        distance=10000,
        base_year=2022,
    )
    val = a.intensity(0)
    assert 0.20 <= val <= 0.25
    # newest vintage (lowest intensity) gets full survival weight -> average below simple mean
    assert val == pytest.approx(
        sum(
            MethodABenchmark.survival(2022 - y, 14.0, 4.0) * i
            for y, i in zip([2020, 2021, 2022], [0.25, 0.22, 0.20], strict=True)
        )
        / sum(MethodABenchmark.survival(2022 - y, 14.0, 4.0) for y in [2020, 2021, 2022]),
        rel=1e-9,
    )


def test_method_a_survival_monotonic():
    s0 = MethodABenchmark.survival(0, 14, 4)
    s10 = MethodABenchmark.survival(10, 14, 4)
    s20 = MethodABenchmark.survival(20, 14, 4)
    assert s0 == pytest.approx(1.0)
    assert s0 > s10 > s20 >= 0


def test_method_c_two_bin_recursion():
    c = MethodCBenchmark(
        intensity_base=0.20,
        i_new=[0.20, 0.15, 0.12, 0.10],
        renewal_rate=0.10,
        distance=10000,
        scrappage=0.0,
    )
    # t=0 is the base; t=1 = RR*i_new[1] + (1-RR)*I0
    assert c.intensity(0) == pytest.approx(0.20)
    assert c.intensity(1) == pytest.approx(0.10 * 0.15 + 0.90 * 0.20)


def test_bc_divergence_flag():
    b = MethodBBenchmark(intensity_base=0.20, r_fleet=0.05, distance=10000)
    # Method C declining much faster -> should exceed 30% within the horizon
    c = MethodCBenchmark(
        intensity_base=0.20,
        i_new=[0.20] + [0.02] * 20,
        renewal_rate=0.5,
        distance=10000,
    )
    out = bc_divergence(b, c, 15)
    assert out["exceeds_30pct"] is True
    assert out["max_divergence"] > 0.30


def test_bc_divergence_identical_is_zero():
    b = MethodBBenchmark(intensity_base=0.20, r_fleet=0.05, distance=10000)
    out = bc_divergence(b, b, 10)
    assert out["max_divergence"] == pytest.approx(0.0)
    assert out["exceeds_30pct"] is False
