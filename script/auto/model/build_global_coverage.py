"""Step 5e — how much of each company's worldwide sales the assessed markets actually capture.

Inputs
    sales/processed/global_sales_totals.csv   the company's own worldwide figure for that year
    sales/processed/sales_*.csv               every sales row held, market-side
    output/ti_by_model.csv                    the units that carry a result
    sales/method/companies.csv                which brands are in scope
Output
    output/ti_global_coverage.csv

    global_units            the company's worldwide sales, and the brands that figure covers
    assessed_units            units carrying a result, in the markets with a benchmark
    assessed_share_of_global  assessed_units / global_units
    held_units              every unit held for those brands, assessed or not
    held_share_of_global    held_units / global_units

Read the two shares together. The assessed share is what the result speaks for; the held share is
how far the data reaches. The gap between them is the sales we have but cannot yet price, market
by market, which ``ti_coverage.csv`` lists by destination.

A group figure covers brands the cohorts hold apart (Lexus from Toyota, Infiniti from Nissan,
Genesis from Hyundai). Those brands' units are counted in ``held_units`` and named in
``brands_out_of_scope``, so a share is never quietly measured against a wider denominator.

Run from the repository root:  .venv/bin/python script/auto/model/build_global_coverage.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
SALES = DATA / "sales" / "processed"
GLOBAL_TOTALS = SALES / "global_sales_totals.csv"
COMPANIES = DATA / "sales" / "method" / "companies.csv"
CELLS = DATA / "output" / "ti_by_model.csv"
OUT = DATA / "output" / "ti_global_coverage.csv"

MARKET_SIDE = {"registrations", "retail_sales", "brand_total_sales", "domestic_sales"}
FIELDS = [
    "company",
    "cohort_year",
    "global_units",
    "global_basis",
    "global_derived",
    "brands_in_denominator",
    "brands_out_of_scope",
    "assessed_units",
    "assessed_share_of_global",
    "assessed_markets",
    "assessed_countries",
    "held_units",
    "held_share_of_global",
    "source_id",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    """Write one row per company and cohort year that has a worldwide figure."""
    in_scope = {r["company"] for r in read_csv(COMPANIES) if r["in_scope"] == "yes"}

    held: dict[tuple[str, int], int] = defaultdict(int)
    for path in sorted(SALES.glob("sales_*.csv")):
        for r in read_csv(path):
            if r["basis"] not in MARKET_SIDE:
                continue
            held[(r["company"], int(r["cohort_year"]))] += int(r["units"])

    cells = read_csv(CELLS)
    first_scenario: dict[tuple[str, int], str] = {}
    for c in cells:
        key = (c["company"], int(c["cohort_year"]))
        scenario = c["scenario"]
        if key not in first_scenario or scenario < first_scenario[key]:
            first_scenario[key] = scenario
    assessed: dict[tuple[str, int], int] = defaultdict(int)
    markets: dict[tuple[str, int], set[str]] = defaultdict(set)
    countries: dict[tuple[str, int], set[str]] = defaultdict(set)
    for c in cells:
        key = (c["company"], int(c["cohort_year"]))
        if c["scenario"] != first_scenario[key]:
            continue
        assessed[key] += int(c["units"])
        markets[key].add(c["market"])
        countries[key].add(c["destination"])

    rows: list[dict[str, object]] = []
    for g in read_csv(GLOBAL_TOTALS):
        company, year = g["company"], int(g["cohort_year"])
        if company not in in_scope:
            continue
        key = (company, year)
        total = int(g["units"])
        brands = [b for b in g["brands_covered"].split(";") if b]
        held_units = sum(held.get((brand, year), 0) for brand in brands)
        assessed_units = assessed.get(key, 0)
        if not assessed_units and not held_units:
            continue
        rows.append(
            {
                "company": company,
                "cohort_year": year,
                "global_units": total,
                "global_basis": g["basis"],
                "global_derived": g["derived"],
                "brands_in_denominator": g["brands_covered"],
                "brands_out_of_scope": ";".join(b for b in brands if b not in in_scope),
                "assessed_units": assessed_units,
                "assessed_share_of_global": round(assessed_units / total, 6) if total else None,
                "assessed_markets": ";".join(sorted(markets.get(key, set()))),
                "assessed_countries": len(countries.get(key, set())),
                "held_units": held_units,
                "held_share_of_global": round(held_units / total, 6) if total else None,
                "source_id": g["source_id"],
            }
        )
    rows.sort(key=lambda r: (str(r["company"]), int(str(r["cohort_year"]))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print(
            f"{r['company']} {r['cohort_year']}: assessed "
            f"{float(str(r['assessed_share_of_global'])):.1%} of {int(str(r['global_units'])):,} "
            f"worldwide, held {float(str(r['held_share_of_global'])):.1%} "
            f"({r['assessed_countries']} countries assessed in {r['assessed_markets']})"
        )
    print(f"{OUT.relative_to(REPO)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
