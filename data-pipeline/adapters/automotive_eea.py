#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""EEA passenger-car adapter for the Toyota 2024 EU27 pilot.

The remote EEA API is used only by ``--refresh``. Normal dataset builds transform the committed
aggregation snapshot, so CI and reviewers reproduce the same result without a live dependency.
The adapter publishes reporting-year registrations, powertrain shares, and registration-weighted
WLTP intensity. It does not estimate vehicle use, lifetime, or greenhouse-gas tonnes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "data-pipeline" / "source-snapshots" / "eea_toyota_2024_final.json"
API = "https://co2cars.apps.eea.europa.eu/tools/api"
DATASET_URL = "https://co2cars.apps.eea.europa.eu/"
TARGET_URL = (
    "https://www.eea.europa.eu/en/analysis/indicators/"
    "co2-performance-of-new-passenger"
)
REGULATION_URL = "https://eur-lex.europa.eu/eli/reg/2019/631/2025-07-09/eng"
EU27 = (
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
)
POWERTRAINS = ("BEV", "FCEV", "PHEV", "HEV", "ICE_OTHER")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def build_query() -> dict[str, Any]:
    powertrain_filters = {
        "BEV": {"term": {"Fm": "E"}},
        "FCEV": {"term": {"Ft": "hydrogen"}},
        "PHEV": {"term": {"Fm": "P"}},
        "HEV": {"term": {"Fm": "H"}},
        "ICE_OTHER": {
            "bool": {
                "must_not": [
                    {"terms": {"Fm": ["E", "P", "H"]}},
                    {"term": {"Ft": "hydrogen"}},
                ]
            }
        },
    }
    subaggregations = {
        "registrations": {"sum": {"field": "r"}},
        "co2_mapped": {
            "filter": {"exists": {"field": "Ewltp__g_km_"}},
            "aggs": {
                "registrations": {"sum": {"field": "r"}},
                "weighted_average": {
                    "weighted_avg": {
                        "value": {"field": "Ewltp__g_km_"},
                        "weight": {"field": "r"},
                    }
                },
            },
        },
        "powertrains": {
            "filters": {"filters": powertrain_filters},
            "aggs": {"registrations": {"sum": {"field": "r"}}},
        },
    }
    return {
        "track_total_hits": True,
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {"term": {"year": 2024}},
                    {"match": {"scStatus": "Final"}},
                    {"term": {"Mk": "TOYOTA"}},
                    {"terms": {"MS": list(EU27)}},
                ]
            }
        },
        "aggs": {
            **subaggregations,
            "countries": {
                "terms": {"field": "MS", "size": 30, "order": {"_key": "asc"}},
                "aggs": subaggregations,
            },
        },
    }


