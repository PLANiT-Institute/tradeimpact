"""Upsert helpers for the two provenance registries a sector keeps under data/<sector>/registry.

registry/sources.csv    one row per source_id: publisher, title, link, how obtained, access date,
                        licence, which datasets use it
registry/raw_files.csv  one row per raw file: dataset, file, source_id, original name, SHA-256, note

Fetchers import this module (sys.path insert of script/) so that every raw file written to disk
is registered in the same call that writes it. Each function takes the sector's data root
(``data/auto``, ``data/power``); the automotive root is the default so the older fetchers need
no argument.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA_AUTO = REPO / "data" / "auto"
SOURCE_FIELDS = [
    "source_id",
    "publisher",
    "title",
    "url",
    "how_obtained",
    "accessed_date",
    "license",
    "used_by",
]
RAW_FILE_FIELDS = ["dataset", "file", "source_id", "original_name", "sha256", "note"]


def _read(path: Path, fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(newline="")))


def _rewrite(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in fields} for r in rows)


def upsert_source(row: dict[str, str], data_root: Path = DATA_AUTO) -> None:
    """Replace or append the sources.csv row with the same source_id."""
    path = data_root / "registry" / "sources.csv"
    rows = [r for r in _read(path, SOURCE_FIELDS) if r["source_id"] != row["source_id"]]
    rows.append(row)
    _rewrite(path, SOURCE_FIELDS, rows)


def upsert_raw_file(
    dataset: str,
    path: Path,
    source_id: str,
    original_name: str,
    note: str,
    data_root: Path = DATA_AUTO,
) -> str:
    """Replace or append the raw_files.csv row for (dataset, file); return the SHA-256."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    registry = data_root / "registry" / "raw_files.csv"
    rows = [
        r
        for r in _read(registry, RAW_FILE_FIELDS)
        if not (r["dataset"] == dataset and r["file"] == path.name)
    ]
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
    _rewrite(registry, RAW_FILE_FIELDS, rows)
    return digest


def remove_source(source_id: str, data_root: Path = DATA_AUTO) -> None:
    """Drop a superseded sources.csv row (no raw file may still point at it)."""
    path = data_root / "registry" / "sources.csv"
    rows = [r for r in _read(path, SOURCE_FIELDS) if r["source_id"] != source_id]
    _rewrite(path, SOURCE_FIELDS, rows)
