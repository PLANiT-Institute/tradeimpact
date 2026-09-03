#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""JERA Japan FY2024 adapter.

The adapter publishes two independently assured company observations. Japan's national power
targets are retained as context only because the 2030 factor is measured at the point of use and
the 2040 power-mix ranges describe the national system rather than JERA's portfolio. No numeric
company gap is produced from those incompatible boundaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "data-pipeline" / "source-snapshots" / "jera_japan_fy2024.json"
JERA_DATA_URL = "https://www.jera.co.jp/en/sustainability/data/e"
ASSURANCE_URL = (
    "https://www.jera.co.jp/static/files/sustainability/pdf/"
    "JERA_Independent_Assurance_Report_20250930.pdf"
)
PLAN_URL = "https://www.meti.go.jp/english/press/2025/0218_001.html"
PLAN_OUTLINE_URL = (
    "https://www.enecho.meti.go.jp/en/category/others/basic_plan/pdf/7th_outline.pdf"
)
USE_END_FACTOR_URL = (
    "https://www.meti.go.jp/shingikai/sankoshin/sangyo_gijutsu/chikyu_kankyo/"
    "shigen_wg/pdf/2022_001_s01_00.pdf"
)


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


def _extract_domestic_group(html: bytes) -> tuple[float, float]:
    parser = _TableParser()
    parser.feed(html.decode("utf-8"))
    in_group = False
    generation: float | None = None
    intensity: float | None = None
    for row in parser.rows:
        label = row[0] if row else ""
        if label.startswith("Domestic / JERA Group"):
            in_group = True
            continue
        if in_group and label.startswith("Global / JERA Group"):
            break
        if not in_group or len(row) < 3:
            continue
        if label.startswith("Net electricity generation"):
            generation = float(row[-2])
            if row[-1] != "★":
                raise ValueError("JERA net generation is no longer marked externally assured")
        elif "emission intensity of power generation" in label:
            intensity = float(row[-2])
            if row[-1] != "★":
                raise ValueError("JERA generation intensity is no longer marked externally assured")
    if generation is None or intensity is None:
        raise ValueError("JERA domestic-group FY2024 rows were not found")
    return generation, intensity


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "tradeimpact/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        return response.read()


