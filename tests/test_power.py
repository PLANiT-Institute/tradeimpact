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
own = load("roles/extract_gem_roles.py")
ir = load("roles/extract_company_ir_roles.py")
anchors = load("targets/extract_ndc_anchors.py")
wiki = load("roles/extract_wiki_roles.py")
cf_country = load("utilisation/extract_capacity_factors.py")


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


def test_wiki_sentences_are_read_by_company_type_and_role_words() -> None:
    """A wiki sentence gives the tier-1 role only, so the tier-2 key is always *_unspecified."""
    epc = "In March 2013, Korean company Daelim Industrial took over the project as EPC contractor."
    assert wiki.classify(epc, "epc_contractor", (30, 47)) == "epc_unspecified"
    loan = "In June 2016, JBIC approved a US$3.4 billion loan agreement for the plant."
    assert wiki.classify(loan, "eca_bank", (14, 18)) == "loan_unspecified"
    cover = "The commercial bank loans are being insured by Kexim and NEXI."
    assert wiki.classify(cover, "eca_insurer", (57, 61)) == "cover_unspecified"  # insurer covers
    named_only = "Affected firms would include Kepco and Korea Trade Insurance Corporation."
    assert wiki.classify(named_only, "eca_insurer", (38, 72)) is None
    noise = "JBIC was considering funding 60% of the plant's construction."
    assert wiki.classify(noise, "eca_bank", (0, 4)) is None
    assert wiki.share_after("KEPCO acquired a 40% stake in the project", 5) == 0.4
    assert wiki.share_after("KEPCO acquired the project", 5) is None


# ---------------------------------------------------------------- attribution


def test_roles_are_attributed_separately_and_shares_stay_columns() -> None:
    """Two tier-1 roles on one unit give two rows, totals per role, weighted = share x full."""
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
            "role_tier1": "epc_contractor",
            "role_tier2": "epc_lead",
            "role_tier2_all": "epc_lead|epc_civil_works",
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
            "role_tier1": "equity_owner",
            "role_tier2": "equity_direct",
            "role_tier2_all": "equity_direct",
            "phase": "investment",
            "share": "",
            "share_basis": "equity_share",
            "source_url": "https://example.org",
        },
    ]
    rows = agg.attribute(role_rows, [unit])
    assert len(rows) == 2
    epc = next(r for r in rows if r["role_tier1"] == "epc_contractor")
    assert epc["ti_lifetime_full_tco2"] == 1000.0 and epc["ti_lifetime_weighted_tco2"] == 500.0
    assert epc["role_tier2"] == "epc_lead"  # the most specific scope on file is the primary
    owner = next(r for r in rows if r["role_tier1"] == "equity_owner")
    assert owner["ti_lifetime_weighted_tco2"] == ""  # no share on file: blank, never assumed
    totals = agg.company_totals(rows)
    assert {(t["company_id"], t["role_tier1"]) for t in totals} == {
        ("doosan_enerbility", "epc_contractor"),
        ("kepco", "equity_owner"),
    }
    epc_total = next(t for t in totals if t["company_id"] == "doosan_enerbility")
    assert epc_total["role_tier2_all"] == "epc_civil_works|epc_lead"


