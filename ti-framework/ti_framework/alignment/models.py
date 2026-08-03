# SPDX-License-Identifier: GPL-3.0-or-later
"""Evidence-first, sector-neutral alignment contracts.

The original TI calculation engine models use-phase emissions over a product life.  These
contracts serve a different public-product boundary: compare an observed company metric with
an official market benchmark only when the metric definition and unit are compatible.  A
sector pathway or economy-wide NDC may still be returned as context, but cannot produce a
numeric company gap unless a separately sourced translation exists.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from math import isfinite


class ComparisonMode(StrEnum):
    """Whether a benchmark supports arithmetic or context only."""

    DIRECT = "direct"
    CONTEXTUAL = "contextual"


class TargetRelation(StrEnum):
    """How a company value satisfies a directly comparable target."""

    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    CONTEXT_ONLY = "context_only"


class EvidenceClass(StrEnum):
    """Provenance class; never silently collapsed into a single quality score."""

    OFFICIAL_PRIMARY = "official_primary"
    REGULATORY_DATASET = "regulatory_dataset"
    COMPANY_REPORTED = "company_reported"
    LICENSED_REGISTRY = "licensed_registry"
    PROJECT_DERIVED = "project_derived"
    INDEPENDENT_SECONDARY = "independent_secondary"


class AlignmentStatus(StrEnum):
    AVAILABLE = "available"
    CONTEXT_ONLY = "context_only"
    NOT_COMPARABLE = "not_comparable"
    NOT_AVAILABLE = "not_available"


@dataclass(frozen=True)
class SourceRef:
    """A traceable source record used by company metrics or benchmarks."""

    source_id: str
    title: str
    publisher: str
    url: str
    evidence_class: EvidenceClass
    published_date: str | None = None
    accessed_date: str | None = None
    license: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class MetricPoint:
    """One observed company metric, normally aggregated from disclosed activity data."""

    metric_id: str
    sector: str
    company_id: str
    geography: str
    observation_year: int
    value: float
    unit: str
    source_ids: tuple[str, ...]
    evidence_class: EvidenceClass
    scope: dict[str, str] = field(default_factory=dict)
    derivation: str | None = None

    def __post_init__(self) -> None:
        if not self.metric_id or not self.sector or not self.company_id or not self.geography:
            raise ValueError("metric identity fields must be non-empty")
        if not isfinite(self.value):
            raise ValueError("metric value must be finite")
        if not self.unit:
            raise ValueError("metric unit must be non-empty")
        if not self.source_ids:
            raise ValueError("metric must cite at least one source")


@dataclass(frozen=True)
class BenchmarkPoint:
    """One market target or contextual pathway with explicit comparability."""

    benchmark_id: str
    metric_id: str
    sector: str
    geography: str
    benchmark_type: str
    authority_status: str
    comparison_mode: ComparisonMode
    relation: TargetRelation
    source_ids: tuple[str, ...]
    value: float | None = None
    value_min: float | None = None
    value_max: float | None = None
    unit: str | None = None
    target_year: int | None = None
    applicable_geographies: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.benchmark_id or not self.metric_id or not self.sector or not self.geography:
            raise ValueError("benchmark identity fields must be non-empty")
        if not self.source_ids:
            raise ValueError("benchmark must cite at least one source")
        if (self.value_min is None) != (self.value_max is None):
            raise ValueError("benchmark range needs both value_min and value_max")
        if self.value_min is not None and self.value_max is not None:
            if not isfinite(self.value_min) or not isfinite(self.value_max):
                raise ValueError("benchmark range must be finite")
            if self.value_min > self.value_max:
                raise ValueError("benchmark value_min cannot exceed value_max")
        if self.comparison_mode is ComparisonMode.DIRECT:
            if self.relation is TargetRelation.CONTEXT_ONLY:
                raise ValueError("a direct benchmark needs an at_least or at_most relation")
            if self.value is None or not isfinite(self.value):
                raise ValueError("a direct benchmark needs a finite value")
            if not self.unit or self.target_year is None:
                raise ValueError("a direct benchmark needs unit and target_year")
            if self.value_min is not None:
                raise ValueError("a direct benchmark cannot use a contextual range")
        elif self.relation is not TargetRelation.CONTEXT_ONLY:
            raise ValueError("a contextual benchmark must use relation=context_only")
        elif self.value is not None or self.value_min is not None:
            if not self.unit or self.target_year is None:
                raise ValueError("a numerical contextual benchmark needs unit and target_year")

    def applies_to(self, geography: str) -> bool:
        return geography == self.geography or geography in self.applicable_geographies


@dataclass(frozen=True)
class Coverage:
    """Activity-weighted mapping coverage for the company metric."""

    mapped_activity: float
    reported_activity: float
    activity_unit: str
    unmatched_records: int = 0

    def __post_init__(self) -> None:
        if not all(isfinite(v) for v in (self.mapped_activity, self.reported_activity)):
            raise ValueError("coverage values must be finite")
        if self.reported_activity < 0 or self.mapped_activity < 0:
            raise ValueError("coverage values cannot be negative")
        if self.mapped_activity > self.reported_activity:
            raise ValueError("mapped activity cannot exceed reported activity")
        if self.unmatched_records < 0:
            raise ValueError("unmatched_records cannot be negative")
        if not self.activity_unit:
            raise ValueError("coverage activity_unit must be non-empty")

    @property
    def ratio(self) -> float | None:
        if self.reported_activity == 0:
            return None
        return self.mapped_activity / self.reported_activity


@dataclass(frozen=True)
class AlignmentResult:
    """Auditable result. Positive margin always means meeting or exceeding the target."""

    status: AlignmentStatus
    company_metric: MetricPoint
    benchmark: BenchmarkPoint
    coverage: Coverage
    alignment_margin: float | None
    margin_unit: str | None
    meets_target: bool | None
    reason: str | None
    warnings: tuple[str, ...]
    method_version: str = "alignment-v2"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["coverage"]["ratio"] = self.coverage.ratio
        return payload


def assess_alignment(
    company_metric: MetricPoint,
    benchmark: BenchmarkPoint,
    coverage: Coverage,
) -> AlignmentResult:
    """Compare like with like and fail closed for incompatible scopes or units."""

    warnings: list[str] = []
    if company_metric.sector != benchmark.sector:
        return _not_comparable(company_metric, benchmark, coverage, "sector differs")
    if company_metric.metric_id != benchmark.metric_id:
        return _not_comparable(company_metric, benchmark, coverage, "metric definition differs")
    if not benchmark.applies_to(company_metric.geography):
        return _not_comparable(company_metric, benchmark, coverage, "geography is out of scope")
    if benchmark.comparison_mode is ComparisonMode.CONTEXTUAL:
        return AlignmentResult(
            status=AlignmentStatus.CONTEXT_ONLY,
            company_metric=company_metric,
            benchmark=benchmark,
            coverage=coverage,
            alignment_margin=None,
            margin_unit=None,
            meets_target=None,
            reason="benchmark is policy context and does not share a directly comparable target",
            warnings=(),
        )
    if company_metric.unit != benchmark.unit:
        return _not_comparable(company_metric, benchmark, coverage, "unit differs")

    if company_metric.observation_year != benchmark.target_year:
        warnings.append(
            "snapshot year differs from target year; margin is distance to the target, not "
            "proof of current regulatory compliance"
        )
    assert benchmark.value is not None  # enforced by BenchmarkPoint
    if benchmark.relation is TargetRelation.AT_LEAST:
        margin = company_metric.value - benchmark.value
    else:
        margin = benchmark.value - company_metric.value
    return AlignmentResult(
        status=AlignmentStatus.AVAILABLE,
        company_metric=company_metric,
        benchmark=benchmark,
        coverage=coverage,
        alignment_margin=margin,
        margin_unit=company_metric.unit,
        meets_target=margin >= 0,
        reason=None,
        warnings=tuple(warnings),
    )


def _not_comparable(
    metric: MetricPoint,
    benchmark: BenchmarkPoint,
    coverage: Coverage,
    reason: str,
) -> AlignmentResult:
    return AlignmentResult(
        status=AlignmentStatus.NOT_COMPARABLE,
        company_metric=metric,
        benchmark=benchmark,
        coverage=coverage,
        alignment_margin=None,
        margin_unit=None,
        meets_target=None,
        reason=reason,
        warnings=(),
    )
