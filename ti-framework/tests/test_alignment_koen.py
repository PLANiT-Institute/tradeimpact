from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data-pipeline"))

from adapters.power_koen import SNAPSHOT, build_records  # noqa: E402


def test_koen_snapshot_is_hashed_and_preserves_reported_totals() -> None:
    snapshot = json.loads(SNAPSHOT.read_text())
    records = build_records()

    assert snapshot["adapter_version"] == "koen-korea-2024-v1"
    assert len(snapshot["content_sha256"]) == 64
    assert snapshot["company"]["generation_gwh"] == 39_660
    assert snapshot["company"]["scope1_reported_total_tco2e"] == 30_606_585
    assert snapshot["company"]["scope2_reported_total_tco2e"] == 103_752
    assert len(records["sources"]) == 2


def test_koen_plant_rows_do_not_reconcile_and_intensity_stays_missing() -> None:
    snapshot = json.loads(SNAPSHOT.read_text())
    metrics = build_records()["company_metrics"]
    scope1_sum = sum(snapshot["company"]["scope1_plant_tco2e"].values())
    scope2_sum = sum(snapshot["company"]["scope2_plant_tco2e"].values())

    assert snapshot["company"]["scope1_reported_total_tco2e"] - scope1_sum == -2_000
    assert snapshot["company"]["scope2_reported_total_tco2e"] - scope2_sum == -269
    assert {row["metric_id"] for row in metrics} == {
        "reported_generation",
        "scope1_emissions",
        "scope2_emissions",
    }
    assert all(row["metric_id"] != "generation_emissions_intensity" for row in metrics)
    assert "gross/net basis is not stated" in metrics[0]["derivation"]


def test_korea_electricity_plan_is_context_only() -> None:
    benchmarks = build_records()["benchmarks"]

    assert len(benchmarks) == 3
    assert all(row["comparison_mode"] == "contextual" for row in benchmarks)
    assert all(row["relation"] == "context_only" for row in benchmarks)
    assert [(row["target_year"], row["value"]) for row in benchmarks] == [
        (2030, 145.9),
        (2030, 0.53),
        (2038, 0.707),
    ]
    assert all("National power-system context only" in row["notes"] for row in benchmarks)
