# SPDX-License-Identifier: GPL-3.0-or-later
"""Shipping sector — STUB (Methodological Challenges, Challenge 5; Todo M2).

Not implemented. The Layer-1 benchmark for shipping substitutes the IMO GHG Strategy
Carbon Intensity Indicator (CII) trajectory for the national NDC, and the operating-country
boundary becomes flag-state vs voyage-weighted. These classes fix the *interface* so the
implementation slots into the unchanged Layer-3 core later.
"""

from __future__ import annotations

from ti_framework.layer1.base import Benchmark
from ti_framework.layer2.base import ProductEmissions


class IMOCIIBenchmark(Benchmark):
    """Layer 1 for shipping: IMO CII trajectory (STUB)."""

    def __init__(self, distance: float = 0.0) -> None:
        self.distance = distance

    def intensity(self, t: int) -> float:  # pragma: no cover - stub
        raise NotImplementedError(
            "Shipping Layer 1 (IMO CII trajectory) is not implemented — see Todo M2."
        )


class VesselEmissions(ProductEmissions):
    """Layer 2 for shipping: vessel emissions by type × fuel (STUB)."""

    def emissions(self, t: int) -> float:  # pragma: no cover - stub
        raise NotImplementedError(
            "Shipping Layer 2 (vessel type × fuel, WtW/TtW) is not implemented — see Todo M2."
        )
