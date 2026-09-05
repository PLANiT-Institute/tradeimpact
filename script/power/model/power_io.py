"""Paths, CSV helpers and the hand-file rule shared by every script in the power sector.

The power case study keeps its data under ``data/power/<dataset>/{raw,processed,method}`` and
its results under ``data/power/output``, mirroring the automotive sector. Two inputs cannot be
fetched by a script — the Global Energy Monitor tracker (behind a download form) and the
company-role register (read off project pages and company releases) — so every script that
needs one calls :func:`hand_file_required` when it is missing and exits with status 3. The
runner shows that status as ``[hand]`` and stops: a missing input is never a silent empty result.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "power"
OUT = DATA / "output"
REGISTRY = DATA / "registry"
#: Exit status meaning "waiting on a hand-gathered file" (see run_all.py).
EXIT_HAND = 3


def read_csv(path: Path) -> list[dict[str, str]]:
    """Rows of a CSV as dicts; an empty list when the file is header-only."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    """Write rows with a fixed field order, creating the directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def hand_file_required(path: Path, how: str) -> None:
    """Stop with status 3 and say which hand-gathered file is missing and how to obtain it."""
    print(f"HAND FILE REQUIRED: {path.relative_to(REPO)}\n  {how}")
    sys.exit(EXIT_HAND)


def num(value: str | None) -> float | None:
    """Float of a cell, None when blank or not numeric."""
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text in ("", "-", "—", "n/a", "N/A", "unknown"):
        return None
    try:
        return float(text)
    except ValueError:
        return None
