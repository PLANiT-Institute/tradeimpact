"""Step 1 — the target set, with guideline §6.3's market-selection criteria evaluated on it.

The unit of analysis is fixed here and nowhere else: which exporter, sold into which market, in
which cohort year, over what operating life. The guideline does not merely ask for that list —
it sets four tests a market selection has to pass (§6.3), and this table answers each of them
from the data rather than asserting them. A criterion that fails is written down as failing.

Inputs
    sales/method/companies.csv                 exporters and whether they are in scope
    sales/method/destination_notes.csv         markets held but not built, and why
    output/ti_company.csv                      the assessed company x market x cohort rows
    output/ti_coverage.csv                     units held per company x destination, assessed or not
    output/ti_global_coverage.csv              the assessed share of each company's worldwide sales
    output/destination_parameters_*.csv        operating life and grid intensity per destination
    output/cohorts.csv                         the sales basis and period behind each cohort
    emission_targets/processed/*.csv           whether the market has a committed path at all
Output
    output/target_set.csv

The four criteria, and how each is answered here:

    6.3-1  markets ranked by volume        `volume_rank` within the company's assessed set
    6.3-2  >= 70 % of global sales, >= 3   `share_of_global` and `markets_assessed`
    6.3-3  one high- and one low-grid      `grid_spread`, the ratio of the highest assessed
                                           destination's grid intensity to the lowest
    6.3-4  per market: (a) a submitted target, (b) grid data, (c) an accessible registration
           database                        `target_level`, `grid_source`, `registration_database`

Two of those need a rule the guideline does not give, and both rules are ours and say so:

    §6.3-3 names "high" and "low" grid intensity without defining either. The rule here is that
    the assessed set must span a factor of two, which the EU27 alone does (35 to 608 gCO2/kWh).

    §6.3-4(c) asks for an accessible registration database. A market is credited with one only
    where its cohort is actually built on `registrations` — the EU27 on the EEA monitoring
    database and Japan on the JADA ranking. The United States and Korea are built on the
    companies' own market-side releases instead, which is a different and weaker thing, so they
    are marked as failing rather than being read as equivalent.

Run from the repository root:  .venv/bin/python script/auto/model/build_target_set.py
"""

from __future__ import annotations

from collections import defaultdict

from model_io import DATA, OUT_DIR, REPO, read_csv, write_csv

COMPANIES = DATA / "sales" / "method" / "companies.csv"
DESTINATION_NOTES = DATA / "sales" / "method" / "destination_notes.csv"
TARGETS = DATA / "emission_targets" / "processed"
OUT = OUT_DIR / "target_set.csv"

#: The guideline's coverage test: this share of the firm's worldwide sales, over this many markets.
GLOBAL_SHARE_REQUIRED = 0.70
MARKETS_REQUIRED = 3
#: Our reading of "one high and one low grid-intensity market", which §6.3 leaves undefined.
GRID_SPREAD_REQUIRED = 2.0
#: The sales basis that counts as an accessible registration database under §6.3-4(c).
REGISTRATION_BASIS = "registrations"

FIELDS = [
    "company",
    "market",
    "cohort_year",
    "segment",
    "status",
    "period",
    "units_held",
    "units_assessed",
    "covered_share",
    "lifetime_years",
    "lifetime_low_years",
    "lifetime_high_years",
    "volume_rank",
    "share_of_global",
    "markets_assessed",
    "grid_min_gco2_kwh",
    "grid_max_gco2_kwh",
    "grid_spread",
    "target_level",
    "registration_database",
    "criteria_met",
    "criteria_failed",
    "note",
]


def destination_parameters() -> dict[str, list[dict[str, str]]]:
    """Market -> its destination parameter rows."""
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in sorted(OUT_DIR.glob("destination_parameters_*.csv")):
        for r in read_csv(path):
            out[r["market"]].append(r)
    return out


def target_levels() -> dict[str, str]:
    """Market -> how its committed path was derived, or empty where it has none."""
    market_of = {"eu27": "EU27", "us": "US", "kr": "KR", "jp": "JP", "au": "AU"}
    out: dict[str, str] = {}
    for path in sorted(TARGETS.glob("emission_targets_*.csv")):
        market = market_of.get(path.stem.rsplit("_", 1)[-1], "")
        levels = {r["target_level"] for r in read_csv(path) if r["scenario"] == "S2"}
        if market and levels:
            out[market] = ";".join(sorted(levels))
    return out


