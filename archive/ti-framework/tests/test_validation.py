# SPDX-License-Identifier: GPL-3.0-or-later
"""Validation (build brief M5): engine output must match the committed reference fixture's
independently hand-calculated expected values to within ±1%."""
from pathlib import Path

import pytest

from ti_framework.core.aggregate import decomposition_identity_holds
from ti_framework.core.scenarios import run
from ti_framework.io.fixtures import load_fixture
from ti_framework.models import Scenario

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "reference_case.json"
TOL = 0.01  # ±1%


@pytest.fixture(scope="module")
def result_and_expected():
    fx = load_fixture(_FIXTURE)
    res = run(fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config)
    return res, fx.expected


def test_cohort_totals_within_1pct(result_and_expected):
    res, expected = result_and_expected
    for sc in (Scenario.S1, Scenario.S2, Scenario.S3):
        exp = expected["cohorts"][sc.value]
        got = res.cohorts[sc].total
        rel = abs(got - exp) / abs(exp)
        assert rel <= TOL, f"{sc.value}: expected {exp}, got {got}, rel={rel:.3%}"


def test_per_vehicle_cumulative_within_1pct(result_and_expected):
    res, expected = result_and_expected
    for ev in expected["vehicles"]:
        match = [
            vr for vr in res.vehicle_results
            if vr.country_code == ev["country"]
            and vr.powertrain.value == ev["powertrain"]
            and vr.scenario.value == ev["scenario"]
        ]
        assert match, f"no result for {ev}"
        rel = abs(match[0].cumulative - ev["cumulative"]) / abs(ev["cumulative"])
        assert rel <= TOL


def test_decomposition_identity_all_scenarios(result_and_expected):
    res, _ = result_and_expected
    for cohort in res.cohorts.values():
        assert decomposition_identity_holds(cohort)


def test_crossover_closed_forms_match_expected(result_and_expected):
    res, expected = result_and_expected
    xref = expected["crossover"]
    by_key = {
        (vr.country_code, vr.powertrain.value, vr.scenario.value): vr.crossover_year
        for vr in res.vehicle_results
    }
    ice = by_key[("KR", "ICE", "S2")]
    assert ice == pytest.approx(xref["KR_ICE_S2"], rel=TOL)
    bev = by_key[("KR", "BEV", "S2")]
    assert bev is None
    assert xref["KR_BEV_S2"] is None
