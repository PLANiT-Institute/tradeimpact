#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the published dataset the web app renders.

    workbook.xlsx / *.csv + fixtures + firm universe
        -> data/published/{firms.json, {firm}.json, meta.json}

All numbers originate in ti_framework (build brief §1 boundary rule); this script only
orchestrates runs and serialises. Firms run only from collected inputs or explicitly
documented estimates; firms without either are published as ``runnable: false``.

Usage:  ti-framework/.venv/bin/python data-pipeline/build_dataset.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO / "ti-framework"
WORKBOOK = ENGINE_DIR / "data" / "TI_Data_Workbook_v0.1.xlsx"
OUT = REPO / "data" / "published"

sys.path.insert(0, str(ENGINE_DIR))

from ti_framework.core.scenarios import run  # noqa: E402
from ti_framework.core.sensitivity import run_sensitivity  # noqa: E402
from ti_framework.io.fixtures import load_fixture, parse_fixture  # noqa: E402
from ti_framework.io.schema import FLAG_REASONS  # noqa: E402
from ti_framework.io.workbook import load_workbook_inputs  # noqa: E402
from ti_framework.models import BenchmarkStatus  # noqa: E402
from ti_framework.report.outputs import to_json_dict  # noqa: E402

# firm slug -> fixture powering its report. ReferenceCo is the validation fixture;
# Toyota/Hyundai run on rough documented Tier B/C estimates (ESTIMATES.md) until
# collection lands (COLLECTION_STATUS.md is the backlog).
FIXTURES: dict[str, Path] = {
    "referenceco": ENGINE_DIR / "fixtures" / "reference_case.json",
    "toyota": REPO / "data-pipeline" / "fixtures" / "toyota.json",
    "hyundai": REPO / "data-pipeline" / "fixtures" / "hyundai.json",
}

# provenance note surfaced on the report page for estimate-based firms
NOTES_BY_SLUG = {
    "toyota": "Estimated-input case: NDC rates and grid intensities are collected (Tier A/B); "
    "volumes, vehicle parameters and S1/S3 rates are rough documented estimates "
    "(data-pipeline/ESTIMATES.md, Tier B/C). Replace with collected data as it lands.",
    "hyundai": "Estimated-input case: NDC rates and grid intensities are collected (Tier A/B); "
    "volumes, vehicle parameters and S1/S3 rates are rough documented estimates "
    "(data-pipeline/ESTIMATES.md, Tier B/C). Replace with collected data as it lands.",
}

# Published coverage denominators. These do not enter the TI calculation; they make
# the visible firm comparison honest about how much of the firm's reported cohort-year
# sales is represented by the placement rows. URLs and scope notes are audited in
# ESTIMATES.md. Field names are cohort-neutral: the year lives in cohort_year.
COVERAGE_BY_SLUG = {
    "toyota": {
        "reported_units": 10_160_000,
        "source": "https://global.toyota/pages/fact-data/fact-data_001_06_en.pdf",
        "scope": "Toyota + Lexus global 2024 sales; fixture uses selected Toyota/Lexus market mixes",
    },
    "hyundai": {
        "reported_units": 4_141_959,
        "source": "https://www.hyundai.com/worldwide/en/newsroom/detail/0000000897",
        "scope": "Hyundai Motor global 2024 wholesale sales; fixture covers selected operating markets",
    },
}

RATE_FIELDS = ("s1", "s2", "s3", "s2_upper")

