# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests against the real TI_Data_Workbook / reference DB (skipped if not present, e.g. CI)."""
from pathlib import Path

import pytest

from ti_framework.io.schema import is_placeholder, parse_rate_fraction, parse_status
from ti_framework.io.workbook import load_reference_db, load_workbook_inputs
from ti_framework.models import BenchmarkStatus

_DATA = Path(__file__).resolve().parents[1] / "data"
_WORKBOOK = _DATA / "TI_Data_Workbook_v0.1.xlsx"
_REFDB = _DATA / "TI_CaseStudy_Reference_DB_v0.1.xlsx"


def test_is_placeholder():
    assert is_placeholder(None)
    assert is_placeholder("")
    assert is_placeholder("TO COLLECT")
    assert is_placeholder("FLAG: no baseline")
    assert is_placeholder("[model]")
    assert not is_placeholder(0.42)
    assert not is_placeholder("Hyundai")


def test_parse_rate_fraction():
    assert parse_rate_fraction(4.34) == pytest.approx(0.0434)
    assert parse_rate_fraction(0.0434) == pytest.approx(0.0434)
    assert parse_rate_fraction("TO EXTRACT") is None


def test_parse_status():
    assert parse_status("COMPUTED (pro-rata pending)") is BenchmarkStatus.COMPUTED
    assert parse_status("FLAG: no benchmark") is BenchmarkStatus.FLAG_NO_BENCHMARK
    assert parse_status("FLAG: intensity target") is BenchmarkStatus.FLAG_INTENSITY


@pytest.mark.skipif(not _WORKBOOK.exists(), reason="data workbook not available")
def test_load_real_workbook_partial_data():
    inp = load_workbook_inputs(_WORKBOOK)
    # nine operating countries load even though most cells are empty
    assert set(inp.countries) >= {"AU", "US", "EU", "JP", "KR", "IN", "ID", "SA", "CN"}
    # US is a FLAG market (no NDC)
    assert inp.countries["US"].is_flag
    # D1: KR gets the pro-rata identity warning and a tier downgrade
    kr = inp.countries["KR"]
    assert kr.r_fleet.s2 == kr.r_power.s2
    assert any("PRORATA_IDENTITY" in w for w in kr.warnings)
    # missing inputs are surfaced, not fabricated
    assert inp.missing_inputs


@pytest.mark.skipif(not _WORKBOOK.exists(), reason="data workbook not available")
def test_grid_intensity_converted_to_kg():
    inp = load_workbook_inputs(_WORKBOOK)
    # KR Ember 2024 ~415.51 gCO2/kWh -> 0.41551 kgCO2e/kWh
    assert inp.countries["KR"].grid_intensity == pytest.approx(0.41551, rel=1e-3)


@pytest.mark.skipif(not _REFDB.exists(), reason="reference DB not available")
def test_load_reference_db():
    countries = load_reference_db(_REFDB)
    assert "KR" in countries
    assert countries["KR"].grid_intensity == pytest.approx(0.41551, rel=1e-3)
    # FLAG markets carry their status from the reference DB too
    assert countries["US"].is_flag
