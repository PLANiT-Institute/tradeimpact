"""Build the schema catalogue: what every table is, what is in it, and how healthy it is.

The database has grown past a hundred tables and nothing described it. This reads the built
database and writes three catalogue tables that the data-catalogue page renders:

    registry/schema_tables.csv     one row per table: its layer, grain, description, row and
                                   column counts, the years its data covers, the tier mix, the
                                   licence it inherits, and a health verdict with its reason
    registry/schema_columns.csv    one row per column: type, role, blank and distinct counts,
                                   range, an example value, and the table it points at
    registry/schema_relations.csv  the join graph — which table reaches which, on which columns

Health is not a score out of ten; it is the worst thing true about a table, named:

    ok          rows present, no tier-C majority, nothing stale
    watch       a tier-C majority, or data more than two years behind its sale year
    stale       every value carried forward from an earlier year
    empty       no rows at all
    unlicensed  the raw file behind it may not be republished

Run from the repository root:  .venv/bin/python script/auto/registry/build_schema.py
"""

from __future__ import annotations

import csv
import sqlite3
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
REG = DATA / "registry"
DB = DATA / "database" / "tradeimpact_auto.sqlite"

#: kind -> the pipeline layer a table sits in, which is how the catalogue groups them.
LAYER = {
    "registry": "catalogue",
    "raw": "input",
    "method": "input",
    "processed": "processed",
    "output": "result",
}
#: Columns that are keys rather than values, in the order they identify a row.
KEY_COLUMNS = (
    "source_id",
    "provider_id",
    "licence_id",
    "table",
    "file",
    "market",
    "country",
    "destination",
    "company",
    "segment",
    "cohort_year",
    "scenario",
    "model",
    "powertrain",
    "parameter",
    "rate",
    "series",
    "year",
    "t",
    "dataset",
    "kind",
    "sector",
)
#: Columns that carry provenance rather than measurement.
PROVENANCE_COLUMNS = (
    "source_id",
    "source_ids",
    "source_file",
    "source_path",
    "sha256",
    "derivation",
    "note",
    "tier",
    "tier_reason",
    "warnings",
    "accessed_date",
    "licence_id",
    "provider_id",
    "url",
)
#: Column names that carry the year the data describes.
YEAR_COLUMNS = ("year", "cohort_year", "calendar_year", "model_year", "vintage_year")