def refresh_snapshot(path: Path = SNAPSHOT, accessed_date: str = "2026-08-03") -> None:
    query = build_query()
    url = f"{API}?source={urllib.parse.quote(json.dumps(query, separators=(',', ':')))}"
    request = urllib.request.Request(url, headers={"User-Agent": "tradeimpact/0.1 source audit"})
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310
        body = json.load(response)
    payload = {
        "adapter_version": "eea-toyota-eu27-v1",
        "accessed_date": accessed_date,
        "dataset_status": "Final",
        "dataset_year": 2024,
        "brand_filter": "Mk=TOYOTA",
        "geography": "EU27",
        "source_page": DATASET_URL,
        "api_endpoint": API,
        "query": query,
        "query_sha256": _sha256(query),
        "response_sha256": _sha256(body),
        "response": body,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def build_records(path: Path = SNAPSHOT) -> dict[str, list[dict[str, Any]]]:
    snapshot = json.loads(path.read_text())
    if snapshot["query_sha256"] != _sha256(snapshot["query"]):
        raise ValueError("EEA snapshot query hash mismatch")
    if snapshot["response_sha256"] != _sha256(snapshot["response"]):
        raise ValueError("EEA snapshot response hash mismatch")
    if snapshot["query"] != build_query():
        raise ValueError("EEA snapshot was not produced by the current adapter query")
    response = snapshot["response"]
    if response.get("timed_out") or response.get("_shards", {}).get("failed"):
        raise ValueError("EEA query was incomplete")
    aggregations = response["aggregations"]
    _validate_aggregate(aggregations, expected_countries=set(EU27))

    source_id = "eea-co2-cars-2024-final-toyota-eu27"
    target_source_id = "eea-eu-new-car-fleet-targets"
    regulation_source_id = "eu-regulation-2019-631"
    sources = [
        {
            "source_id": source_id,
            "title": "Monitoring of CO2 emissions from new passenger cars, 2024 final",
            "publisher": "European Environment Agency",
            "url": DATASET_URL,
            "evidence_class": "regulatory_dataset",
            "published_date": None,
            "accessed_date": snapshot["accessed_date"],
            "license": "EEA CC-BY/re-use policy; acknowledge EEA and check item-specific terms",
            "snapshot_sha256": snapshot["response_sha256"],
            "query_sha256": snapshot["query_sha256"],
            "notes": (
                "Exact EEA API filter: 2024, Final, Mk=TOYOTA, EU27. The committed artifact "
                "contains aggregate results, not individual registration rows."
            ),
        },
        {
            "source_id": target_source_id,
            "title": "CO2 emissions performance of new passenger cars in Europe",
            "publisher": "European Environment Agency",
            "url": TARGET_URL,
            "evidence_class": "official_primary",
            "published_date": None,
            "accessed_date": snapshot["accessed_date"],
            "license": "EEA CC-BY unless otherwise indicated",
            "notes": "Publishes EU-wide WLTP fleet targets of 93.6 g/km for 2025-2029 and 49.5 g/km for 2030-2034.",
        },
        {
            "source_id": regulation_source_id,
            "title": "Regulation (EU) 2019/631, consolidated text",
            "publisher": "European Parliament and Council of the European Union",
            "url": REGULATION_URL,
            "evidence_class": "official_primary",
            "published_date": "2025-07-09",
            "accessed_date": snapshot["accessed_date"],
            "license": "EU law/public document; EUR-Lex reuse notice applies",
            "notes": "Legal basis for EU fleet-wide and manufacturer-specific CO2 performance standards.",
        },
    ]

    metrics: list[dict[str, Any]] = []
    metrics.extend(_metrics_for_geography("EU27", aggregations, source_id))
    for bucket in aggregations["countries"]["buckets"]:
        metrics.extend(_metrics_for_geography(bucket["key"], bucket, source_id))

    benchmark_note = (
        "EU-wide new-passenger-car fleet target. It is directly comparable as a portfolio "
        "intensity pathway but is not Toyota's manufacturer-specific compliance target; the "
        "2024 company snapshot is unadjusted for eco-innovation or pooling."
    )
    benchmarks = [
        {
            "benchmark_id": "eu27-new-car-fleet-2025",
            "metric_id": "new_vehicle_tailpipe_intensity",
            "sector": "automotive",
            "geography": "EU27",
            "benchmark_type": "EU-wide new passenger car fleet CO2 target",
            "authority_status": "adopted regulation",
            "comparison_mode": "direct",
            "relation": "at_most",
            "source_ids": [target_source_id, regulation_source_id],
            "value": 93.6,
            "unit": "gCO2/km",
            "target_year": 2025,
            "applicable_geographies": [],
            "notes": benchmark_note,
        },
        {
            "benchmark_id": "eu27-new-car-fleet-2030",
            "metric_id": "new_vehicle_tailpipe_intensity",
            "sector": "automotive",
            "geography": "EU27",
            "benchmark_type": "EU-wide new passenger car fleet CO2 target",
            "authority_status": "adopted regulation",
            "comparison_mode": "direct",
            "relation": "at_most",
            "source_ids": [target_source_id, regulation_source_id],
            "value": 49.5,
            "unit": "gCO2/km",
            "target_year": 2030,
            "applicable_geographies": [],
            "notes": benchmark_note,
        },
    ]
    return {"company_metrics": metrics, "benchmarks": benchmarks, "sources": sources}


def _metrics_for_geography(
    geography: str,
    aggregate: dict[str, Any],
    source_id: str,
) -> list[dict[str, Any]]:
    total = float(aggregate["registrations"]["value"])
    mapped = float(aggregate["co2_mapped"]["registrations"]["value"])
    average = float(aggregate["co2_mapped"]["weighted_average"]["value"])
    common = {
        "sector": "automotive",
        "company_id": "toyota",
        "geography": geography,
        "observation_year": 2024,
        "source_ids": [source_id],
        "evidence_class": "project_derived",
    }
    full_coverage = {
        "mapped_activity": total,
        "reported_activity": total,
        "activity_unit": "registrations",
        "unmatched_records": 0,
    }
    rows: list[dict[str, Any]] = [
        {
            **common,
            "metric_id": "new_vehicle_registrations",
            "value": total,
            "unit": "registrations",
            "scope": {
                "brand": "TOYOTA",
                "vehicle_class": "EEA monitored new passenger cars",
                "dataset_status": "Final",
            },
            "derivation": "sum of EEA total-new-registration field r",
            "coverage": full_coverage,
        },
        {
            **common,
            "metric_id": "new_vehicle_tailpipe_intensity",
            "value": average,
            "unit": "gCO2/km",
            "scope": {
                "brand": "TOYOTA",
                "vehicle_class": "EEA monitored new passenger cars",
                "test_regime": "WLTP",
                "adjustments": "none",
                "dataset_status": "Final",
            },
            "derivation": "sum(r × Ewltp) / sum(r) for registrations with Ewltp",
            "coverage": {
                "mapped_activity": mapped,
                "reported_activity": total,
                "activity_unit": "registrations",
                "unmatched_records": int(total - mapped),
            },
        },
    ]
    for powertrain in POWERTRAINS:
        registrations = float(
            aggregate["powertrains"]["buckets"][powertrain]["registrations"]["value"]
        )
        rows.append(
            {
                **common,
                "metric_id": "powertrain_sales_share",
                "value": registrations / total,
                "unit": "fraction",
                "scope": {
                    "brand": "TOYOTA",
                    "vehicle_class": "EEA monitored new passenger cars",
                    "powertrain": powertrain,
                    "classification": "EEA fuel mode/fuel type adapter v1",
                    "dataset_status": "Final",
                },
                "derivation": f"{powertrain} classified registrations / all Toyota registrations",
                "coverage": full_coverage,
            }
        )
    return rows


def _validate_aggregate(
    aggregate: dict[str, Any],
    expected_countries: set[str] | None = None,
) -> None:
    total = float(aggregate["registrations"]["value"])
    mapped = float(aggregate["co2_mapped"]["registrations"]["value"])
    if total <= 0 or not 0 <= mapped <= total:
        raise ValueError("invalid EEA registration or WLTP coverage totals")
    powertrain_total = sum(
        float(aggregate["powertrains"]["buckets"][name]["registrations"]["value"])
        for name in POWERTRAINS
    )
    if powertrain_total != total:
        raise ValueError("EEA powertrain buckets overlap or do not cover all registrations")
    if expected_countries is not None:
        buckets = aggregate["countries"]["buckets"]
        actual_countries = {bucket["key"] for bucket in buckets}
        if actual_countries != expected_countries:
            raise ValueError(
                f"EEA EU27 coverage changed: missing={sorted(expected_countries - actual_countries)}, "
                f"extra={sorted(actual_countries - expected_countries)}"
            )
        if sum(float(bucket["registrations"]["value"]) for bucket in buckets) != total:
            raise ValueError("EEA country totals do not reconcile to EU27 total")
        for bucket in buckets:
            _validate_aggregate(bucket)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="refresh the committed EEA snapshot")
    parser.add_argument("--accessed-date", default="2026-08-03")
    args = parser.parse_args()
    if args.refresh:
        refresh_snapshot(accessed_date=args.accessed_date)
    records = build_records()
    print(
        f"Toyota EEA adapter: {len(records['company_metrics'])} metrics, "
        f"{len(records['benchmarks'])} benchmarks, {len(records['sources'])} sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
