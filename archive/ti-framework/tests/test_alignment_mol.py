from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data-pipeline"))

from adapters.shipping_mol import SNAPSHOT, build_records  # noqa: E402


def test_mol_snapshot_is_hashed_and_matches_classnk_assurance() -> None:
    snapshot = json.loads(SNAPSHOT.read_text())
    records = build_records()

    assert snapshot["adapter_version"] == "mol-global-fy2024-v1"
    assert len(snapshot["content_sha256"]) == 64
    assert snapshot["company"]["eeoi_gco2e_per_ton_mile"] == 10.95
    assert snapshot["company"]["eeoi_gco2e_per_ton_mile"] == snapshot["assurance"][
        "intensity_gco2e_per_ton_mile"
    ]
    assert snapshot["company"]["applicable_vessels"] == 783
    assert snapshot["company"]["applicable_vessels"] == snapshot["assurance"][
        "applicable_vessels"
    ]
    assert len(records["sources"]) == 4
    assert all(len(source["snapshot_sha256"]) == 64 for source in records["sources"])


def test_mol_publishes_current_assured_eeoi_without_reconstruction() -> None:
    metrics = build_records()["company_metrics"]

    assert len(metrics) == 1
    assert metrics[0]["metric_id"] == "shipping_eeoi"
    assert metrics[0]["value"] == 10.95
    assert metrics[0]["unit"] == "gCO2e/ton-mile"
    assert metrics[0]["observation_year"] == 2024
    assert metrics[0]["coverage"] == {
        "mapped_activity": 783.0,
        "reported_activity": 783.0,
        "activity_unit": "applicable vessels",
        "unmatched_records": 0,
    }
    assert "no project recomputation" in metrics[0]["derivation"]
    assert "not appropriate for customer-specific" in metrics[0]["scope"][
        "allocation_caveat"
    ]


def test_imo_targets_are_context_only_for_mol() -> None:
    benchmarks = build_records()["benchmarks"]

    assert len(benchmarks) == 3
    assert all(row["comparison_mode"] == "contextual" for row in benchmarks)
    assert all(row["relation"] == "context_only" for row in benchmarks)
    assert benchmarks[0]["value"] == 0.4
    assert (benchmarks[1]["value_min"], benchmarks[1]["value_max"]) == (0.2, 0.3)
    assert (benchmarks[2]["value_min"], benchmarks[2]["value_max"]) == (0.05, 0.1)
    assert all("No company gap is calculated" in row["notes"] for row in benchmarks)
