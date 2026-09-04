"""Final step — one SQLite database holding every input, output, source and reference.

Loads, as one table each:
    data/auto/registry/*.csv                               sources, raw files, tiers, value tiers
    data/auto/<dataset>/raw/*.csv                          hand-transcribed raw tables
    data/auto/<dataset>/method/*.csv                       lookup tables used by the scripts
    data/auto/<dataset>/processed/*.csv                    processed datasets
    data/auto/output/*.csv                                 model results (steps 3-5)
plus ``tiers`` and ``value_tiers`` (the A/B/C data-quality hierarchy and the per-value rules;
every processed and output row a rule covers gains ``tier`` and ``tier_reason`` columns),
``tables`` (what each table is, where it came from, row count, file hash) and
``columns`` (every column's SQLite type, non-null count, distinct count and an example value)
into ``data/auto/database/tradeimpact_auto.sqlite`` — the single source of truth for raw,
processed and
result data alike. Table names are the CSV file stems. Column types are
inferred per column (INTEGER, REAL, TEXT); empty cells load as NULL — never as zero.

The build is deterministic: the file is recreated from scratch and nothing time-dependent
is written.

Run from the repository root:  .venv/bin/python script/auto/model/build_database.py
"""

from __future__ import annotations

import csv
import hashlib
import re
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
REGISTRY = DATA / "registry"
OUT = DATA / "database" / "tradeimpact_auto.sqlite"
DATASETS = (
    "sales",
    "country_emissions",
    "emission_targets",
    "vehicle_usage",
    "vehicle_technology",
    "trade_flows",
    "dashboard",
)
TIERS = REGISTRY / "tiers.csv"
VALUE_TIERS = REGISTRY / "value_tiers.csv"
TIER_ORDER = {"A": 0, "B": 1, "C": 2}


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


def load_tier_rules() -> list[tuple[re.Pattern[str], str, re.Pattern[str], str, str]]:
    """The per-value tier rules of data/auto/value_tiers.csv, patterns compiled."""
    rules = []
    for r in csv.DictReader(VALUE_TIERS.open(newline="")):
        rules.append(
            (
                re.compile(f"^(?:{r['table_pattern']})$"),
                r["column"],
                re.compile(f"^(?:{r['value_pattern']})$"),
                r["tier"],
                r["reason"],
            )
        )
    return rules


def tier_columns(
    table: str,
    header: list[str],
    rows: list[list[str]],
    rules: list[tuple[re.Pattern[str], str, re.Pattern[str], str, str]],
) -> tuple[list[str], list[list[str]]]:
    """Append ``tier`` and ``tier_reason`` to every row of a table the rules cover.

    The worst matching tier wins (C over B over A); every matching reason is kept. Tables with
    no rule are returned unchanged, so the flag is never a silent default.
    """
    mine = [r for r in rules if r[0].match(table) and r[1] in header]
    if not mine or "tier" in header:  # a model-declared tier (ti_by_model) is never overwritten
        return header, rows
    idx = {c: i for i, c in enumerate(header)}
    out = []
    for row in rows:
        tier, reasons = "", []
        for _t, column, pattern, level, reason in mine:
            if pattern.match(row[idx[column]] or ""):
                if not tier or TIER_ORDER[level] > TIER_ORDER[tier]:
                    tier = level
                reasons.append(f"{level}: {reason}")
        out.append(row + [tier, "; ".join(reasons)])
    return header + ["tier", "tier_reason"], out


def load_csv(
    conn: sqlite3.Connection,
    path: Path,
    rules: list[tuple[re.Pattern[str], str, re.Pattern[str], str, str]] | None = None,
) -> int:
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
    if rules:
        header, rows = tier_columns(path.stem, header, rows, rules)
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
        (REGISTRY / "sources.csv", "registry", "auto"),
        (REGISTRY / "raw_files.csv", "registry", "auto"),
        (TIERS, "registry", "auto"),
        (VALUE_TIERS, "registry", "auto"),
    ]
    rules = load_tier_rules()
    for dataset in DATASETS:
        for kind in ("raw", "method", "processed"):
            for path in sorted((DATA / dataset / kind).glob("*.csv")):
                plan.append((path, kind, dataset))
    for path in sorted((DATA / "output").glob("*.csv")):
        plan.append((path, "output", "model"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    conn = sqlite3.connect(OUT)
    conn.execute(
        'CREATE TABLE "tables" ("table" TEXT PRIMARY KEY, dataset TEXT, kind TEXT, '
        "source_path TEXT, rows INTEGER, sha256 TEXT)"
    )
    for path, kind, dataset in plan:
        n = load_csv(conn, path, rules if kind in ("processed", "output") else None)
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
