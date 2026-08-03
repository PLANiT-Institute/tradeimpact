from __future__ import annotations

import json
from pathlib import Path

import pytest

from ti_framework.alignment import TradeImpactService

REPO = Path(__file__).resolve().parents[2]


def test_published_service_exposes_multisector_registry() -> None:
    service = TradeImpactService(REPO / "data" / "published")

    payload = service.list_sectors()

    assert payload["status"] == "available"
    assert {row["sector_id"] for row in payload["sectors"]} == {
        "automotive",
        "power",
        "shipping",
        "steel",
        "petrochemicals",
    }


def test_published_toyota_eu27_snapshot_is_source_backed() -> None:
    service = TradeImpactService(REPO / "data" / "published")

    payload = service.get_company_snapshot("toyota", 2024, "EU27")

    assert payload["status"] == "available"
    assert len(payload["metrics"]) == 7
    intensity = next(
        row for row in payload["metrics"] if row["metric_id"] == "new_vehicle_tailpipe_intensity"
    )
    assert intensity["value"] == pytest.approx(107.07329255505938)
    assert intensity["coverage"]["mapped_activity"] == 803_042
    assert intensity["coverage"]["reported_activity"] == 803_094


def test_published_jera_snapshot_is_assured_and_policy_is_context_only() -> None:
    service = TradeImpactService(REPO / "data" / "published")

    snapshot = service.get_company_snapshot("jera", 2024, "JP")
    benchmarks = service.get_market_benchmarks("power", "JP")
    alignment = service.assess_company_alignment(
        "jera", "power", "JP", 2024, "generation_emissions_intensity", 2030
    )

    assert snapshot["status"] == "available"
    assert len(snapshot["metrics"]) == 2
    intensity = next(
        row for row in snapshot["metrics"] if row["metric_id"] == "generation_emissions_intensity"
    )
    assert intensity["value"] == 520
    assert intensity["coverage"]["reported_activity"] == 242_000_000
    assert benchmarks["status"] == "available"
    assert len(benchmarks["benchmarks"]) == 3
    assert all(row["comparison_mode"] == "contextual" for row in benchmarks["benchmarks"])
    assert alignment["status"] == "not_available"
    assert "no directly comparable benchmark" in alignment["reason"]


def test_published_koen_snapshot_exposes_data_quality_without_derived_intensity() -> None:
    service = TradeImpactService(REPO / "data" / "published")

    snapshot = service.get_company_snapshot("koen", 2024, "KR")
    benchmarks = service.get_market_benchmarks("power", "KR")
    alignment = service.assess_company_alignment(
        "koen", "power", "KR", 2024, "generation_emissions_intensity", 2030
    )

    assert snapshot["status"] == "available"
    assert {row["metric_id"] for row in snapshot["metrics"]} == {
        "reported_generation",
        "scope1_emissions",
        "scope2_emissions",
    }
    assert benchmarks["status"] == "available"
    assert len(benchmarks["benchmarks"]) == 3
    assert all(row["comparison_mode"] == "contextual" for row in benchmarks["benchmarks"])
    assert alignment["status"] == "not_available"
    assert "no directly comparable benchmark" in alignment["reason"]


def test_missing_company_data_stays_missing() -> None:
    service = TradeImpactService(REPO / "data" / "published")

    payload = service.get_company_snapshot("hyundai", 2024, "EU27")

    assert payload["status"] == "not_available"
    assert payload["metrics"] == []
    assert "withheld" in payload["reason"]


def test_toyota_target_distance_is_not_labeled_compliance() -> None:
    service = TradeImpactService(REPO / "data" / "published")

    payload = service.assess_company_alignment(
        "toyota", "automotive", "EU27", 2024, "new_vehicle_tailpipe_intensity", 2025
    )

    assert payload["status"] == "available"
    assert payload["alignment_margin"] == pytest.approx(93.6 - 107.07329255505938)
    assert payload["meets_target"] is False
    assert payload["coverage"]["ratio"] == pytest.approx(803_042 / 803_094)
    assert "not proof of current regulatory compliance" in payload["warnings"][0]


def test_power_context_uses_power_pathway_not_transport_pathway() -> None:
    service = TradeImpactService(REPO / "data" / "published")

    power = service.get_market_context("KR", "power")
    automotive = service.get_market_context("KR", "automotive")

    assert power["status"] == "context_only"
    assert power["pathway_rates"] != automotive["pathway_rates"]
    assert power["pathway_rates"]["s2"] == pytest.approx(0.065024)


def test_service_runs_direct_comparison_from_published_contract(tmp_path: Path) -> None:
    files = {
        "firms.json": [{"slug": "demo", "sector": "Power", "runnable": True}],
        "countries.json": [],
        "sources.json": [],
        "company_metrics.json": [
            {
                "metric_id": "generation_emissions_intensity",
                "sector": "power",
                "company_id": "demo",
                "geography": "KR",
                "observation_year": 2024,
                "value": 250,
                "unit": "kgCO2e/MWh",
                "source_ids": ["company-source"],
                "evidence_class": "company_reported",
                "scope": {"generation_basis": "net"},
                "derivation": "reported emissions / net generation",
                "coverage": {
                    "mapped_activity": 95,
                    "reported_activity": 100,
                    "activity_unit": "MWh",
                    "unmatched_records": 1,
                },
            }
        ],
        "benchmarks.json": [
            {
                "benchmark_id": "kr-power-2030",
                "metric_id": "generation_emissions_intensity",
                "sector": "power",
                "geography": "KR",
                "benchmark_type": "power-sector standard",
                "authority_status": "test",
                "comparison_mode": "direct",
                "relation": "at_most",
                "source_ids": ["policy-source"],
                "value": 300,
                "unit": "kgCO2e/MWh",
                "target_year": 2030,
                "applicable_geographies": [],
            }
        ],
    }
    for name, value in files.items():
        (tmp_path / name).write_text(json.dumps(value))
    service = TradeImpactService(tmp_path)

    result = service.assess_company_alignment(
        "demo", "power", "KR", 2024, "generation_emissions_intensity", 2030
    )

    assert result["status"] == "available"
    assert result["alignment_margin"] == 50
    assert result["meets_target"] is True
    assert result["coverage"]["ratio"] == 0.95
