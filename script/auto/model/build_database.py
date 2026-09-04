"""Final step — one SQLite database holding every input, output, source and reference.

Loads, as one table each:
    data/auto/sources.csv, data/auto/raw_files.csv        source registry and raw-file provenance
    data/auto/<dataset>/raw/*.csv                          hand-transcribed raw tables
    data/auto/<dataset>/method/*.csv                       lookup tables used by the scripts
    data/auto/<dataset>/processed/*.csv                    processed datasets
    data/auto/output/*.csv                                 model results (steps 3-5)
plus ``tables`` (what each table is, where it came from, row count, file hash) and
``columns`` (every column's SQLite type, non-null count, distinct count and an example value)
into ``data/auto/tradeimpact_auto.sqlite`` — the single source of truth for raw, processed and
result data alike. Table names are the CSV file stems. Column types are
inferred per column (INTEGER, REAL, TEXT); empty cells load as NULL — never as zero.

The build is deterministic: the file is recreated from scratch and nothing time-dependent
is written.

Run from the repository root:  .venv/bin/python script/auto/model/build_database.py
"""

from __future__ import annotations

import csv
import hashlib
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
OUT = DATA / "tradeimpact_auto.sqlite"
DATASETS = (
    "sales",
    "country_emissions",
    "emission_targets",
    "vehicle_usage",
    "vehicle_technology",
    "trade_flows",
)


def sha256(path: Path) -> str:
    """Hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer_type(values: list[str]) -> str:
    """INTEGER if every non-empty value is an int, REAL if numeric, else TEXT."""
    seen = [v for v in values if v != ""]
    if not seen:
        return "TEXT"
    try:
        for v in seen:
            int(v)
        return "INTEGER"
    except ValueError:
        pass
    try:
        for v in seen:
            float(v)
        return "REAL"
    except ValueError:
        return "TEXT"


def load_csv(conn: sqlite3.Connection, path: Path) -> int:
    """Create a table named after the file stem and load every row; return the row count."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp949")  # Korean open-data CSVs (KOTSA, NIER)
    reader = csv.reader(text.splitlines())
    header = next(reader)
    rows = list(reader)
    bad = [i + 2 for i, r in enumerate(rows) if len(r) != len(header)]
    if bad:
        raise SystemExit(
            f"{path.relative_to(REPO)}: {len(bad)} row(s) do not match the header width "
            f"(first at line {bad[0]}); the file is malformed or truncated"
        )
    types = [infer_type([r[i] for r in rows]) for i in range(len(header))]
    columns = ", ".join(f'"{h}" {t}' for h, t in zip(header, types, strict=True))
    conn.execute(f'CREATE TABLE "{path.stem}" ({columns})')
    converters = [int if t == "INTEGER" else float if t == "REAL" else str for t in types]

    def convert(row: list[str]) -> list[object]:
        return [None if v == "" else conv(v) for v, conv in zip(row, converters, strict=True)]

    conn.executemany(
        f'INSERT INTO "{path.stem}" VALUES ({", ".join("?" * len(header))})',
        (convert(r) for r in rows),
    )
    return len(rows)


def main() -> None:
    """Rebuild the database from every CSV under data/auto."""
    plan: list[tuple[Path, str, str]] = [
        (DATA / "sources.csv", "registry", "auto"),
        (DATA / "raw_files.csv", "registry", "auto"),
    ]
    for dataset in DATASETS:
        for kind in ("raw", "method", "processed"):
            for path in sorted((DATA / dataset / kind).glob("*.csv")):
                plan.append((path, kind, dataset))
    for path in sorted((DATA / "output").glob("*.csv")):
        plan.append((path, "output", "model"))

    if OUT.exists():
        OUT.unlink()
    conn = sqlite3.connect(OUT)
    conn.execute(
        'CREATE TABLE "tables" ("table" TEXT PRIMARY KEY, dataset TEXT, kind TEXT, '
        "source_path TEXT, rows INTEGER, sha256 TEXT)"
    )
    for path, kind, dataset in plan:
        n = load_csv(conn, path)
        conn.execute(
            'INSERT INTO "tables" VALUES (?, ?, ?, ?, ?, ?)',
            (path.stem, dataset, kind, str(path.relative_to(REPO)), n, sha256(path)),
        )
        print(f"{path.stem:40s} {kind:9s} {n:>7,d} rows")
    conn.execute(
        'CREATE TABLE "columns" ("table" TEXT, "column" TEXT, sqlite_type TEXT, '
        "non_null INTEGER, distinct_values INTEGER, example TEXT, "
        'PRIMARY KEY ("table", "column"))'
    )
    for path, _kind, _dataset in plan:
        name = path.stem
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
    print(f"{OUT.relative_to(REPO)}: {len(plan)} tables, {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
