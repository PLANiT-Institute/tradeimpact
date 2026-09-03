# SPDX-License-Identifier: GPL-3.0-or-later
"""Annual TI gap per vehicle (Whitepaper §3.3 [eq-3.3-annual-gap], Guideline §4.1).

    TI_gap,v,c(t) = E_ref,c(t) - E_prod,v,c(t)   [kgCO2e/vehicle/yr]

Positive = climate contribution; negative = carbon lock-in liability.
"""

from __future__ import annotations

import numpy as np

from ti_framework.layer1.base import Benchmark
from ti_framework.layer2.base import ProductEmissions


def ti_gap_at(benchmark: Benchmark, product: ProductEmissions, t: int) -> float:
    """TI gap at a single year t [kgCO2e/vehicle/yr]."""
    return benchmark.e_ref(t) - product.emissions(t)


def ti_gap_series(benchmark: Benchmark, product: ProductEmissions, T: int) -> np.ndarray:
    """TI gap series for t = 0..T-1 [kgCO2e/vehicle/yr]."""
    if T < 1:
        raise ValueError(f"T must be >= 1, got {T}")
    return benchmark.e_ref_series(T) - product.series(T)
