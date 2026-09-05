"""Tests for the power-sector pipeline: the arithmetic, the attribution rule and the extractors.

The Global Energy Monitor tracker and the role register are hand-gathered and may not be on
disk, so the model's functions are exercised on synthetic inputs here and the published tables
are checked only when they exist.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from openpyxl import Workbook

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "script" / "power"
DATA = REPO / "data" / "power"
OUT = DATA / "output"


def load(relative: str) -> ModuleType:
    """Import a pipeline script by path without running it."""
    path = SCRIPTS / relative
    sys.path.insert(0, str(SCRIPTS / "model"))
    sys.path.insert(0, str(REPO / "script"))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ti = load("model/build_ti_power.py")
rates = load("targets/derive_power_rates.py")
gem = load("projects/extract_gem_tracker.py")
roles = load("roles/extract_roles.py")
agg = load("model/aggregate_roles.py")
factors = load("emission_factors/extract_emission_factors.py")


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- arithmetic


def test_intensity_reproduces_the_textbook_coal_figure() -> None:
    """94.6 tCO2/TJ at 10 MJ/kWh (36 % efficiency) is 946 gCO2/kWh."""
    assert ti.intensity_gco2_per_kwh(10.0, 94_600) == pytest.approx(946.0)
    # Combined-cycle gas at 55 % efficiency: 3.6/0.55 MJ/kWh x 56.1 kg/TJ.
    assert ti.intensity_gco2_per_kwh(3.6 / 0.55, 56_100) == pytest.approx(367.2, abs=0.1)


def test_unit_flow_matches_the_closed_form_geometric_sum() -> None:
    """Constant generation G and intensity I against a grid declining at rate r from g0.

    TI = sum_{t<L} G (I - g0 (1-r)^t) = G (L I - g0 (1 - (1-r)^L) / r), in tonnes after 1e-6.
    """
    G, I, g0, r, L = 3.0e9, 800.0, 500.0, 0.05, 20  # noqa: E741 - mirrors the equation
    years = list(range(2030, 2030 + L))
    grid = {y: (g0 * (1 - r) ** t, "pathway") for t, y in enumerate(years)}
    flow = ti.unit_flow(G, I, grid, years)
    assert len(flow) == L
    total = sum(float(row["ti_tco2"]) for row in flow)
    expected = G * (L * I - g0 * (1 - (1 - r) ** L) / r) / 1e6
    assert total == pytest.approx(expected, rel=1e-6)
    # Both sides of the comparison are stated and the identity holds row by row.
    for row in flow:
        e_prod, e_ref, gap = (float(row[k]) for k in ("e_prod_tco2", "e_ref_tco2", "ti_tco2"))
        assert gap == pytest.approx(e_prod - e_ref, abs=2e-3)
    assert float(flow[-1]["cumulative_ti_tco2"]) == pytest.approx(total, abs=1e-2 * L)


def test_unit_flow_drops_years_the_grid_path_does_not_cover() -> None:
    """A unit commissioned before the first grid observation loses those years, never fills them."""
    grid = {2010: (600.0, "observed"), 2011: (590.0, "observed")}
    flow = ti.unit_flow(1e9, 900.0, grid, [2008, 2009, 2010, 2011])
    assert [row["calendar_year"] for row in flow] == [2010, 2011]


def test_s1_rate_recovers_a_known_exponential_decline() -> None:
    """A series falling 4 % a year since 2015 yields r = 0.04 to the digit."""
    series = {y: 500.0 * (1 - 0.04) ** (y - 2015) for y in range(2012, 2025)}
    value, y0, y1 = rates.log_linear_rate(series)
    assert (y0, y1) == (2015, 2024)
    assert value == pytest.approx(0.04, abs=1e-9)
    assert rates.log_linear_rate({2022: 1.0, 2023: 0.9}) is None


def test_s2_target_level_reads_each_anchor_type() -> None:
    series = {2010: 600.0, 2020: 500.0, 2024: 450.0}
    base = {"base_year": "2010", "target_type": "reduction_from_base", "reduction": "0.4"}
    assert rates.target_level(base, series)[0] == pytest.approx(360.0)
    absolute = {
        "base_year": "2020",
        "target_type": "absolute_level",
        "base_value": "200",
        "target_value": "50",
        "reduction": "",
    }
    assert rates.target_level(absolute, series)[0] == pytest.approx(125.0)
    intensity = {"base_year": "", "target_type": "intensity_target", "target_value": "100"}
    assert rates.target_level(intensity, series)[0] == pytest.approx(100.0)
    assert rates.target_level({"base_year": "2010", "target_type": "bau_reduction"}, series) is None


# ---------------------------------------------------------------- attribution


def test_roles_are_attributed_separately_and_shares_stay_columns() -> None:
    """Two roles on one unit give two rows, totals stay per role, weighted = share x full."""
    unit = {
        "gem_unit_id": "G1",
        "gem_location_id": "L1",
        "plant_name": "P",
        "country": "VN",
        "fuel_type": "coal",
        "status": "operating",
        "capacity_mw": "600",
        "start_year": "2022",
        "scenario": "S2",
        "ti_lifetime_tco2": "1000.0",
        "ti_remaining_tco2": "800.0",
        "direction": "liability",
        "tier": "C",
        "latitude": "1",
        "longitude": "2",
    }
    role_rows = [
        {
            "company_id": "doosan_enerbility",
            "company_name": "Doosan",
            "company_country": "KR",
            "gem_unit_id": "G1",
            "gem_location_id": "",
            "role": "epc_contractor",
            "phase": "construction",
            "share": "0.5",
            "share_basis": "contract_share",
            "source_url": "https://example.org",
        },
        {
            "company_id": "kepco",
            "company_name": "KEPCO",
            "company_country": "KR",
            "gem_unit_id": "",
            "gem_location_id": "L1",
            "role": "equity_owner",
            "phase": "operation",
            "share": "",
            "share_basis": "equity_share",
            "source_url": "https://example.org",
        },
    ]
    rows = agg.attribute(role_rows, [unit])
    assert len(rows) == 2
    epc = next(r for r in rows if r["role"] == "epc_contractor")
    assert epc["ti_lifetime_full_tco2"] == 1000.0 and epc["ti_lifetime_weighted_tco2"] == 500.0
    owner = next(r for r in rows if r["role"] == "equity_owner")
    assert owner["ti_lifetime_weighted_tco2"] == ""  # no share on file: blank, never assumed
    totals = agg.company_totals(rows)
    assert {(t["company_id"], t["role"]) for t in totals} == {
        ("doosan_enerbility", "epc_contractor"),
        ("kepco", "equity_owner"),
    }


def test_role_register_validation_names_the_failing_row() -> None:
    vocab = {"epc_contractor": {"phase": "construction", "share_basis": "contract_share"}}
    companies = {"doosan_enerbility": {}}
    good = {
        "company_id": "doosan_enerbility",
        "plant_name": "P",
        "role": "epc_contractor",
        "phase": "construction",
        "share": "0.5",
        "share_basis": "contract_share",
        "gem_unit_id": "G1",
        "gem_location_id": "",
        "source_url": "https://example.org/page",
        "accessed_date": "2026-09-05",
    }
    assert roles.validate([good], vocab, companies) == []
    bad = {**good, "company_id": "unknown", "phase": "operation", "share": "1.5", "source_url": ""}
    problems = roles.validate([bad], vocab, companies)
    assert len(problems) == 4 and all(p.startswith("row 2") for p in problems)


# ---------------------------------------------------------------- extractors


def test_gem_extractor_maps_headers_and_keeps_only_in_scope_units(tmp_path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(
        [
            "GEM unit/phase ID",
            "GEM location ID",
            "Country/area",
            "Plant / Project name",
            "Unit / Phase name",
            "Type",
            "Fuel",
            "Technology",
            "Capacity (MW)",
            "Status",
            "Start year",
            "Retired year",
            "Owner",
            "Parent",
            "Latitude",
            "Longitude",
            "Heat rate (Btu per kWh)",
        ]
    )
    ws.append(
        [
            "U1",
            "L1",
            "Viet Nam",
            "Nghi Son",
            "Unit 1",
            "coal",
            "bituminous",
            "supercritical",
            600,
            "operating",
            2022,
            None,
            "Nghi Son 2 Power LLC",
            "Marubeni Corp; KEPCO",
            19.3,
            105.7,
            9000,
        ]
    )
    ws.append(
        [
            "U2",
            "L2",
            "Viet Nam",
            "Other",
            "Unit 1",
            "gas",
            "LNG",
            "combined cycle",
            750,
            "construction",
            2027,
            None,
            "Someone Else",
            "Nobody",
            10.0,
            106.0,
            None,
        ]
    )
    ws.append(
        [
            "U3",
            "L3",
            "Atlantis",
            "Lost",
            "1",
            "coal",
            "",
            "",
            100,
            "operating",
            2000,
            None,
            "Doosan",
            "",
            0,
            0,
            None,
        ]
    )
    path = tmp_path / "gem_test.xlsx"
    wb.save(path)
    spec = read(DATA / "projects" / "method" / "gem_columns.csv")
    matchers = gem.company_matcher(read(DATA / "companies" / "method" / "companies.csv"))
    names = {"viet nam": "VN"}
    kept, unmapped = gem.extract([path], spec, matchers, {"L2"}, names)
    assert unmapped == {"Atlantis"}
    assert [r["gem_unit_id"] for r in kept] == ["U1", "U2"]
    u1 = kept[0]
    assert u1["country"] == "VN"
    assert set(u1["matched_companies"].split(";")) == {"marubeni", "kepco"}
    assert u1["heat_rate_mj_per_kwh"] == pytest.approx(9000 * 1.055056e-3, abs=1e-4)
    assert kept[1]["matched_companies"] == ""  # kept because a role row names its location


def test_ipcc_transcription_check_finds_numbers_as_the_pdf_renders_them() -> None:
    rows = [
        {
            "fuel_id": "gas",
            "ef_kgco2_per_tj": "56100",
            "ef_low_kgco2_per_tj": "54300",
            "ef_high_kgco2_per_tj": "58300",
        }
    ]
    assert factors.verify_transcription(rows, "Natural Gas 56 100 54,300 58300") == []
    assert factors.verify_transcription(rows, "Natural Gas 56 100 54,300") == [
        "gas.ef_high_kgco2_per_tj=58300"
    ]
    assert factors.number_pattern(98300).search("factor 198300 here") is None


# ---------------------------------------------------------------- published tables (when built)


@pytest.mark.skipif(not (OUT / "ti_power_by_unit.csv").exists(), reason="tracker not on disk")
def test_published_unit_results_state_both_sides_and_carry_coordinates() -> None:
    rows = read(OUT / "ti_power_by_unit.csv")
    assert rows
    for r in rows:
        prod, ref, gap = (
            float(r[k]) for k in ("e_prod_lifetime_tco2", "e_ref_lifetime_tco2", "ti_lifetime_tco2")
        )
        assert gap == pytest.approx(prod - ref, abs=1e-2 * max(1, int(r["years_counted"])))
        assert r["latitude"] != "" and r["longitude"] != ""
        assert r["tier"] in {"A", "B", "C"}


@pytest.mark.skipif(not (OUT / "ti_power_company.csv").exists(), reason="roles not on disk")
def test_published_company_table_never_sums_across_roles() -> None:
    rows = read(OUT / "ti_power_company.csv")
    keys = [(r["company_id"], r["role"], r["scenario"]) for r in rows]
    assert len(keys) == len(set(keys))
    assert all(r["role"] for r in rows)
