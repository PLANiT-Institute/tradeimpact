# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only query service shared by the web application and MCP adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from ti_framework.alignment.models import (
    BenchmarkPoint,
    ComparisonMode,
    Coverage,
    EvidenceClass,
    MetricPoint,
    TargetRelation,
    assess_alignment,
)
from ti_framework.alignment.registry import get_sector_profile, list_sector_profiles


class TradeImpactService:
    """Query the content-addressed public dataset without adding hidden assumptions."""

    def __init__(self, published_dir: str | Path) -> None:
        self.published_dir = Path(published_dir)

    def _read(self, name: str) -> Any:
        path = self.published_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"published dataset file not found: {path}")
        return json.loads(path.read_text())

    def list_sectors(self) -> dict[str, object]:
        return {"status": "available", "sectors": list_sector_profiles()}

    def get_sector_requirements(self, sector_id: str) -> dict[str, object]:
        try:
            profile = get_sector_profile(sector_id)
        except KeyError as exc:
            return {"status": "not_available", "reason": str(exc)}
        return {"status": "available", "sector": profile.to_dict()}

    def list_companies(self, sector_id: str | None = None) -> dict[str, object]:
        firms = self._read("firms.json")
        if sector_id:
            wanted = sector_id.strip().lower()
            firms = [firm for firm in firms if _sector_id(firm.get("sector", "")) == wanted]
        return {"status": "available", "companies": firms}

    def get_company_snapshot(
        self,
        company_id: str,
        year: int,
        geography: str | None = None,
    ) -> dict[str, object]:
        firms = self._read("firms.json")
        firm = next((row for row in firms if row.get("slug") == company_id), None)
        if firm is None:
            return {"status": "not_available", "reason": f"unknown company: {company_id}"}
        metrics = self._read("company_metrics.json")
        matches = [
            row
            for row in metrics
            if row.get("company_id") == company_id
            and row.get("observation_year") == year
            and (geography is None or row.get("geography") == geography)
        ]
        if not matches:
            return {
                "status": "not_available",
                "company": firm,
                "requested_scope": {"year": year, "geography": geography},
                "metrics": [],
                "reason": firm.get("note") or "no source-backed company metric for this scope",
            }
        return {"status": "available", "company": firm, "metrics": matches}

    def get_market_context(
        self,
        geography: str,
        sector_id: str,
    ) -> dict[str, object]:
        try:
            profile = get_sector_profile(sector_id)
        except KeyError as exc:
            return {"status": "not_available", "reason": str(exc)}
        countries = self._read("countries.json")
        lookup_geography = "EU" if geography == "EU27" else geography
        country = next((row for row in countries if row.get("code") == lookup_geography), None)
        if country is None:
            return {
                "status": "not_available",
                "reason": f"no operating-country record for {geography}",
            }
        rate_field = "r_power" if profile.sector_id == "power" else "r_fleet"
        return {
            "status": "context_only",
            "sector": profile.sector_id,
            "geography": geography,
            "pathway_rates": country.get(rate_field, {}),
            "benchmark_status": country.get("status"),
            "evidence_tier": country.get("tier"),
            "source": country.get("source"),
            "warnings": country.get("warnings", []),
            "flag_reason": country.get("flag_reason"),
            "reason": (
                "sector pathway rates provide policy context; they are not directly subtracted "
                "from company activity metrics"
            ),
        }

    def get_market_benchmarks(
        self,
        sector_id: str,
        geography: str,
        metric_id: str | None = None,
    ) -> dict[str, object]:
        try:
            get_sector_profile(sector_id)
        except KeyError as exc:
            return {"status": "not_available", "reason": str(exc)}
        rows = self._read("benchmarks.json")
        matches = [
            row
            for row in rows
            if row.get("sector") == sector_id
            and (
                row.get("geography") == geography
                or geography in row.get("applicable_geographies", [])
            )
            and (metric_id is None or row.get("metric_id") == metric_id)
        ]
        return {
            "status": "available" if matches else "not_available",
            "benchmarks": matches,
            "reason": None if matches else "no directly comparable benchmark for this scope",
        }

    def trace_source(self, source_id: str) -> dict[str, object]:
        sources = self._read("sources.json")
        source = next((row for row in sources if row.get("source_id") == source_id), None)
        if source is None:
            return {"status": "not_available", "reason": f"unknown source: {source_id}"}
        return {"status": "available", "source": source}

    def assess_company_alignment(
        self,
        company_id: str,
        sector_id: str,
        geography: str,
        observation_year: int,
        metric_id: str,
        target_year: int,
    ) -> dict[str, object]:
        """Resolve one exact metric/benchmark pair and run the fail-closed comparison."""
        snapshot = self.get_company_snapshot(company_id, observation_year, geography)
        if snapshot["status"] != "available":
            return snapshot
        benchmark_result = self.get_market_benchmarks(sector_id, geography, metric_id)
        if benchmark_result["status"] != "available":
            return benchmark_result
        snapshot_metrics = cast(list[dict[str, Any]], snapshot.get("metrics", []))
        benchmark_rows = cast(
            list[dict[str, Any]], benchmark_result.get("benchmarks", [])
        )
        metric_row = next(
            (
                row
                for row in snapshot_metrics
                if row.get("sector") == sector_id and row.get("metric_id") == metric_id
            ),
            None,
        )
        benchmark_row = next(
            (
                row
                for row in benchmark_rows
                if row.get("target_year") == target_year
            ),
            None,
        )
        if metric_row is None:
            return {"status": "not_available", "reason": "company metric is not available"}
        if benchmark_row is None:
            return {
                "status": "not_available",
                "reason": f"benchmark is not available for target year {target_year}",
            }
        try:
            metric = _metric_from_dict(metric_row)
            benchmark = _benchmark_from_dict(benchmark_row)
            metric_coverage = _coverage_from_dict(metric_row.get("coverage", {}))
        except (KeyError, TypeError, ValueError) as exc:
            return {"status": "not_available", "reason": f"invalid published contract: {exc}"}
        return assess_alignment(metric, benchmark, metric_coverage).to_dict()


