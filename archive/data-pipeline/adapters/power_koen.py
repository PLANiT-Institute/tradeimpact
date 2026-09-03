#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""KOEN Korea 2024 power adapter.

KOEN publishes generation and Scope 1/2 totals on its ESG data-center page. The reported
emissions totals do not reconcile exactly with the displayed plant rows, and the generation
amount does not state whether it is gross or net. The adapter therefore publishes the reported
observations but deliberately does not derive a generation emissions intensity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "data-pipeline" / "source-snapshots" / "koen_korea_2024.json"
KOEN_DATA_URL = (
    "https://www.koenergy.kr/kosep/hw/fr/st/sthw41/main.do?menuCd=FN060101"
)
PLAN_NOTICE_URL = "https://www.motir.go.kr/kor/article/ATCLc01b2801b/70083/view"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _snapshot_content(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in snapshot.items()
        if key not in {"accessed_date", "content_sha256"}
    }


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def _number(value: str) -> int:
    return int(value.replace(",", ""))


def _extract_company_values(html: bytes) -> dict[str, Any]:
    parser = _TableParser()
    parser.feed(html.decode("utf-8"))
    generation: int | None = None
    scope1_total: int | None = None
    scope2_total: int | None = None
    scope1_plants: dict[str, int] = {}
    scope2_plants: dict[str, int] = {}
    current_plant: str | None = None
    in_emissions = False

    for row in parser.rows:
        if row and row[0] == "발전량" and len(row) >= 5:
            generation = _number(row[-2])
        if row and "직접 온실가스배출량(Scope1)" in row[0]:
            in_emissions = True
            continue
        if not in_emissions:
            continue
        if row and row[0] == "기타 간접 온실가스배출량(Scope3)":
            break
        if len(row) >= 6 and row[0] == "합계" and row[1] == "Scope1":
            scope1_total = _number(row[-2])
            current_plant = "Total"
            continue
        if len(row) >= 5 and row[0] == "Scope2" and current_plant == "Total":
            scope2_total = _number(row[-2])
            continue
        if len(row) >= 6 and row[1] == "Scope1":
            current_plant = row[0]
            scope1_plants[current_plant] = _number(row[-2])
            continue
        if len(row) >= 5 and row[0] == "Scope2" and current_plant not in {None, "Total"}:
            scope2_plants[current_plant] = _number(row[-2])

    if generation is None or scope1_total is None or scope2_total is None:
        raise ValueError("KOEN 2024 generation or emissions totals were not found")
    if len(scope1_plants) != 6 or len(scope2_plants) != 6:
        raise ValueError("KOEN 2024 plant emissions rows were not found")
    return {
        "generation_gwh": generation,
        "scope1_reported_total_tco2e": scope1_total,
        "scope2_reported_total_tco2e": scope2_total,
        "scope1_plant_tco2e": scope1_plants,
        "scope2_plant_tco2e": scope2_plants,
    }


def _download(url: str) -> bytes:
    completed = subprocess.run(  # noqa: S603
        ["curl", "--fail", "--location", "--silent", "--show-error", url],  # noqa: S607
        check=True,
        capture_output=True,
        timeout=120,
    )
    return completed.stdout


