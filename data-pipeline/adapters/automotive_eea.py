#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""EEA passenger-car adapter for the Toyota 2024 EU27 destination cohort.

The remote EEA API is used only by ``--refresh``. Normal dataset builds transform the committed
aggregation snapshot, so CI and reviewers reproduce the same result without a live dependency.
The adapter publishes observed destination registrations by commercial name and powertrain,
together with certified WLTP tailpipe and electricity-consumption fields where reported.

It deliberately does *not* turn a certified value into annual or lifetime emissions. Those
results require independently sourced destination-market use, survival, real-world, grid, fuel,
and policy-pathway inputs and are gated by the Trade Impact calculation contract.
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
EU_NDC_URL = (
    "https://unfccc.int/sites/default/files/2025-11/"
    "DK-2025-11-05%20EU%20NDC.pdf"
)
EU_TRANSPORT_PATHWAY_URL = (
    "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52024SC0063"
)
EUROSTAT_GHG_URL = (
    "https://ec.europa.eu/eurostat/databrowser/view/env_air_gge/default/table?lang=en"
)
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
    co2_aggregations = {
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
    }
    product_aggregations = {
        **co2_aggregations,
        "energy_mapped": {
            "filter": {"exists": {"field": "z__Wh_km_"}},
            "aggs": {
                "registrations": {"sum": {"field": "r"}},
                "weighted_average": {
                    "weighted_avg": {
                        "value": {"field": "z__Wh_km_"},
                        "weight": {"field": "r"},
                    }
                },
            },
        },
    }
    summary_powertrain_aggregation = {
        "filters": {"filters": powertrain_filters},
        "aggs": {"registrations": {"sum": {"field": "r"}}},
    }
    product_powertrain_aggregation = {
        "filters": {"filters": powertrain_filters},
        "aggs": product_aggregations,
    }
    model_aggregation = {
        "terms": {
            "field": "Cn",
            "size": 500,
            "missing": "NOT_REPORTED",
            "order": {"_key": "asc"},
        },
        "aggs": {
            "registrations": {"sum": {"field": "r"}},
            "powertrains": product_powertrain_aggregation,
        },
    }
    subaggregations = {
        **co2_aggregations,
        "powertrains": summary_powertrain_aggregation,
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
                "aggs": {**subaggregations, "models": model_aggregation},
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
        "adapter_version": "eea-toyota-eu27-v2",
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
    ndc_source_id = "unfccc-eu-ndc-2025"
    transport_pathway_source_id = "ec-2040-impact-assessment-transport-pathway"
    eurostat_source_id = "eurostat-env-air-gge-2023"
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
        {
            "source_id": ndc_source_id,
            "title": "The NDC of the European Union and its Member States",
            "publisher": "European Union and its Member States / UNFCCC NDC Registry",
            "url": EU_NDC_URL,
            "evidence_class": "official_primary",
            "published_date": "2025-11-05",
            "accessed_date": snapshot["accessed_date"],
            "license": "UNFCCC public document; source terms apply",
            "notes": (
                "Collective EU NDC: at least 55% net GHG reduction by 2030 and an "
                "indicative 66.25%-72.5% reduction range by 2035, relative to 1990."
            ),
        },
        {
            "source_id": transport_pathway_source_id,
            "title": "Impact assessment accompanying the EU 2040 climate target",
            "publisher": "European Commission",
            "url": EU_TRANSPORT_PATHWAY_URL,
            "evidence_class": "official_primary",
            "published_date": "2024-02-06",
            "accessed_date": snapshot["accessed_date"],
            "license": "EU public document; EUR-Lex reuse notice applies",
            "notes": (
                "Table 3 reports a 2030 domestic-transport pathway value of 583 MtCO2e. "
                "It covers domestic transport, not passenger cars alone."
            ),
        },
        {
            "source_id": eurostat_source_id,
            "title": "Greenhouse gas emissions by source sector (env_air_gge)",
            "publisher": "Eurostat",
            "url": EUROSTAT_GHG_URL,
            "evidence_class": "official_primary",
            "published_date": None,
            "accessed_date": snapshot["accessed_date"],
            "license": "Eurostat reuse policy applies",
            "notes": (
                "2023 EU domestic-transport total used as the base observation for the "
                "regional sector-pathway proxy."
            ),
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
    product_cohorts = [_build_product_cohort(snapshot, source_id)]
    pathways = _build_pathways(
        ndc_source_id,
        transport_pathway_source_id,
        eurostat_source_id,
    )
    readiness = [_build_readiness(product_cohorts[0]["cohort_id"])]
    return {
        "company_metrics": metrics,
        "benchmarks": benchmarks,
        "sources": sources,
        "product_cohorts": product_cohorts,
        "pathways": pathways,
        "impact_readiness": readiness,
    }


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


def _weighted_value(bucket: dict[str, Any], aggregation: str) -> float | None:
    value = bucket.get(aggregation, {}).get("weighted_average", {}).get("value")
    return float(value) if value is not None else None


def _mapped_units(bucket: dict[str, Any], aggregation: str) -> float:
    return float(bucket.get(aggregation, {}).get("registrations", {}).get("value", 0.0))


def _impact_channel(powertrain: str) -> tuple[str, str]:
    channels = {
        "BEV": ("grid_electricity", "power"),
        "FCEV": ("hydrogen_supply", "energy_and_transport"),
        "PHEV": ("fuel_and_grid_electricity", "road_transport_and_power"),
        "HEV": ("fuel_combustion", "road_transport"),
        "ICE_OTHER": ("fuel_combustion", "road_transport"),
    }
    return channels[powertrain]


def _build_product_cohort(snapshot: dict[str, Any], source_id: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    countries = snapshot["response"]["aggregations"]["countries"]["buckets"]
    for country in countries:
        destination = country["key"]
        for model in country["models"]["buckets"]:
            product_name = str(model["key"]).strip() or "NOT_REPORTED"
            for powertrain in POWERTRAINS:
                bucket = model["powertrains"]["buckets"][powertrain]
                units = float(bucket["registrations"]["value"])
                if units <= 0:
                    continue
                channel, ndc_sector = _impact_channel(powertrain)
                co2_mapped = _mapped_units(bucket, "co2_mapped")
                energy_mapped = _mapped_units(bucket, "energy_mapped")
                records.append(
                    {
                        "destination_geography": destination,
                        "product_name": product_name,
                        "product_type": powertrain,
                        "units": units,
                        "unit": "registrations",
                        "certified_tailpipe_gco2_per_km": _weighted_value(
                            bucket, "co2_mapped"
                        ),
                        "tailpipe_mapped_units": co2_mapped,
                        "certified_electricity_kwh_per_km": (
                            value / 1_000
                            if (value := _weighted_value(bucket, "energy_mapped")) is not None
                            else None
                        ),
                        "electricity_mapped_units": energy_mapped,
                        "use_phase_channel": channel,
                        "destination_inventory_sector": ndc_sector,
                        "source_ids": [source_id],
                    }
                )
    records.sort(
        key=lambda row: (
            row["destination_geography"],
            row["product_name"],
            row["product_type"],
        )
    )
    total = float(snapshot["response"]["aggregations"]["registrations"]["value"])
    if sum(row["units"] for row in records) != total:
        raise ValueError("product cohort records do not reconcile to EU27 registrations")
    return {
        "cohort_id": "toyota-eu27-passenger-cars-2024",
        "contract_version": "export-impact-v1",
        "company_id": "toyota",
        "company_name": "Toyota",
        "company_boundary": "TOYOTA brand; not the consolidated Toyota Motor group",
        "sector": "automotive",
        "cohort_year": 2024,
        "product_class": "new passenger cars",
        "activity_basis": "destination-country first registrations",
        "destination_scope": "EU27",
        "origin_mapping_status": "not_collected",
        "origin_mapping_note": (
            "EEA registrations establish where vehicles enter use, not where they were produced "
            "or whether a cross-border export occurred. Production-to-destination mapping is a "
            "separate Level 2 input."
        ),
        "source_ids": [source_id],
        "coverage": {
            "reported_units": total,
            "mapped_destination_units": total,
            "mapped_product_name_units": sum(
                row["units"] for row in records if row["product_name"] != "NOT_REPORTED"
            ),
            "mapped_product_type_units": total,
            "unit": "registrations",
        },
        "records": records,
    }


def _build_pathways(
    ndc_source_id: str,
    transport_pathway_source_id: str,
    eurostat_source_id: str,
) -> list[dict[str, Any]]:
    transport_base = 795.6
    transport_target = 583.0
    annual_rate = 1 - (transport_target / transport_base) ** (1 / (2030 - 2023))
    return [
        {
            "pathway_id": "eu27-economy-wide-ndc-2035",
            "sector": "economy_wide",
            "geography": "EU27",
            "applies_to": list(EU27),
            "policy_level": "ndc",
            "authority_status": "submitted_ndc",
            "scenario": "S2",
            "baseline_year": 1990,
            "target_year": 2035,
            "reduction_min": 0.6625,
            "reduction_max": 0.725,
            "unit": "fraction_net_ghg_reduction",
            "comparison_role": "fallback_context",
            "calculation_status": "not_directly_usable",
            "source_ids": [ndc_source_id],
            "notes": (
                "The EU and its Member States submit one collective NDC. The economy-wide range "
                "does not by itself define a passenger-car service-intensity benchmark."
            ),
        },
        {
            "pathway_id": "eu27-domestic-transport-pathway-2030",
            "sector": "automotive",
            "geography": "EU27",
            "applies_to": list(EU27),
            "policy_level": "regional_sector_pathway",
            "authority_status": "commission_impact_assessment",
            "scenario": "S2",
            "baseline_year": 2023,
            "target_year": 2030,
            "baseline_value": transport_base,
            "target_value": transport_target,
            "unit": "MtCO2e_domestic_transport",
            "annual_reduction_rate": annual_rate,
            "comparison_role": "sector_proxy",
            "calculation_status": "proxy_requires_disclosure",
            "source_ids": [eurostat_source_id, transport_pathway_source_id],
            "notes": (
                "Derived CAGR from the 2023 domestic-transport inventory and the Commission's "
                "2030 pathway. It covers all domestic transport and is not a country-specific "
                "passenger-car target; using it as r_fleet requires an explicit proxy caveat."
            ),
        },
    ]


def _build_readiness(cohort_id: str) -> dict[str, Any]:
    return {
        "cohort_id": cohort_id,
        "method_version": "export-impact-v1",
        "status": "inputs_incomplete",
        "observed_inputs": [
            "destination-country registration volume",
            "commercial name",
            "powertrain classification",
            "certified WLTP tailpipe intensity where reported",
            "certified WLTP electricity consumption where reported",
        ],
        "missing_required_inputs": [
            "production/export origin mapping",
            "destination-country annual vehicle-kilometres travelled",
            "destination-country vehicle survival and operating lifetime",
            "real-world correction by powertrain and market",
            "destination-country passenger-car fleet service-intensity baseline",
            "destination-country S1/S2/S3 road-transport pathway",
            "destination-country S1/S2/S3 grid pathway",
            "PHEV real-world utility factor",
            "FCEV hydrogen supply emissions intensity",
        ],
        "available_target_level": "EU regional sector proxy and collective economy-wide NDC",
        "preferred_target_level": "destination-country road-transport or passenger-car pathway",
        "publication_decision": "withhold_lifetime_ti",
        "publication_reason": (
            "A lifetime TI value would currently be driven by unsourced assumptions rather than "
            "the observed sales cohort. Missing inputs remain visible and are not assigned zero."
        ),
    }


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
