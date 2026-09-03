from __future__ import annotations

import pytest

from ti_framework.alignment import (
    AlignmentStatus,
    BenchmarkPoint,
    ComparisonMode,
    Coverage,
    EvidenceClass,
    MetricPoint,
    TargetRelation,
    assess_alignment,
    get_sector_profile,
)


def metric(**changes) -> MetricPoint:
    values = {
        "metric_id": "zev_sales_share",
        "sector": "automotive",
        "company_id": "toyota",
        "geography": "DE",
        "observation_year": 2024,
        "value": 0.12,
        "unit": "fraction",
        "source_ids": ("eea-2024-final",),
        "evidence_class": EvidenceClass.REGULATORY_DATASET,
        "scope": {"vehicle_class": "M1"},
        "derivation": "eligible registrations / mapped registrations",
    }
    values.update(changes)
    return MetricPoint(**values)


def benchmark(**changes) -> BenchmarkPoint:
    values = {
        "benchmark_id": "eu-zev-2030",
        "metric_id": "zev_sales_share",
        "sector": "automotive",
        "geography": "EU",
        "benchmark_type": "vehicle sales policy",
        "authority_status": "illustrative test benchmark",
        "comparison_mode": ComparisonMode.DIRECT,
        "relation": TargetRelation.AT_LEAST,
        "source_ids": ("eu-policy",),
        "value": 0.30,
        "unit": "fraction",
        "target_year": 2030,
        "applicable_geographies": ("DE",),
    }
    values.update(changes)
    return BenchmarkPoint(**values)


def coverage() -> Coverage:
    return Coverage(900, 1000, "registrations", unmatched_records=7)


def test_at_least_margin_is_positive_only_when_target_met() -> None:
    result = assess_alignment(metric(value=0.35), benchmark(), coverage())

    assert result.status is AlignmentStatus.AVAILABLE
    assert result.alignment_margin == pytest.approx(0.05)
    assert result.meets_target is True
    assert result.coverage.ratio == 0.9


def test_at_most_margin_has_consistent_direction() -> None:
    result = assess_alignment(
        metric(metric_id="generation_emissions_intensity", sector="power", value=450, unit="kgCO2e/MWh"),
        benchmark(
            benchmark_id="power-limit",
            metric_id="generation_emissions_intensity",
            sector="power",
            value=300,
            unit="kgCO2e/MWh",
            relation=TargetRelation.AT_MOST,
        ),
        coverage(),
    )

    assert result.alignment_margin == -150
    assert result.meets_target is False


def test_sector_pathway_is_context_only_not_a_numeric_gap() -> None:
    contextual = benchmark(
        benchmark_id="de-transport-path",
        comparison_mode=ComparisonMode.CONTEXTUAL,
        relation=TargetRelation.CONTEXT_ONLY,
        value=None,
        unit=None,
        target_year=None,
    )

    result = assess_alignment(metric(), contextual, coverage())

    assert result.status is AlignmentStatus.CONTEXT_ONLY
    assert result.alignment_margin is None
    assert result.meets_target is None


def test_contextual_benchmark_accepts_range_but_never_creates_a_gap() -> None:
    contextual = benchmark(
        benchmark_id="jp-renewables-2040",
        metric_id="renewable_generation_share",
        sector="power",
        geography="JP",
        comparison_mode=ComparisonMode.CONTEXTUAL,
        relation=TargetRelation.CONTEXT_ONLY,
        value=None,
        value_min=0.4,
        value_max=0.5,
        unit="fraction",
        target_year=2040,
        applicable_geographies=(),
    )

    result = assess_alignment(
        metric(
            metric_id="renewable_generation_share",
            sector="power",
            geography="JP",
            value=0.2,
        ),
        contextual,
        coverage(),
    )

    assert result.status is AlignmentStatus.CONTEXT_ONLY
    assert result.alignment_margin is None
    assert result.meets_target is None


def test_benchmark_rejects_partial_or_inverted_ranges() -> None:
    with pytest.raises(ValueError, match="both value_min and value_max"):
        benchmark(
            comparison_mode=ComparisonMode.CONTEXTUAL,
            relation=TargetRelation.CONTEXT_ONLY,
            value=None,
            value_min=0.4,
        )
    with pytest.raises(ValueError, match="cannot exceed"):
        benchmark(
            comparison_mode=ComparisonMode.CONTEXTUAL,
            relation=TargetRelation.CONTEXT_ONLY,
            value=None,
            value_min=0.5,
            value_max=0.4,
        )


def test_unit_mismatch_fails_closed() -> None:
    result = assess_alignment(metric(unit="percent"), benchmark(), coverage())

    assert result.status is AlignmentStatus.NOT_COMPARABLE
    assert result.reason == "unit differs"


def test_power_profile_preserves_technology_decomposition_requirement() -> None:
    profile = get_sector_profile("power")

    assert profile.implementation_status == "pilot"
    assert "generation technology" in profile.required_dimensions
    assert any("masking" in risk for risk in profile.boundary_risks)
