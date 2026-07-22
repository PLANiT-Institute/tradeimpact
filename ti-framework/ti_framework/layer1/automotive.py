# SPDX-License-Identifier: GPL-3.0-or-later
"""Automotive Layer 1 — fleet benchmark intensity (Guideline §2.3).

Three methods:
    Method B  — Transport NDC trajectory (exponential decline). DEFAULT.
    Method A  — Fleet stock model (Weibull survival over vintages).
    Method C  — Volume-weighted two-bin approximation (cross-validation / no-NDC fallback).

All return I_fleet,seg,c(t) [kgCO2e/km]; E_ref,c(t) = intensity(t) * D_c is provided by the
base class. Method B optionally uses an S-curve (logistic) shape instead of the exponential
(NOTES.md §3, Challenge B).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from ti_framework.layer1.base import Benchmark


@dataclass
class MethodBBenchmark(Benchmark):
    """Method B — NDC trajectory: I(t) = I0 * (1 - r_fleet)^t.

    Parameters
    ----------
    intensity_base : I_fleet,seg,c(0) [kgCO2e/km]
    r_fleet : annual fleet reduction rate (fraction/yr)
    distance : D_c [km/yr]
    s_curve : if True, use a logistic shape passing through I0 at t=0 and the exponential
        endpoint at t=horizon (documented alternative for fast-transition markets).
    horizon : the year at which the S-curve endpoint matches the exponential (default 15).
    s_curve_k : logistic steepness.
    """

    intensity_base: float
    r_fleet: float
    distance: float
    s_curve: bool = False
    horizon: int = 15
    s_curve_k: float = 0.4

    def intensity(self, t: int) -> float:
        if not self.s_curve:
            return self.intensity_base * (1.0 - self.r_fleet) ** t
        # Logistic between I0 (t=0) and the exponential endpoint at the horizon.
        endpoint = self.intensity_base * (1.0 - self.r_fleet) ** self.horizon
        t_mid = self.horizon / 2.0
        # normalised logistic in [0,1], 0 at -inf, 1 at +inf
        def logit(x: float) -> float:
            return 1.0 / (1.0 + math.exp(-self.s_curve_k * (x - t_mid)))

        l0, lh = logit(0.0), logit(self.horizon)
        frac = (logit(t) - l0) / (lh - l0) if lh != l0 else 0.0
        return self.intensity_base + (endpoint - self.intensity_base) * frac


@dataclass
class MethodABenchmark(Benchmark):
    """Method A — fleet stock model with Weibull survival (Guideline §2.3 Method A).

    I_fleet(t) = sum_y [ S(y,t) * I_new(y) ] / sum_y S(y,t),
    S(y,t) = N_new(y) * SR(t - y),  SR(age) = exp(-(age/alpha)^beta).

    ``vintages`` are calendar years (ascending); ``n_new`` and ``i_new`` align with them.
    ``base_year`` is the cohort sale year Y0 (t=0). New-entrant intensity for vintages beyond
    the supplied data is held flat at the last known value (documented extrapolation).
    """

    vintages: Sequence[int]
    n_new: Sequence[float]
    i_new: Sequence[float]  # kgCO2e/km
    alpha: float
    beta: float
    distance: float
    base_year: int

    @staticmethod
    def survival(age: float, alpha: float, beta: float) -> float:
        if age < 0:
            return 0.0
        return math.exp(-((age / alpha) ** beta))

    def _i_new_for(self, year: int) -> float:
        vmin, vmax = self.vintages[0], self.vintages[-1]
        if year <= vmin:
            return self.i_new[0]
        if year >= vmax:
            return self.i_new[-1]
        # linear interpolation between bracketing vintages
        for k in range(len(self.vintages) - 1):
            if self.vintages[k] <= year <= self.vintages[k + 1]:
                y0, y1 = self.vintages[k], self.vintages[k + 1]
                f = (year - y0) / (y1 - y0)
                return self.i_new[k] + f * (self.i_new[k + 1] - self.i_new[k])
        return self.i_new[-1]

    def _n_new_for(self, year: int) -> float:
        if year < self.vintages[0]:
            return 0.0
        if year >= self.vintages[-1]:
            return self.n_new[-1]
        for k in range(len(self.vintages) - 1):
            if self.vintages[k] <= year < self.vintages[k + 1]:
                return self.n_new[k]
        return self.n_new[-1]

    def intensity(self, t: int) -> float:
        cal = self.base_year + t
        num = 0.0
        den = 0.0
        # include all vintages up to and including the analysis calendar year
        years = list(range(self.vintages[0], cal + 1))
        for y in years:
            s = self._n_new_for(y) * self.survival(cal - y, self.alpha, self.beta)
            num += s * self._i_new_for(y)
            den += s
        return num / den if den > 0 else self._i_new_for(cal)


@dataclass
class MethodCBenchmark(Benchmark):
    """Method C — volume-weighted two-bin approximation (Guideline §2.3 Method C).

    I(t) = RR * I_new(t) + (1 - RR) * I(t-1) * (1 + delta_scrap), with I(0) = intensity_base.
    ``i_new`` is the new-entrant intensity trajectory (callable of t or a sequence).
    """

    intensity_base: float
    i_new: Sequence[float]  # new-entrant intensity by t [kgCO2e/km]
    renewal_rate: float  # RR_c
    distance: float
    scrappage: float = 0.0  # delta_scrap,c

    def _i_new_at(self, t: int) -> float:
        if t < len(self.i_new):
            return self.i_new[t]
        return self.i_new[-1]

    def intensity(self, t: int) -> float:
        val = self.intensity_base
        for k in range(1, t + 1):
            val = self.renewal_rate * self._i_new_at(k) + (1.0 - self.renewal_rate) * val * (
                1.0 + self.scrappage
            )
        return val


def bc_divergence(b: Benchmark, c: Benchmark, T: int) -> dict[str, object]:
    """Method B vs Method C divergence check (Guideline §2.3, §6.1).

    Returns max relative divergence over t=0..T-1 and a flag if it exceeds 30% at any year.
    """
    ib = np.array([b.intensity(t) for t in range(T)], dtype=float)
    ic = np.array([c.intensity(t) for t in range(T)], dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.abs(ib - ic) / np.where(ib != 0, np.abs(ib), np.nan)
    rel = np.nan_to_num(rel, nan=0.0)
    max_div = float(np.max(rel)) if rel.size else 0.0
    return {
        "max_divergence": max_div,
        "per_year": rel.tolist(),
        "exceeds_30pct": bool(max_div > 0.30),
        "flag_year": int(np.argmax(rel)) if rel.size else None,
    }
