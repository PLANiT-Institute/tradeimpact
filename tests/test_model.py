"""Numerical checks on the published model outputs (run after the pipeline).

Analytical: the lifetime sum of a constant-vs-exponential gap has a closed form,
    sum_{t=0}^{T-1} (E_ref0 (1-r)^t - E_prod) = E_ref0 (1-(1-r)^T)/r - T E_prod,
so every ICE/HEV cell in ti_by_model must satisfy it from its own published year-0 values.
Consistency: the annual flow summed over years equals the cell totals; company x market totals
equal the country and powertrain sums; sales totals equal the snapshot totals; covered plus
withheld equals the source volume in every market; every excluded scenario is published.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data" / "auto"
OUT = DATA / "output"
SALES = DATA / "sales" / "processed"
SALES_RAW = DATA / "sales" / "raw"
EU27, US, KR = "EU27", "US", "KR"
#: Processed sales files behind the US market cohort, and the destination they contribute.
US_SALES_FILES = ("sales_hyundai_us.csv", "sales_kia_us.csv", "sales_kia_ir_2026.csv")
#: Processed sales files behind the Korea market cohort (destination KR rows).
KR_SALES_FILES = ("sales_hyundai_kr.csv", "sales_kia_ir_2026.csv")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def in_scope_companies() -> set[str]:
    """Companies flagged in scope in sales/method/companies.csv."""
    return {
        r["company"]
        for r in rows(SALES.parent / "method" / "companies.csv")
        if r["in_scope"] == "yes"
    }


@pytest.fixture(scope="module")
def cells() -> list[dict[str, str]]:
    return rows(OUT / "ti_by_model.csv")


@pytest.fixture(scope="module")
def company_rows() -> list[dict[str, str]]:
    return [r for r in rows(OUT / "ti_company.csv") if r["status"] == "reported"]


@pytest.fixture(scope="module")
def rates() -> dict[tuple[str, str, str], float]:
    """(market, country, scenario) -> r_fleet, read off the year-0 trajectory row."""
    out: dict[tuple[str, str, str], float] = {}
    for path in sorted(OUT.glob("reference_trajectories_*.csv")):
        for r in rows(path):
            if r["t"] == "0":
                out[(r["market"], r["country"], r["scenario"])] = float(r["r_fleet"])
    return out


def covered_units(cells: list[dict[str, str]], market: str) -> dict[str, int]:
    """Company -> units carrying a result in ``market`` (units are scenario-invariant)."""
    scenarios = sorted({c["scenario"] for c in cells if c["market"] == market})
    out: dict[str, int] = defaultdict(int)
    for c in cells:
        if c["market"] == market and c["scenario"] == scenarios[0]:
            out[c["company"]] += int(c["units"])
    return out


def withheld_units(market: str) -> dict[str, int]:
    """Company -> units withheld in ``market``."""
    out: dict[str, int] = defaultdict(int)
    for r in rows(OUT / "ti_withheld.csv"):
        if r["market"] == market:
            out[r["company"]] += int(r["units"])
    return out


def test_ice_hev_cells_match_closed_form(
    cells: list[dict[str, str]], rates: dict[tuple[str, str, str], float]
) -> None:
    checked = 0
    for c in cells:
        if c["powertrain"] not in ("ICE", "HEV"):
            continue
        r = rates[(c["market"], c["destination"], c["scenario"])]
        T = int(c["lifetime_years"])
        e_ref0, e_prod = float(c["e_ref_year0_kgco2e"]), float(c["e_prod_year0_kgco2e"])
        geometric = T if abs(r) < 1e-15 else (1 - (1 - r) ** T) / r
        expected = e_ref0 * geometric - T * e_prod
        # year-0 values are published to 4 dp; a T-term sum inherits at most T * 1e-4 of that
        assert abs(float(c["ti_per_vehicle_kgco2e"]) - expected) <= 2e-4 * T + 1e-6, c
        checked += 1
    assert checked > 1000


def test_annual_flow_equals_cell_totals(cells: list[dict[str, str]]) -> None:
    by_cells: dict[tuple[str, str, str, str], float] = defaultdict(float)
    for c in cells:
        by_cells[(c["company"], c["market"], c["cohort_year"], c["scenario"])] += float(
            c["ti_tco2e"]
        )
    by_annual: dict[tuple[str, str, str, str], float] = defaultdict(float)
    for r in rows(OUT / "ti_annual.csv"):
        by_annual[(r["company"], r["market"], r["cohort_year"], r["scenario"])] += float(
            r["ti_tco2e"]
        )
    assert by_cells.keys() == by_annual.keys()
    for key, total in by_cells.items():
        assert abs(by_annual[key] - total) <= 1e-6 * max(1.0, abs(total)), key


def test_company_totals_equal_country_and_powertrain_sums(
    company_rows: list[dict[str, str]],
) -> None:
    company = {
        (r["company"], r["market"], r["cohort_year"], r["scenario"]): float(r["ti_tco2e"])
        for r in company_rows
    }
    for name in ("ti_country.csv", "ti_powertrain.csv"):
        sums: dict[tuple[str, str, str, str], float] = defaultdict(float)
        for r in rows(OUT / name):
            sums[(r["company"], r["market"], r["cohort_year"], r["scenario"])] += float(
                r["ti_tco2e"]
            )
        assert sums.keys() == company.keys(), name
        for key, total in company.items():
            assert abs(sums[key] - total) <= 1e-9 * max(1.0, abs(total)), (name, key)
    assert all(r["decomposition_identity_holds"] == "True" for r in company_rows)


def test_markets_are_never_summed_together(company_rows: list[dict[str, str]]) -> None:
    """Each published company row belongs to exactly one market."""
    assert {r["market"] for r in company_rows} == {EU27, US, KR}
    for r in company_rows:
        assert r["market"] in (EU27, US, KR)


def test_sales_totals_match_snapshots() -> None:
    sales: dict[str, int] = defaultdict(int)
    for r in rows(SALES / "sales_eea_eu27_2024.csv"):
        sales[r["company"]] += int(r["units"])
    for path in SALES_RAW.glob("eea_*_final.json"):
        snap = json.loads(path.read_text())
        brand = snap["brand_filter"].split("=", 1)[1].lower()
        if brand not in sales:
            continue  # pinned but out of scope
        assert sales[brand] == int(snap["response"]["aggregations"]["registrations"]["value"]), (
            brand
        )


def test_eu27_covered_plus_withheld_equals_registrations(cells: list[dict[str, str]]) -> None:
    covered, withheld = covered_units(cells, EU27), withheld_units(EU27)
    sales: dict[str, int] = defaultdict(int)
    for r in rows(SALES / "sales_eea_eu27_2024.csv"):
        sales[r["company"]] += int(r["units"])
    assert sales
    for company, units in sales.items():
        assert covered[company] + withheld[company] == units, company


def test_us_covered_plus_withheld_equals_sales(cells: list[dict[str, str]]) -> None:
    covered, withheld = covered_units(cells, US), withheld_units(US)
    sales: dict[str, int] = defaultdict(int)
    for name in US_SALES_FILES:
        for r in rows(SALES / name):
            if r["destination"] == US and r["company"] in in_scope_companies():
                sales[r["company"]] += int(r["units"])
    assert sales
    for company, units in sales.items():
        assert covered[company] + withheld[company] == units, company


def test_cohorts_cover_every_sales_row_exactly_once() -> None:
    """Central cohort units plus step-3a withheld units equal the source volume, per market."""
    cohorts: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows(OUT / "cohorts.csv"):
        if r["variant"] == "central":
            cohorts[(r["market"], r["company"])] += int(r["units"])
    for r in rows(OUT / "cohorts_withheld.csv"):
        cohorts[(r["market"], r["company"])] += int(r["units"])
    source: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows(SALES / "sales_eea_eu27_2024.csv"):
        source[(EU27, r["company"])] += int(r["units"])
    in_scope = {
        r["company"]
        for r in rows(SALES.parent / "method" / "companies.csv")
        if r["in_scope"] == "yes"
    }
    for name in US_SALES_FILES:
        for r in rows(SALES / name):
            if r["destination"] == US and r["company"] in in_scope:
                source[(US, r["company"])] += int(r["units"])
    for name in KR_SALES_FILES:
        for r in rows(SALES / name):
            if r["destination"] == KR and r["company"] in in_scope:
                source[(KR, r["company"])] += int(r["units"])
    assert cohorts == source


def test_real_world_factor_matches_the_test_cycle_lookup(cells: list[dict[str, str]]) -> None:
    """The correction is keyed on (test cycle, powertrain); EPA label values carry 1.0."""
    lookup = {
        (r["test_cycle"], r["powertrain"]): float(r["factor"])
        for r in rows(DATA / "vehicle_technology" / "method" / "real_world_correction.csv")
    }
    assert lookup[("EPA", "ICE")] == 1.0
    for c in cells:
        assert float(c["real_world_factor"]) == lookup[(c["test_cycle"], c["powertrain"])], c


def test_excluded_scenarios_are_published_not_silent(cells: list[dict[str, str]]) -> None:
    """Every scenario a market excludes appears in ti_exclusions and in ti_company."""
    excluded: dict[str, set[str]] = defaultdict(set)
    for path in sorted(OUT.glob("destination_parameters_*.csv")):
        for r in rows(path):
            excluded[r["market"]] |= {s for s in r["scenarios_excluded"].split(";") if s}
    assert excluded[US] == {"S2"}
    exclusions = rows(OUT / "ti_exclusions.csv")
    company_table = rows(OUT / "ti_company.csv")
    for market, scenarios in excluded.items():
        companies = {c["company"] for c in cells if c["market"] == market}
        for scenario in scenarios:
            for company in companies:
                assert any(
                    (e["market"], e["company"], e["scenario"]) == (market, company, scenario)
                    and e["reason"]
                    for e in exclusions
                ), (market, company, scenario)
                assert any(
                    (r["market"], r["company"], r["scenario"]) == (market, company, scenario)
                    and r["status"] == "excluded"
                    and r["exclusion_reason"]
                    for r in company_table
                ), (market, company, scenario)
            assert not any(c["market"] == market and c["scenario"] == scenario for c in cells), (
                market,
                scenario,
            )


def test_sensitivity_central_equals_the_published_total(company_rows: list[dict[str, str]]) -> None:
    """Every sensitivity dimension's central variant reproduces the headline cohort total."""
    published = {
        (r["company"], r["market"], r["cohort_year"], r["scenario"]): float(r["ti_tco2e"])
        for r in company_rows
    }
    checked = 0
    for r in rows(OUT / "ti_sensitivity.csv"):
        if r["variant"] != "central":
            continue
        key = (r["company"], r["market"], r["cohort_year"], r["scenario"])
        assert abs(float(r["ti_tco2e"]) - published[key]) <= 0.1 + 1e-6 * abs(published[key]), r
        checked += 1
    assert checked > 0


