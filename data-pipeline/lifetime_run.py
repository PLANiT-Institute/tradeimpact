#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Assemble engine runs from the published observed cohorts and destination inputs.

This is the join that turns two separate published objects into one calculation:

    product_cohorts.json      observed registrations, certified product intensities
    destination_eu.py         destination distance, lifetime, fleet baseline, grid, pathways
        -> one engine fixture per company cohort -> lifetime TI across S1/S2/S3

The join never invents a value. A product type whose emission model needs an input that is not
sourced (PHEV charge-depleting split, FCEV hydrogen intensity) is withheld with its unit count
recorded, so the published result states the share of the cohort it actually covers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PUBLISHED = REPO / "data" / "published"
sys.path.insert(0, str(REPO / "ti-framework"))
sys.path.insert(0, str(REPO / "data-pipeline"))

from adapters.destination_eu import REALWORLD_GAP, build_records as build_destination_records

# Registration-database product types mapped onto the engine's emission models.
_POWERTRAIN = {"ICE_OTHER": "ICE", "HEV": "HEV", "BEV": "BEV"}
_WITHHELD = {
    "PHEV": (
        "PHEV needs the charge-depleting and charge-sustaining split and a real-world utility "
        "factor. The registration dataset publishes only the weighted combined values, so no "
        "utility factor can be recovered without assuming one."
    ),
    "FCEV": "FCEV needs a hydrogen supply emissions intensity for the destination market.",
}

# Real-world correction applied to the certified value before it reaches the engine.
# EEA on-board monitoring, model-year 2022 registrations.
_PETROL, _DIESEL = REALWORLD_GAP["petrol"], REALWORLD_GAP["diesel"]
_CORRECTION = {
    # Toyota and Hyundai hybrids in this cohort are petrol hybrids.
    "HEV": 1.0 + _PETROL,
    # ICE_OTHER pools petrol and diesel; the midpoint is used and the span drives sensitivity.
    "ICE": 1.0 + (_PETROL + _DIESEL) / 2,
    # No official real-world gap is published for battery-electric energy consumption, so the
    # certified value is passed through uncorrected. This flatters BEV against corrected ICE.
    "BEV": 1.0,
}
_CORRECTION_RANGE = (1.0 + _DIESEL, 1.0 + _PETROL)

_TIER_RANK = {"A": 0, "B": 1, "C": 2, "?": 3}


def _worst(*tiers: str | None) -> str:
    return max((t or "?" for t in tiers), key=lambda t: _TIER_RANK.get(t, 3))


