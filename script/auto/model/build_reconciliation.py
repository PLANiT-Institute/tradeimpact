"""Step 5d — every sales source held for the same company, destination and year, side by side.

A company's own figures differ between its publications: a market-side release counts what was
sold in the country, a plant-side release counts what its factories there shipped, and an
investor release may fold a second brand in. This table puts them next to each other so the
spread is visible rather than assumed, and marks which file the cohort was actually built from.

Input    sales/processed/sales_*.csv, sales/method/companies.csv
Output   output/ti_source_reconciliation.csv

    basis_side          market (registrations, retail, brand total, domestic sales) or plant
    used_by_cohort      yes where this file feeds the priced cohort for that market
    spread_vs_used_pct  difference from the used file, market-side sources only; blank where the
                        bases are not comparable

Run from the repository root:  .venv/bin/python script/auto/model/build_reconciliation.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
SALES = DATA / "sales" / "processed"
COMPANIES = DATA / "sales" / "method" / "companies.csv"
RAW_FILES = DATA / "registry" / "raw_files.csv"
CROSS_CHECK = DATA / "sales" / "raw" / "company_us_totals_cross_check.csv"
OUT = DATA / "output" / "ti_source_reconciliation.csv"

MARKET_SIDE = {"registrations", "retail_sales", "brand_total_sales", "domestic_sales"}
PLANT_SIDE = {"plant_sales", "export_shipments"}
#: The processed file each market's cohort is built from (build_cohorts.py).
COHORT_FILES = {
    "EU27": {"sales_eea_eu27_2024.csv"},
    "US": {
        "sales_hyundai_us.csv",
        "sales_kia_us.csv",
        "sales_kia_ir_2026.csv",
        "sales_toyota_us.csv",
        "sales_nissan_us.csv",
    },
    "KR": {"sales_hyundai_kr.csv", "sales_kia_ir_2026.csv"},
}
EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
    "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}  # fmt: skip
FIELDS = [
    "company",
    "destination",
    "cohort_year",
    "source_id",
    "source_file",
    "basis",
    "basis_side",
    "units",
    "in_scope",
    "boundary_companies",
    "used_by_cohort",
    "spread_vs_used_pct",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def source_ids_by_raw_file() -> dict[str, str]:
    """raw file name -> source_id, to fill the id for the sales tables that omit the column."""
    return {r["file"]: r["source_id"] for r in read_csv(RAW_FILES)}


def market_of(destination: str) -> str:
    """Which market's cohort a destination belongs to."""
    if destination in EU27:
        return "EU27"
    return destination


def main() -> None:
    """Write one row per company x destination x year x source file."""
    in_scope = {r["company"] for r in read_csv(COMPANIES) if r["in_scope"] == "yes"}
    by_raw_file = source_ids_by_raw_file()
    totals: dict[tuple[str, str, int, str, str, str], int] = defaultdict(int)
    for path in sorted(SALES.glob("sales_*.csv")):
        for r in read_csv(path):
            if r["destination_level"] != "country":
                continue
            key = (
                r["company"],
                r["destination"],
                int(r["cohort_year"]),
                r.get("source_id") or by_raw_file.get(r["source_file"], ""),
                path.name,
                r["basis"],
            )
            totals[key] += int(r["units"])

    # A second figure the same company published for the same cell, hand-transcribed with its
    # URL, so the spread between a company's own publications is a number and not a claim.
    boundaries: dict[tuple[str, str, int], str] = {}
    for r in read_csv(CROSS_CHECK):
        boundaries[(r["company"], r["destination"], int(r["cohort_year"]))] = r[
            "boundary_companies"
        ]
        key = (
            r["company"],
            r["destination"],
            int(r["cohort_year"]),
            "company_us_totals_cross_check",
            CROSS_CHECK.name,
            r["basis"],
        )
        totals[key] += int(r["units"])

    rows: list[dict[str, object]] = []
    for (company, destination, year, source_id, source_file, basis), units in sorted(
        totals.items()
    ):
        side = "market" if basis in MARKET_SIDE else "plant" if basis in PLANT_SIDE else "other"
        used = source_file in COHORT_FILES.get(market_of(destination), set())
        rows.append(
            {
                "company": company,
                "destination": destination,
                "cohort_year": year,
                "source_id": source_id,
                "source_file": source_file,
                "basis": basis,
                "basis_side": side,
                "units": units,
                "in_scope": "yes" if company in in_scope else "no",
                "boundary_companies": boundaries.get((company, destination, year), ""),
                "used_by_cohort": "yes" if used else "no",
                "spread_vs_used_pct": None,
            }
        )

    used_units: dict[tuple[str, str, int], int] = {}
    for r in rows:
        if r["used_by_cohort"] == "yes" and r["basis_side"] == "market":
            key = (str(r["company"]), str(r["destination"]), int(str(r["cohort_year"])))
            used_units[key] = used_units.get(key, 0) + int(str(r["units"]))
    for r in rows:
        # A group figure covers brands the cohort holds apart (Lexus from Toyota, Infiniti from
        # Nissan, Genesis from Hyundai), so it is compared against the same set of brands.
        brands = str(r["boundary_companies"]).split(";") if r["boundary_companies"] else []
        if not brands or r["used_by_cohort"] == "yes" or r["basis_side"] != "market":
            continue
        reference = sum(
            used_units.get((brand, str(r["destination"]), int(str(r["cohort_year"]))), 0)
            for brand in brands
        )
        if reference:
            r["spread_vs_used_pct"] = round(100.0 * (int(str(r["units"])) / reference - 1), 3)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    compared = [r for r in rows if r["spread_vs_used_pct"] is not None]
    worst = max((abs(float(str(r["spread_vs_used_pct"]))) for r in compared), default=0.0)
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} source rows; {len(compared)} market-side "
        f"comparisons, widest spread {worst:.2f} %"
    )


if __name__ == "__main__":
    main()
