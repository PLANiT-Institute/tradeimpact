# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line interface: ``ti run`` / ``ti validate`` / ``ti report``."""

from __future__ import annotations

import argparse
import sys

from ti_framework.core.aggregate import decomposition_identity_holds
from ti_framework.core.scenarios import run
from ti_framework.core.sensitivity import run_sensitivity
from ti_framework.io.fixtures import FixtureRun, load_fixture
from ti_framework.io.workbook import load_workbook_inputs
from ti_framework.models import RunResult, Scenario
from ti_framework.report.outputs import data_quality_text, write_all


def _run_fixture(path: str) -> tuple[FixtureRun, RunResult]:
    fx = load_fixture(path)
    result = run(
        fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support,
        fx.config, analysis_level=fx.analysis_level, layer1_method=fx.layer1_method,
    )
    return fx, result


def _print_summary(result: RunResult) -> None:
    print(f"\n=== TI run: {result.firm} | cohort {result.cohort_year} ===")
    for sc in (Scenario.S1, Scenario.S2, Scenario.S3):
        c = result.cohorts.get(sc)
        if c is None:
            continue
        tag = " [DIRECTIONAL ONLY]" if c.directional_only else ""
        print(f"  TI_cohort {sc.value} ({sc.label}): {c.total:,.1f} tCO2e{tag}")
        if c.by_country:
            print("    by country:    " + ", ".join(f"{k}={v:,.1f}" for k, v in c.by_country.items()))
        if c.by_powertrain:
            print("    by powertrain: " + ", ".join(f"{k}={v:,.1f}" for k, v in c.by_powertrain.items()))


def cmd_run(args: argparse.Namespace) -> int:
    if args.workbook:
        inputs = load_workbook_inputs(args.workbook)
        print(f"Loaded workbook: {len(inputs.countries)} countries, "
              f"{len(inputs.vehicles)} vehicle rows, {len(inputs.volumes)} volume rows.")
        if inputs.missing_inputs:
            print("Missing / not-yet-collected inputs:")
            for m in inputs.missing_inputs:
                print(f"  - {m}")
        if inputs.warnings:
            print("Warnings:")
            for w in inputs.warnings:
                print(f"  ! {w}")
        if not args.fixture:
            print("\n(No fixture provided — workbook is a template with empty cells, so no "
                  "end-to-end TI is computed. Provide --fixture for a runnable case.)")
            return 0
    if not args.fixture:
        print("error: provide --fixture (runnable case) and/or --workbook (template inspection)",
              file=sys.stderr)
        return 2

    fx, result = _run_fixture(args.fixture)
    _print_summary(result)
    if args.out:
        sens = run_sensitivity(fx.firm, fx.cohort_year, fx.placements, fx.countries,
                               fx.support, fx.config)
        written = write_all(result, args.out, sensitivity=sens)
        print(f"\nWrote {len(written)} files to {args.out}")
    print("\n" + data_quality_text(result))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from ti_framework.report.plots import write_plots

    fx, result = _run_fixture(args.fixture)
    sens = run_sensitivity(fx.firm, fx.cohort_year, fx.placements, fx.countries,
                           fx.support, fx.config)
    written = write_all(result, args.out, sensitivity=sens)
    plots = write_plots(result, args.out)
    _print_summary(result)
    print(f"\nWrote {len(written)} data files and {len(plots)} plots to {args.out}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    fx, result = _run_fixture(args.fixture)
    if fx.expected is None:
        print("error: fixture has no 'expected' block to validate against", file=sys.stderr)
        return 2
    tol = args.tol
    ok = True

    for sc in (Scenario.S1, Scenario.S2, Scenario.S3):
        exp = fx.expected.get("cohorts", {}).get(sc.value)
        if exp is None:
            continue
        got = result.cohorts[sc].total
        rel = abs(got - exp) / (abs(exp) if exp != 0 else 1.0)
        status = "OK " if rel <= tol else "FAIL"
        if rel > tol:
            ok = False
        print(f"[{status}] TI_cohort {sc.value}: expected {exp:,.3f}, got {got:,.3f}, rel={rel:.3%}")

    for ev in fx.expected.get("vehicles", []):
        match = [
            vr for vr in result.vehicle_results
            if vr.country_code == ev["country"]
            and vr.powertrain.value == ev["powertrain"]
            and vr.scenario.value == ev["scenario"]
        ]
        if not match:
            print(f"[FAIL] no vehicle result for {ev}")
            ok = False
            continue
        vr = match[0]
        if "cumulative" in ev:
            rel = abs(vr.cumulative - ev["cumulative"]) / (abs(ev["cumulative"]) or 1.0)
            st = "OK " if rel <= tol else "FAIL"
            ok = ok and rel <= tol
            print(f"[{st}] cumulative {ev['country']}/{ev['powertrain']}/{ev['scenario']}: "
                  f"expected {ev['cumulative']:,.3f}, got {vr.cumulative:,.3f}, rel={rel:.3%}")

    # decomposition identity must hold for every scenario
    for sc, c in result.cohorts.items():
        if not decomposition_identity_holds(c):
            print(f"[FAIL] decomposition identity broken for {sc.value}")
            ok = False

    print("\nVALIDATION:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ti", description="Trade Impact (TI) Framework engine")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("run", help="Run the engine on a fixture and/or inspect a workbook")
    pr.add_argument("--fixture", help="JSON fixture with a fully-specified runnable case")
    pr.add_argument("--workbook", help="TI_Data_Workbook .xlsx to inspect (partial-data demo)")
    pr.add_argument("--out", help="output directory for CSV/JSON")
    pr.set_defaults(func=cmd_run)

    pt = sub.add_parser("report", help="Run + write CSV/JSON + plots")
    pt.add_argument("--fixture", required=True)
    pt.add_argument("--out", default="outputs")
    pt.set_defaults(func=cmd_report)

    pv = sub.add_parser("validate", help="Run a fixture and assert it matches its 'expected' block")
    pv.add_argument("--fixture", required=True)
    pv.add_argument("--tol", type=float, default=0.01, help="relative tolerance (default 1%%)")
    pv.set_defaults(func=cmd_validate)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
