"""Tests for the power-sector pipeline: the arithmetic, the attribution rule and the extractors.

The Global Energy Monitor tracker and the role register are hand-gathered and may not be on
disk, so the model's functions are exercised on synthetic inputs here and the published tables
are checked only when they exist.
"""

from __future__ import annotations

import csv
import importlib.util
import re
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
own = load("roles/extract_gem_ownership.py")
anchors = load("targets/extract_ndc_anchors.py")


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


def test_ndc_sentences_are_read_the_way_the_rule_says() -> None:
    """Unconditional figure, lower bound of a range, base year, furthest stated target year."""

    def read(text: str, years: list[int]) -> dict | None:
        return anchors.parse_base_year_target(anchors.clean(text), years)

    us = read("The United States commits to reducing its emissions by 61-66 percent below 2005 "
              "levels by 2035.", [2035])  # fmt: skip
    assert us == {"reduction": 0.61, "reduction_upper": 0.66, "base_year": 2005,
                  "target_year": 2035}  # fmt: skip
    jp = read("Japan commits to reduce its emissions by 60% in FY 2035 and by 73% by FY 2040 "
              "respectively, compared to FY 2013 levels.", [2035, 2040])  # fmt: skip
    assert (jp["reduction"], jp["base_year"], jp["target_year"]) == (0.73, 2013, 2040)
    om = read("Oman commits to an absolute reduction of 33% in national total GHG emissions by "
              "2035 relative to a 2024 base year of 93.6 MtCO2e - 7% unconditional and 26% "
              "conditional on international finance", [2035])  # fmt: skip
    assert (om["reduction"], om["base_year"], om["target_year"]) == (0.07, 2024, 2035)
    th = read("Thailand commits to reducing its net GHG emissions to 152 million tCO2eq in 2035 "
              "compared to 2019 levels, which is equaivalent to a 47 percent reduction.",
              [2035])  # fmt: skip
    assert (th["reduction"], th["base_year"], th["target_year"]) == (0.47, 2019, 2035)
    nz = read("New Zealand commits to reduce net greenhouse gas emissions to 51\u201355 per cent "
              "below gross 2005 levels by 2035.", [2035])  # fmt: skip
    assert (nz["reduction"], nz["reduction_upper"], nz["base_year"]) == (0.51, 0.55, 2005)
    sa = read("Saudi Arabia commits to reduce emissions by 335 mtCO2e by 2040 relative to 2019 "
              "levels.", [2040])  # fmt: skip
    assert sa is None
    assert anchors.classify("Baseline scenario target") == "bau_reduction"
    assert anchors.classify("Base year target; Trajectory target") == "reduction_from_base"
    assert anchors.classify("Intensity target") == "gdp_intensity"


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