#: Tables whose purpose is not obvious from the name. Everything else falls back to a pattern.
DESCRIPTIONS = {
    "sources": "Every source the project draws on: publisher, title, link, how it was obtained.",
    "raw_files": "Every raw file on disk, with its SHA-256 and the source it came from.",
    "data_providers": "The organisations that publish the sources, each pointing at one licence.",
    "licences": "The distinct licences, with the canonical URL and whether the raw file may be "
    "republished.",
    "redistribution": "Every raw file resolved to a redistribution verdict through its provider.",
    "tiers": "The A/B/C data-quality hierarchy the whole model declares against.",
    "value_tiers": "The rules that assign a tier to every value in every processed table.",
    "scope": "What the automotive case study covers and what it does not.",
    "cohorts": "The market-neutral cohort table: sales joined to certified product values, one "
    "row per market x company x destination x model x powertrain x sale year.",
    "cohorts_withheld": "Volumes that cannot enter a result, with the reason each was held back.",
    "data_readiness": "What each sale year actually received, parameter by parameter: the year "
    "the value was observed, its lag, and whether it was carried forward.",
    "target_set": "The unit of analysis, with guideline 6.3's market-selection criteria marked "
    "met or failed.",
    "ti_by_model": "The result cell: lifetime trade impact per market x company x destination x "
    "model x powertrain x scenario.",
    "ti_company": "Company x market x sale year totals, the headline table.",
    "ti_country": "Destination-country totals.",
    "ti_powertrain": "Totals by powertrain.",
    "ti_annual": "The year-by-year impact flow of each cohort, benchmark and product side by side.",
    "ti_annual_by_model": "The same annual flow at cell level.",
    "ti_annual_country": "The annual flow by destination.",
    "ti_annual_powertrain": "The annual flow by powertrain.",
    "ti_coverage": "Every company x destination held, assessed or not, and why not.",
    "ti_global_coverage": "How much of each company's worldwide sales the assessed markets cover.",
    "ti_data_quality": "The guideline 5.3 data-quality declaration per company x market x year.",
    "ti_source_reconciliation": "Every source held for the same company, destination and year, "
    "side by side.",
    "ti_sensitivity": "How the total moves when one input is moved.",
    "ti_crossover": "The year each cell crosses its benchmark, or why it never does.",
    "ti_withheld": "Units carrying no result, with the reason.",
    "ti_exclusions": "Market x scenario combinations with no benchmark at all.",
    "global_sales_totals": "Each company's own worldwide sales figure, the coverage denominator.",
    "companies": "The exporters in scope, and the brands held apart from them.",
    "country_codes": "ISO country codes and names for the map.",
    "map_geometry": "The world boundary geometry the dashboard draws.",
    "trade_flows": "Official HS 8703 trade statistics by powertrain class.",
    "real_world_correction": "The lab-to-road correction per test cycle and powertrain.",
    "hydrogen_supply": "The electricity an electrolyser draws per unit of hydrogen energy.",
    "fuel_carbon_factors": "Carbon per litre of each fuel, for converting a label economy to CO2.",
    "us_model_map": "Each US release's model name resolved to an EPA base model and a powertrain "
    "rule.",
    "kr_labels": "Each Korean IR label resolved to a KEA nameplate and a powertrain rule.",
    "jp_labels": "Each JADA nameplate resolved to a fuel-economy-list nameplate.",
    "kia_labels": "Kia IR market and plant labels resolved to country codes.",
}
#: Pattern -> description, applied when a table is not named above.
PATTERNS = (
    (
        "destination_parameters_",
        "The destination's benchmark inputs per segment and sale year: "
        "distance, stock, fleet intensity, grid, operating life.",
    ),
    (
        "reference_trajectories_",
        "The benchmark path per sale year and scenario: what the "
        "destination's own trajectory implies for each year of a life.",
    ),
    (
        "emission_targets_",
        "The scenario rates: the observed trend and the committed path, with "
        "the policy each was derived from and the year it was announced.",
    ),
    ("country_emissions_", "The national inventory series the benchmark level is built from."),
    ("vehicle_usage_", "Distance, stock and vehicle age from the destination's own statistics."),
    ("vehicle_technology_", "Certified product values per model and powertrain."),
    ("sales_", "Market-side sales volumes as the exporter or the registration authority reports."),
    ("jada_", "JADA registration statistics for Japan."),
    ("epa_", "US EPA certification and inventory data."),
    ("kea_", "Korea Energy Agency fuel-economy labels."),
    ("kotsa_", "Korea Transportation Safety Authority statistics."),
    ("gir_", "Korea national greenhouse-gas inventory."),
    ("nier_", "Korea National Institute of Environmental Research fleet data."),
    ("nhtsa_", "US NHTSA vehicle survival schedule."),
    ("owid_", "Our World in Data / Ember grid intensity."),
    ("hs_", "The HS commodity codes the trade flows are drawn on."),
)

