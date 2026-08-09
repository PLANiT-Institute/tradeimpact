# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests against the real TI_Data_Workbook / reference DB (skipped if not present, e.g. CI)."""
from pathlib import Path

import pytest

from ti_framework.io.schema import (
    SchemaError,
    is_placeholder,
    parse_rate_fraction,
    parse_rate_percent,
    parse_status,
)
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
    assert parse_rate_fraction(0.0434) == pytest.approx(0.0434)
    assert parse_rate_fraction("TO EXTRACT") is None
    with pytest.raises(SchemaError):
        parse_rate_fraction(4.34)  # percent in a fraction column: loud, never rescaled


def test_parse_rate_percent():
    assert parse_rate_percent(4.34) == pytest.approx(0.0434)
    assert parse_rate_percent(0.5) == pytest.approx(0.005)  # 0.5 %/yr, not rescaled
    assert parse_rate_percent("TO EXTRACT") is None


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
    # KR carries collected sectoral S2 rates (기본계획 2024→2030) — no pro-rata identity
    kr = inp.countries["KR"]
    assert kr.r_fleet.s2 != kr.r_power.s2
    assert not any("PRORATA_IDENTITY" in w for w in kr.warnings)
    # D1 still applies where only the economy-wide rate exists (AU S2 stays pro-rata)
    au = inp.countries["AU"]
    assert au.r_fleet.s2 == au.r_power.s2
    assert any("PRORATA_IDENTITY" in w for w in au.warnings)
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


def test_mistyped_header_fails_loudly_instead_of_loading_as_missing(tmp_path):
    """A renamed column must raise, not silently read as a column of uncollected data."""
    import csv as _csv

    import pytest

    from ti_framework.io.csv_adapter import load_csv_inputs
    from ti_framework.io.schema import (
        LAYER1_COLUMNS,
        REG_COLUMNS,
        SHEET_LAYER1,
        SHEET_REG,
        SchemaError,
    )

    def write(name: str, header: list[str]) -> None:
        with (tmp_path / f"{name}.csv").open("w", newline="", encoding="utf-8") as fh:
            _csv.writer(fh).writerow(header)

    write(SHEET_REG, REG_COLUMNS)
    broken = list(LAYER1_COLUMNS)
    broken[broken.index("Grid intensity G_c(0) gCO2/kWh (2024)")] = "Grid intensity"
    write(SHEET_LAYER1, broken)

    with pytest.raises(SchemaError, match="Grid intensity G_c"):
        load_csv_inputs(tmp_path)

    write(SHEET_LAYER1, LAYER1_COLUMNS)
    assert load_csv_inputs(tmp_path).countries == {}
