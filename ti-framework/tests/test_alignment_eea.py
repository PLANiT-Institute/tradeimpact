from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data-pipeline"))

from adapters.automotive_eea import (  # noqa: E402
    HYUNDAI_SNAPSHOT,
    POWERTRAINS,
    SNAPSHOT,
    build_all_records,
    build_records,
)


def test_eea_snapshot_is_aggregated_hashed_and_reproducible() -> None:
    snapshot = json.loads(SNAPSHOT.read_text())
    records = build_records()

    assert snapshot["adapter_version"] == "eea-toyota-eu27-v2"
    assert snapshot["dataset_status"] == "Final"
    assert snapshot["brand_filter"] == "Mk=TOYOTA"
    assert snapshot["query_sha256"]
    assert snapshot["response_sha256"]
    assert records["sources"][0]["snapshot_sha256"] == snapshot["response_sha256"]
    assert len(records["company_metrics"]) == 28 * 7


def test_eea_eu27_observed_metrics_reconcile_without_fixed_distance_load() -> None:
    metrics = [
        row for row in build_records()["company_metrics"] if row["geography"] == "EU27"
    ]
    registrations = next(row for row in metrics if row["metric_id"] == "new_vehicle_registrations")
    intensity = next(
        row for row in metrics if row["metric_id"] == "new_vehicle_tailpipe_intensity"
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
    assert "normalized_tailpipe_co2_load" not in {row["metric_id"] for row in metrics}
    assert "cohort-1000km" not in json.dumps(metrics)


def test_product_cohort_reconciles_destination_model_and_powertrain() -> None:
    cohort = build_records()["product_cohorts"][0]
    records = cohort["records"]

    assert cohort["cohort_id"] == "toyota-eu27-passenger-cars-2024"
    assert cohort["contract_version"] == "export-impact-v1"
    assert cohort["coverage"]["reported_units"] == 803_094
    assert len(records) == 660
    assert sum(row["units"] for row in records) == 803_094
    assert len({row["destination_geography"] for row in records}) == 27
    assert len({row["product_name"] for row in records}) == 72
    assert {row["product_type"] for row in records} == set(POWERTRAINS)
    assert cohort["origin_mapping_status"] == "not_collected"
    assert cohort["coverage"]["mapped_product_name_units"] == 803_092
    assert sum(row["tailpipe_mapped_units"] for row in records) == 803_042
    assert sum(row["electricity_mapped_units"] for row in records) == 34_776


def test_product_channels_route_tailpipe_and_energy_to_destination_sectors() -> None:
    records = build_records()["product_cohorts"][0]["records"]
    bev = next(
        row
        for row in records
        if row["product_type"] == "BEV"
        and row["certified_electricity_kwh_per_km"] is not None
    )
    hev = next(row for row in records if row["product_type"] == "HEV")
    phev = next(row for row in records if row["product_type"] == "PHEV")

    assert bev["use_phase_channel"] == "grid_electricity"
    assert bev["destination_inventory_sector"] == "power"
    assert bev["certified_tailpipe_gco2_per_km"] == 0
    assert bev["certified_electricity_kwh_per_km"] > 0
    assert hev["use_phase_channel"] == "fuel_combustion"
    assert hev["destination_inventory_sector"] == "road_transport"
    assert phev["destination_inventory_sector"] == "road_transport_and_power"


def test_target_hierarchy_retains_proxy_and_ndc_roles() -> None:
    pathways = build_records()["pathways"]
    sector = next(row for row in pathways if row["comparison_role"] == "sector_proxy")
    ndc = next(row for row in pathways if row["comparison_role"] == "fallback_context")

    assert sector["policy_level"] == "regional_sector_pathway"
    assert sector["annual_reduction_rate"] == pytest.approx(0.04344369190911768)
    assert sector["calculation_status"] == "proxy_requires_disclosure"
    assert ndc["reduction_min"] == 0.6625
    assert ndc["reduction_max"] == 0.725
    assert ndc["calculation_status"] == "not_directly_usable"
    assert len(sector["applies_to"]) == 27


def test_readiness_gate_withholds_lifetime_result() -> None:
    readiness = build_records()["impact_readiness"][0]

    assert readiness["status"] == "inputs_incomplete"
    assert readiness["publication_decision"] == "withhold_lifetime_ti"
    assert len(readiness["missing_required_inputs"]) == 9
    assert "unsourced assumptions" in readiness["publication_reason"]


def test_hyundai_uses_the_same_eea_boundary_without_claiming_korean_exports() -> None:
    snapshot = json.loads(HYUNDAI_SNAPSHOT.read_text())
    payload = build_records(company_id="hyundai", include_shared=False)
    cohort = payload["product_cohorts"][0]
    metrics = [row for row in payload["company_metrics"] if row["geography"] == "EU27"]

    assert snapshot["adapter_version"] == "eea-hyundai-eu27-v2"
    assert snapshot["brand_filter"] == "Mk=HYUNDAI"
    assert cohort["cohort_id"] == "hyundai-eu27-passenger-cars-2024"
    assert cohort["coverage"]["reported_units"] == 429_936
    assert len(cohort["records"]) == 626
    assert len({row["destination_geography"] for row in cohort["records"]}) == 27
    assert len({row["product_name"] for row in cohort["records"]}) == 67
    assert cohort["origin_mapping_status"] == "not_collected"
    assert cohort["origin_context"]["comparability"] == "context_only_not_cohort_mapping"
    assert "does not map individual registrations" in cohort["origin_context"]["notes"]
    registrations = next(row for row in metrics if row["metric_id"] == "new_vehicle_registrations")
    intensity = next(row for row in metrics if row["metric_id"] == "new_vehicle_tailpipe_intensity")
    assert registrations["value"] == 429_936
    assert intensity["value"] == pytest.approx(112.8914806759633)


def test_combined_automotive_adapter_publishes_shared_policy_sources_once() -> None:
    payload = build_all_records()

    assert {row["company_id"] for row in payload["product_cohorts"]} == {
        "toyota",
        "hyundai",
    }
    assert len(payload["impact_readiness"]) == 2
    assert len(payload["pathways"]) == 2
    source_ids = [row["source_id"] for row in payload["sources"]]
    assert len(source_ids) == len(set(source_ids))