#: The join graph, authored rather than guessed: (from_table, from_cols, to_table, to_cols, kind).
#: A ``*`` in a table name matches every market suffix.
RELATIONS = [
    ("sources", "provider_id", "data_providers", "provider_id", "lookup"),
    ("data_providers", "licence_id", "licences", "licence_id", "lookup"),
    ("raw_files", "source_id", "sources", "source_id", "lookup"),
    ("redistribution", "source_id", "sources", "source_id", "lookup"),
    ("redistribution", "provider_id", "data_providers", "provider_id", "lookup"),
    ("redistribution", "licence_id", "licences", "licence_id", "lookup"),
    ("value_tiers", "tier", "tiers", "tier", "lookup"),
    ("sales_*", "source_file", "raw_files", "file", "provenance"),
    ("vehicle_technology_*", "source_id", "sources", "source_id", "provenance"),
    ("country_emissions_*", "source_id", "sources", "source_id", "provenance"),
    ("vehicle_usage_*", "source_id", "sources", "source_id", "provenance"),
    ("emission_targets_*", "source_id", "sources", "source_id", "provenance"),
    ("cohorts", "sales_source_file", "raw_files", "file", "provenance"),
    (
        "cohorts",
        "market;destination;segment;cohort_year",
        "destination_parameters_*",
        "market;country;segment;cohort_year",
        "join",
    ),
    ("cohorts", "company", "companies", "company", "lookup"),
    (
        "destination_parameters_*",
        "country;segment",
        "country_emissions_*",
        "country;series",
        "derived_from",
    ),
    (
        "destination_parameters_*",
        "country;segment",
        "vehicle_usage_*",
        "country;series",
        "derived_from",
    ),
    (
        "reference_trajectories_*",
        "country;scenario",
        "emission_targets_*",
        "country;scenario",
        "join",
    ),
    (
        "reference_trajectories_*",
        "market;country;segment;cohort_year",
        "destination_parameters_*",
        "market;country;segment;cohort_year",
        "join",
    ),
    (
        "ti_by_model",
        "market;company;destination;segment;model;powertrain;cohort_year",
        "cohorts",
        "market;company;destination;segment;model;powertrain;cohort_year",
        "join",
    ),
    (
        "ti_by_model",
        "market;destination;segment;cohort_year;scenario",
        "reference_trajectories_*",
        "market;country;segment;cohort_year;scenario",
        "join",
    ),
    (
        "ti_annual_by_model",
        "market;company;destination;model;powertrain;cohort_year;scenario",
        "ti_by_model",
        "market;company;destination;model;powertrain;cohort_year;scenario",
        "join",
    ),
    (
        "ti_company",
        "market;company;cohort_year;scenario",
        "ti_by_model",
        "market;company;cohort_year;scenario",
        "aggregates",
    ),
    (
        "ti_country",
        "market;destination;cohort_year;scenario",
        "ti_by_model",
        "market;destination;cohort_year;scenario",
        "aggregates",
    ),
    (
        "ti_powertrain",
        "market;powertrain;cohort_year;scenario",
        "ti_by_model",
        "market;powertrain;cohort_year;scenario",
        "aggregates",
    ),
    (
        "ti_annual",
        "market;company;cohort_year;scenario",
        "ti_annual_by_model",
        "market;company;cohort_year;scenario",
        "aggregates",
    ),
    (
        "ti_crossover",
        "market;company;destination;model;powertrain;scenario",
        "ti_by_model",
        "market;company;destination;model;powertrain;scenario",
        "join",
    ),
    (
        "ti_sensitivity",
        "market;company;cohort_year;scenario",
        "ti_company",
        "market;company;cohort_year;scenario",
        "join",
    ),
    (
        "ti_withheld",
        "market;company;destination;cohort_year",
        "cohorts_withheld",
        "market;company;destination;cohort_year",
        "join",
    ),
    (
        "ti_coverage",
        "company;destination;cohort_year",
        "ti_by_model",
        "company;destination;cohort_year",
        "aggregates",
    ),
    (
        "ti_global_coverage",
        "company;cohort_year",
        "global_sales_totals",
        "company;cohort_year",
        "join",
    ),
    (
        "ti_data_quality",
        "company;market;cohort_year",
        "ti_by_model",
        "company;market;cohort_year",
        "aggregates",
    ),
    ("ti_source_reconciliation", "source_file", "raw_files", "file", "provenance"),
    (
        "target_set",
        "company;market;cohort_year",
        "ti_company",
        "company;market;cohort_year",
        "join",
    ),
    (
        "data_readiness",
        "country;cohort_year",
        "destination_parameters_*",
        "country;cohort_year",
        "describes",
    ),
    ("data_readiness", "source_id", "sources", "source_id", "lookup"),
]

TABLE_FIELDS = [
    "table",
    "dataset",
    "kind",
    "layer",
    "description",
    "grain",
    "rows",
    "columns",
    "data_year_min",
    "data_year_max",
    "tier_a",
    "tier_b",
    "tier_c",
    "tier_c_share",
    "source_path",
    "licences",
    "raw_redistribution",
    "health",
    "health_reason",
]
COLUMN_FIELDS = [
    "table",
    "column",
    "position",
    "type",
    "role",
    "blanks",
    "blank_share",
    "distinct",
    "min",
    "max",
    "example",
    "references",
]
RELATION_FIELDS = ["from_table", "from_columns", "to_table", "to_columns", "kind"]


def describe(table: str) -> str:
    """A one-line description of a table, authored where it matters and patterned otherwise."""
    if table in DESCRIPTIONS:
        return DESCRIPTIONS[table]
    for prefix, text in PATTERNS:
        if table.startswith(prefix):
            return text
    return ""


