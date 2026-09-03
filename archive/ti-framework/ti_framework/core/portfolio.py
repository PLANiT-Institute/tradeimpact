# SPDX-License-Identifier: GPL-3.0-or-later
"""Annual TI flow and rolling portfolio TI (Whitepaper §3.8 [eq-3.8-portfolio], Guideline §4.5, §4.6).

    TI_annual,F,Y0,tau,S  = sum_v sum_c [ V_c,v * TI_gap,v,c(tau - Y0) ]   [tCO2e/yr]
    TI_portfolio,F,tau,S  = sum_{Y0 = tau-T+1}^{tau} TI_annual,F,Y0,tau,S   [tCO2e/yr]

The single-cohort annual series produced by ``aggregate.compute_cohort`` is exactly
TI_annual indexed by t = tau - Y0. The rolling portfolio sums the active cohorts.
"""

from __future__ import annotations


def ti_annual_at(cohort_annual: list[float], t: int) -> float:
    """TI_annual for one cohort at age t (years since sale); 0 outside [0, T-1]."""
    if 0 <= t < len(cohort_annual):
        return cohort_annual[t]
    return 0.0


def rolling_portfolio(
    cohort_annual_by_year: dict[int, list[float]],
    tau_range: range,
) -> dict[int, float]:
    """Rolling portfolio TI per calendar year tau over a set of cohorts.

    Parameters
    ----------
    cohort_annual_by_year : {Y0 -> annual TI series (t=0..T-1)} for each sales cohort.
    tau_range : calendar years tau to evaluate.
    """
    out: dict[int, float] = {}
    for tau in tau_range:
        total = 0.0
        for y0, annual in cohort_annual_by_year.items():
            total += ti_annual_at(annual, tau - y0)
        out[tau] = total
    return out


def steady_state_portfolio(cohort_annual: list[float]) -> float:
    """Rolling portfolio TI under the steady-state assumption (identical cohort each year).

    When every cohort has the same annual profile, the rolling portfolio equals the sum of
    the single-cohort annual series, which equals TI_cohort. Useful as a single-number proxy
    when only one cohort's data is available.
    """
    return float(sum(cohort_annual))