def test_role_register_validation_names_the_failing_row() -> None:
    vocab = {"epc_lead": {"phase": "construction", "share_basis": "contract_share"}}
    companies = {"doosan_enerbility": {}}
    good = {
        "company_id": "doosan_enerbility",
        "plant_name": "P",
        "role_tier2": "epc_lead",
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


def test_tracker_fields_yield_investment_and_operation_rows() -> None:
    """Owner and parent give equity with shares; the operator field gives the O&M role."""
    assert own.parse_entities("Marubeni Corp [50.0%]; Chubu Electric Power Co Inc [50.0%]") == [
        ("Marubeni Corp", 0.5),
        ("Chubu Electric Power Co Inc", 0.5),
    ]
    assert own.parse_entities("Elecseed; Korea Midland Power Co Ltd") == [
        ("Elecseed", None),
        ("Korea Midland Power Co Ltd", None),
    ]
    companies = read(DATA / "companies" / "method" / "companies.csv")
    vocab = {v["role_tier2"]: v for v in read(DATA / "roles" / "method" / "roles.csv")}
    unit = {
        "gem_unit_id": "U1", "gem_location_id": "L1", "plant_name": "Nghi Son", "country": "VN",
        "owner": "Nghi Son 2 Power LLC [100%]",
        "parent": "Marubeni Corp [50.0%]; Korea Electric Power Corp [50.0%]",
        "operator": "Korea Electric Power",
        "wiki_url": "https://www.gem.wiki/x",
    }  # fmt: skip
    rows = own.tracker_rows([unit], companies, vocab)
    assert {
        (r["company_id"], r["role_tier1"], r["role_tier2"], r["phase"], r["share"]) for r in rows
    } == {
        ("marubeni", "equity_owner", "equity_parent", "investment", 0.5),
        ("kepco", "equity_owner", "equity_parent", "investment", 0.5),
        ("kepco", "om_contractor", "operator_of_record", "operation", ""),
    }
    domestic = {**unit, "country": "JP"}
    assert {r["company_id"] for r in own.tracker_rows([domestic], companies, vocab)} == {"kepco"}


def test_company_register_rejects_a_row_whose_page_is_not_on_disk() -> None:
    """Every role and every share must cite a page in the fetched index, by key and by URL."""
    vocab = {v["role_tier2"]: v for v in read(DATA / "roles" / "method" / "roles.csv")}
    companies = {c["company_id"]: c for c in read(DATA / "companies" / "method" / "companies.csv")}
    pages = {"kepco_page": {"url": "https://example.org/kepco", "sha256": "x"}}
    good = {
        "company_id": "kepco", "gem_unit_id": "G1", "gem_location_id": "", "plant_name": "P",
        "country": "VN", "role_tier2": "equity_direct", "share": "0.4", "from_year": "",
        "to_year": "",
        "role_as_stated": "acquired a 40% stake", "role_source_key": "kepco_page",
        "role_source_url": "https://example.org/kepco", "role_quote": "KEPCO acquired 40%",
        "share_source_key": "kepco_page", "share_source_url": "https://example.org/kepco",
        "share_quote": "KEPCO acquired 40%", "accessed_date": "2026-09-07", "note": "",
    }  # fmt: skip
    assert ir.validate([good], vocab, companies, pages) == []
    missing = {**good, "role_source_key": "not_fetched", "share_source_key": "not_fetched"}
    assert len(ir.validate([missing], vocab, companies, pages)) == 2
    wrong_url = {**good, "role_source_url": "https://example.org/other"}
    assert any("does not match" in m for m in ir.validate([wrong_url], vocab, companies, pages))
    no_quote = {**good, "role_quote": " "}
    assert any("quote is required" in m for m in ir.validate([no_quote], vocab, companies, pages))
    unsourced_share = {**good, "share_source_key": "", "share_source_url": ""}
    assert ir.validate([unsourced_share], vocab, companies, pages)


def test_country_capacity_factor_is_generation_over_capacity_and_rejects_impossible_pairs() -> None:
    """The implied factor is closed form; a tiny fleet or a lagging capacity series is dropped."""
    # Viet Nam coal 2024 as Ember publishes it: 152.77 TWh on 27.06 GW.
    assert cf_country.capacity_factor(152.77, 27.06) == pytest.approx(
        152.77 * 1e6 / (27.06 * 1e3 * 8760), rel=1e-12
    )
    assert cf_country.capacity_factor(152.77, 27.06) == pytest.approx(0.6445, abs=5e-4)
    assert cf_country.capacity_factor(10.0, 0.01) is None  # fleet below the size floor
    assert cf_country.capacity_factor(10.0, 0.5) is None  # implies a factor above one
    assert cf_country.capacity_factor(0.0, 5.0) is None  # no generation is not a capacity factor


@pytest.mark.skipif(not (OUT / "ti_power_by_unit.csv").exists(), reason="model output not on disk")
def test_a_unit_on_its_destinations_capacity_factor_carries_that_countrys_band() -> None:
    """Every unit not on the tracker's own factor states the band the sensitivity varies."""
    rows = [r for r in read(OUT / "ti_power_by_unit.csv") if r["scenario"] == "S1"]
    assert rows
    for r in rows:
        assert r["cf_source"] in {"gem", "country_implied", "default"}
        if r["cf_source"] == "gem":
            continue
        low, high = float(r["cf_low"]), float(r["cf_high"])
        assert 0 < low <= float(r["capacity_factor"]) <= high <= 1, r["gem_unit_id"]


def test_a_register_quote_must_be_the_pages_own_words(tmp_path: Path) -> None:
    """A paraphrase, an invented sentence or a station-level key is rejected."""
    page = tmp_path / "release.html"
    page.write_text(
        "<html><body><p>Sumitomo Corporation recently commenced construction in Vietnam on "
        "the Van Phong 1 coal-fired power project through its wholly-owned subsidiary.</p>"
        "</body></html>"
    )
    vocab = {v["role_tier2"]: v for v in read(DATA / "roles" / "method" / "roles.csv")}
    companies = {c["company_id"]: c for c in read(DATA / "companies" / "method" / "companies.csv")}
    pages = {"release": {"url": "https://example.org/r", "file": "release.html"}}
    good = {
        "company_id": "sumitomo_corp", "gem_unit_id": "G1", "gem_location_id": "",
        "plant_name": "Van Phong", "country": "VN", "role_tier2": "equity_direct", "share": "",
        "from_year": "", "to_year": "", "role_as_stated": "wholly owned subsidiary",
        "role_source_key": "release", "role_source_url": "https://example.org/r",
        "role_quote": "commenced construction in Vietnam on the Van Phong 1 coal-fired power "
        "project through its wholly-owned subsidiary",
        "share_source_key": "", "share_source_url": "", "share_quote": "",
        "accessed_date": "2026-09-07", "note": "",
    }  # fmt: skip
    assert ir.validate([good], vocab, companies, pages, page_dir=tmp_path) == []
    elided = {**good, "role_quote": "Sumitomo Corporation ... its wholly-owned subsidiary"}
    assert ir.validate([elided], vocab, companies, pages, page_dir=tmp_path) == []
    paraphrase = {**good, "role_quote": "Sumitomo began building the Van Phong 1 coal plant"}
    problems = ir.validate([paraphrase], vocab, companies, pages, page_dir=tmp_path)
    assert any("not in release.html" in m for m in problems)
    station_level = {**good, "gem_unit_id": "", "gem_location_id": "L1"}
    assert any(
        "needs gem_unit_id" in m
        for m in ir.validate([station_level], vocab, companies, pages, page_dir=tmp_path)
    )


def test_merge_prefers_sourced_rows_and_drops_domestic_ones() -> None:
    """Register beats company_ir beats tracker beats wiki, per company x plant x tier-1 role."""
    companies = {c["company_id"]: c for c in read(DATA / "companies" / "method" / "companies.csv")}
    vocab = {v["role_tier2"]: v for v in read(DATA / "roles" / "method" / "roles.csv")}
    company_ir = [{
        "company_id": "kepco", "company_name": "KEPCO", "company_country": "KR",
        "company_type": "utility", "gem_unit_id": "U1", "gem_location_id": "", "plant_name": "P",
        "country": "VN", "role_tier2": "equity_direct", "phase": "investment", "share": "0.4",
        "share_basis": "equity_share", "from_year": "", "to_year": "",
        "source_url": "https://example.org", "source_note": "", "accessed_date": "2026-09-07",
    }]  # fmt: skip
    tracker = [
        {"company_id": "kepco", "gem_unit_id": "U1", "gem_location_id": "L1", "plant_name": "P",
         "country": "VN", "role_tier2": "equity_parent", "share": "0.5", "level": "parent",
         "entity": "Korea Electric Power Corp", "source_url": ""},
        {"company_id": "marubeni", "gem_unit_id": "U1", "gem_location_id": "L1", "plant_name": "P",
         "country": "VN", "role_tier2": "equity_parent", "share": "0.5", "level": "parent",
         "entity": "Marubeni Corp", "source_url": ""},
        {"company_id": "marubeni", "gem_unit_id": "U9", "gem_location_id": "L9", "plant_name": "Q",
         "country": "JP", "role_tier2": "equity_direct", "share": "1.0", "level": "owner",
         "entity": "Marubeni Corp", "source_url": ""},
    ]  # fmt: skip
    wiki = [
        {"company_id": "doosan_enerbility", "gem_location_id": "L1", "plant_name": "P",
         "country": "VN", "role_tier2": "epc_unspecified", "share": "",
         "sentence": "Doosan built it", "source_url": "https://www.gem.wiki/P"},
        {"company_id": "doosan_enerbility", "gem_location_id": "L1", "plant_name": "P",
         "country": "VN", "role_tier2": "equipment_unspecified", "share": "",
         "sentence": "Doosan supplied the boilers", "source_url": "https://www.gem.wiki/P"},
    ]  # fmt: skip
    merged, domestic = agg.merge_registers(
        [], tracker, wiki, companies, vocab, exclude_home=True, company_ir=company_ir
    )
    assert domestic == 1  # Marubeni's Japanese unit is not a trade
    assert [
        (r["company_id"], r["role_tier1"], r["role_tier2"], r["origin"], r["share"]) for r in merged
    ] == [
        ("kepco", "equity_owner", "equity_direct", "company_ir", "0.4"),
        ("marubeni", "equity_owner", "equity_parent", "gem", "0.5"),
        ("doosan_enerbility", "epc_contractor", "epc_unspecified", "gem_wiki", ""),
        ("doosan_enerbility", "equipment_supplier", "equipment_unspecified", "gem_wiki", ""),
    ]
    # The tracker also states KEPCO's equity, at a lower standing: the row is not repeated, the
    # agreement is recorded instead.
    assert merged[0]["also_stated_by"] == "gem"


def test_two_scopes_of_one_tier1_role_are_one_row_with_both_scopes_named() -> None:
    """Sumitomo's civil works and port works at Matarbari are one EPC role, not two."""
    companies = {c["company_id"]: c for c in read(DATA / "companies" / "method" / "companies.csv")}
    vocab = {v["role_tier2"]: v for v in read(DATA / "roles" / "method" / "roles.csv")}
    base = {
        "company_id": "sumitomo_corp", "company_name": "Sumitomo Corporation",
        "company_country": "JP", "company_type": "trading_house", "gem_unit_id": "U1",
        "gem_location_id": "", "plant_name": "Matarbari", "country": "BD", "phase": "construction",
        "share": "", "share_basis": "contract_share", "from_year": "", "to_year": "",
        "source_url": "https://example.org", "source_note": "", "accessed_date": "2026-09-07",
    }  # fmt: skip
    company_ir = [
        {**base, "role_tier2": "epc_unspecified"},
        {**base, "role_tier2": "epc_civil_works"},
        {**base, "role_tier2": "epc_port_works"},
    ]
    merged, _ = agg.merge_registers([], [], [], companies, vocab, company_ir=company_ir)
    assert len(merged) == 1
    assert merged[0]["role_tier1"] == "epc_contractor"
    assert merged[0]["role_tier2"] == "epc_civil_works"  # a stated scope outranks *_unspecified
    assert merged[0]["role_tier2_all"] == "epc_unspecified|epc_civil_works|epc_port_works"


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
        "analysis_year": "2026", "lifetime_source": "default", "cf_source": "country_implied",
        "cf_low": "0.40", "cf_high": "0.75",
        "heat_rate_mj_per_kwh": "9.2308", "heat_rate_source": "default",
        "ef_kgco2_per_tj": "94600",
        "ef_basis": "ipcc_default",
        "biogenic": "no", "fuel_type": "coal", "fuel_id": "bituminous",
        "technology": "supercritical",
    }  # fmt: skip
    d = {"fuel_type": "coal", "technology_pattern": "super", "lifetime_years": "40",
         "lifetime_low_years": "30", "lifetime_high_years": "50", "capacity_factor": "0.55",
         "efficiency_lhv": "0.39",
         "efficiency_low_lhv": "0.363", "efficiency_high_lhv": "0.417"}  # fmt: skip
    bound = {"ef_low_kgco2_per_tj": "89500", "ef_high_kgco2_per_tj": "99700"}
    rows = sens.variants_for(unit, d, bound, grid)
    by = {(r["dimension"], r["variant"]): r for r in rows}
    dims = ("lifetime", "capacity_factor", "efficiency", "emission_factor")
    assert {k[0] for k in by} == set(dims)
    central = {by[(dim, "central")]["ti_lifetime_tco2"] for dim in dims}
    assert len(central) == 1  # one published value, restated identically on every dimension
    c = central.pop()
    for dim in dims:
        lo, hi = by[(dim, "low")]["ti_lifetime_tco2"], by[(dim, "high")]["ti_lifetime_tco2"]
        assert min(lo, hi) < c < max(lo, hi), dim
    assert by[("lifetime", "high")]["parameter"] == 50
    # A higher efficiency burns less fuel per kWh, so it lowers the emissions added.
    assert by[("efficiency", "high")]["ti_lifetime_tco2"] < c


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
    keys = [(r["company_id"], r["role_tier1"], r["scenario"]) for r in rows]
    assert len(keys) == len(set(keys))
    assert all(r["role_tier1"] and r["phase"] for r in rows)