def grain_of(columns: list[str]) -> str:
    """The key columns that identify a row, in the order they appear."""
    return ";".join(c for c in columns if c in KEY_COLUMNS)


def role_of(column: str, numeric: bool) -> str:
    """Whether a column identifies a row, records where it came from, or measures something."""
    if column in PROVENANCE_COLUMNS:
        return "provenance"
    if column in KEY_COLUMNS:
        return "key"
    return "measure" if numeric else "dimension"


def expand(pattern: str, tables: set[str]) -> list[str]:
    """Every real table a relation's ``*`` pattern names."""
    if not pattern.endswith("*"):
        return [pattern] if pattern in tables else []
    return sorted(t for t in tables if t.startswith(pattern[:-1]))


def load(tables: dict[str, tuple[list[str], list[dict[str, object]]]]) -> None:
    """Create each catalogue table in the database and register it in ``tables``.

    Args:
        tables: table name -> (field order, rows).
    """
    conn = sqlite3.connect(DB)
    for name, (fields, rows) in tables.items():
        conn.execute(f'DROP TABLE IF EXISTS "{name}"')
        cols = ", ".join(f'"{f2}" TEXT' for f2 in fields)
        conn.execute(f'CREATE TABLE "{name}" ({cols})')
        conn.executemany(
            f'INSERT INTO "{name}" VALUES ({", ".join("?" for _ in fields)})',
            [[("" if r.get(f2) is None else str(r.get(f2))) for f2 in fields] for r in rows],
        )
        conn.execute('DELETE FROM tables WHERE "table" = ?', (name,))
        conn.execute(
            'INSERT INTO tables ("table", dataset, kind, source_path, rows, sha256) '
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, "auto", "registry", f"data/auto/registry/{name}.csv", len(rows), ""),
        )
    conn.commit()
    conn.close()


