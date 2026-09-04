"""Upsert helpers for the two provenance registries under data/auto.

registry/registry/sources.csv    one row per source_id: publisher, title, link, how obtained, access
                        date, licence
registry/raw_files.csv  one row per raw file: dataset, file, source_id, original name, SHA-256, note

Fetchers import this module (sys.path insert of script/auto) so that every raw file written to
disk is registered in the same call that writes it.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data" / "auto"
REGISTRY = DATA / "registry"
SOURCES = REGISTRY / "sources.csv"
RAW_FILES = REGISTRY / "raw_files.csv"


def _rewrite(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def upsert_source(row: dict[str, str]) -> None:
    """Replace or append the sources.csv row with the same source_id."""
    rows = list(csv.DictReader(SOURCES.open(newline="")))
    fields = list(rows[0])
    rows = [r for r in rows if r["source_id"] != row["source_id"]]
    rows.append({k: row.get(k, "") for k in fields})
    _rewrite(SOURCES, rows)


def upsert_raw_file(dataset: str, path: Path, source_id: str, original_name: str, note: str) -> str:
    """Replace or append the raw_files.csv row for (dataset, file); return the SHA-256."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = list(csv.DictReader(RAW_FILES.open(newline="")))
    rows = [r for r in rows if not (r["dataset"] == dataset and r["file"] == path.name)]
    rows.append(
        {
            "dataset": dataset,
            "file": path.name,
            "source_id": source_id,
            "original_name": original_name,
            "sha256": digest,
            "note": note,
        }
    )
    _rewrite(RAW_FILES, rows)
    return digest


def remove_source(source_id: str) -> None:
    """Drop a superseded sources.csv row (no raw file may still point at it)."""
    rows = list(csv.DictReader(SOURCES.open(newline="")))
    _rewrite(SOURCES, [r for r in rows if r["source_id"] != source_id])
