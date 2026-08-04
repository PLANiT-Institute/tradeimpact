from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data-pipeline"))

from adapters.automotive_eea import POWERTRAINS, SNAPSHOT, build_records  # noqa: E402


def test_eea_snapshot_is_aggregated_hashed_and_reproducible() -> None:
    snapshot = json.loads(SNAPSHOT.read_text())
    records = build_records()

    assert snapshot["adapter_version"] == "eea-toyota-eu27-v1"
    assert snapshot["dataset_status"] == "Final"
    assert snapshot["brand_filter"] == "Mk=TOYOTA"
    assert snapshot["query_sha256"]
    assert snapshot["response_sha256"]
    assert records["sources"][0]["snapshot_sha256"] == snapshot["response_sha256"]
    assert len(records["company_metrics"]) == 28 * 8


def test_eea_eu27_metrics_reconcile_without_vehicle_use_estimates() -> None:
    metrics = [
        row for row in build_records()["company_metrics"] if row["geography"] == "EU27"
    ]
    registrations = next(row for row in metrics if row["metric_id"] == "new_vehicle_registrations")
    intensity = next(
        row for row in metrics if row["metric_id"] == "new_vehicle_tailpipe_intensity"
    )
    normalized_load = next(
        row for row in metrics if row["metric_id"] == "normalized_tailpipe_co2_load"
    )
    shares = [row for row in metrics if row["metric_id"] == "powertrain_sales_share"]

    assert registrations["value"] == 803_094
    assert intensity["value"] == pytest.approx(107.07329255505938)
    assert intensity["coverage"] == {
        "mapped_activity": 803_042.0,
        "reported_activity": 803_094.0,
        "activity_unit": "registrations",
        "unmatched_records": 52,
    }
    assert {row["scope"]["powertrain"] for row in shares} == set(POWERTRAINS)
    assert sum(row["value"] for row in shares) == pytest.approx(1.0)
    assert normalized_load["value"] == pytest.approx(85_984.351)
    assert normalized_load["unit"] == "tCO2/cohort-1000km"
    assert normalized_load["coverage"] == intensity["coverage"]
    assert "1,000 km" in normalized_load["scope"]["normalization"]
    assert "actual annual distance" in normalized_load["scope"]["emissions_boundary"]
    assert "lifetime" in normalized_load["scope"]["emissions_boundary"]
    metric_ids = {row["metric_id"] for row in metrics}
    assert not any("lifetime" in metric_id for metric_id in metric_ids)
    assert not any("vkt" in metric_id for metric_id in metric_ids)
    serialized = json.dumps(metrics).lower()
    assert "vkt" not in serialized
    assert "vehicle_km" not in serialized
    assert "tco2e" not in serialized


def test_eea_country_normalized_loads_reconcile_to_eu27() -> None:
    metrics = build_records()["company_metrics"]
    eu27 = next(
        row
        for row in metrics
        if row["geography"] == "EU27"
        and row["metric_id"] == "normalized_tailpipe_co2_load"
    )
    countries = [
        row
        for row in metrics
        if row["geography"] != "EU27"
        and row["metric_id"] == "normalized_tailpipe_co2_load"
    ]

    assert len(countries) == 27
    assert sum(row["value"] for row in countries) == pytest.approx(eu27["value"])
    france = next(row for row in countries if row["geography"] == "FR")
    assert france["value"] == pytest.approx(13_522.581)
    assert france["value"] / eu27["value"] == pytest.approx(0.15726793123088179)


def test_eea_benchmarks_are_adopted_direct_intensity_targets() -> None:
    benchmarks = build_records()["benchmarks"]

    assert [(row["target_year"], row["value"]) for row in benchmarks] == [
        (2025, 93.6),
        (2030, 49.5),
    ]
    assert all(row["metric_id"] == "new_vehicle_tailpipe_intensity" for row in benchmarks)
    assert all(row["comparison_mode"] == "direct" for row in benchmarks)
    assert all(row["relation"] == "at_most" for row in benchmarks)
    assert all("not Toyota's manufacturer-specific compliance target" in row["notes"] for row in benchmarks)
