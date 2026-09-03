# SPDX-License-Identifier: GPL-3.0-or-later
"""Layer 1 benchmark interface.

A ``Benchmark`` yields the operating-country fleet-average emission *intensity*
(kgCO2e/km) at year ``t`` and the per-vehicle-year benchmark emissions
``E_ref,c(t) = intensity(t) * D_c``. This is the sector-agnostic contract Layer 3
computes against; automotive/shipping/power supply concrete implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class Benchmark(ABC):
    """Operating-country fleet benchmark trajectory (Whitepaper §3.1, Guideline §2)."""

    #: annual distance D_c [km/yr], used to convert intensity -> per-vehicle-year emissions
    distance: float

    @abstractmethod
    def intensity(self, t: int) -> float:
        """Fleet-average segment emission intensity at year t [kgCO2e/km]."""

    def e_ref(self, t: int) -> float:
        """Per-vehicle-year benchmark emissions E_ref,c(t) [kgCO2e/vehicle/yr]."""
        return self.intensity(t) * self.distance

    def e_ref_series(self, T: int) -> np.ndarray:
        """Vectorised E_ref,c(t) for t = 0..T-1."""
        return np.array([self.e_ref(t) for t in range(T)], dtype=float)