def test_gem_extractor_maps_headers_and_keeps_only_overseas_in_scope_units(
    tmp_path: Path,
) -> None:
    wb = Workbook()
    ws = wb.active
    header = [
        "Type", "Country/area", "Plant / Project name", "Unit / Phase name", "Capacity (MW)",
        "Status", "Start year", "Retired year", "Technology", "Fuel (combustion only)",
        "Operator(s)", "Owner(s)", "Parent(s)", "Latitude", "Longitude", "GEM location ID",
        "GEM unit/phase ID", "GEM.Wiki URL",
    ]  # fmt: skip
    ws.append(header)
    ws.append(["coal", "Viet Nam", "Nghi Son", "Unit 1", 600, "operating", 2022, None,
               "supercritical", "coal: bituminous", "Nghi Son 2 Power",
               "Nghi Son 2 Power LLC [100%]",
               "Marubeni Corp [50.0%]; Korea Electric Power Corp [50.0%]",
               19.3, 105.7, "L1", "U1", "https://www.gem.wiki/x"])  # fmt: skip
    ws.append(["oil/gas", "Viet Nam", "Other", "1", 750, "construction", 2027, None,
               "combined cycle", "fossil gas: LNG, fossil liquids: diesel", "",
               "Someone Else [100%]",
               "Nobody [100.0%]", 10.0, 106.0, "L2", "U2", ""])  # fmt: skip
    ws.append(["coal", "South Korea", "Dangjin", "9", 1020, "operating", 2016, None,
               "ultra-supercritical",
               "coal: bituminous", "", "Korea East-West Power Co Ltd [100%]",
               "Korea Electric Power Corp [100.0%]", 37.0, 126.6, "L3", "U3", ""])  # fmt: skip
    ws.append(["coal", "Atlantis", "Lost", "1", 100, "operating", 2000, None, "", "", "",
               "Doosan Enerbility [100%]", "", 0, 0, "L4", "U4", ""])  # fmt: skip
    path = tmp_path / "gem_test.xlsx"
    wb.save(path)
    spec = read(DATA / "projects" / "method" / "gem_columns.csv")
    companies = read(DATA / "companies" / "method" / "companies.csv")
    names = {"viet nam": "VN", "south korea": "KR"}
    kept, unmapped, domestic = gem.extract([path], spec, companies, {"L2"}, names)
    assert unmapped == {"Atlantis"}
    assert domestic == 1  # KEPCO's Korean plant is not a trade
    assert [r["gem_unit_id"] for r in kept] == ["U1", "U2"]
    u1, u2 = kept
    assert u1["country"] == "VN" and u1["fuel_type"] == "coal"
    assert set(u1["matched_companies"].split(";")) == {"marubeni", "kepco"}
    assert u2["fuel_type"] == "gas"  # oil/gas split on the first listed fuel
    assert u2["matched_companies"] == ""  # kept because a role row names its location


def test_fuel_type_normalisation_follows_the_first_listed_fuel() -> None:
    assert (
        gem.fuel_type_of("oil/gas", "fossil liquids: heavy fuel oil, fossil gas: natural gas")
        == "oil"
    )
    assert gem.fuel_type_of("oil/gas", "fossil gas: natural gas, fossil liquids: diesel") == "gas"
    assert gem.fuel_type_of("oil/gas", "") == "gas"
    assert gem.fuel_type_of("utility-scale solar", "") == "solar"
    assert gem.fuel_type_of("hydropower", "") == "hydro"


def test_tracker_owner_strings_yield_equity_rows_with_shares() -> None:
    assert own.parse_entities("Marubeni Corp [50.0%]; Chubu Electric Power Co Inc [50.0%]") == [
        ("Marubeni Corp", 0.5),
        ("Chubu Electric Power Co Inc", 0.5),
    ]
    assert own.parse_entities("Elecseed; Korea Midland Power Co Ltd") == [
        ("Elecseed", None),
        ("Korea Midland Power Co Ltd", None),
    ]
    companies = read(DATA / "companies" / "method" / "companies.csv")
    unit = {
        "gem_unit_id": "U1", "gem_location_id": "L1", "plant_name": "Nghi Son", "country": "VN",
        "owner": "Nghi Son 2 Power LLC [100%]",
        "parent": "Marubeni Corp [50.0%]; Korea Electric Power Corp [50.0%]",
        "wiki_url": "https://www.gem.wiki/x",
    }  # fmt: skip
    rows = own.ownership_rows([unit], companies)
    assert {(r["company_id"], r["share"], r["level"]) for r in rows} == {
        ("marubeni", 0.5, "parent"),
        ("kepco", 0.5, "parent"),
    }
    domestic = {**unit, "country": "JP"}
    assert {r["company_id"] for r in own.ownership_rows([domestic], companies)} == {"kepco"}


