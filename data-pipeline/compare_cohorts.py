#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Why do two cohorts differ in lifetime TI per vehicle?

The published result answers "how large"; the mandatory decomposition answers "where".
Neither answers the question a manufacturer actually asks when it sees a competitor's
number: *which of my decisions put me here* — the markets I sell into, the powertrain mix
I sell, or the vehicles themselves.

This splits the per-vehicle gap between two cohorts into exactly those three parts:

    A_F = sum_c sum_v  s_F(c,v) * t_F(c,v)          [kgCO2e per covered vehicle]

    destination mix    sum_c (w_B(c) - w_A(c)) * tbar(c)
    powertrain mix     sum_c wbar(c) * sum_v (p_B(v|c) - p_A(v|c)) * tbar(c,v)
    product intensity  sum_c wbar(c) * sum_v pbar(v|c) * (t_B(c,v) - t_A(c,v))

Averaging the weights across the two cohorts is what keeps the three terms summing to the
gap; the leftover interaction is reported as a residual rather than silently absorbed.

Cells come from the engine's own published joint (``cohorts[S].by_cell``), which the engine
holds to the decomposition identity against both margins before it is written. The crossover
table cannot stand in for it: that carries one row per (destination, powertrain), while
per-vehicle TI varies by model inside a powertrain.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ti-framework"))
sys.path.insert(0, str(REPO / "data-pipeline"))

from lifetime_run import run_lifetime  # noqa: E402

RECONCILE_TOL = 1e-6


def _cells(payload: dict[str, Any], scenario: str) -> dict[tuple[str, str], tuple[float, float]]:
    """(destination, powertrain) -> (covered units, units-weighted per-vehicle TI in kg)."""
    return {
        (cell["country"], cell["powertrain"]): (cell["units"], cell["TI_per_vehicle_kgCO2e"])
        for cell in payload["cohorts"][scenario]["by_cell"]
        if cell["units"]
    }