def refresh_snapshot(path: Path = SNAPSHOT, accessed_date: str = "2026-08-03") -> None:
    existing = json.loads(path.read_text())
    page = _download(JERA_DATA_URL)
    generation, intensity = _extract_domestic_group(page)
    assurance = _download(ASSURANCE_URL)
    company = dict(existing["company"])
    company.update(
        {
            "net_generation_billion_kwh": generation,
            "intensity_kgco2e_per_kwh": intensity,
            "source_page_sha256": hashlib.sha256(page).hexdigest(),
        }
    )
    payload = {
        **existing,
        "accessed_date": accessed_date,
        "company": company,
        "assurance": {
            **existing["assurance"],
            "document_sha256": hashlib.sha256(assurance).hexdigest(),
        },
    }
    payload["content_sha256"] = _sha256(_snapshot_content(payload))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def build_records(path: Path = SNAPSHOT) -> dict[str, list[dict[str, Any]]]:
    snapshot = json.loads(path.read_text())
    if snapshot["content_sha256"] != _sha256(_snapshot_content(snapshot)):
        raise ValueError("JERA snapshot content hash mismatch")
    if snapshot["adapter_version"] != "jera-japan-fy2024-v1":
        raise ValueError("unsupported JERA snapshot adapter version")
    company = snapshot["company"]
    assurance = snapshot["assurance"]
    if company["net_generation_billion_kwh"] != assurance["net_generation_billion_kwh"]:
        raise ValueError("JERA generation differs from the assurance appendix")
    if company["intensity_kgco2e_per_kwh"] != assurance["intensity_kgco2e_per_kwh"]:
        raise ValueError("JERA intensity differs from the assurance appendix")

    company_source_id = "jera-environmental-data-fy2024"
    assurance_source_id = "jera-independent-assurance-fy2024"
    plan_source_id = "jp-seventh-strategic-energy-plan"
    use_end_source_id = "jp-power-action-plan-2030"
    sources = [
        {
            "source_id": company_source_id,
            "title": "JERA Environmental Data — FY2024 domestic group",
            "publisher": "JERA Co., Inc.",
            "url": JERA_DATA_URL,
            "evidence_class": "company_reported",
            "published_date": None,
            "accessed_date": snapshot["accessed_date"],
            "license": "JERA website terms; extracted facts only, source linked",
            "snapshot_sha256": company["source_page_sha256"],
            "notes": (
                "Domestic/JERA Group boundary; joint ventures are proportionately included. "
                "The source marks FY2024 net generation and intensity as externally assured."
            ),
        },
        {
            "source_id": assurance_source_id,
            "title": "Independent Assurance Report on JERA environmental data FY2024",
            "publisher": assurance["provider"],
            "url": ASSURANCE_URL,
            "evidence_class": "independent_secondary",
            "published_date": assurance["assurance_date"],
            "accessed_date": snapshot["accessed_date"],
            "license": "Copyright holder terms; extracted facts only, source linked",
            "snapshot_sha256": assurance["document_sha256"],
            "notes": "Appendix table 2 confirms 242 billion kWh and 0.520 kg-CO2e/kWh.",
        },
        {
            "source_id": plan_source_id,
            "title": "Seventh Strategic Energy Plan and FY2040 power-mix outlook",
            "publisher": "Ministry of Economy, Trade and Industry, Government of Japan",
            "url": PLAN_OUTLINE_URL,
            "evidence_class": "official_primary",
            "published_date": snapshot["policy"]["cabinet_decision_date"],
            "accessed_date": snapshot["accessed_date"],
            "license": "Government of Japan Standard Terms of Use 2.0",
            "notes": (
                "The Cabinet-decided outlook gives national FY2040 generation ranges: "
                "renewables 40–50% and thermal power 30–40%."
            ),
        },
        {
            "source_id": use_end_source_id,
            "title": "Power-sector carbon-neutral action plan — FY2030 review response",
            "publisher": "Ministry of Economy, Trade and Industry, Government of Japan",
            "url": USE_END_FACTOR_URL,
            "evidence_class": "official_primary",
            "published_date": "2022-12-21",
            "accessed_date": snapshot["accessed_date"],
            "license": "Government of Japan Standard Terms of Use 2.0",
            "notes": (
                "Records the national 0.25 kg-CO2/kWh FY2030 outlook at the point of use; "
                "it is not a generator-boundary limit."
            ),
        },
    ]

    generation_mwh = float(company["net_generation_billion_kwh"]) * 1_000_000
    intensity_per_mwh = float(company["intensity_kgco2e_per_kwh"]) * 1_000
    coverage = {
        "mapped_activity": generation_mwh,
        "reported_activity": generation_mwh,
        "activity_unit": "MWh",
        "unmatched_records": 0,
    }
    common = {
        "sector": "power",
        "company_id": "jera",
        "geography": "JP",
        "observation_year": 2024,
        "source_ids": [company_source_id, assurance_source_id],
        "evidence_class": "company_reported",
        "scope": {
            "company_boundary": company["boundary"],
            "generation_basis": company["generation_basis"],
            "reporting_period": (
                f"{company['reporting_period_start']}/{company['reporting_period_end']}"
            ),
            "assurance": "independent limited assurance; appendix table 2",
        },
        "coverage": coverage,
    }
    metrics = [
        {
            **common,
            "metric_id": "net_generation",
            "value": generation_mwh,
            "unit": "MWh",
            "derivation": "reported billion kWh × 1,000,000 MWh/billion kWh",
        },
        {
            **common,
            "metric_id": "generation_emissions_intensity",
            "value": intensity_per_mwh,
            "unit": "kgCO2e/MWh",
            "derivation": "reported kg-CO2e/kWh × 1,000 kWh/MWh; not recomputed from rounded totals",
        },
    ]

    policy = snapshot["policy"]
    context_note = (
        "National-system context only. JERA's company-generation boundary cannot be treated as "
        "the entire Japanese power system or as electricity delivered at the point of use."
    )
    benchmarks = [
        {
            "benchmark_id": "jp-use-end-grid-factor-2030",
            "metric_id": "electricity_use_end_emissions_factor",
            "sector": "power",
            "geography": "JP",
            "benchmark_type": "national electricity factor outlook at point of use",
            "authority_status": "industry action plan aligned with government outlook",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [use_end_source_id],
            "value": policy["electricity_use_end_factor_2030_kgco2_per_kwh"] * 1_000,
            "unit": "kgCO2/MWh",
            "target_year": 2030,
            "applicable_geographies": [],
            "notes": f"{context_note} Original source unit is kg-CO2/kWh.",
        },
        {
            "benchmark_id": "jp-renewable-generation-share-2040",
            "metric_id": "renewable_generation_share",
            "sector": "power",
            "geography": "JP",
            "benchmark_type": "national renewable generation share outlook",
            "authority_status": "Cabinet-decided Strategic Energy Plan outlook",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [plan_source_id],
            "value": None,
            "value_min": policy["renewable_generation_share_2040"]["min"],
            "value_max": policy["renewable_generation_share_2040"]["max"],
            "unit": "fraction",
            "target_year": 2040,
            "applicable_geographies": [],
            "notes": (
                f"{context_note} JERA does not publish renewable generation MWh on this "
                "domestic-group boundary."
            ),
        },
        {
            "benchmark_id": "jp-thermal-generation-share-2040",
            "metric_id": "thermal_generation_share",
            "sector": "power",
            "geography": "JP",
            "benchmark_type": "national thermal generation share outlook",
            "authority_status": "Cabinet-decided Strategic Energy Plan outlook",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [plan_source_id],
            "value": None,
            "value_min": policy["thermal_generation_share_2040"]["min"],
            "value_max": policy["thermal_generation_share_2040"]["max"],
            "unit": "fraction",
            "target_year": 2040,
            "applicable_geographies": [],
            "notes": context_note,
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
        f"JERA power adapter: {len(records['company_metrics'])} metrics, "
        f"{len(records['benchmarks'])} contextual benchmarks, "
        f"{len(records['sources'])} sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