def cohort_facts() -> tuple[dict[tuple[str, str, int], str], dict[tuple[str, str, int], str]]:
    """(company, market, year) -> its period, and -> the sales bases behind it."""
    periods: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    bases: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    for r in read_csv(OUT_DIR / "cohorts.csv"):
        if r["variant"] != "central":
            continue
        key = (r["company"], r["market"], int(r["cohort_year"]))
        periods[key].add(r["period"])
        bases[key].add(r["basis"])
    spans = {}
    for key, values in periods.items():
        months = sorted(m for p in values for m in p.split("..") if m)
        spans[key] = f"{months[0]}..{months[-1]}"
    return spans, {k: ";".join(sorted(v)) for k, v in bases.items()}


def main() -> None:
    """Write one row per target, with every §6.3 criterion marked met or failed."""
    in_scope = {r["company"] for r in read_csv(COMPANIES) if r["in_scope"] == "yes"}
    parameters = destination_parameters()
    levels = target_levels()
    periods, bases = cohort_facts()
    notes = {r["destination"]: r["status_note"] for r in read_csv(DESTINATION_NOTES)}

    # One row per target, not per scenario: the unit of analysis is the same under both, and
    # the first scenario alphabetically carries the volumes.
    assessed: dict[tuple[str, str, int], dict[str, str]] = {}
    for r in read_csv(OUT_DIR / "ti_company.csv"):
        key = (r["company"], r["market"], int(r["cohort_year"]))
        if r["company"] in in_scope and (
            key not in assessed or r["scenario"] < assessed[key]["scenario"]
        ):
            assessed[key] = r

    global_share = {
        (r["company"], int(r["cohort_year"])): r
        for r in read_csv(OUT_DIR / "ti_global_coverage.csv")
    }
    #: Destinations a firm sells into that no cohort assesses: counted here, never dropped.
    held: dict[tuple[str, str], int] = defaultdict(int)
    held_status: dict[tuple[str, str], set[str]] = defaultdict(set)
    for r in read_csv(OUT_DIR / "ti_coverage.csv"):
        # `not_in_cohort` is a second file for a destination that IS assessed, from another
        # source; it is a reconciliation row, not an unbuilt market.
        if r["company"] not in in_scope or r["status"] in {"assessed", "not_in_cohort"}:
            continue
        key = (r["company"], r["destination"])
        held[key] += int(r["units"])
        held_status[key].add(r["status"])

    # Rank each company's assessed markets by volume, per cohort year (criterion 6.3-1).
    by_company_year: dict[tuple[str, int], list[tuple[int, str]]] = defaultdict(list)
    for (company, market, year), row in assessed.items():
        by_company_year[(company, year)].append((int(row["covered_units"]), market))
    ranks: dict[tuple[str, str, int], int] = {}
    markets_per_year: dict[tuple[str, int], int] = {}
    #: 6.3-3 asks of the whole selection, not of one market: does the set contain a high- and a
    #: low-grid destination? So the spread is taken over every destination the firm assesses
    #: that year, and every row of that firm and year carries the same answer.
    spread_per_year: dict[tuple[str, int], tuple[float, float]] = {}
    for key, pairs in by_company_year.items():
        pairs.sort(reverse=True)
        markets_per_year[key] = len(pairs)
        for i, (_units, market) in enumerate(pairs, start=1):
            ranks[(key[0], market, key[1])] = i
        grids = [
            float(p["grid_gco2_kwh"])
            for _units, market in pairs
            for p in parameters.get(market, [])
            if p["grid_gco2_kwh"]
        ]
        if grids:
            spread_per_year[key] = (min(grids), max(grids))

    rows: list[dict[str, object]] = []
    for (company, market, year), row in sorted(assessed.items()):
        params = parameters.get(market, [])
        grids = [float(p["grid_gco2_kwh"]) for p in params if p["grid_gco2_kwh"]]
        grid_low, grid_high = spread_per_year.get((company, year), (0.0, 0.0))
        lives = [int(p["lifetime_years"]) for p in params if p["lifetime_years"]]
        lows = [int(p["lifetime_low_years"]) for p in params if p["lifetime_low_years"]]
        highs = [int(p["lifetime_high_years"]) for p in params if p["lifetime_high_years"]]
        share = global_share.get((company, year))
        share_value = float(share["assessed_share_of_global"]) if share else None
        markets = markets_per_year[(company, year)]
        spread = grid_high / grid_low if grid_low else 0.0
        basis = bases.get((company, market, year), "")
        registration = REGISTRATION_BASIS in basis.split(";")

        met, failed = [], []
        (met if ranks.get((company, market, year)) else failed).append("6.3-1")
        coverage_ok = (
            share_value is not None
            and share_value >= GLOBAL_SHARE_REQUIRED
            and markets >= MARKETS_REQUIRED
        )
        (met if coverage_ok else failed).append("6.3-2")
        (met if spread >= GRID_SPREAD_REQUIRED else failed).append("6.3-3")
        (met if market in levels else failed).append("6.3-4a")
        (met if grids else failed).append("6.3-4b")
        (met if registration else failed).append("6.3-4c")

        rows.append(
            {
                "company": company,
                "market": market,
                "cohort_year": year,
                "segment": ";".join(sorted({p["segment"] for p in params})),
                "status": "assessed",
                "period": periods.get((company, market, year), ""),
                "units_held": int(row["covered_units"]) + int(row["withheld_units"]),
                "units_assessed": int(row["covered_units"]),
                "covered_share": row["covered_share"],
                "lifetime_years": min(lives) if lives else "",
                "lifetime_low_years": min(lows) if lows else "",
                "lifetime_high_years": max(highs) if highs else "",
                "volume_rank": ranks.get((company, market, year), ""),
                "share_of_global": round(share_value, 6) if share_value is not None else "",
                "markets_assessed": markets,
                "grid_min_gco2_kwh": round(grid_low, 2) if grid_low else "",
                "grid_max_gco2_kwh": round(grid_high, 2) if grid_high else "",
                "grid_spread": round(spread, 2) if grid_low else "",
                "target_level": levels.get(market, ""),
                "registration_database": "yes" if registration else f"no ({basis})",
                "criteria_met": ";".join(met),
                "criteria_failed": ";".join(failed),
                "note": "",
            }
        )

    # Markets held but never built: counted here rather than dropped, with the stage's own reason
    # where the dataset records one and the coverage table's own status where it does not.
    for company, destination in sorted(held):
        units = held[(company, destination)]
        if not units:
            continue
        note = notes.get(destination, "")
        if True:
            rows.append(
                {
                    "company": company,
                    "market": destination,
                    "cohort_year": "",
                    "segment": "",
                    "status": ";".join(sorted(held_status[(company, destination)])),
                    "period": "",
                    "units_held": units,
                    "units_assessed": 0,
                    "covered_share": 0,
                    "lifetime_years": "",
                    "lifetime_low_years": "",
                    "lifetime_high_years": "",
                    "volume_rank": "",
                    "share_of_global": "",
                    "markets_assessed": "",
                    "grid_min_gco2_kwh": "",
                    "grid_max_gco2_kwh": "",
                    "grid_spread": "",
                    "target_level": levels.get(destination, ""),
                    "registration_database": "",
                    "criteria_met": "",
                    "criteria_failed": "not evaluated: no benchmark built",
                    "note": note,
                }
            )

    write_csv(OUT, FIELDS, rows)
    built = [r for r in rows if r["status"] == "assessed"]
    passing = [r for r in built if not r["criteria_failed"]]
    failures: dict[str, set[str]] = defaultdict(set)
    for r in built:
        failures[str(r["company"])].update(f for f in str(r["criteria_failed"]).split(";") if f)
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows, {len(built)} assessed targets, "
        f"{len(passing)} meeting every criterion; "
        + ", ".join(f"{c} fails {sorted(v)}" for c, v in sorted(failures.items()))
    )


if __name__ == "__main__":
    main()