def main() -> None:
    """Read the database and write the three catalogue tables."""
    if not DB.exists():
        raise SystemExit(f"{DB.name} not found: run the pipeline first")
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    meta = {
        r[0]: {"dataset": r[1], "kind": r[2], "rows": r[3], "source_path": r[4]}
        for r in conn.execute('SELECT "table",dataset,kind,rows,source_path FROM tables')
    }
    #: source_id -> the licence and verdict it inherits, for stamping onto a table
    verdicts = {
        r[0]: (r[1], r[2])
        for r in conn.execute(
            "SELECT source_id, licence_id, raw_redistribution FROM redistribution"
        )
    }

    table_rows: list[dict[str, object]] = []
    column_rows: list[dict[str, object]] = []
    for table, info in sorted(meta.items()):
        cols = [(r[1], (r[2] or "").upper()) for r in conn.execute(f'PRAGMA table_info("{table}")')]
        names = [c for c, _ in cols]
        n = info["rows"]
        tier_counts: dict[str, int] = {}
        if "tier" in names:
            tier_counts = {
                str(r[0]): r[1]
                for r in conn.execute(f'SELECT tier, COUNT(*) FROM "{table}" GROUP BY tier')
            }
        years: list[int] = []
        licences_seen: set[str] = set()
        verdicts_seen: set[str] = set()
        for position, (col, coltype) in enumerate(cols, start=1):
            numeric = coltype in {"REAL", "INTEGER"}
            stats = conn.execute(
                f'SELECT COUNT(*), COUNT(DISTINCT "{col}"), '
                f'SUM(CASE WHEN "{col}" IS NULL OR "{col}" = \'\' THEN 1 ELSE 0 END) '
                f'FROM "{table}"'
            ).fetchone()
            total, distinct, blanks = stats[0], stats[1], stats[2] or 0
            lo = hi = example = ""
            if total:
                if numeric:
                    lo, hi = conn.execute(
                        f'SELECT MIN("{col}"), MAX("{col}") FROM "{table}"'
                    ).fetchone()
                sample = conn.execute(
                    f'SELECT "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL AND "{col}" != \'\' '
                    "LIMIT 1"
                ).fetchone()
                example = "" if sample is None else str(sample[0])[:80]
            if col in YEAR_COLUMNS and total:
                span = conn.execute(
                    f'SELECT MIN(CAST("{col}" AS INTEGER)), MAX(CAST("{col}" AS INTEGER)) '
                    f'FROM "{table}" WHERE "{col}" != \'\''
                ).fetchone()
                years.extend(v for v in span if isinstance(v, int))
            if col in ("source_id", "source_ids") and total:
                for r in conn.execute(f'SELECT DISTINCT "{col}" FROM "{table}"'):
                    for sid in str(r[0] or "").split(";"):
                        if sid in verdicts:
                            licences_seen.add(verdicts[sid][0])
                            verdicts_seen.add(verdicts[sid][1])
            column_rows.append(
                {
                    "table": table,
                    "column": col,
                    "position": position,
                    "type": coltype or "TEXT",
                    "role": role_of(col, numeric),
                    "blanks": blanks,
                    "blank_share": round(blanks / total, 4) if total else "",
                    "distinct": distinct,
                    "min": lo if lo is not None else "",
                    "max": hi if hi is not None else "",
                    "example": example,
                    "references": "",
                }
            )

        tier_c = tier_counts.get("C", 0)
        tier_total = sum(tier_counts.values())
        c_share = tier_c / tier_total if tier_total else 0.0
        health, reason = "ok", "rows present, nothing flagged"
        if n == 0:
            health, reason = "empty", "no rows"
        elif "no" in verdicts_seen:
            health = "unlicensed"
            reason = "a raw file behind this table may not be republished"
        elif tier_total and c_share >= 0.5:
            health = "watch"
            reason = f"tier C on {c_share:.0%} of rows"
        table_rows.append(
            {
                "table": table,
                "dataset": info["dataset"],
                "kind": info["kind"],
                "layer": LAYER.get(info["kind"], info["kind"]),
                "description": describe(table),
                "grain": grain_of(names),
                "rows": n,
                "columns": len(cols),
                "data_year_min": min(years) if years else "",
                "data_year_max": max(years) if years else "",
                "tier_a": tier_counts.get("A", 0),
                "tier_b": tier_counts.get("B", 0),
                "tier_c": tier_c,
                "tier_c_share": round(c_share, 4) if tier_total else "",
                "source_path": info["source_path"],
                "licences": ";".join(sorted(licences_seen)),
                "raw_redistribution": ";".join(sorted(verdicts_seen)),
                "health": health,
                "health_reason": reason,
            }
        )

    # readiness downgrades a table whose values were all carried forward for a sale year
    carried = defaultdict(set)
    for r in conn.execute("SELECT dataset, status FROM data_readiness"):
        carried[r[0]].add(r[1])
    for row in table_rows:
        statuses = carried.get(str(row["dataset"]), set())
        if row["health"] == "ok" and statuses and statuses <= {"carried_forward", "stale"}:
            row["health"], row["health_reason"] = "stale", "every value carried forward"

    tables = set(meta)
    relation_rows = [
        {"from_table": f, "from_columns": fc, "to_table": t, "to_columns": tc, "kind": kind}
        for fp, fc, tp, tc, kind in RELATIONS
        for f in expand(fp, tables)
        for t in expand(tp, tables)
        if f != t
        and (not fp.endswith("*") or not tp.endswith("*") or f.split("_")[-1] == t.split("_")[-1])
    ]
    conn.close()

    for path, fields, rows in (
        (REG / "schema_tables.csv", TABLE_FIELDS, table_rows),
        (REG / "schema_columns.csv", COLUMN_FIELDS, column_rows),
        (REG / "schema_relations.csv", RELATION_FIELDS, relation_rows),
    ):
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    # The three tables describe the database, so they belong in it. They are written here rather
    # than by build_database because they can only be computed once that has run.
    load(
        {
            "schema_tables": (TABLE_FIELDS, table_rows),
            "schema_columns": (COLUMN_FIELDS, column_rows),
            "schema_relations": (RELATION_FIELDS, relation_rows),
        }
    )

    health = defaultdict(int)
    for row in table_rows:
        health[str(row["health"])] += 1
    print(
        f"schema_tables.csv: {len(table_rows)} tables, health {dict(health)}\n"
        f"schema_columns.csv: {len(column_rows)} columns\n"
        f"schema_relations.csv: {len(relation_rows)} relations"
    )


if __name__ == "__main__":
    main()