def decompose(
    cohort_a: str,
    cohort_b: str,
    scenario: str = "S2",
    published: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Split cohort B's per-vehicle TI gap against cohort A into its three sources."""
    published = published if published is not None else run_lifetime()

    units: dict[str, dict[tuple[str, str], float]] = {}
    per_vehicle: dict[str, dict[tuple[str, str], float]] = {}
    reconciliation: dict[str, float] = {}
    for cohort_id in (cohort_a, cohort_b):
        built = _cells(published[cohort_id], scenario)
        units[cohort_id] = {key: value[0] for key, value in built.items()}
        per_vehicle[cohort_id] = {key: value[1] for key, value in built.items()}
        rebuilt = sum(u * per_vehicle[cohort_id][k] for k, u in units[cohort_id].items()) / 1000.0
        reference = published[cohort_id]["cohorts"][scenario]["total_tCO2e"]
        relative = abs(rebuilt - reference) / abs(reference)
        if relative > RECONCILE_TOL:
            raise ValueError(
                f"{cohort_id}/{scenario}: the published cells give {rebuilt:,.0f} tCO2e against "
                f"the published total {reference:,.0f} (relative {relative:.2e}). The "
                "decomposition would describe a run that was never published."
            )
        reconciliation[cohort_id] = relative

    destinations = sorted({c for cid in units for (c, _) in units[cid]})
    powertrains = sorted({v for cid in units for (_, v) in units[cid]})
    totals = {cid: sum(units[cid].values()) for cid in units}

    def share(cid: str, code: str) -> float:
        return sum(u for (c, _), u in units[cid].items() if c == code) / totals[cid]

    def within(cid: str, code: str, powertrain: str) -> float:
        """Powertrain share inside one destination. Zero where the cohort sells nothing."""
        in_destination = sum(u for (c, _), u in units[cid].items() if c == code)
        return units[cid].get((code, powertrain), 0.0) / in_destination if in_destination else 0.0

    def ti(cid: str, code: str, powertrain: str) -> float | None:
        return per_vehicle[cid].get((code, powertrain))

    average = {
        cid: sum(u * per_vehicle[cid][k] for k, u in units[cid].items()) / totals[cid]
        for cid in units
    }
    gap = average[cohort_b] - average[cohort_a]

    # A cell only one cohort sells still carries its own TI; a cell neither sells is absent.
    ti_bar_cell: dict[tuple[str, str], float] = {}
    for code in destinations:
        for powertrain in powertrains:
            observed = [
                value
                for value in (ti(cohort_a, code, powertrain), ti(cohort_b, code, powertrain))
                if value is not None
            ]
            if observed:
                ti_bar_cell[(code, powertrain)] = sum(observed) / len(observed)

    mix_bar = {
        (code, powertrain): (within(cohort_a, code, powertrain) + within(cohort_b, code, powertrain))
        / 2
        for code in destinations
        for powertrain in powertrains
    }
    weight_bar = {code: (share(cohort_a, code) + share(cohort_b, code)) / 2 for code in destinations}
    ti_bar_destination = {
        code: sum(
            mix_bar[(code, pt)] * ti_bar_cell[(code, pt)]
            for pt in powertrains
            if (code, pt) in ti_bar_cell
        )
        for code in destinations
    }

    destination_term = {
        code: (share(cohort_b, code) - share(cohort_a, code)) * ti_bar_destination[code]
        for code in destinations
    }
    mix_term = {
        code: weight_bar[code]
        * sum(
            (within(cohort_b, code, pt) - within(cohort_a, code, pt)) * ti_bar_cell[(code, pt)]
            for pt in powertrains
            if (code, pt) in ti_bar_cell
        )
        for code in destinations
    }
    intensity_term = {
        code: weight_bar[code]
        * sum(
            mix_bar[(code, pt)] * (ti(cohort_b, code, pt) - ti(cohort_a, code, pt))
            for pt in powertrains
            if ti(cohort_a, code, pt) is not None and ti(cohort_b, code, pt) is not None
        )
        for code in destinations
    }
    terms = {
        "destination_mix": sum(destination_term.values()),
        "powertrain_mix": sum(mix_term.values()),
        "product_intensity": sum(intensity_term.values()),
    }

    return {
        "scenario": scenario,
        "baseline_cohort": cohort_a,
        "compared_cohort": cohort_b,
        "unit": "kgCO2e per covered vehicle",
        "per_vehicle": average,
        "gap": gap,
        "terms": terms,
        "residual": gap - sum(terms.values()),
        "by_destination": {
            code: {
                "destination_mix": destination_term[code],
                "powertrain_mix": mix_term[code],
                "product_intensity": intensity_term[code],
                "share_baseline": share(cohort_a, code),
                "share_compared": share(cohort_b, code),
                "ti_per_vehicle_average": ti_bar_destination[code],
            }
            for code in destinations
        },
        "by_powertrain": {
            powertrain: {
                cid: {
                    "unit_share": sum(u for (_, pt), u in units[cid].items() if pt == powertrain)
                    / totals[cid],
                    "ti_per_vehicle": (
                        sum(
                            u * per_vehicle[cid][k]
                            for k, u in units[cid].items()
                            if k[1] == powertrain
                        )
                        / n
                        if (n := sum(u for (_, pt), u in units[cid].items() if pt == powertrain))
                        else None
                    ),
                }
                for cid in units
            }
            for powertrain in powertrains
        },
        "reconciliation_relative_error": reconciliation,
    }


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="toyota-eu27-passenger-cars-2024")
    parser.add_argument("--compared", default="hyundai-eu27-passenger-cars-2024")
    parser.add_argument("--scenario", default="S2", choices=("S1", "S2", "S3"))
    parser.add_argument("--json", action="store_true", help="emit the full payload")
    args = parser.parse_args()

    result = decompose(args.baseline, args.compared, args.scenario)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(f"=== {args.scenario}: lifetime TI per covered vehicle, {result['unit']} ===")
    for cohort_id, value in result["per_vehicle"].items():
        print(f"  {cohort_id:42s} {value:>10,.0f}")
    print(f"  {'gap (compared - baseline)':42s} {result['gap']:>10,.0f}")
    print("\ndecomposition")
    for label, value in result["terms"].items():
        print(f"  {label:<20s} {value:>10,.0f}   {value / result['gap'] * 100:>6.1f}% of gap")
    print(f"  {'residual':<20s} {result['residual']:>10,.0f}")
    print("\nper-vehicle TI and unit share by powertrain")
    for powertrain, rows in result["by_powertrain"].items():
        line = f"  {powertrain:5s}"
        for cohort_id, row in rows.items():
            label = cohort_id.split("-")[0]
            line += f"   {label:8s} {row['unit_share']:6.2%} {row['ti_per_vehicle']:>9,.0f}"
        print(line)
    return 0


def _self_check() -> None:
    """The three terms must reconstruct the gap, and a cohort must not differ from itself."""
    published = run_lifetime()
    toyota, hyundai = (
        "toyota-eu27-passenger-cars-2024",
        "hyundai-eu27-passenger-cars-2024",
    )
    for scenario in ("S1", "S2", "S3"):
        result = decompose(toyota, hyundai, scenario, published)
        assert abs(result["residual"]) < 0.01 * abs(result["gap"]), (
            f"{scenario}: residual {result['residual']:,.0f} exceeds 1% of the "
            f"{result['gap']:,.0f} gap — the weighting no longer closes"
        )
        identical = decompose(toyota, toyota, scenario, published)
        assert abs(identical["gap"]) < 1e-9, f"{scenario}: a cohort differs from itself"
        assert all(abs(v) < 1e-9 for v in identical["terms"].values()), (
            f"{scenario}: a cohort compared with itself produced a non-zero term"
        )
    print("compare_cohorts self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
        raise SystemExit(0)
    raise SystemExit(main())
