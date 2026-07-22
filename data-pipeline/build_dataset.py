#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the published dataset the web app renders.

    workbook.xlsx / *.csv + fixtures + firm universe
        -> data/published/{firms.json, {firm}.json, meta.json}

All numbers originate in ti_framework (build brief §1 boundary rule); this script only
orchestrates runs and serialises. Firms without collected data are published as
``runnable: false`` with their collection backlog — never with fabricated results.

Usage:  ti-framework/.venv/bin/python data-pipeline/build_dataset.py
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import version as pkg_version
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO / "ti-framework"
WORKBOOK = ENGINE_DIR / "data" / "TI_Data_Workbook_v0.1.xlsx"
OUT = REPO / "data" / "published"

sys.path.insert(0, str(ENGINE_DIR))

from ti_framework.core.scenarios import run  # noqa: E402
from ti_framework.core.sensitivity import run_sensitivity  # noqa: E402
from ti_framework.io.fixtures import load_fixture  # noqa: E402
from ti_framework.io.workbook import load_workbook_inputs  # noqa: E402
from ti_framework.report.outputs import to_json_dict  # noqa: E402

# firm slug -> fixture powering its report. ReferenceCo is the validation fixture;
# Toyota/Hyundai run on rough documented Tier B/C estimates (ESTIMATES.md) until
# collection lands (COLLECTION_STATUS.md is the backlog).
FIXTURES: dict[str, Path] = {
    "referenceco": ENGINE_DIR / "fixtures" / "reference_case.json",
    "toyota": REPO / "data-pipeline" / "fixtures" / "toyota.json",
    "hyundai": REPO / "data-pipeline" / "fixtures" / "hyundai.json",
}

# provenance note surfaced on the report page for estimate-based firms
NOTES_BY_SLUG = {
    "toyota": "Estimated-input case: NDC rates and grid intensities are collected (Tier A/B); "
    "volumes, vehicle parameters and S1/S3 rates are rough documented estimates "
    "(data-pipeline/ESTIMATES.md, Tier B/C). Replace with collected data as it lands.",
    "hyundai": "Estimated-input case: NDC rates and grid intensities are collected (Tier A/B); "
    "volumes, vehicle parameters and S1/S3 rates are rough documented estimates "
    "(data-pipeline/ESTIMATES.md, Tier B/C). Replace with collected data as it lands.",
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _rows(path: Path, expect_first_header: str) -> list[dict]:
    """Read a target-companies sheet: find the header row, return data-row dicts."""
    ws = openpyxl.load_workbook(path, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    header_i = next(i for i, r in enumerate(rows) if r[0] == expect_first_header)
    header = [str(c) if c else "" for c in rows[header_i]]
    out = []
    for r in rows[header_i + 1 :]:
        if not r[0] or not r[2]:  # needs Sector and Company columns
            continue
        out.append(dict(zip(header, (str(c) if c is not None else "" for c in r))))
    return out


def build_universe() -> list[dict]:
    firms: list[dict] = [
        {
            "slug": "referenceco",
            "name": "ReferenceCo",
            "sector": "Automotive",
            "country": "—",
            "project": "TI",
            "runnable": True,
            "illustrative": True,
            "note": "Committed validation fixture with illustrative parameters (NOTES.md D4). "
            "Demonstrates the full report until real-firm data is collected.",
        }
    ]
    for r in _rows(REPO / "TI_CaseStudy_Target_Companies.xlsx", "Sector"):
        name = r["Company (candidate)"]
        slug = slugify(name)
        firms.append(
            {
                "slug": slug,
                "name": name,
                "sector": r["Sector"],
                "country": r["Country"],
                "project": "TI",
                "runnable": slug in FIXTURES,
                "basis": "estimated" if slug in NOTES_BY_SLUG else None,
                "note": NOTES_BY_SLUG.get(slug),
                "status": r.get("Status", ""),
                "selection_criteria": r.get("Selection criteria", ""),
            }
        )
    for r in _rows(REPO / "CAP_Target_Companies_Draft.xlsx", "Sector"):
        name = r["Company (candidate)"]
        firms.append(
            {
                "slug": slugify(name),
                "name": name,
                "sector": r["Sector"],
                "country": r["Country"],
                "project": "CAP",
                "runnable": False,
                "ticker": r.get("Ticker/Listing", ""),
            }
        )
    return firms


def build_meta() -> dict:
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.strip()
    wb_inputs = load_workbook_inputs(WORKBOOK)
    return {
        "engine": "ti_framework",
        "engine_version": pkg_version("ti-framework"),
        "engine_git_sha": sha,
        "workbook": WORKBOOK.name,
        "workbook_sha256": hashlib.sha256(WORKBOOK.read_bytes()).hexdigest()[:16],
        "build_date": datetime.now(UTC).isoformat(timespec="seconds"),
        "collection_status": {
            "countries_loaded": len(wb_inputs.countries),
            "missing_inputs": wb_inputs.missing_inputs,
            "warnings": wb_inputs.warnings,
        },
    }


# slugs whose fixture country benchmarks are refreshed from the workbook at build time —
# the workbook stays the single source of truth for Layer 1 (grid, S2 rates, status).
# ReferenceCo is excluded: it is the frozen validation case (NOTES.md D4).
MERGE_WORKBOOK = {"toyota", "hyundai"}


def merge_workbook_benchmarks(fx, workbook_countries) -> None:
    """Overwrite fixture Layer-1 values with collected workbook values where present.

    Fixture keeps anything the workbook has not collected (e.g. Tier C S1/S3 estimates)
    — no collected value is ever shadowed by an estimate, and no empty workbook cell
    ever erases a documented estimate.
    """
    for code, c in fx.countries.items():
        wb = workbook_countries.get(code)
        if wb is None:
            continue
        if wb.grid_intensity is not None:
            c.grid_intensity = wb.grid_intensity
        for attr in ("r_fleet", "r_power"):
            for s in ("s1", "s2", "s3", "s2_upper"):
                v = getattr(getattr(wb, attr), s)
                if v is not None:
                    setattr(getattr(c, attr), s, v)
        c.status = wb.status


def run_firm(slug: str, fixture_path: Path) -> dict:
    fx = load_fixture(fixture_path)
    if slug in MERGE_WORKBOOK:
        merge_workbook_benchmarks(fx, load_workbook_inputs(WORKBOOK).countries)
    result = run(
        fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config,
        analysis_level=fx.analysis_level, layer1_method=fx.layer1_method,
    )
    payload = to_json_dict(result)
    payload["sensitivity"] = run_sensitivity(
        fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config
    )
    payload["inputs"] = json.loads(fixture_path.read_text())  # calculator prefill
    payload["inputs"].pop("expected", None)
    return payload


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = build_meta()
    firms = build_universe()

    for firm in firms:
        if not firm["runnable"]:
            continue
        payload = run_firm(firm["slug"], FIXTURES[firm["slug"]])
        payload["provenance"] = {k: meta[k] for k in
                                 ("engine_version", "engine_git_sha", "workbook", "build_date")}
        (OUT / f"{firm['slug']}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False)
        )
        print(f"built {firm['slug']}.json  (TI_cohort S2 = "
              f"{payload['cohorts']['S2']['total_tCO2e']:,.1f} tCO2e)")

    (OUT / "firms.json").write_text(json.dumps(firms, indent=2, ensure_ascii=False))
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"built firms.json ({len(firms)} firms, "
          f"{sum(f['runnable'] for f in firms)} runnable) and meta.json -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
