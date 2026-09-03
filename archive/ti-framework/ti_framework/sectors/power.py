# SPDX-License-Identifier: GPL-3.0-or-later
"""Power-generation sector — STUB (Methodological Challenges, Challenge 6; Todo M3).

Not implemented. Layer 1 is the operating-country grid emission-intensity trajectory; Layer 2
is per-generation-technology emissions, with mandatory technology-level decomposition to avoid
the company-average masking effect (Appendix E). Interface fixed so it slots into Layer 3.
"""

from __future__ import annotations

from ti_framework.layer1.base import Benchmark
from ti_framework.layer2.base import ProductEmissions


class GridIntensityBenchmark(Benchmark):
    """Layer 1 for power: operating-country grid intensity trajectory (STUB)."""

    def __init__(self, distance: float = 1.0) -> None:
        # 'distance' is the per-unit service basis (e.g. MWh) for the power sector.
        self.distance = distance

    def intensity(self, t: int) -> float:  # pragma: no cover - stub
        raise NotImplementedError(
            "Power Layer 1 (grid intensity trajectory) is not implemented — see Todo M3."
        )


class GenerationEmissions(ProductEmissions):
    """Layer 2 for power: per-technology generation emissions (STUB)."""

    def emissions(self, t: int) -> float:  # pragma: no cover - stub
        raise NotImplementedError(
            "Power Layer 2 (per-technology emissions) is not implemented — see Todo M3."
        )