def build_fixtures(
    cohorts: list[dict[str, Any]] | None = None,
    destination: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """One engine fixture per observed product cohort."""
    if cohorts is None:
        cohorts = json.loads((PUBLISHED / "product_cohorts.json").read_text())
    records = build_destination_records()
    if destination is None:
        destination = records["destination_inputs"]
    by_code = {row["country_code"]: row for row in destination}
    notes = {row["rate"]: row["note"] for row in records["pathway_notes"]}
    scenario_sources = {
        scenario: f"r_fleet — {notes[f'r_fleet_{scenario.lower()}']} "
        f"r_power — {notes[f'r_power_{scenario.lower()}']}"
        for scenario in ("S1", "S2", "S3")
    }

    fixtures: dict[str, dict[str, Any]] = {}
    for cohort in cohorts:
        countries: dict[str, Any] = {}
        placements: list[dict[str, Any]] = []
        withheld: dict[str, dict[str, Any]] = {}
        uncovered: list[dict[str, Any]] = []
        unpriced: list[dict[str, Any]] = []

        for record in cohort["records"]:
            code = record["destination_geography"]
            product = record["product_type"]
            units = record["units"]
            if product in _WITHHELD:
                entry = withheld.setdefault(
                    product, {"units": 0.0, "reason": _WITHHELD[product], "destinations": set()}
                )
                entry["units"] += units
                entry["destinations"].add(code)
                continue
            powertrain = _POWERTRAIN.get(product)
            destination_row = by_code.get(code)
            if powertrain is None or destination_row is None:
                uncovered.append({"destination": code, "product_type": product, "units": units})
                continue

            if code not in countries:
                countries[code] = _country_payload(destination_row)

            correction = _CORRECTION[powertrain]
            tailpipe = record["certified_tailpipe_gco2_per_km"]
            electricity = record["certified_electricity_kwh_per_km"]
            placement: dict[str, Any] = {
                "country": code,
                "brand": cohort["company_name"],
                "model": record["product_name"],
                "powertrain": powertrain,
                "units": units,
                "realworld_correction": correction,
                "vehicle_source": ",".join(record["source_ids"]),
                "volume_source": ",".join(record["source_ids"]),
                "volume_tier": "A",
            }
            if powertrain == "BEV":
                placement["eta_ev"] = None if electricity is None else electricity * correction
                placement["vehicle_tier"] = "A" if electricity is not None else "?"
                priced = electricity is not None
            else:
                placement["ice_intensity"] = (
                    None if tailpipe is None else tailpipe * correction / 1000.0
                )
                placement["vehicle_tier"] = "A" if tailpipe is not None else "?"
                priced = tailpipe is not None
            placements.append(placement)
            if not priced:
                # The engine records these as missing and drops them from the total. Counting
                # them as covered would overstate what the published number actually spans.
                unpriced.append(
                    {
                        "destination": code,
                        "product_type": product,
                        "product_name": record["product_name"],
                        "units": units,
                        "reason": "the registration dataset reports no certified intensity",
                    }
                )

        unpriced_units = sum(row["units"] for row in unpriced)
        covered_units = sum(p["units"] for p in placements) - unpriced_units
        withheld_units = sum(entry["units"] for entry in withheld.values())
        total_units = (
            covered_units + unpriced_units + withheld_units + sum(row["units"] for row in uncovered)
        )
        lifetimes = {
            code: by_code[code]["operating_lifetime_years"]
            for code in countries
            if by_code[code]["operating_lifetime_years"] is not None
        }
        central_lifetime = _units_weighted_lifetime(placements, lifetimes)

        fixtures[cohort["cohort_id"]] = {
            "firm": cohort["company_name"],
            "cohort_year": cohort["cohort_year"],
            "analysis_level": "Level 1",
            "layer1_method": "B",
            "countries": countries,
            "support": {
                "lifetime_T": central_lifetime,
                "lifetime_sens": 3,
                "lifetime_by_country": lifetimes,
                "vkt": {
                    code: by_code[code]["vkt_km_per_year"]
                    for code in countries
                    if by_code[code]["vkt_km_per_year"] is not None
                },
                "uf_band": 0.15,
                "realworld_range": list(_CORRECTION_RANGE),
            },
            "placements": placements,
            "config": {"scenarios": ["S1", "S2", "S3"], "flag_market_rule": "exclude"},
            "scenario_sources": scenario_sources,
            "coverage": {
                "cohort_id": cohort["cohort_id"],
                "company_id": cohort["company_id"],
                "total_units": total_units,
                "covered_units": covered_units,
                "covered_share": covered_units / total_units if total_units else 0.0,
                "withheld_product_types": {
                    product: {
                        "units": entry["units"],
                        "share": entry["units"] / total_units if total_units else 0.0,
                        "reason": entry["reason"],
                        "destinations": sorted(entry["destinations"]),
                    }
                    for product, entry in sorted(withheld.items())
                },
                "unmatched_records": uncovered,
                "unpriced_records": unpriced,
                "unpriced_units": unpriced_units,
                "vkt_proxy": _vkt_proxy_summary(placements, by_code, covered_units),
                "real_world_correction": {
                    "applied": True,
                    "factors": dict(_CORRECTION),
                    "sensitivity_range": list(_CORRECTION_RANGE),
                    "source_id": "eea-real-world-obfcm",
                    "note": (
                        "Certified WLTP values are multiplied once, at fixture build time. The "
                        "engine never re-applies a correction, so double counting is impossible. "
                        "No official real-world gap exists for battery-electric consumption, so "
                        "BEV passes through at 1.0 and is the optimistic end of the comparison."
                    ),
                },
            },
        }
    return fixtures


def _vkt_proxy_summary(
    placements: list[dict[str, Any]], by_code: dict[str, Any], covered_units: float
) -> dict[str, Any]:
    """Which destinations run on a proxied distance, how many units that is, and its band."""
    proxied = sorted(
        {p["country"] for p in placements if by_code[p["country"]]["vkt_tier"] == "C"}
    )
    units = sum(p["units"] for p in placements if p["country"] in proxied)
    sample = next((by_code[code] for code in proxied), None)
    return {
        "destinations": proxied,
        "units": units,
        "unit_share": units / covered_units if covered_units else 0.0,
        "central_km_per_year": sample["vkt_km_per_year"] if sample else None,
        "low_km_per_year": sample["vkt_low_km_per_year"] if sample else None,
        "high_km_per_year": sample["vkt_high_km_per_year"] if sample else None,
    }


def _country_payload(row: dict[str, Any]) -> dict[str, Any]:
    """Engine-unit country parameters: kgCO2e/km and kgCO2e/kWh."""
    fleet = row["fleet_intensity_base_gco2_per_km"]
    grid = row["grid_intensity_gco2_per_kwh"]
    return {
        "name": row["country_code"],
        "grid_intensity": None if grid is None else grid / 1000.0,
        "fleet_intensity_base": None if fleet is None else fleet / 1000.0,
        "r_fleet": {"s1": row["r_fleet_s1"], "s2": row["r_fleet_s2"], "s3": row["r_fleet_s3"]},
        "r_power": {"s1": row["r_power_s1"], "s2": row["r_power_s2"], "s3": row["r_power_s3"]},
        "status": "COMPUTED",
        "tier": _worst(
            row["fleet_intensity_tier"], row["vkt_tier"], row["grid_intensity_tier"],
            row["operating_lifetime_tier"],
        ),
        "source": ",".join(row["source_ids"]),
        "warnings": row["warnings"],
    }


def _units_weighted_lifetime(
    placements: list[dict[str, Any]], lifetimes: dict[str, int]
) -> int | None:
    """Central horizon for reporting; per-country values still drive each cell."""
    weighted = sum(p["units"] * lifetimes[p["country"]] for p in placements if p["country"] in lifetimes)
    total = sum(p["units"] for p in placements if p["country"] in lifetimes)
    return int(round(weighted / total)) if total else None


def _sweep_vkt_proxy(raw: dict[str, Any]) -> dict[str, Any]:
    """Re-run with the proxied distances at the low and high quartile of measured markets.

    Distance is the single input the destinations without a national traffic series depend on,
    and the product side scales with it linearly. This sweep is what makes that dependence a
    published number instead of a caveat.
    """
    from ti_framework.core.scenarios import run
    from ti_framework.io.fixtures import parse_fixture

    proxy = raw["coverage"]["vkt_proxy"]
    if not proxy["destinations"] or proxy["low_km_per_year"] is None:
        return {"status": "not_applicable", "reason": "every destination has a measured distance"}

    def totals(bound: str) -> dict[str, float]:
        variant = json.loads(json.dumps(raw))
        for code in proxy["destinations"]:
            variant["support"]["vkt"][code] = proxy[f"{bound}_km_per_year"]
        fx = parse_fixture(variant)
        result = run(
            fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config,
            analysis_level=fx.analysis_level, layer1_method=fx.layer1_method,
        )
        return {scenario.value: cohort.total for scenario, cohort in result.cohorts.items()}

    low, high = totals("low"), totals("high")
    return {
        "status": "available",
        "proxied_destinations": proxy["destinations"],
        "proxied_unit_share": proxy["unit_share"],
        "central_km_per_year": proxy["central_km_per_year"],
        "low_km_per_year": proxy["low_km_per_year"],
        "high_km_per_year": proxy["high_km_per_year"],
        "low_distance": low,
        "high_distance": high,
        "sign_stable": {
            scenario: (low[scenario] > 0) == (high[scenario] > 0) for scenario in low
        },
        "note": (
            "Low and high are the lower and upper quartile of the distances actually measured "
            "across the member states that publish one. A longer assumed distance raises the "
            "product's emissions while the benchmark, which is CO2 per car, does not move."
        ),
    }


def run_lifetime(fixtures: dict[str, dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    """Run every fixture through the engine and return publishable payloads."""
    from ti_framework.core.aggregate import decomposition_identity_holds
    from ti_framework.core.scenarios import run
    from ti_framework.core.sensitivity import run_sensitivity
    from ti_framework.io.fixtures import parse_fixture
    from ti_framework.report.outputs import to_json_dict

    fixtures = fixtures if fixtures is not None else build_fixtures()
    results: dict[str, dict[str, Any]] = {}
    for cohort_id, raw in fixtures.items():
        fx = parse_fixture(raw)
        result = run(
            fx.firm,
            fx.cohort_year,
            fx.placements,
            fx.countries,
            fx.support,
            fx.config,
            analysis_level=fx.analysis_level,
            layer1_method=fx.layer1_method,
            scenario_sources=fx.scenario_sources,
        )
        payload = to_json_dict(result)
        payload["sensitivity"] = run_sensitivity(
            fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config
        )
        # The engine's portfolio series answers "what if an identical cohort were sold every
        # year". With one observed cohort that is a counterfactual, not an observation, so it
        # is withheld rather than published next to sourced numbers.
        payload["portfolio"] = {}
        payload["portfolio_withheld"] = {
            "reason": (
                "Rolling portfolio TI needs multi-year cohorts. Only the "
                f"{raw['cohort_year']} cohort is observed, and repeating it would publish a "
                "counterfactual as a result."
            ),
            "unblocked_by": "registration cohorts for at least T consecutive years",
        }
        payload["coverage"] = raw["coverage"]
        payload["cohort_id"] = cohort_id
        payload["sensitivity"]["vkt_proxy"] = _sweep_vkt_proxy(raw)
        payload["decomposition_identity_holds"] = all(
            decomposition_identity_holds(cohort) for cohort in result.cohorts.values()
        )
        if not payload["decomposition_identity_holds"]:
            raise ValueError(f"{cohort_id}: TI_cohort != sum by destination / by product type")
        results[cohort_id] = payload
    return results


def write_reports(outdir: Path) -> list[Path]:
    """Write the per-cohort report bundle: input fixture, five CSVs, declaration, charts."""
    from dataclasses import replace as _replace

    from ti_framework.core.scenarios import run
    from ti_framework.core.sensitivity import run_sensitivity
    from ti_framework.io.fixtures import parse_fixture
    from ti_framework.report.outputs import write_all
    from ti_framework.report.plots import write_plots

    written: list[Path] = []
    for cohort_id, raw in build_fixtures().items():
        target = outdir / cohort_id
        target.mkdir(parents=True, exist_ok=True)
        fixture_path = target / "run_input.json"
        fixture_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
        written.append(fixture_path)

        fx = parse_fixture(raw)
        result = run(
            fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config,
            analysis_level=fx.analysis_level, layer1_method=fx.layer1_method,
            scenario_sources=fx.scenario_sources,
        )
        # Same withholding rule as the published payload: no counterfactual portfolio.
        result = _replace(result, portfolio={})
        sensitivity = run_sensitivity(
            fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config
        )
        written.extend(write_all(result, target, sensitivity=sensitivity))
        written.extend(write_plots(result, target))
    return written


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="write the full report bundle to this directory")
    args = parser.parse_args()

    results = run_lifetime()
    for cohort_id, payload in results.items():
        coverage = payload["coverage"]
        print(f"{cohort_id}: {coverage['covered_share']:.1%} of units covered")
        for scenario, cohort in sorted(payload["cohorts"].items()):
            print(
                f"   {scenario}: {cohort['total_tCO2e'] / 1e6:+.3f} MtCO2e  "
                f"{cohort['direction']}  ({len(cohort['by_country'])} destinations)"
            )
    if args.out:
        written = write_reports(Path(args.out))
        print(f"wrote {len(written)} report files to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
