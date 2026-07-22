# SPDX-License-Identifier: GPL-3.0-or-later
"""Level 2 — production-country attribution (STUB; Whitepaper §2.3, Challenge 2).

Level 1 (operating-country basis) is fully implemented. Level 2 traces use-phase impact back
to the production plant via the V_p,c,v matrix and allocates multi-factory models by IR
volume ratios. This module fixes the interface; the allocation logic is Todo (CA4).
"""

from __future__ import annotations

from dataclasses import dataclass

from ti_framework.models import Powertrain


@dataclass
class ProductionPlacement:
    """V_p,c,v — vehicles produced in country p of type v operating in country c (STUB)."""

    production_country: str
    operating_country: str
    powertrain: Powertrain
    units: float | None
    mapping: str = "estimated"  # "exact" | "estimated" (volume-ratio allocated)


def attribute_to_production(*args: object, **kwargs: object) -> None:  # pragma: no cover - stub
    """Attribute operating-country TI back to production countries (NOT IMPLEMENTED)."""
    raise NotImplementedError(
        "Level 2 production attribution is not implemented — see Methodological Challenges "
        "Challenge 2 / Todo CA4. Level 1 (operating-country basis) is the supported analysis."
    )
