"""Every figure the analysis report states, read once from the database.

The report has no numbers of its own. This module holds the queries; the report module holds
the prose and the layout, and interpolates from here — so a rebuild after a data change moves
the sentences as well as the charts, and a claim cannot drift away from the table it rests on.

One convention runs through it. Cross-market comparisons use the 2024 cohorts, the only sale
year every market has, because cohort years are never pooled: a 2024 and a 2025 cohort are
different vehicles sold into a benchmark at different levels.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
#: The sale year every market in scope has, used wherever markets are compared with each other.
COMMON_COHORT = 2024
#: Market codes in reporting order, with the name the report uses for each.
MARKETS = {"EU27": "European Union (27)", "US": "United States", "JP": "Japan", "KR": "Korea"}
#: Company keys in reporting order, with their display names.
COMPANIES = {"toyota": "Toyota", "hyundai": "Hyundai", "kia": "Kia", "nissan": "Nissan"}
#: Guideline §5.3: above this share of proxied-distance units a result is directional only.
DIRECTIONAL_THRESHOLD = 0.5


def rows(conn: sqlite3.Connection, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
    """Every row of one query as mappings."""
    conn.row_factory = sqlite3.Row
    return list(conn.execute(sql, args))


def one(conn: sqlite3.Connection, sql: str, args: tuple = ()) -> sqlite3.Row:
    """The single row of an aggregate query."""
    return rows(conn, sql, args)[0]


@dataclass
class Facts:
    """Everything the report says, keyed the way the report reads it."""

    as_of: str
    company_results: list[sqlite3.Row]
    coverage: list[sqlite3.Row]
    crossover: list[sqlite3.Row]
    powertrain: list[sqlite3.Row]
    parameters: list[sqlite3.Row]
    rate_rows: list[sqlite3.Row]
    sensitivity: dict[tuple[str, str], dict[str, tuple[float, float, float]]]
    quality: list[sqlite3.Row]
    withheld: list[sqlite3.Row]
    cohort_withheld: list[sqlite3.Row]
    eu_country: list[sqlite3.Row]
    annual: dict[tuple[str, str, int, str], list[sqlite3.Row]]
    nameplates: list[sqlite3.Row]
    segments: list[sqlite3.Row]
    sources: list[sqlite3.Row]
    manifest: list[sqlite3.Row]
    derived: dict[str, object] = field(default_factory=dict)


def load() -> Facts:
    """Run every query the report needs."""
    if not DB.exists():
        raise SystemExit(f"{DB} is missing; run script/auto/run_all.py first")
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

    as_of = one(conn, "select max(accessed_date) d from sources")["d"]
    company_results = rows(
        conn,
        """select market, company, cohort_year, scenario, status, covered_units, withheld_units,
                  covered_share, ti_tco2e, ti_per_vehicle_kgco2e, direction
           from ti_company order by market, cohort_year, company, scenario""",
    )
    coverage = rows(
        conn,
        """select company, cohort_year, global_units, global_basis, assessed_units,
                  assessed_share_of_global, assessed_markets, assessed_countries, held_units,
                  held_share_of_global, brands_out_of_scope
           from ti_global_coverage order by company, cohort_year""",
    )
    crossover = rows(
        conn,
        """select market, scenario,
                  sum(units) units,
                  sum(case when crossover_year <> '' then units else 0 end) units_with,
                  sum(case when crossover_year <> '' then crossover_year * units else 0 end) wsum
           from ti_crossover group by market, scenario order by market, scenario""",
    )
    powertrain = rows(
        conn,
        """select market, powertrain, scenario, sum(units) units, sum(ti_tco2e) ti,
                  sum(ti_tco2e) * 1000.0 / sum(units) per_vehicle
           from ti_powertrain where cohort_year = ?
           group by market, powertrain, scenario order by market, scenario, powertrain""",
        (COMMON_COHORT,),
    )
    parameters = []
    for market in ("eu27", "us", "jp", "kr"):
        parameters += rows(
            conn,
            f"""select market, country, segment, vkt_km, vkt_tier, fleet_intensity_gco2_km,
                       fleet_intensity_tier, grid_gco2_kwh, mean_age_years, lifetime_years,
                       lifetime_low_years, lifetime_high_years, lifetime_tier, co2_year, vkt_year
                from destination_parameters_{market} order by country, segment""",
        )
    rate_rows = []
    for market in ("eu27", "us", "jp", "kr"):
        rate_rows += rows(
            conn,
            f"""select '{market.upper()}' as tbl, country, scenario, rate, value, target_level,
                       base_year, target_year, derivation, source_id
                from emission_targets_{market} order by country, scenario, rate""",
        )

    sensitivity: dict[tuple[str, str], dict[str, tuple[float, float, float]]] = {}
    raw = rows(
        conn,
        """select company, market, cohort_year, scenario, dimension, variant, ti_tco2e
           from ti_sensitivity where scenario = 'S2' and cohort_year = ?""",
        (COMMON_COHORT,),
    )
    grouped: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
    for r in raw:
        grouped[(r["company"], r["market"], r["dimension"])][r["variant"]] = float(r["ti_tco2e"])
    for (company, market, dimension), variants in grouped.items():
        central = variants.get("central")
        others = [v for k, v in variants.items() if k != "central"]
        if central is None or not others:
            continue
        low, high = min(others + [central]), max(others + [central])
        sensitivity.setdefault((company, market), {})[dimension] = (low, central, high)

    quality = rows(
        conn,
        """select market, company, cohort_year, tier_c_share, directional_only, units_tier_a,
                  units_tier_b, units_tier_c, tier_c_units_share, countries_covered,
                  countries_withheld, lifetime_t_central_years, test_cycles, sales_basis
           from ti_data_quality order by market, company, cohort_year""",
    )
    withheld = rows(
        conn,
        """select market, reason, sum(units) units, count(*) cells from ti_withheld
           group by market, reason order by units desc""",
    )
    cohort_withheld = rows(
        conn,
        """select market, company, model, reason, sum(units) units from cohorts_withheld
           group by market, company, model, reason order by units desc""",
    )
    eu_country = rows(
        conn,
        """select destination, scenario, sum(units) units,
                  sum(ti_tco2e) * 1000.0 / sum(units) per_vehicle
           from ti_country where market = 'EU27' and cohort_year = ?
           group by destination, scenario""",
        (COMMON_COHORT,),
    )
    annual: dict[tuple[str, str, int, str], list[sqlite3.Row]] = {}
    for r in rows(
        conn,
        """select market, company, cohort_year, scenario, calendar_year, surviving_vehicles,
                  e_ref_tco2e, e_prod_tco2e, ti_tco2e, cumulative_ti_tco2e
           from ti_annual order by market, company, cohort_year, scenario, calendar_year""",
    ):
        key = (r["market"], r["company"], int(r["cohort_year"]), r["scenario"])
        annual.setdefault(key, []).append(r)
    nameplates = rows(
        conn,
        """select market, company, model, powertrain, scenario, sum(units) units,
                  sum(e_prod_year0_kgco2e * units) / sum(units) prod0,
                  sum(e_ref_year0_kgco2e * units) / sum(units) ref0,
                  sum(ti_per_vehicle_kgco2e * units) / sum(units) per_vehicle,
                  avg(lifetime_years) life, avg(vkt_km) vkt
           from ti_by_model where cohort_year = ?
           group by market, company, model, powertrain, scenario""",
        (COMMON_COHORT,),
    )
    segments = rows(
        conn,
        """select market, segment, scenario, sum(units) units, sum(ti_tco2e) ti,
                  sum(ti_tco2e) * 1000.0 / sum(units) per_vehicle
           from ti_by_model group by market, segment, scenario
           order by market, segment, scenario""",
    )
    sources = rows(
        conn,
        """select source_id, publisher, title, url, license, used_by from sources
           order by source_id""",
    )
    manifest = rows(
        conn,
        """select "table", dataset, kind, rows, sha256 from tables
           where kind = 'output' order by "table" """,
    )
    conn.close()

    facts = Facts(
        as_of=as_of,
        company_results=company_results,
        coverage=coverage,
        crossover=crossover,
        powertrain=powertrain,
        parameters=parameters,
        rate_rows=rate_rows,
        sensitivity=sensitivity,
        quality=quality,
        withheld=withheld,
        cohort_withheld=cohort_withheld,
        eu_country=eu_country,
        annual=annual,
        nameplates=nameplates,
        segments=segments,
        sources=sources,
        manifest=manifest,
    )
    facts.derived = derive(facts)
    return facts


def derive(f: Facts) -> dict[str, object]:
    """Figures the prose quotes that are counts or sums over the queried rows."""
    reported = [r for r in f.company_results if r["status"] == "reported"]
    by_scenario: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for r in reported:
        by_scenario[r["scenario"]].append(r)
    out: dict[str, object] = {
        "cohorts": len({(r["market"], r["company"], r["cohort_year"]) for r in reported}),
        "markets": sorted({r["market"] for r in reported}),
        "companies": sorted({r["company"] for r in reported}),
        "units": sum(int(r["covered_units"]) for r in reported if r["scenario"] == "S1"),
        "withheld_units": sum(int(r["withheld_units"]) for r in reported if r["scenario"] == "S1"),
    }
    for scenario, group in by_scenario.items():
        out[f"{scenario}_total_mt"] = sum(float(r["ti_tco2e"]) for r in group) / 1e6
        out[f"{scenario}_contributions"] = sum(1 for r in group if float(r["ti_tco2e"]) > 0)
        out[f"{scenario}_liabilities"] = sum(1 for r in group if float(r["ti_tco2e"]) < 0)
        out[f"{scenario}_n"] = len(group)
    out["scenarios"] = sorted(by_scenario)

    crossings = {
        (r["market"], r["scenario"]): (float(r["wsum"]) / float(r["units_with"]))
        if float(r["units_with"])
        else None
        for r in f.crossover
    }
    out["crossings"] = crossings
    s2 = [v for (_, scenario), v in crossings.items() if scenario == "S2" and v is not None]
    out["s2_crossing_min"], out["s2_crossing_max"] = min(s2), max(s2)

    pt: dict[tuple[str, str], float] = {}
    for r in f.powertrain:
        pt[(r["powertrain"], r["scenario"])] = pt.get(
            (r["powertrain"], r["scenario"]), 0.0
        ) + float(r["ti"])
    out["powertrain_totals"] = pt
    out["bev_markets_positive_s2"] = sum(
        1
        for r in f.powertrain
        if r["powertrain"] == "BEV" and r["scenario"] == "S2" and float(r["ti"]) > 0
    )
    out["bev_markets_s2"] = sum(
        1 for r in f.powertrain if r["powertrain"] == "BEV" and r["scenario"] == "S2"
    )
    return out
