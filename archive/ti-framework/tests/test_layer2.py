# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from ti_framework.layer2.automotive import (
    BEVEmissions,
    GridTrajectory,
    ICEEmissions,
    PHEVEmissions,
)


def test_ice_is_constant():
    ice = ICEEmissions(ice_intensity=0.16, distance=13000)
    assert ice.emissions(0) == pytest.approx(0.16 * 13000)
    assert ice.emissions(0) == ice.emissions(20)


def test_grid_trajectory_declines():
    g = GridTrajectory(g0=0.4, r_power=0.05)
    assert g.at(0) == pytest.approx(0.4)
    assert g.at(1) == pytest.approx(0.4 * 0.95)
    assert g.at(10) == pytest.approx(0.4 * 0.95**10)


def test_bev_tracks_grid():
    g = GridTrajectory(g0=0.4, r_power=0.05)
    bev = BEVEmissions(eta_ev=0.18, grid=g, distance=13000)
    assert bev.emissions(0) == pytest.approx(0.18 * 0.4 * 13000)
    assert bev.emissions(5) == pytest.approx(0.18 * g.at(5) * 13000)


def test_phev_uf_zero_equals_ice_mode():
    g = GridTrajectory(g0=0.4, r_power=0.05)
    phev = PHEVEmissions(uf=0.0, eta_elec=0.2, ice_mode_intensity=0.18, grid=g, distance=13000)
    # UF=0 -> all combustion
    assert phev.emissions(3) == pytest.approx(0.18 * 13000)


def test_phev_uf_one_equals_pure_ev():
    g = GridTrajectory(g0=0.4, r_power=0.05)
    phev = PHEVEmissions(uf=1.0, eta_elec=0.2, ice_mode_intensity=0.18, grid=g, distance=13000)
    # UF=1 -> all electric, equals a BEV with eta=0.2
    assert phev.emissions(3) == pytest.approx(0.2 * g.at(3) * 13000)


def test_phev_composite_midpoint():
    g = GridTrajectory(g0=0.4, r_power=0.0)
    phev = PHEVEmissions(uf=0.5, eta_elec=0.2, ice_mode_intensity=0.18, grid=g, distance=10000)
    expected = (0.5 * 0.2 * 0.4 + 0.5 * 0.18) * 10000
    assert phev.emissions(0) == pytest.approx(expected)
