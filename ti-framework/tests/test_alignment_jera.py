from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data-pipeline"))

from adapters.power_jera import SNAPSHOT, build_records  # noqa: E402


def test_jera_snapshot_is_hashed_and_matches_independent_assurance() -> None:
    snapshot = json.loads(SNAPSHOT.read_text())
    records = build_records()

    assert snapshot["adapter_version"] == "jera-japan-fy2024-v1"
    assert snapshot["content_sha256"]
    assert snapshot["company"]["net_generation_billion_kwh"] == 242
    assert snapshot["company"]["intensity_kgco2e_per_kwh"] == 0.52
    assert snapshot["company"]["net_generation_billion_kwh"] == snapshot["assurance"][
        "net_generation_billion_kwh"
    ]
    assert snapshot["company"]["intensity_kgco2e_per_kwh"] == snapshot["assurance"][
        "intensity_kgco2e_per_kwh"
    ]
    assert len(records["sources"]) == 4
    assured = [source for source in records["sources"] if source.get("snapshot_sha256")]
    assert len(assured) == 2
    assert all(len(source["snapshot_sha256"]) == 64 for source in assured)


def test_jera_metrics_reconcile_without_estimating_generation_mix() -> None:
    metrics = build_records()["company_metrics"]
    generation = next(row for row in metrics if row["metric_id"] == "net_generation")
    intensity = next(
        row for row in metrics if row["metric_id"] == "generation_emissions_intensity"
    )

    assert generation["value"] == 242_000_000
    assert intensity["value"] == 520
    assert intensity["coverage"] == {
        "mapped_activity": 242_000_000.0,
        "reported_activity": 242_000_000.0,
        "activity_unit": "MWh",
        "unmatched_records": 0,
    }
    serialized = json.dumps(metrics).lower()
    assert "renewable_generation_share" not in serialized
    assert "thermal_generation_share" not in serialized


def test_japan_targets_are_explicitly_contextual() -> None:
    benchmarks = build_records()["benchmarks"]

    assert len(benchmarks) == 3
    assert all(row["comparison_mode"] == "contextual" for row in benchmarks)
    assert all(row["relation"] == "context_only" for row in benchmarks)
    renewable = next(row for row in benchmarks if "renewable" in row["metric_id"])
    thermal = next(row for row in benchmarks if "thermal" in row["metric_id"])
    assert (renewable["value_min"], renewable["value_max"]) == (0.4, 0.5)
    assert (thermal["value_min"], thermal["value_max"]) == (0.3, 0.4)
    assert all("National-system context only" in row["notes"] for row in benchmarks)
