# SPDX-License-Identifier: GPL-3.0-or-later
"""Plots (Guideline §7.2 / build brief §6): rolling-portfolio S1/S2/S3 band,
decomposition bars, single-cohort time-series. Uses a non-interactive backend.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ti_framework.models import RunResult, Scenario  # noqa: E402

_SCEN_ORDER = (Scenario.S1, Scenario.S2, Scenario.S3)


def plot_portfolio_band(run: RunResult, path: str | Path) -> Path:
    """Rolling-portfolio TI with the S1/S2/S3 band (headline chart)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    series = {sc: run.portfolio.get(sc, []) for sc in _SCEN_ORDER if sc in run.portfolio}
    for sc, s in series.items():
        ax.plot(range(len(s)), s, label=f"{sc.value} — {sc.label}", marker="o", markersize=3)
    if Scenario.S1 in series and Scenario.S3 in series:
        s1, s3 = series[Scenario.S1], series[Scenario.S3]
        n = min(len(s1), len(s3))
        lo = [min(s1[i], s3[i]) for i in range(n)]
        hi = [max(s1[i], s3[i]) for i in range(n)]
        ax.fill_between(range(n), lo, hi, alpha=0.12, label="S1–S3 band")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Year index (portfolio build-up)")
    ax.set_ylabel("TI_portfolio [tCO₂e/yr]")
    ax.set_title(f"{run.firm} — Rolling portfolio TI ({run.cohort_year} cohort basis)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    p = Path(path)
    fig.savefig(p, dpi=120)
    plt.close(fig)
    return p


def plot_decomposition(run: RunResult, path: str | Path, scenario: Scenario = Scenario.S2) -> Path:
    """Decomposition bars by operating country and by powertrain for one scenario."""
    cohort = run.cohorts.get(scenario)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    if cohort is not None:
        if cohort.by_country:
            ax1.bar(list(cohort.by_country.keys()), list(cohort.by_country.values()))
        ax1.axhline(0, color="black", linewidth=0.8)
        ax1.set_title(f"By operating country ({scenario.value})")
        ax1.set_ylabel("TI [tCO₂e]")
        if cohort.by_powertrain:
            ax2.bar(list(cohort.by_powertrain.keys()), list(cohort.by_powertrain.values()),
                    color="tab:orange")
        ax2.axhline(0, color="black", linewidth=0.8)
        ax2.set_title(f"By powertrain ({scenario.value})")
    fig.suptitle(f"{run.firm} — TI decomposition")
    fig.tight_layout()
    p = Path(path)
    fig.savefig(p, dpi=120)
    plt.close(fig)
    return p


def plot_single_cohort(run: RunResult, path: str | Path) -> Path:
    """Single-cohort annual TI time-series (t = 0..T-1), S1/S2/S3."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for sc in _SCEN_ORDER:
        c = run.cohorts.get(sc)
        if c is not None and c.annual:
            ax.plot(range(len(c.annual)), c.annual, label=f"{sc.value} — {sc.label}", marker="o",
                    markersize=3)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("t (years since sale)")
    ax.set_ylabel("TI_annual [tCO₂e/yr]")
    ax.set_title(f"{run.firm} — Single-cohort annual TI ({run.cohort_year})")
    ax.legend(fontsize=8)
    fig.tight_layout()
    p = Path(path)
    fig.savefig(p, dpi=120)
    plt.close(fig)
    return p


def write_plots(run: RunResult, outdir: str | Path) -> list[Path]:
    """Write the report charts.

    The rolling-portfolio band is drawn only when the run actually carries a portfolio series.
    With a single observed cohort that series is a counterfactual (the same cohort repeated),
    so the caller withholds it and the chart is skipped rather than drawn from an assumption.
    """
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    if any(run.portfolio.values()):
        paths.append(plot_portfolio_band(run, out / "portfolio_band.png"))
    paths.append(plot_decomposition(run, out / "decomposition.png"))
    paths.append(plot_single_cohort(run, out / "single_cohort.png"))
    return paths
