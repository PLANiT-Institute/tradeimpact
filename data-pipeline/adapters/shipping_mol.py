#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""MOL global shipping FY2024 adapter.

MOL's FY2024 company-wide EEOI is independently assured on a lifecycle-GHG standard-method
boundary. The IMO 2030 ambitions remain context only because they use a 2008 international-
shipping average CO2/transport-work baseline rather than MOL's FY2019 WtW standard method.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import urllib.request
from html import unescape
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "data-pipeline" / "source-snapshots" / "mol_global_fy2024.json"
MOL_DATA_URL = "https://www.mol.co.jp/en/sustainability/data/pdf/environmental/data.pdf"
ASSURANCE_URL = (
    "https://www.mol.co.jp/en/sustainability/data/pdf/environmental/assurance-statement.pdf"
)
APPENDIX_URL = (
    "https://www.mol.co.jp/en/sustainability/data/pdf/environmental/appendix.pdf"
)
IMO_STRATEGY_URL = (
    "https://www.imo.org/en/ourwork/environment/pages/"
    "2023-imo-strategy-on-reduction-of-ghg-emissions-from-ships.aspx"
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


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "tradeimpact/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        return response.read()


def _pdf_text(payload: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf:
        pdf.write(payload)
        pdf.flush()
        completed = subprocess.run(  # noqa: S603
            ["pdftotext", "-layout", pdf.name, "-"],  # noqa: S607
            check=True,
            capture_output=True,
            timeout=120,
        )
    return completed.stdout.decode("utf-8")


def _verify_downloaded_values(
    environmental_data: bytes,
    assurance_statement: bytes,
    assurance_appendix: bytes,
    imo_page: bytes,
) -> None:
    company_text = " ".join(_pdf_text(environmental_data).split())
    statement_text = " ".join(_pdf_text(assurance_statement).split())
    appendix_text = " ".join(_pdf_text(assurance_appendix).split())
    imo_text = " ".join(unescape(imo_page.decode("utf-8", errors="ignore")).split())
    if "GHG Emissions Intensity" not in company_text or not re.search(
        r"FY2024.*?10\.95", company_text
    ):
        raise ValueError("MOL FY2024 EEOI was not found in environmental data")
    if "10.95" not in statement_text or "gCO2e/ton-mile" not in statement_text:
        raise ValueError("ClassNK assurance no longer confirms 10.95 gCO2e/ton-mile")
    if "783 vessels" not in appendix_text or "Standard Method" not in appendix_text:
        raise ValueError("ClassNK appendix no longer confirms the assured fleet/method")
    required_imo_phrases = ("at least 40% by 2030", "striving for 30%", "striving for 10%")
    if any(phrase not in imo_text for phrase in required_imo_phrases):
        raise ValueError("IMO 2030 strategy phrases were not found")


def refresh_snapshot(path: Path = SNAPSHOT, accessed_date: str = "2026-08-03") -> None:
    existing = json.loads(path.read_text())
    environmental_data = _download(MOL_DATA_URL)
    assurance_statement = _download(ASSURANCE_URL)
    assurance_appendix = _download(APPENDIX_URL)
    imo_page = _download(IMO_STRATEGY_URL)
    _verify_downloaded_values(
        environmental_data, assurance_statement, assurance_appendix, imo_page
    )
    payload = {
        **existing,
        "accessed_date": accessed_date,
        "company": {
            **existing["company"],
            "source_document_sha256": hashlib.sha256(environmental_data).hexdigest(),
        },
        "assurance": {
            **existing["assurance"],
            "statement_sha256": hashlib.sha256(assurance_statement).hexdigest(),
            "appendix_sha256": hashlib.sha256(assurance_appendix).hexdigest(),
        },
        "policy": {
            **existing["policy"],
            "source_page_sha256": hashlib.sha256(imo_page).hexdigest(),
        },
    }
    payload["content_sha256"] = _sha256(_snapshot_content(payload))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def build_records(path: Path = SNAPSHOT) -> dict[str, list[dict[str, Any]]]:
    snapshot = json.loads(path.read_text())
    if snapshot["content_sha256"] != _sha256(_snapshot_content(snapshot)):
        raise ValueError("MOL snapshot content hash mismatch")
    if snapshot["adapter_version"] != "mol-global-fy2024-v1":
        raise ValueError("unsupported MOL snapshot adapter version")

    company = snapshot["company"]
    assurance = snapshot["assurance"]
    if company["eeoi_gco2e_per_ton_mile"] != assurance["intensity_gco2e_per_ton_mile"]:
        raise ValueError("MOL EEOI differs from the ClassNK assurance statement")
    if company["applicable_vessels"] != assurance["applicable_vessels"]:
        raise ValueError("MOL applicable-vessel count differs from the ClassNK appendix")

    company_source_id = "mol-environmental-data-fy2024"
    assurance_source_id = "mol-classnk-eeoi-assurance-fy2024"
    appendix_source_id = "mol-classnk-eeoi-appendix-fy2024"
    imo_source_id = "imo-2023-ghg-strategy"
    sources = [
        {
            "source_id": company_source_id,
            "title": "MOL Environmental Data — FY2024 GHG emissions intensity",
            "publisher": "Mitsui O.S.K. Lines, Ltd.",
            "url": MOL_DATA_URL,
            "evidence_class": "company_reported",
            "published_date": None,
            "accessed_date": snapshot["accessed_date"],
            "license": "MOL website terms; extracted facts only, source linked",
            "snapshot_sha256": company["source_document_sha256"],
            "notes": (
                "Reports FY2024 company-wide standard-method EEOI of 10.95 gCO2e/ton-mile "
                "for MOL and major ocean-going vessels of group subsidiaries."
            ),
        },
        {
            "source_id": assurance_source_id,
            "title": "Independent Assurance Statement — MOL FY2024 GHG emissions intensity",
            "publisher": assurance["provider"],
            "url": ASSURANCE_URL,
            "evidence_class": "independent_secondary",
            "published_date": assurance["assurance_date"],
            "accessed_date": snapshot["accessed_date"],
            "license": "Copyright holder terms; extracted facts only, source linked",
            "snapshot_sha256": assurance["statement_sha256"],
            "notes": "ClassNK confirms 10.95 gCO2e/ton-mile and the standard-method calculation.",
        },
        {
            "source_id": appendix_source_id,
            "title": "ClassNK assurance appendix — MOL FY2024 EEOI method and fleet",
            "publisher": assurance["provider"],
            "url": APPENDIX_URL,
            "evidence_class": "independent_secondary",
            "published_date": assurance["assurance_date"],
            "accessed_date": snapshot["accessed_date"],
            "license": "Copyright holder terms; extracted facts only, source linked",
            "snapshot_sha256": assurance["appendix_sha256"],
            "notes": (
                f"Defines lifecycle-GHG EEOI and the {assurance['applicable_vessels']}-vessel "
                f"scope. At least {assurance['minimum_sampled_vessels']} vessels and "
                f"{assurance['minimum_sampled_lifecycle_ghg_tco2e']:,} tCO2e were sampled."
            ),
        },
        {
            "source_id": imo_source_id,
            "title": snapshot["policy"]["strategy_name"],
            "publisher": "International Maritime Organization",
            "url": IMO_STRATEGY_URL,
            "evidence_class": "official_primary",
            "published_date": snapshot["policy"]["adoption_month"],
            "accessed_date": snapshot["accessed_date"],
            "license": "IMO website terms; extracted facts only, source linked",
            "snapshot_sha256": snapshot["policy"]["source_page_sha256"],
            "notes": (
                "Official international-shipping strategy: 2030 carbon-intensity ambition, "
                "absolute-GHG checkpoint, and zero/near-zero energy ambition."
            ),
        },
    ]

    coverage = {
        "mapped_activity": float(company["applicable_vessels"]),
        "reported_activity": float(company["applicable_vessels"]),
        "activity_unit": "applicable vessels",
        "unmatched_records": 0,
    }
    metrics = [
        {
            "metric_id": "shipping_eeoi",
            "sector": "shipping",
            "company_id": "mitsui",
            "geography": "GLOBAL",
            "observation_year": 2024,
            "value": float(company["eeoi_gco2e_per_ton_mile"]),
            "unit": "gCO2e/ton-mile",
            "source_ids": [company_source_id, assurance_source_id, appendix_source_id],
            "evidence_class": "company_reported",
            "scope": {
                "company_boundary": company["reporting_boundary"],
                "metric_boundary": company["metric_boundary"],
                "calculation_method": company["calculation_method"],
                "reporting_period": (
                    f"{company['reporting_period_start']}/{company['reporting_period_end']}"
                ),
                "assurance": (
                    f"ClassNK independent assurance; {assurance['applicable_vessels']} vessels; "
                    f"sample at least {assurance['minimum_sampled_vessels']} vessels"
                ),
                "allocation_caveat": company["allocation_caveat"],
            },
            "derivation": "reported and independently assured value; no project recomputation",
            "coverage": coverage,
        }
    ]

    policy = snapshot["policy"]
    context_note = (
        "International-shipping context only. MOL reports lifecycle GHG EEOI using a FY2019 "
        "company standard method, while the IMO ambition uses an international-shipping average "
        "CO2/transport-work baseline from 2008. No company gap is calculated."
    )
    benchmarks = [
        {
            "benchmark_id": "imo-carbon-intensity-reduction-2030",
            "metric_id": "shipping_carbon_intensity_reduction",
            "sector": "shipping",
            "geography": "GLOBAL",
            "benchmark_type": "international-shipping carbon-intensity reduction ambition",
            "authority_status": "adopted 2023 IMO GHG Strategy",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [imo_source_id],
            "value": policy["carbon_intensity_reduction_2030"],
            "unit": "fraction",
            "target_year": 2030,
            "applicable_geographies": [],
            "notes": context_note,
        },
        {
            "benchmark_id": "imo-absolute-ghg-reduction-2030",
            "metric_id": "shipping_absolute_ghg_reduction",
            "sector": "shipping",
            "geography": "GLOBAL",
            "benchmark_type": "international-shipping absolute GHG reduction checkpoint",
            "authority_status": "adopted 2023 IMO GHG Strategy; at least 20%, striving for 30%",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [imo_source_id],
            "value": None,
            "value_min": policy["absolute_ghg_reduction_2030_min"],
            "value_max": policy["absolute_ghg_reduction_2030_max"],
            "unit": "fraction",
            "target_year": 2030,
            "applicable_geographies": [],
            "notes": context_note,
        },
        {
            "benchmark_id": "imo-zero-near-zero-energy-share-2030",
            "metric_id": "zero_near_zero_energy_share",
            "sector": "shipping",
            "geography": "GLOBAL",
            "benchmark_type": "zero/near-zero GHG energy uptake ambition",
            "authority_status": "adopted 2023 IMO GHG Strategy; at least 5%, striving for 10%",
            "comparison_mode": "contextual",
            "relation": "context_only",
            "source_ids": [imo_source_id],
            "value": None,
            "value_min": policy["zero_near_zero_energy_share_2030_min"],
            "value_max": policy["zero_near_zero_energy_share_2030_max"],
            "unit": "fraction",
            "target_year": 2030,
            "applicable_geographies": [],
            "notes": (
                f"{context_note} MOL's policy-compatible energy share is not disclosed on the "
                "same assured boundary."
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
        f"MOL shipping adapter: {len(records['company_metrics'])} metric, "
        f"{len(records['benchmarks'])} contextual benchmarks, "
        f"{len(records['sources'])} sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
