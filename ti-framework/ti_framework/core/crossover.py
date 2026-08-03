# SPDX-License-Identifier: GPL-3.0-or-later
"""Crossover point t* — the year TI_gap changes sign (NOTES.md §4 [rule-n4-crossover], Guideline §3.3).

Closed form where the gap is linear-in-exponentials:
  * ICE/HEV (constant E_prod vs exponential benchmark):
        t* = ln(E_prod / (I0 * D)) / ln(1 - r_fleet)
  * BEV (two exponentials):
        t* = ln((eta * G0) / I0) / ln((1 - r_fleet) / (1 - r_power))
Numeric bisection fallback for the general case (e.g. PHEV: constant + exponential mix).
"""

from __future__ import annotations

import math

import numpy as np

from ti_framework.layer1.base import Benchmark
from ti_framework.layer2.base import ProductEmissions


def crossover_ice(intensity_base: float, r_fleet: float, distance: float, e_prod: float) -> tuple[float | None, str | None]:
    """Closed-form t* for constant ICE emissions vs exponential benchmark."""
    e_ref0 = intensity_base * distance
    if r_fleet <= 0:
        return None, "r_fleet <= 0: benchmark non-declining, no crossover"
    if e_ref0 <= 0:
        return None, "non-positive base benchmark"
    ratio = e_prod / e_ref0
    if ratio <= 0:
        return None, "non-positive emissions ratio"
    t_star = math.log(ratio) / math.log(1.0 - r_fleet)
    if t_star < 0:
        return None, "crossover before sale year (product already above benchmark at t=0)"
    return t_star, None


def crossover_bev(
    intensity_base: float,
    r_fleet: float,
    eta_ev: float,
    g0: float,
    r_power: float,
) -> tuple[float | None, str | None]:
    """Closed-form t* for BEV (two exponential trajectories)."""
    a = 1.0 - r_fleet  # benchmark base
    b = 1.0 - r_power  # product (grid) base
    denom_num = a / b
    e_prod0 = eta_ev * g0  # intensity terms; distance cancels in the ratio
    if e_prod0 <= 0 or intensity_base <= 0:
        return None, "non-positive intensity"
    if denom_num <= 0:
        return None, "degenerate decline rate"
    if abs(a - b) < 1e-12:
        return None, "r_fleet == r_power: parallel trajectories, no finite crossover"
    # I0*a^t = E0*b^t  =>  (a/b)^t = E0/I0.
    t_star = math.log(e_prod0 / intensity_base) / math.log(a / b)
    if t_star < 0:
        return None, "crossover before sale year"
    return t_star, None


def crossover_numeric(gap_series: np.ndarray | list[float]) -> tuple[float | None, str | None]:
    """First sign change in a gap series, linearly interpolated between integer years."""
    arr = np.asarray(gap_series, dtype=float)
    if arr.size < 2:
        return None, "series too short for crossover"
    for t in range(arr.size - 1):
        g0, g1 = arr[t], arr[t + 1]
        if g0 == 0.0:
            return float(t), None
        if g0 * g1 < 0:  # sign change between t and t+1
            frac = g0 / (g0 - g1)
            return float(t) + float(frac), None
    if arr[-1] == 0.0:
        return float(arr.size - 1), None
    return None, "no sign change over lifetime"


def crossover(benchmark: Benchmark, product: ProductEmissions, T: int) -> tuple[float | None, str | None]:
    """Generic numeric crossover over an arbitrary benchmark/product pair."""
    from ti_framework.core.gap import ti_gap_series

    return crossover_numeric(ti_gap_series(benchmark, product, T))
