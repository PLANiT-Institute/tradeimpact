# SPDX-License-Identifier: GPL-3.0-or-later
"""Layer 2 sold-product emissions interface.

A ``ProductEmissions`` yields the per-vehicle-year use-phase emissions
``E_prod,v,c(t)`` [kgCO2e/vehicle/year] of one sold product type. This is the
sector-agnostic contract Layer 3 subtracts from the Layer-1 benchmark.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class ProductEmissions(ABC):
    """Sold-product use-phase emissions (Whitepaper §3.2, Guideline §3)."""

    @abstractmethod
    def emissions(self, t: int) -> float:
        """Use-phase emissions at year t [kgCO2e/vehicle/yr]."""

    def series(self, T: int) -> np.ndarray:
        """Vectorised E_prod,v,c(t) for t = 0..T-1."""
        return np.array([self.emissions(t) for t in range(T)], dtype=float)