# Sector-wide support parameters (models.SupportParams). These are country/sector
# properties, not firm properties — every real firm must agree on them, exactly like
# the country benchmark contract below.
SUPPORT_SCALARS = ("lifetime_T", "lifetime_sens", "uf_band", "realworld_range")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_sha256(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return _sha256_bytes(canonical.encode())


def _tree_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(REPO)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    """One canonical JSON writer for reviewable, reproducible published artifacts."""
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def _prune_stale_json_outputs(expected_names: set[str]) -> list[str]:
    """Remove report JSON that is no longer part of the successfully built inventory."""
    removed: list[str] = []
    for path in OUT.glob("*.json"):
        if path.name not in expected_names:
            path.unlink()
            removed.append(path.name)
    return sorted(removed)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _rows(path: Path, expect_first_header: str) -> list[dict]:
    """Read a target-companies sheet: find the header row, return data-row dicts."""
    ws = openpyxl.load_workbook(path, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    header_i = next(i for i, r in enumerate(rows) if r[0] == expect_first_header)
    header = [str(c) if c else "" for c in rows[header_i]]
    out = []
    for r in rows[header_i + 1 :]:
        if not r[0] or not r[2]:  # needs Sector and Company columns
            continue
        out.append(dict(zip(header, (str(c) if c is not None else "" for c in r), strict=False)))
    return out


def build_universe() -> list[dict]:
    firms: list[dict] = [
        {
            "slug": "referenceco",
            "name": "ReferenceCo",
            "sector": "Automotive",
            "country": "—",
            "project": "TI",
            "runnable": True,
            "illustrative": True,
            "note": "Committed validation fixture with illustrative parameters (NOTES.md D4). "
            "Demonstrates the full report until real-firm data is collected.",
        }
    ]
    for r in _rows(REPO / "TI_CaseStudy_Target_Companies.xlsx", "Sector"):
        name = r["Company (candidate)"]
        slug = slugify(name)
        firms.append(
            {
                "slug": slug,
                "name": name,
                "sector": r["Sector"],
                "country": r["Country"],
                "project": "TI",
                "runnable": slug in FIXTURES,
                "basis": "estimated" if slug in NOTES_BY_SLUG else None,
                "note": NOTES_BY_SLUG.get(slug),
                "status": r.get("Status", ""),
                "selection_criteria": r.get("Selection criteria", ""),
            }
        )
    for r in _rows(REPO / "CAP_Target_Companies_Draft.xlsx", "Sector"):
        name = r["Company (candidate)"]
        firms.append(
            {
                "slug": slugify(name),
                "name": name,
                "sector": r["Sector"],
                "country": r["Country"],
                "project": "CAP",
                "runnable": False,
                "ticker": r.get("Ticker/Listing", ""),
            }
        )
    return firms


def build_meta() -> dict:
    wb_inputs = load_workbook_inputs(WORKBOOK)
    engine_paths = list((ENGINE_DIR / "ti_framework").rglob("*.py")) + [
        ENGINE_DIR / "pyproject.toml"
    ]
    return {
        "engine": "ti_framework",
        "engine_version": pkg_version("ti-framework"),
        "engine_source_sha256": _tree_sha256(engine_paths),
        "workbook": WORKBOOK.name,
        "workbook_sha256": _file_sha256(WORKBOOK),
        # The public calculator's validation boundary is content-addressed too —
        # api/compute.py can change engine-facing behaviour without touching
        # ti_framework, so it gets its own hash.
        "compute_service_sha256": _file_sha256(REPO / "api" / "compute.py"),
        "target_sources_sha256": {
            "TI_CaseStudy_Target_Companies.xlsx": _file_sha256(
                REPO / "TI_CaseStudy_Target_Companies.xlsx"
            ),
            "CAP_Target_Companies_Draft.xlsx": _file_sha256(
                REPO / "CAP_Target_Companies_Draft.xlsx"
            ),
        },
        "collection_status": {
            "countries_loaded": len(wb_inputs.countries),
            "missing_inputs": wb_inputs.missing_inputs,
            "warnings": wb_inputs.warnings,
        },
    }


# slugs whose fixture country benchmarks are refreshed from the workbook at build time —
# the workbook is the source of truth for the Layer-1 fields it carries (grid, S2 rates,
# status). fleet_intensity_base has no workbook column (io/schema.py LAYER1_COLUMNS), so
# fixtures remain its source; build_countries rejects cross-firm drift on it.
# ReferenceCo is excluded: it is the frozen validation case (NOTES.md D4).
MERGE_WORKBOOK = {"toyota", "hyundai"}


def merge_workbook_benchmarks(fx, workbook_countries) -> None:
    """Overwrite fixture Layer-1 values with collected workbook values where present.

    Fixture keeps anything the workbook has not collected (e.g. Tier C S1/S3 estimates)
    — no collected value is ever shadowed by an estimate, and no empty workbook cell
    ever erases a documented estimate.
    """
    for code, c in fx.countries.items():
        wb = workbook_countries.get(code)
        if wb is None:
            continue
        if wb.grid_intensity is not None:
            c.grid_intensity = wb.grid_intensity
        for attr in ("r_fleet", "r_power"):
            for s in ("s1", "s2", "s3", "s2_upper"):
                v = getattr(getattr(wb, attr), s)
                if v is not None:
                    setattr(getattr(c, attr), s, v)
        c.status = wb.status


def effective_inputs(fx, fixture_path: Path) -> dict:
    """Serialise the exact post-merge inputs used by the engine and calculator."""
    raw = json.loads(fixture_path.read_text())
    raw.pop("expected", None)
    for code, c in fx.countries.items():
        target = raw["countries"][code]
        if c.grid_intensity is not None:
            target["grid_intensity"] = c.grid_intensity
        target["status"] = c.status.value
        target["tier"] = c.tier.value
        for attr in ("r_fleet", "r_power"):
            rate = getattr(c, attr)
            target[attr] = {
                name: value for name in RATE_FIELDS if (value := getattr(rate, name)) is not None
            }
    for target, placement in zip(raw.get("placements", []), fx.placements, strict=True):
        target.setdefault("vehicle_tier", placement.vehicle.tier.value)
        target.setdefault("volume_tier", placement.volume_tier.value)
        if placement.vehicle.source:
            target.setdefault("vehicle_source", placement.vehicle.source)
        if placement.volume_source:
            target.setdefault("volume_source", placement.volume_source)
    return raw


def build_countries(real_payloads: dict[str, dict]) -> tuple[list[dict], dict]:
    """Build one canonical country contract and reject firm-specific benchmark drift.

    Guards the full shared-input surface: country benchmarks (``inputs.countries``)
    AND sector-wide support parameters (``inputs.support``) — a per-country VKT or a
    lifetime that differs between two firms would silently benchmark them against
    different pathways, so any divergence fails the build.

    Returns ``(countries, support_contract)`` where ``support_contract`` is the agreed
    scalar block plus the merged per-country ``vkt`` map.
    """
    countries: dict[str, dict] = {}
    owner: dict[str, str] = {}
    support_contract: dict | None = None
    support_owner = ""
    vkt: dict[str, float] = {}
    vkt_owner: dict[str, str] = {}
    for slug, payload in real_payloads.items():
        support = payload["inputs"].get("support") or {}
        scalars = {key: support.get(key) for key in SUPPORT_SCALARS}
        if support_contract is None:
            support_contract, support_owner = scalars, slug
        elif support_contract != scalars:
            differing = sorted(
                key for key in SUPPORT_SCALARS if support_contract.get(key) != scalars.get(key)
            )
            raise ValueError(
                f"support contract drift: {support_owner} vs {slug}; fields={differing}"
            )
        for code, value in (support.get("vkt") or {}).items():
            if code in vkt and vkt[code] != value:
                raise ValueError(
                    f"support contract drift for vkt.{code}: "
                    f"{vkt_owner[code]}={vkt[code]} vs {slug}={value}"
                )
            vkt[code] = value
            vkt_owner[code] = slug
        for code, country in payload["inputs"]["countries"].items():
            status = BenchmarkStatus(country["status"])
            candidate = {
                "code": code,
                **country,
                "warnings": country.get("warnings") or [],
                "flag_reason": FLAG_REASONS.get(status) if status.is_flag else None,
            }
            previous = countries.get(code)
            if previous is not None and previous != candidate:
                differing = sorted(
                    key
                    for key in previous.keys() | candidate.keys()
                    if previous.get(key) != candidate.get(key)
                )
                raise ValueError(
                    f"country contract drift for {code}: {owner[code]} vs {slug}; "
                    f"fields={differing}"
                )
            countries[code] = candidate
            owner[code] = slug
    for code, country in countries.items():
        country["vkt"] = vkt.get(code)
    return (
        [countries[code] for code in sorted(countries)],
        {**(support_contract or {}), "vkt": {code: vkt[code] for code in sorted(vkt)}},
    )


def build_contract(payloads: dict[str, dict]) -> dict:
    """Publish the emitted key sets so the web layer can pin the data contract.

    to_json_dict (report/outputs.py) is the single source of truth for the report
    shape; this records it as data, and rejects payloads that disagree on shape.
    """
    reference_slug, reference = next(iter(payloads.items()))
    contract = {
        "firm_result": sorted(reference),
        "cohort": sorted(next(iter(reference["cohorts"].values()))),
        "crossover": sorted({key for row in reference["crossover"] for key in row}),
        "data_quality": sorted(reference["data_quality"]),
        "provenance": sorted(reference["provenance"]),
    }
    for slug, payload in payloads.items():
        if sorted(payload) != contract["firm_result"]:
            raise ValueError(f"contract drift: {slug} top-level keys differ from {reference_slug}")
        for scenario, cohort in payload["cohorts"].items():
            if sorted(cohort) != contract["cohort"]:
                raise ValueError(f"contract drift: {slug}.cohorts.{scenario} keys differ")
        if sorted(payload["data_quality"]) != contract["data_quality"]:
            raise ValueError(f"contract drift: {slug}.data_quality keys differ")
    return contract


BY_YEAR_NOTE = (
    "Benchmarks and support parameters held at the current workbook vintage; "
    "year-over-year differences isolate export volume and powertrain-mix changes."
)


def build_by_year(raw: dict, fx) -> dict:
    """Run the engine once per historical cohort year (``placements_by_year``).

    Benchmarks and support parameters are held at the current workbook vintage, so
    differences across years isolate the export volume / powertrain-mix effect —
    they are NOT restated historical benchmarks. The primary cohort year is always
    included so the series is complete. Reused verbatim by check_published.py.
    """
    by_year_placements = raw.get("placements_by_year") or {}
    series: list[dict] = []
    for year_str in sorted({*by_year_placements, str(fx.cohort_year)}):
        year = int(year_str)
        if year == fx.cohort_year:
            placements = fx.placements
        else:
            # Only the placements differ per year — countries/support come from the
            # already-merged fx, so no workbook re-merge is needed here.
            placements = parse_fixture(
                {**raw, "cohort_year": year, "placements": by_year_placements[year_str]}
            ).placements
        result = run(
            fx.firm,
            year,
            placements,
            fx.countries,
            fx.support,
            fx.config,
            analysis_level=fx.analysis_level,
            layer1_method=fx.layer1_method,
        )
        year_payload = to_json_dict(result)
        series.append(
            {
                "year": year,
                "units": sum(p.units or 0 for p in placements),
                "units_by_country": _units_by_country(placements),
                "cohorts": {
                    scenario: {
                        key: cohort[key]
                        for key in ("total_tCO2e", "direction", "directional_only", "by_country")
                    }
                    for scenario, cohort in year_payload["cohorts"].items()
                },
            }
        )
    return {"note": BY_YEAR_NOTE, "series": series}


def _units_by_country(placements) -> dict[str, float]:
    out: dict[str, float] = {}
    for p in placements:
        out[p.country_code] = out.get(p.country_code, 0.0) + (p.units or 0)
    return out


def run_firm(slug: str, fixture_path: Path) -> dict:
    fx = load_fixture(fixture_path)
    if slug in MERGE_WORKBOOK:
        merge_workbook_benchmarks(fx, load_workbook_inputs(WORKBOOK).countries)
    result = run(
        fx.firm,
        fx.cohort_year,
        fx.placements,
        fx.countries,
        fx.support,
        fx.config,
        analysis_level=fx.analysis_level,
        layer1_method=fx.layer1_method,
    )
    payload = to_json_dict(result)
    payload["sensitivity"] = run_sensitivity(
        fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config
    )
    payload["inputs"] = effective_inputs(fx, fixture_path)
    # by_year runs from the effective (post-merge) inputs so check_published can
    # recompute it from the published payload alone.
    payload["by_year"] = build_by_year(payload["inputs"], fx)
    return payload


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = build_meta()
    firms = build_universe()
    payloads: dict[str, dict] = {}

    for firm in firms:
        if not firm["runnable"]:
            continue
        payload = run_firm(firm["slug"], FIXTURES[firm["slug"]])
        input_sha = _json_sha256(payload["inputs"])
        payload["provenance"] = {
            key: meta[key]
            for key in (
                "engine_version",
                "engine_source_sha256",
                "workbook",
                "workbook_sha256",
            )
        } | {"input_sha256": input_sha}
        payloads[firm["slug"]] = payload
        firm["cohort_year"] = payload["cohort_year"]
        # Net-zero commitment lives in the fixture (with sources); surfaced on the
        # firm card so TI direction can be read against the firm's own target.
        firm["netzero"] = payload["inputs"].get("netzero")
        coverage = COVERAGE_BY_SLUG.get(firm["slug"])
        if coverage:
            assessed_units = sum(p.get("units") or 0 for p in payload["inputs"]["placements"])
            firm["assessed_units"] = assessed_units
            firm["reported_units"] = coverage["reported_units"]
            firm["coverage_ratio"] = assessed_units / coverage["reported_units"]
            firm["coverage_source"] = coverage["source"]
            firm["coverage_scope"] = coverage["scope"]
        print(
            f"built {firm['slug']}.json  (TI_cohort S2 = "
            f"{payload['cohorts']['S2']['total_tCO2e']:,.1f} tCO2e)"
        )

    real_payloads = {
        firm["slug"]: payloads[firm["slug"]]
        for firm in firms
        if firm["runnable"] and not firm.get("illustrative")
    }
    countries, support_contract = build_countries(real_payloads)
    meta["support_contract"] = support_contract
    meta["dataset_sha256"] = _json_sha256(
        {
            "countries": countries,
            "firms": firms,
            "inputs": {
                slug: payload["provenance"]["input_sha256"]
                for slug, payload in sorted(payloads.items())
            },
            "engine_source_sha256": meta["engine_source_sha256"],
            "workbook_sha256": meta["workbook_sha256"],
        }
    )
    for payload in payloads.values():
        payload["provenance"]["dataset_sha256"] = meta["dataset_sha256"]
    expected_names = {
        "contract.json",
        "countries.json",
        "firms.json",
        "meta.json",
        *(f"{slug}.json" for slug in payloads),
    }
    removed = _prune_stale_json_outputs(expected_names)
    if removed:
        print(f"removed stale published outputs: {', '.join(removed)}")
    for slug, payload in payloads.items():
        _write_json(OUT / f"{slug}.json", payload)
    _write_json(OUT / "contract.json", build_contract(payloads))
    _write_json(OUT / "countries.json", countries)
    _write_json(OUT / "firms.json", firms)
    _write_json(OUT / "meta.json", meta)
    print(
        f"built firms.json ({len(firms)} firms, "
        f"{sum(f['runnable'] for f in firms)} runnable) and meta.json -> {OUT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