def _sector_id(label: str) -> str:
    normalized = label.strip().lower()
    aliases = {
        "automotive": "automotive",
        "power": "power",
        "shipping": "shipping",
        "steel": "steel",
        "petrochemical": "petrochemicals",
        "petrochemicals": "petrochemicals",
    }
    return aliases.get(normalized, normalized)


def _metric_from_dict(row: dict[str, Any]) -> MetricPoint:
    return MetricPoint(
        metric_id=row["metric_id"],
        sector=row["sector"],
        company_id=row["company_id"],
        geography=row["geography"],
        observation_year=int(row["observation_year"]),
        value=float(row["value"]),
        unit=row["unit"],
        source_ids=tuple(row["source_ids"]),
        evidence_class=EvidenceClass(row["evidence_class"]),
        scope=dict(row.get("scope", {})),
        derivation=row.get("derivation"),
    )


def _benchmark_from_dict(row: dict[str, Any]) -> BenchmarkPoint:
    return BenchmarkPoint(
        benchmark_id=row["benchmark_id"],
        metric_id=row["metric_id"],
        sector=row["sector"],
        geography=row["geography"],
        benchmark_type=row["benchmark_type"],
        authority_status=row["authority_status"],
        comparison_mode=ComparisonMode(row["comparison_mode"]),
        relation=TargetRelation(row["relation"]),
        source_ids=tuple(row["source_ids"]),
        value=float(row["value"]) if row.get("value") is not None else None,
        value_min=float(row["value_min"]) if row.get("value_min") is not None else None,
        value_max=float(row["value_max"]) if row.get("value_max") is not None else None,
        unit=row.get("unit"),
        target_year=int(row["target_year"]) if row.get("target_year") is not None else None,
        applicable_geographies=tuple(row.get("applicable_geographies", [])),
        notes=row.get("notes"),
    )


def _coverage_from_dict(row: dict[str, Any]) -> Coverage:
    return Coverage(
        mapped_activity=float(row["mapped_activity"]),
        reported_activity=float(row["reported_activity"]),
        activity_unit=row["activity_unit"],
        unmatched_records=int(row.get("unmatched_records", 0)),
    )