def refresh_snapshot(path: Path = SNAPSHOT, accessed_date: str = "2026-08-03") -> None:
    existing = json.loads(path.read_text())
    company_page = _download(KOEN_DATA_URL)
    company_values = _extract_company_values(company_page)
    notice_page = _download(PLAN_NOTICE_URL)
    payload = {
        **existing,
        "accessed_date": accessed_date,
        "company": {
            **existing["company"],
            **company_values,
            "source_page_sha256": hashlib.sha256(company_page).hexdigest(),
        },
        "policy": {
            **existing["policy"],
            "notice_page_sha256": hashlib.sha256(notice_page).hexdigest(),
        },
    }
    payload["content_sha256"] = _sha256(_snapshot_content(payload))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def build_records(path: Path = SNAPSHOT) -> dict[str, list[dict[str, Any]]]:
    snapshot = json.loads(path.read_text())
    if snapshot["content_sha256"] != _sha256(_snapshot_content(snapshot)):
        raise ValueError("KOEN snapshot content hash mismatch")
    if snapshot["adapter_version"] != "koen-korea-2024-v1":
        raise ValueError("unsupported KOEN snapshot adapter version")

    company = snapshot["company"]
    scope1_plant_sum = sum(company["scope1_plant_tco2e"].values())
    scope2_plant_sum = sum(company["scope2_plant_tco2e"].values())
    scope1_difference = company["scope1_reported_total_tco2e"] - scope1_plant_sum
    scope2_difference = company["scope2_reported_total_tco2e"] - scope2_plant_sum
    company_source_id = "koen-esg-data-2024"
    policy_source_id = "kr-eleventh-electricity-plan"
    sources = [
        {
            "source_id": company_source_id,
            "title": "KOEN ESG Data Center — 2024 generation and GHG emissions",
            "publisher": "Korea South-East Power Co., Ltd. (KOEN)",
            "url": KOEN_DATA_URL,
            "evidence_class": "company_reported",
            "published_date": None,
            "accessed_date": snapshot["accessed_date"],
            "license": "KOEN website terms; extracted facts only, source linked",
            "snapshot_sha256": company["source_page_sha256"],
            "notes": (
                "The page reports 2024 generation and Scope 1/2 totals. The displayed plant "
                f"rows differ from the reported totals by {scope1_difference:,} tCO2e for "
                f"Scope 1 and {scope2_difference:,} tCO2e for Scope 2. No independent "
                "assurance statement was identified for this web table."
            ),
        },
        {
            "source_id": policy_source_id,
            "title": snapshot["policy"]["plan_name"],
            "publisher": "Ministry of Trade, Industry and Resources, Republic of Korea",
            "url": PLAN_NOTICE_URL,
            "evidence_class": "official_primary",
            "published_date": snapshot["policy"]["notice_date"],
            "accessed_date": snapshot["accessed_date"],
            "license": "Korea Open Government License; item-specific terms apply",
            "snapshot_sha256": snapshot["policy"]["notice_page_sha256"],
            "notes": (
                "Official notice and attached Eleventh Electricity Plan. The plan gives the "
                "national 2030 transition-sector emissions level and 2030/2038 generation mix."
            ),
        },
    ]

    generation_mwh = float(company["generation_gwh"]) * 1_000
    common = {
        "sector": "power",
        "company_id": "koen",
        "geography": "KR",
        "observation_year": 2024,
        "source_ids": [company_source_id],
        "evidence_class": "company_reported",
        "scope": {
            "company_boundary": company["reporting_boundary"],
            "generation_basis": company["generation_basis"],
            "assurance": "not identified for the web table",
        },
    }
    metrics = [
        {
            **common,
            "metric_id": "reported_generation",
            "value": generation_mwh,
            "unit": "MWh",
            "derivation": "reported GWh × 1,000 MWh/GWh; gross/net basis is not stated",
            "coverage": {
                "mapped_activity": generation_mwh,
                "reported_activity": generation_mwh,
                "activity_unit": "MWh",
                "unmatched_records": 0,
            },
        },
        {
            **common,
            "metric_id": "scope1_emissions",
            "value": float(company["scope1_reported_total_tco2e"]),
            "unit": "tCO2e",
            "derivation": (
                "reported total retained without re-summing plant rows; displayed plant-row "
                f"difference is {scope1_difference:,} tCO2e"
            ),
            "coverage": {
                "mapped_activity": 1,
                "reported_activity": 1,
                "activity_unit": "reported company total",
                "unmatched_records": 0,
            },
        },
        {
            **common,
            "metric_id": "scope2_emissions",
            "value": float(company["scope2_reported_total_tco2e"]),
            "unit": "tCO2e",
            "derivation": (
                "reported total retained without re-summing plant rows; displayed plant-row "
                f"difference is {scope2_difference:,} tCO2e"
            ),
            "coverage": {
                "mapped_activity": 1,
                "reported_activity": 1,
                "activity_unit": "reported company total",
                "unmatched_records": 0,
            },
        },
    ]

    policy = snapshot["policy"]
    context_note = (
        "National power-system context only. KOEN is one generation company, and the company "
        "data do not disclose a policy-compatible carbon-free share or a matching national-total "
        "allocation."
    )
    benchmarks = [
        {
            "benchmark_id": "kr-transition-sector-emissions-2030",
            "metric_id": "power_sector_emissions",
            "sector": "power",
            "geography": "KR",
            "benchmark_type": "national transition-sector emissions target",
            "authority_status": "adopted Eleventh Electricity Plan aligned with the 2030 NDC",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [policy_source_id],
            "value": policy["transition_sector_emissions_2030_mtco2e"],
            "unit": "MtCO2e",
            "target_year": 2030,
            "applicable_geographies": [],
            "notes": context_note,
        },
        {
            "benchmark_id": "kr-carbon-free-generation-share-2030",
            "metric_id": "carbon_free_generation_share",
            "sector": "power",
            "geography": "KR",
            "benchmark_type": "national carbon-free generation share outlook",
            "authority_status": "adopted Eleventh Electricity Plan",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [policy_source_id],
            "value": policy["carbon_free_generation_share_2030"],
            "unit": "fraction",
            "target_year": 2030,
            "applicable_geographies": [],
            "notes": (
                f"{context_note} The plan defines carbon-free generation as nuclear, renewable, "
                "clean hydrogen, and ammonia generation."
            ),
        },
        {
            "benchmark_id": "kr-carbon-free-generation-share-2038",
            "metric_id": "carbon_free_generation_share",
            "sector": "power",
            "geography": "KR",
            "benchmark_type": "national carbon-free generation share outlook",
            "authority_status": "adopted Eleventh Electricity Plan; post-2030 pathway outlook",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [policy_source_id],
            "value": policy["carbon_free_generation_share_2038"],
            "unit": "fraction",
            "target_year": 2038,
            "applicable_geographies": [],
            "notes": (
                f"{context_note} The plan states that the national post-2030 emissions pathway "
                "was not yet set and applies a linear path consistent with the prior plan."
            ),
        },
    ]
    return {"company_metrics": metrics, "benchmarks": benchmarks, "sources": sources}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--accessed-date", default="2026-08-03")
    args = parser.parse_args()
    if args.refresh:
        refresh_snapshot(accessed_date=args.accessed_date)
    records = build_records()
    print(
        f"KOEN power adapter: {len(records['company_metrics'])} metrics, "
        f"{len(records['benchmarks'])} contextual benchmarks, "
        f"{len(records['sources'])} sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
