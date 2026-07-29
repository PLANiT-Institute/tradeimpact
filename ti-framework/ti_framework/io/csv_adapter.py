# SPDX-License-Identifier: GPL-3.0-or-later
"""CSV input path: one CSV per workbook sheet, same schema contract as the xlsx.

A directory of ``<sheet name>.csv`` files (``Layer1_NDC_benchmark.csv``, ...) loads into
the same ``WorkbookInputs`` as the xlsx workbook. Each CSV is wrapped in a shim exposing
``iter_rows(values_only=True)`` so the *identical* sheet loaders in ``io/workbook.py``
parse it — the schema is never forked (build brief §3). Empty cells stay ``None``.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

import ti_framework.io.schema as S
from ti_framework.io.workbook import (
    WorkbookInputs,
    _collect_missing,
    _load_layer1,
    _load_layer2,
    _load_support,
    _load_volumes,
)


class _CsvSheet:
    """Duck-types the openpyxl worksheet surface the loaders use."""

    def __init__(self, path: Path) -> None:
        with path.open(newline="", encoding="utf-8-sig") as f:
            self._rows = [tuple(c if c.strip() else None for c in row) for row in csv.reader(f)]

    def iter_rows(self, values_only: bool = True) -> Iterator[tuple]:  # noqa: ARG002 - match openpyxl signature
        return iter(self._rows)


def load_csv_inputs(directory: str | Path) -> WorkbookInputs:
    """Load ``<sheet>.csv`` files from ``directory`` into validated models.

    Missing files are treated like missing sheets in the xlsx path: skipped, and the
    resulting gaps surface in ``missing_inputs`` rather than defaults.
    """
    d = Path(directory)
    inputs = WorkbookInputs()

    def sheet(name: str) -> _CsvSheet | None:
        p = d / f"{name}.csv"
        return _CsvSheet(p) if p.exists() else None

    if (ws := sheet(S.SHEET_LAYER1)) is not None:
        inputs.countries = _load_layer1(ws)
    if (ws := sheet(S.SHEET_LAYER2)) is not None:
        inputs.vehicles = _load_layer2(ws)
    if (ws := sheet(S.SHEET_REG)) is not None:
        inputs.volumes = _load_volumes(ws)
    inputs.support = _load_support(sheet(S.SHEET_SUPPORT))

    _collect_missing(inputs)
    return inputs