def test_merge_prefers_the_register_and_drops_domestic_rows() -> None:
    companies = {c["company_id"]: c for c in read(DATA / "companies" / "method" / "companies.csv")}
    register = [{
        "company_id": "kepco", "company_name": "KEPCO", "company_country": "KR",
        "company_type": "utility",
        "gem_unit_id": "U1", "gem_location_id": "L1", "plant_name": "P", "country": "VN",
        "role": "equity_owner", "phase": "operation", "share": "0.4", "share_basis": "equity_share",
        "from_year": "", "to_year": "", "source_url": "https://example.org", "source_note": "",
        "accessed_date": "2026-09-05",
    }]  # fmt: skip
    gem_rows = [
        {"company_id": "kepco", "gem_unit_id": "U1", "gem_location_id": "L1", "plant_name": "P",
         "country": "VN", "level": "parent", "entity": "Korea Electric Power Corp", "share": "0.5",
         "source_url": "", "source_id": "gem"},
        {"company_id": "marubeni", "gem_unit_id": "U1", "gem_location_id": "L1", "plant_name": "P",
         "country": "VN", "level": "parent", "entity": "Marubeni Corp", "share": "0.5",
         "source_url": "", "source_id": "gem"},
        {"company_id": "marubeni", "gem_unit_id": "U9", "gem_location_id": "L9", "plant_name": "Q",
         "country": "JP", "level": "owner", "entity": "Marubeni Corp", "share": "1.0",
         "source_url": "", "source_id": "gem"},
    ]  # fmt: skip
    merged, domestic = agg.merge_registers(register, gem_rows, companies)
    assert domestic == 1
    assert [(r["company_id"], r["origin"], r["share"]) for r in merged] == [
        ("kepco", "register", "0.4"),
        ("marubeni", "gem", "0.5"),
    ]


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


sens = load("model/build_sensitivity_power.py")
REPORT = DATA / "report" / "ti_power_report.html"


def test_sensitivity_varies_one_input_at_a_time_around_the_published_value() -> None:
    """Each dimension's central row equals the published result; low and high bracket it."""
    grid = {y: (500.0 * (1 - 0.03) ** (y - 2024), "pathway") for y in range(2024, 2100)}
    unit = {
        "gem_unit_id": "G1", "scenario": "S2", "capacity_mw": "600", "capacity_factor": "0.55",
        "intensity_gco2_per_kwh": "873.231", "start_year": "2024", "end_year": "2063",
        "analysis_year": "2026", "lifetime_source": "default", "cf_source": "default",
        "heat_rate_mj_per_kwh": "9.2308", "ef_kgco2_per_tj": "94600",
        "ef_basis": "ipcc_default",
        "biogenic": "no", "fuel_type": "coal", "fuel_id": "bituminous",
        "technology": "supercritical",
    }  # fmt: skip
    d = {"fuel_type": "coal", "technology_pattern": "super", "lifetime_years": "40",
         "lifetime_low_years": "30", "lifetime_high_years": "50", "capacity_factor": "0.55",
         "cf_low": "0.40", "cf_high": "0.75"}  # fmt: skip
    bound = {"ef_low_kgco2_per_tj": "89500", "ef_high_kgco2_per_tj": "99700"}
    rows = sens.variants_for(unit, d, bound, grid)
    by = {(r["dimension"], r["variant"]): r for r in rows}
    assert {k[0] for k in by} == {"lifetime", "capacity_factor", "emission_factor"}
    central = {
        by[(dim, "central")]["ti_lifetime_tco2"]
        for dim in ("lifetime", "capacity_factor", "emission_factor")
    }
    assert len(central) == 1  # one published value, restated identically on every dimension
    c = central.pop()
    for dim in ("lifetime", "capacity_factor", "emission_factor"):
        lo, hi = by[(dim, "low")]["ti_lifetime_tco2"], by[(dim, "high")]["ti_lifetime_tco2"]
        assert min(lo, hi) < c < max(lo, hi), dim
    assert by[("lifetime", "high")]["parameter"] == 50


@pytest.mark.skipif(not REPORT.exists(), reason="report not built")
def test_power_report_carries_no_data_of_its_own() -> None:
    """No total, percentage or unit count is written into the page; it queries the database."""
    html = REPORT.read_text(encoding="utf-8")
    assert html.count("data-f=") >= 20 and "tradeimpact_power.sqlite" in html
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    assert not re.search(r"[+\u2212-]\d+\.\d+ ?Mt", text), "a lifetime total is baked in"
    assert not re.search(r"\d+(\.\d+)? ?%", text), "a percentage is baked in"
    scripts = re.findall(
        r"<script src=\"([^\"]+)\"[^>]*integrity=\"(sha(?:384|512)-[^\"]+)\"", html
    )
    assert len(scripts) == 3 and all(
        s.startswith("https://cdnjs.cloudflare.com/ajax/libs/") for s, _ in scripts
    )
    assert "map_geometry" in html


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
