#!/usr/bin/env python3
"""Verify the complete published inventory, provenance, and recomputed report contract."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from numbers import Real
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ti-framework"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_dataset import build_by_year, build_contract, build_countries  # noqa: E402
from ti_framework.core.scenarios import run  # noqa: E402
from ti_framework.core.sensitivity import run_sensitivity  # noqa: E402
from ti_framework.io.fixtures import parse_fixture  # noqa: E402
from ti_framework.report.outputs import to_json_dict  # noqa: E402


def json_sha256(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(REPO)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def compare_values(actual: object, expected: object, path: str, errors: list[str]) -> None:
    """Deep comparison with tight numeric tolerance and useful JSON paths."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        actual_keys = set(actual)
        expected_keys = set(expected)
        if actual_keys != expected_keys:
            errors.append(
                f"{path}: keys differ "
                f"(missing={sorted(expected_keys - actual_keys)}, extra={sorted(actual_keys - expected_keys)})"
            )
            return
        for key in sorted(actual_keys):
            compare_values(actual[key], expected[key], f"{path}.{key}", errors)
        return
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            errors.append(f"{path}: length differs ({len(actual)} != {len(expected)})")
            return
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected, strict=True)):
            compare_values(actual_item, expected_item, f"{path}[{index}]", errors)
        return
    if (
        isinstance(actual, Real)
        and not isinstance(actual, bool)
        and isinstance(expected, Real)
        and not isinstance(expected, bool)
    ):
        if not math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-9):
            errors.append(f"{path}: numeric value differs ({actual} != {expected})")
        return
    if actual != expected:
        errors.append(f"{path}: value differs ({actual!r} != {expected!r})")


def main() -> int:
    published = REPO / "data" / "published"
    firms = json.loads((published / "firms.json").read_text())
    meta = json.loads((published / "meta.json").read_text())
    countries = json.loads((published / "countries.json").read_text())
    errors: list[str] = []
    runnable = [firm for firm in firms if firm["runnable"]]
    expected_files = {
        "contract.json",
        "countries.json",
        "firms.json",
        "meta.json",
        *(f"{firm['slug']}.json" for firm in runnable),
    }
    actual_files = {path.name for path in published.glob("*.json")}
    if actual_files != expected_files:
        errors.append(
            "published file inventory differs "
            f"(missing={sorted(expected_files - actual_files)}, stale={sorted(actual_files - expected_files)})"
        )

    payloads: dict[str, dict] = {}
    for firm in firms:
        if not firm["runnable"]:
            continue
        slug = firm["slug"]
        report_path = published / f"{slug}.json"
        if not report_path.exists():
            continue
        payload = json.loads(report_path.read_text())
        payloads[slug] = payload
        if json_sha256(payload["inputs"]) != payload["provenance"]["input_sha256"]:
            errors.append(f"{slug}: input_sha256 mismatch")
            continue
        fx = parse_fixture(payload["inputs"])
        run_result = run(
            fx.firm,
            fx.cohort_year,
            fx.placements,
            fx.countries,
            fx.support,
            fx.config,
            analysis_level=fx.analysis_level,
            layer1_method=fx.layer1_method,
        )
        recomputed = to_json_dict(run_result)
        recomputed["sensitivity"] = run_sensitivity(
            fx.firm,
            fx.cohort_year,
            fx.placements,
            fx.countries,
            fx.support,
            fx.config,
        )
        recomputed["by_year"] = build_by_year(payload["inputs"], fx)
        for key in (
            "firm",
            "cohort_year",
            "cohorts",
            "portfolio",
            "crossover",
            "data_quality",
            "sensitivity",
            "by_year",
        ):
            compare_values(recomputed[key], payload.get(key), f"{slug}.{key}", errors)

        expected_provenance = {
            "engine_version": meta["engine_version"],
            "engine_source_sha256": meta["engine_source_sha256"],
            "workbook": meta["workbook"],
            "workbook_sha256": meta["workbook_sha256"],
            "input_sha256": json_sha256(payload["inputs"]),
            "dataset_sha256": meta["dataset_sha256"],
        }
        compare_values(
            expected_provenance,
            payload.get("provenance"),
            f"{slug}.provenance",
            errors,
        )

    real_payloads = {
        firm["slug"]: payloads[firm["slug"]]
        for firm in runnable
        if not firm.get("illustrative") and firm["slug"] in payloads
    }
    try:
        recomputed_countries, recomputed_support = build_countries(real_payloads)
    except ValueError as exc:
        errors.append(str(exc))
        recomputed_countries, recomputed_support = [], {}
    compare_values(recomputed_countries, countries, "countries", errors)
    compare_values(recomputed_support, meta.get("support_contract"), "meta.support_contract", errors)
    if payloads:
        try:
            recomputed_contract = build_contract(payloads)
        except ValueError as exc:
            errors.append(str(exc))
            recomputed_contract = {}
        contract = json.loads((published / "contract.json").read_text())
        compare_values(recomputed_contract, contract, "contract", errors)

    expected_dataset_sha = json_sha256(
        {
            "countries": countries,
            "firms": firms,
            "inputs": {
                slug: payload["provenance"]["input_sha256"]
                for slug, payload in sorted(payloads.items())
            },
            "engine_source_sha256": meta["engine_source_sha256"],
            "workbook_sha256": meta["workbook_sha256"],
        }
    )
    if meta["dataset_sha256"] != expected_dataset_sha:
        errors.append("meta.dataset_sha256 mismatch")

    engine_dir = REPO / "ti-framework"
    engine_paths = list((engine_dir / "ti_framework").rglob("*.py")) + [
        engine_dir / "pyproject.toml"
    ]
    if meta["engine_source_sha256"] != tree_sha256(engine_paths):
        errors.append("meta.engine_source_sha256 mismatch")
    workbook = engine_dir / "data" / meta["workbook"]
    if meta["workbook_sha256"] != file_sha256(workbook):
        errors.append("meta.workbook_sha256 mismatch")
    if meta["compute_service_sha256"] != file_sha256(REPO / "api" / "compute.py"):
        errors.append("meta.compute_service_sha256 mismatch")
    for name, expected_hash in meta["target_sources_sha256"].items():
        if expected_hash != file_sha256(REPO / name):
            errors.append(f"meta.target_sources_sha256.{name} mismatch")

    if errors:
        print(f"check_published: FAIL ({len(errors)} problems)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        "check_published: OK — inventory, provenance, country contract, and every "
        "runnable report fully recompute from published inputs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
