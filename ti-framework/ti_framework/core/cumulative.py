# SPDX-License-Identifier: GPL-3.0-or-later
"""Per-vehicle cumulative TI (Guideline §4.3).

    TI_vehicle,v,c,S = sum_{t=0}^{T-1} TI_gap,v,c(t)   [kgCO2e/vehicle over lifetime]
"""

from __future__ import annotations

import numpy as np


def ti_cumulative(gap_series: np.ndarray | list[float]) -> float:
    """Sum the annual TI gap over the vehicle lifetime [kgCO2e/vehicle]."""
    arr = np.asarray(gap_series, dtype=float)
    return float(np.sum(arr))
