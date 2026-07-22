# SPDX-License-Identifier: GPL-3.0-or-later
"""CSV/JSON writers and the data-quality declaration (Guideline §5.1, §5.3 [rule-g5.3-declaration];
Whitepaper §5.1 [rule-5.1-tiers], §5.3 [rule-5.3-no-netting]).

Required outputs (Guideline §5.1):
  1. TI_cohort,F,Y0,S [tCO2e], S1/S2/S3
  2. TI_annual time-series, t=0..T-1, S1/S2/S3
  3. TI_portfolio rolling annual, S1/S2/S3
  4. Decomposition by operating country and powertrain (mandatory)
plus crossover year per vehicle type and a data-quality declaration.

TI is never netted against Scope 3 — it is written as a separate disclosure only (§5.4).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from ti_framework.core.aggregate import direction_label
from ti_framework.models import RunResult, Scenario


def cohort_summary_df(run: RunResult) -> pd.DataFrame:
    rows = []
    for sc, cohort in run.cohorts.items():
        rows.append(
            {
                "firm": run.firm,
                "cohort_year": run.cohort_year,
                "scenario": sc.value,
                "scenario_label": sc.label,
                "TI_cohort_tCO2e": cohort.total,
                "direction": direction_label(cohort.total),
                "directional_only": cohort.directional_only,
                "n_excluded_flag_markets": len(cohort.excluded_flag_markets),
            }
        )
    return pd.DataFrame(rows)


def annual_df(run: RunResult) -> pd.DataFrame:
    data: dict[str, list[float]] = {}
    T = 0
    for sc, cohort in run.cohorts.items():
        data[sc.value] = cohort.annual
        T = max(T, len(cohort.annual))
    df = pd.DataFrame({"t": list(range(T))})
    for k, v in data.items():
        df[f"TI_annual_{k}_tCO2e"] = pd.Series(v)
    return df


def portfolio_df(run: RunResult) -> pd.DataFrame:
    T = max((len(v) for v in run.portfolio.values()), default=0)
    df = pd.DataFrame({"year_index": list(range(T))})
    for sc, series in run.portfolio.items():
        df[f"TI_portfolio_{sc.value}_tCO2e"] = pd.Series(series)
    return df


def decomposition_df(run: RunResult) -> pd.DataFrame:
    rows = []
    for sc, cohort in run.cohorts.items():
        for code, val in cohort.by_country.items():
            rows.append({"scenario": sc.value, "axis": "country", "key": code, "TI_tCO2e": val})
        for pt, val in cohort.by_powertrain.items():
            rows.append({"scenario": sc.value, "axis": "powertrain", "key": pt, "TI_tCO2e": val})
    return pd.DataFrame(rows)


def crossover_df(run: RunResult) -> pd.DataFrame:
    rows = []
    for vr in run.vehicle_results:
        rows.append(
            {
                "country": vr.country_code,
                "powertrain": vr.powertrain.value,
                "scenario": vr.scenario.value,
                "crossover_year": vr.crossover_year,
                "crossover_reason": vr.crossover_reason,
                "TI_per_vehicle_kgCO2e": vr.cumulative,
            }
        )
    return pd.DataFrame(rows)


def data_quality_text(run: RunResult) -> str:
    """Render the data-quality declaration following Guideline §5.3."""
    dq = run.data_quality
    lines: list[str] = []
    lines.append(f"Firm: {dq.firm} | Cohort year: {dq.cohort_year} | Analysis level: {dq.analysis_level}")
    lines.append("")
    lines.append(f"Layer 1 — fleet benchmark:  Method: {dq.layer1_method}")
    lines.append("  Benchmark tiers by country: " + ", ".join(f"{k}={v}" for k, v in dq.benchmark_tiers.items()))
    lines.append("")
    lines.append("Layer 2 tiers: " + (", ".join(f"{k}={v}" for k, v in dq.layer2_tiers.items()) or "(none collected)"))
    lines.append("")
    lines.append(f"Vehicle lifetime T: {dq.lifetime_T} (± {dq.lifetime_sens} yr sensitivity)")
    lines.append("")
    lines.append("Scenario sources:")
    for k, v in dq.scenario_sources.items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("Results (TI_cohort, tCO2e):")
    for sc in (Scenario.S1, Scenario.S2, Scenario.S3):
        if sc in run.cohorts:
            c = run.cohorts[sc]
            tag = " [DIRECTIONAL ONLY]" if c.directional_only else ""
            lines.append(f"  {sc.value} ({sc.label}): {c.total:,.1f}{tag}")
    lines.append("")
    if dq.flag_markets:
        lines.append("FLAG markets excluded from S2 headline (reported separately):")
        for k, v in dq.flag_markets.items():
            lines.append(f"  {k}: {v}")
        lines.append("")
    if dq.missing_inputs:
        lines.append("Missing inputs (not fabricated):")
        for m in dq.missing_inputs:
            lines.append(f"  - {m}")
        lines.append("")
    if dq.warnings:
        lines.append("Warnings:")
        for w in dq.warnings:
            lines.append(f"  ! {w}")
        lines.append("")
    lines.append("NOTE: TI is a separate additional disclosure and is never netted against Scope 3 Category 11.")
    return "\n".join(lines)


def to_json_dict(run: RunResult) -> dict:
    """Serialise the full run result to a JSON-ready dict."""
    return {
        "firm": run.firm,
        "cohort_year": run.cohort_year,
        "cohorts": {
            sc.value: {
                "total_tCO2e": c.total,
                "direction": direction_label(c.total),
                "directional_only": c.directional_only,
                "by_country": c.by_country,
                "by_powertrain": c.by_powertrain,
                "annual_tCO2e": c.annual,
                "excluded_flag_markets": c.excluded_flag_markets,
                "warnings": c.warnings,
            }
            for sc, c in run.cohorts.items()
        },
        "portfolio": {sc.value: series for sc, series in run.portfolio.items()},
        "crossover": [
            {
                "country": vr.country_code,
                "powertrain": vr.powertrain.value,
                "scenario": vr.scenario.value,
                "crossover_year": vr.crossover_year,
                "reason": vr.crossover_reason,
                "TI_per_vehicle_kgCO2e": vr.cumulative,
            }
            for vr in run.vehicle_results
        ],
        "data_quality": asdict(run.data_quality),
    }


def write_all(run: RunResult, outdir: str | Path, sensitivity: dict | None = None) -> list[Path]:
    """Write all CSV/JSON outputs and the data-quality declaration to ``outdir``."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def _csv(df: pd.DataFrame, name: str) -> None:
        p = out / name
        df.to_csv(p, index=False)
        written.append(p)

    _csv(cohort_summary_df(run), "ti_cohort_summary.csv")
    _csv(annual_df(run), "ti_annual_timeseries.csv")
    _csv(portfolio_df(run), "ti_portfolio_rolling.csv")
    _csv(decomposition_df(run), "ti_decomposition.csv")
    _csv(crossover_df(run), "ti_crossover.csv")

    pj = out / "ti_result.json"
    payload = to_json_dict(run)
    if sensitivity is not None:
        payload["sensitivity"] = sensitivity
    pj.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    written.append(pj)

    pq = out / "data_quality_declaration.txt"
    pq.write_text(data_quality_text(run))
    written.append(pq)

    return written