def test_annual_by_model_sums_to_company_annual_flow() -> None:
    """The year-by-year cell table aggregates exactly to the company x market x scenario flow."""
    by_cells: dict[tuple[str, str, str, str, str], float] = defaultdict(float)
    for r in rows(OUT / "ti_annual_by_model.csv"):
        key = (r["market"], r["company"], r["cohort_year"], r["scenario"], r["calendar_year"])
        by_cells[key] += float(r["ti_tco2e"])
    flow = {
        (r["market"], r["company"], r["cohort_year"], r["scenario"], r["calendar_year"]): float(
            r["ti_tco2e"]
        )
        for r in rows(OUT / "ti_annual.csv")
    }
    assert by_cells.keys() == flow.keys()
    for key, total in flow.items():
        assert abs(by_cells[key] - total) <= 1e-6 * max(1.0, abs(total)), key


TIERS = {"A", "B", "C"}


def test_every_result_cell_declares_its_tiers(cells: list[dict[str, str]]) -> None:
    """Whitepaper §5.2: Layer 1 and Layer 2 tiers on every reported cell, worst of both as tier."""
    order = {"A": 0, "B": 1, "C": 2}
    for c in cells:
        assert c["layer1_tier"] in TIERS and c["layer2_tier"] in TIERS, c
        assert c["tier"] == max(c["layer1_tier"], c["layer2_tier"], key=lambda t: order[t]), c
        for col in ("vkt_tier", "fleet_intensity_tier", "grid_tier", "lifetime_tier", "rate_tier"):
            assert c[col] in TIERS, (col, c)


def test_database_flags_every_input_value_with_a_tier() -> None:
    """Every processed input table the model reads carries a tier on every row in the database."""
    import sqlite3

    conn = sqlite3.connect(DATA / "database" / "tradeimpact_auto.sqlite")
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT \"table\" FROM tables WHERE kind = 'processed' AND ("
            "\"table\" LIKE 'country_emissions_%' OR \"table\" LIKE 'vehicle_usage_%' OR "
            "\"table\" LIKE 'emission_targets_%' OR \"table\" LIKE 'vehicle_technology_%' OR "
            "\"table\" LIKE 'sales_%')"
        )
    ]
    assert tables
    for name in tables:
        columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')}
        assert "tier" in columns, name
        missing = conn.execute(
            f"SELECT COUNT(*) FROM \"{name}\" WHERE tier IS NULL OR tier NOT IN ('A', 'B', 'C')"
        ).fetchone()[0]
        assert missing == 0, (name, missing)
    conn.close()
