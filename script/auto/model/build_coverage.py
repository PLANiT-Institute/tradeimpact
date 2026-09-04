"""Step 5c — worldwide coverage: every company x destination in the sales files, priced or not.

The unit of analysis is a company's sales to every destination country (whitepaper Level 1,
operating-country basis); a reader then filters destinations in the dashboard. This table shows,
for every destination that appears in any processed sales file for the companies in scope, how
many units carry a result and why the rest do not.

Inputs   sales/processed/sales_*.csv, sales/method/companies.csv,
         output/destination_parameters_*.csv, output/ti_by_model.csv, output/ti_withheld.csv
Output   output/ti_coverage.csv — company x destination x destination_level x cohort_year x basis

status values
    priced             the destination has a benchmark and the units carry a result
    withheld           benchmark exists; units withheld in the cohort or impact step (reason given)
    no_benchmark       destination is a country but no benchmark has been built for it yet
    region_unpriced    the sales source reports a region, not a country (cannot be priced)
    destination_unknown  the sales source does not state the destination (plant-side exports)

Run from the repository root:  .venv/bin/python script/auto/model/build_coverage.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
SALES = DATA / "sales" / "processed"
SCOPE = DATA / "sales" / "method" / "companies.csv"
OUT_DIR = DATA / "output"
OUT = OUT_DIR / "ti_coverage.csv"

FIELDS = [
    "company",
    "destination",
    "destination_level",
    "cohort_year",
    "basis",
    "units",
    "priced_units",
    "withheld_units",
    "status",
    "market",
    "note",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    """Join sales volumes to priced and withheld volumes per destination."""
    in_scope = {r["company"] for r in read_csv(SCOPE) if r["in_scope"] == "yes"}
    benchmark_market: dict[str, str] = {}
    for path in sorted(OUT_DIR.glob("destination_parameters_*.csv")):
        for r in read_csv(path):
            benchmark_market[r["country"]] = r["market"]

    sales: dict[tuple[str, str, str, int, str], int] = defaultdict(int)
    for path in sorted(SALES.glob("sales_*.csv")):
        for r in read_csv(path):
            if r["company"] not in in_scope:
                continue
            key = (
                r["company"],
                r["destination"],
                r["destination_level"],
                int(r["cohort_year"]),
                r["basis"],
            )
            sales[key] += int(r["units"])

    priced: dict[tuple[str, str, int], int] = defaultdict(int)
    scenarios_seen: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    for r in read_csv(OUT_DIR / "ti_by_model.csv"):
        key = (r["company"], r["destination"], int(r["cohort_year"]))
        scenarios_seen[key].add(r["scenario"])
    for r in read_csv(OUT_DIR / "ti_by_model.csv"):
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
    for (company, dest, level, year, basis), units in sorted(sales.items()):
        key = (company, dest, year)
        p, w = priced.get(key, 0), withheld.get(key, 0)
        if level == "region":
            status, note = (
                "region_unpriced",
                "sales source reports a region; a country benchmark cannot be applied",
            )
        elif level == "unknown":
            status, note = "destination_unknown", "plant-side sales without a stated destination"
        elif dest not in benchmark_market:
            status, note = "no_benchmark", "no destination benchmark built yet for this country"
        elif p == 0 and w > 0:
            status, note = "withheld", "; ".join(sorted(reasons[key]))
        else:
            status, note = "priced", "; ".join(sorted(reasons[key])) if w else ""
        out.append(
            {
                "company": company,
                "destination": dest,
                "destination_level": level,
                "cohort_year": year,
                "basis": basis,
                "units": units,
                "priced_units": p,
                "withheld_units": w,
                "status": status,
                "market": benchmark_market.get(dest, ""),
                "note": note,
            }
        )
    with OUT.open("w", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=FIELDS)
        wri.writeheader()
        wri.writerows(out)
    by_status: dict[str, int] = defaultdict(int)
    for r in out:
        by_status[str(r["status"])] += int(str(r["units"]))
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rows; units by status "
        + ", ".join(f"{k} {v:,}" for k, v in sorted(by_status.items()))
    )


if __name__ == "__main__":
    main()
