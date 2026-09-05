"""Load every CSV of the power sector into one SQLite file, with per-value tier flags.

Output  data/power/database/tradeimpact_power.sqlite

The same construction as the automotive database (whose loaders this script imports): every raw,
method and processed CSV of every dataset, every output table, the registries, the world
geometry as one ``map_geometry`` row, a ``tables`` manifest (dataset, kind, path, rows, SHA-256)
and a ``columns`` dictionary. Processed and output tables get ``tier`` / ``tier_reason`` columns
from ``registry/value_tiers.csv`` unless the model already declared a tier.

Run from the repository root:  .venv/bin/python script/power/model/build_database.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "auto" / "model"))
from build_database import load_csv, load_geometry, load_tier_rules, sha256  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "power"
REGISTRY = DATA / "registry"
GEOMETRY = DATA / "geography" / "raw" / "countries-110m.json"
OUT = DATA / "database" / "tradeimpact_power.sqlite"
DATASETS = ("companies", "geography", "grid", "emission_factors", "projects", "roles", "targets")
#: Raw files that are not CSV (workbooks, JSON, PDF) are recorded in raw_files.csv, not loaded.


def main() -> None:
    """Rebuild the database from every CSV under data/power."""
    plan: list[tuple[Path, str, str]] = [
        (REGISTRY / "sources.csv", "registry", "power"),
        (REGISTRY / "raw_files.csv", "registry", "power"),
        (REGISTRY / "value_tiers.csv", "registry", "power"),
    ]
    for dataset in DATASETS:
        for kind in ("raw", "method", "processed"):
            for path in sorted((DATA / dataset / kind).glob("*.csv")):
                plan.append((path, kind, dataset))
    for path in sorted((DATA / "output").glob("*.csv")):
        plan.append((path, "output", "model"))
    rules = load_tier_rules(REGISTRY / "value_tiers.csv")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    conn = sqlite3.connect(OUT)
    conn.execute(
        'CREATE TABLE "tables" ("table" TEXT PRIMARY KEY, dataset TEXT, kind TEXT, '
        "source_path TEXT, rows INTEGER, sha256 TEXT)"
    )
    stems = [p.stem for p, _k, _d in plan]
    names = []
    for path, kind, dataset in plan:
        # A hand register and its validated copy share a file name: the raw one gets _raw.
        name = f"{path.stem}_raw" if kind == "raw" and stems.count(path.stem) > 1 else path.stem
        names.append(name)
        n = load_csv(conn, path, rules if kind in ("processed", "output") else None, table=name)
        conn.execute(
            'INSERT INTO "tables" VALUES (?, ?, ?, ?, ?, ?)',
            (name, dataset, kind, str(path.relative_to(REPO)), n, sha256(path)),
        )
    rows_geo = load_geometry(conn, GEOMETRY)
    conn.execute(
        'INSERT INTO "tables" VALUES (?, ?, ?, ?, ?, ?)',
        (
            "map_geometry",
            "geography",
            "raw",
            str(GEOMETRY.relative_to(REPO)),
            rows_geo,
            sha256(GEOMETRY),
        ),
    )
    conn.execute(
        'CREATE TABLE "columns" ("table" TEXT, "column" TEXT, sqlite_type TEXT, '
        "non_null INTEGER, distinct_values INTEGER, example TEXT, "
        'PRIMARY KEY ("table", "column"))'
    )
    for name in names + ["map_geometry"]:
        for _cid, col, ctype, *_rest in conn.execute(f'PRAGMA table_info("{name}")'):
            non_null, distinct, example = conn.execute(
                f'SELECT COUNT("{col}"), COUNT(DISTINCT "{col}"), '
                f'(SELECT "{col}" FROM "{name}" WHERE "{col}" IS NOT NULL LIMIT 1) FROM "{name}"'
            ).fetchone()
            conn.execute(
                'INSERT INTO "columns" VALUES (?, ?, ?, ?, ?, ?)',
                (
                    name,
                    col,
                    ctype,
                    non_null,
                    distinct,
                    None if example is None else str(example)[:80],
                ),
            )
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    print(f"{OUT.relative_to(REPO)}: {len(plan) + 1} tables, {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
