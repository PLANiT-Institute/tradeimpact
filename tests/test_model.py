"""Numerical checks on the published model outputs (run after the pipeline).

Analytical: the lifetime sum of a constant-vs-exponential gap has a closed form,
    sum_{t=0}^{T-1} (E_ref0 (1-r)^t - E_prod) = E_ref0 (1-(1-r)^T)/r - T E_prod,
so every ICE/HEV cell in ti_by_model must satisfy it from its own published year-0 values.
Consistency: the annual flow summed over years equals the cell totals; company totals equal
the country and powertrain sums; sales totals equal the snapshot totals.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "auto" / "output"
SALES_RAW = REPO / "data" / "auto" / "sales" / "raw"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def cells() -> list[dict[str, str]]:
    return rows(OUT / "ti_by_model_eu27.csv")


@pytest.fixture(scope="module")
def rates() -> dict[tuple[str, str], float]:
    return {
        (r["country"], r["scenario"]): float(r["r_fleet"])
        for r in rows(OUT / "reference_trajectories_eu27.csv")
        if r["t"] == "0"
    }


def test_ice_hev_cells_match_closed_form(cells, rates) -> None:
    checked = 0
    for c in cells:
        if c["powertrain"] not in ("ICE", "HEV"):
            continue
        r = rates[(c["destination"], c["scenario"])]
        T = int(c["lifetime_years"])
        e_ref0, e_prod = float(c["e_ref_year0_kgco2e"]), float(c["e_prod_year0_kgco2e"])
        geometric = T if abs(r) < 1e-15 else (1 - (1 - r) ** T) / r
        expected = e_ref0 * geometric - T * e_prod
        # year-0 values are published to 4 dp; a T-term sum inherits at most T * 1e-4 of that
        assert abs(float(c["ti_per_vehicle_kgco2e"]) - expected) <= 2e-4 * T + 1e-6, c
        checked += 1
    assert checked > 1000


def test_annual_flow_equals_cell_totals(cells) -> None:
    by_cells: dict[tuple[str, str], float] = defaultdict(float)
    for c in cells:
        by_cells[(c["company"], c["scenario"])] += float(c["ti_tco2e"])
    by_annual: dict[tuple[str, str], float] = defaultdict(float)
    for r in rows(OUT / "ti_annual_eu27.csv"):
        by_annual[(r["company"], r["scenario"])] += float(r["ti_tco2e"])
    for key, total in by_cells.items():
        assert abs(by_annual[key] - total) <= 1e-6 * max(1.0, abs(total)), key


def test_company_totals_equal_country_and_powertrain_sums() -> None:
    company = {
        (r["company"], r["scenario"]): float(r["ti_tco2e"])
        for r in rows(OUT / "ti_company_eu27.csv")
    }
    for name in ("ti_country_eu27.csv", "ti_powertrain_eu27.csv"):
        sums: dict[tuple[str, str], float] = defaultdict(float)
        for r in rows(OUT / name):
            sums[(r["company"], r["scenario"])] += float(r["ti_tco2e"])
        for key, total in company.items():
            assert abs(sums[key] - total) <= 1e-9 * max(1.0, abs(total)), (name, key)
    assert all(
        r["decomposition_identity_holds"] == "True" for r in rows(OUT / "ti_company_eu27.csv")
    )


def test_sales_totals_match_snapshots() -> None:
    sales: dict[str, int] = defaultdict(int)
    for r in rows(REPO / "data" / "auto" / "sales" / "processed" / "sales_eea_eu27_2024.csv"):
        sales[r["company"]] += int(r["units"])
    for path in SALES_RAW.glob("eea_*_final.json"):
        snap = json.loads(path.read_text())
        brand = snap["brand_filter"].split("=", 1)[1].lower()
        if brand not in sales:
            continue  # pinned but out of scope
        assert sales[brand] == int(snap["response"]["aggregations"]["registrations"]["value"]), (
            brand
        )


def test_covered_plus_withheld_equals_registrations(cells) -> None:
    covered: dict[str, int] = defaultdict(int)
    for c in cells:
        if c["scenario"] == "S1":
            covered[c["company"]] += int(c["units"])
    withheld: dict[str, int] = defaultdict(int)
    for r in rows(OUT / "ti_withheld_eu27.csv"):
        withheld[r["company"]] += int(r["units"])
    sales: dict[str, int] = defaultdict(int)
    for r in rows(REPO / "data" / "auto" / "sales" / "processed" / "sales_eea_eu27_2024.csv"):
        sales[r["company"]] += int(r["units"])
    for company, units in sales.items():
        assert covered[company] + withheld[company] == units, company
