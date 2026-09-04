"""Step 5c — worldwide coverage: every company x destination in the sales files, priced or not.

The unit of analysis is a company's sales to every destination country (whitepaper Level 1,
operating-country basis); the reader filters destinations in the dashboard. This table shows,
for every destination that appears in a market-side sales file for the companies in scope, how
many units carry a result and why the rest do not, grouped the way the lead reads them:

    EU27      the 27 member states (priced through the EEA registrations)
    US        United States
    <home>    the company's own headquarters country from companies.csv (KR for Hyundai and
              Kia, JP for Toyota and Honda), flagged ``home_country = yes``
    IN        India
    others    every other country, and region-level rows the sources do not split by country

Source precedence per (company, destination, cohort year): market-side bases (registrations,
retail_sales, brand_total_sales, domestic_sales) are the cohort; plant-side ``plant_sales`` rows
are used only where no market-side file covers that company and destination at all, and are
labelled as such; ``export_shipments`` rows (Korea plant-side exports without a stated
destination) are never counted here — they serve the trade-flow reconciliation.

Inputs   sales/processed/sales_*.csv, sales/method/companies.csv,
         output/destination_parameters_*.csv, output/ti_by_model.csv, output/ti_withheld.csv
Output   output/ti_coverage.csv

Run from the repository root:  .venv/bin/python script/auto/model/build_coverage.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
SALES = DATA / "sales" / "processed"
COMPANIES = DATA / "sales" / "method" / "companies.csv"
DESTINATION_NOTES = DATA / "sales" / "method" / "destination_notes.csv"
OUT_DIR = DATA / "output"
OUT = OUT_DIR / "ti_coverage.csv"

EU27_MEMBERS = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
    "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}  # fmt: skip
NAMED_GROUPS = {"US": "US", "IN": "IN"}
MARKET_SIDE = {"registrations", "retail_sales", "brand_total_sales", "domestic_sales"}
PLANT_SIDE = {"plant_sales"}

FIELDS = [
    "company",
    "destination_group",
    "home_country",
    "destination",
    "destination_level",
    "cohort_year",
    "period",
    "basis",
    "units",
    "priced_units",
    "withheld_units",
    "status",
    "market",
    "source_file",
    "note",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def group_of(destination: str, level: str, home: str) -> str:
    """Destination group label for one sales row."""
    if level != "country":
        return "others"
    if destination in EU27_MEMBERS:
        return "EU27"
    if destination == home:
        return home
    return NAMED_GROUPS.get(destination, "others")


def main() -> None:
    """Join sales volumes to priced and withheld volumes per destination."""
    companies = {r["company"]: r for r in read_csv(COMPANIES)}
    in_scope = {c for c, r in companies.items() if r["in_scope"] == "yes"}
    dest_notes = (
        {r["destination"]: r["status_note"] for r in read_csv(DESTINATION_NOTES)}
        if DESTINATION_NOTES.exists()
        else {}
    )
    benchmark_market: dict[str, str] = {}
    for path in sorted(OUT_DIR.glob("destination_parameters_*.csv")):
        for r in read_csv(path):
            benchmark_market[r["country"]] = r["market"]

    Key = tuple[str, str, str, int, str, str, str]
    sales: dict[Key, int] = defaultdict(int)
    market_side_covered: set[tuple[str, str]] = set()
    for path in sorted(SALES.glob("sales_*.csv")):
        for r in read_csv(path):
            if r["company"] not in in_scope or r["basis"] not in MARKET_SIDE | PLANT_SIDE:
                continue
            key = (
                r["company"],
                r["destination"],
                r["destination_level"],
                int(r["cohort_year"]),
                r["period"],
                r["basis"],
                r["source_file"],
            )
            sales[key] += int(r["units"])
            if r["basis"] in MARKET_SIDE:
                market_side_covered.add((r["company"], r["destination"]))

    priced: dict[tuple[str, str, int], int] = defaultdict(int)
    scenarios_seen: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    by_model = read_csv(OUT_DIR / "ti_by_model.csv")
    for r in by_model:
        scenarios_seen[(r["company"], r["destination"], int(r["cohort_year"]))].add(r["scenario"])
    for r in by_model:
        key = (r["company"], r["destination"], int(r["cohort_year"]))
        if r["scenario"] == min(scenarios_seen[key]):
            priced[key] += int(r["units"])
    withheld: dict[tuple[str, str, int], int] = defaultdict(int)
    reasons: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    for r in read_csv(OUT_DIR / "ti_withheld.csv"):
        key = (r["company"], r["destination"], int(r["cohort_year"]))
        withheld[key] += int(r["units"])
        reasons[key].add(r["reason"].split(":")[0][:60])

    out: list[dict[str, object]] = []
    for (company, dest, level, year, period, basis, source_file), units in sorted(sales.items()):
        home = companies[company]["country"]
        key = (company, dest, year)
        p, w = priced.get(key, 0), withheld.get(key, 0)
        if basis in PLANT_SIDE and (company, dest) in market_side_covered:
            continue  # a market-side file covers this destination; the plant file is reconciliation
        if basis in PLANT_SIDE:
            status = "plant_side_only"
            note = (dest_notes.get(dest, "") + "; " if dest in dest_notes else "") + (
                "only a plant-side source covers this destination: units built at the local plant "
                "and sold there; imports from other plants are not in the source"
            )
            if dest in benchmark_market:
                note += "; benchmark exists but plant-side volumes are not priced"
        elif level == "region":
            status = "region_unpriced"
            note = "sales source reports a region; a country benchmark cannot be applied"
        elif level == "unknown":
            status = "destination_unknown"
            note = "sales without a stated destination"
        elif dest not in benchmark_market:
            status = "no_benchmark"
            note = dest_notes.get(dest, "no destination benchmark built yet for this country")
        elif p == 0 and w > 0:
            status, note = "withheld", "; ".join(sorted(reasons[key]))
        elif p == 0:
            status, note = (
                "not_in_cohort",
                "destination priced elsewhere; this file is not a cohort source",
            )
        else:
            status, note = "priced", "; ".join(sorted(reasons[key])) if w else ""
        out.append(
            {
                "company": company,
                "destination_group": group_of(dest, level, home),
                "home_country": "yes" if dest == home else "no",
                "destination": dest,
                "destination_level": level,
                "cohort_year": year,
                "period": period,
                "basis": basis,
                "units": units,
                "priced_units": p if status == "priced" else 0,
                "withheld_units": w if status in {"priced", "withheld"} else 0,
                "status": status,
                "market": benchmark_market.get(dest, ""),
                "source_file": source_file,
                "note": note,
            }
        )
    with OUT.open("w", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=FIELDS)
        wri.writeheader()
        wri.writerows(out)
    by_group: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for r in out:
        g = by_group[(str(r["company"]), str(r["destination_group"]))]
        g[0] += int(str(r["units"]))
        g[1] += int(str(r["priced_units"]))
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rows; priced/units by company and group "
        + ", ".join(f"{c} {g} {p:,}/{u:,}" for (c, g), (u, p) in sorted(by_group.items()))
    )


if __name__ == "__main__":
    main()
