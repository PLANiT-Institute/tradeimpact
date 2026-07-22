# SPDX-License-Identifier: GPL-3.0-or-later
# Trade Impact (TI) Framework — calculation engine
# Copyright (C) 2026 PLANiT Institute
#
# This program is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version. See the LICENSE file for details.
"""Trade Impact (TI) Framework — open-source calculation engine (automotive sector).

Public API:
    from ti_framework import run, EngineConfig, Scenario, Placement
"""

from __future__ import annotations

from ti_framework.core.aggregate import Placement, decomposition_identity_holds
from ti_framework.core.scenarios import placements_from_volumes, run
from ti_framework.core.sensitivity import run_sensitivity
from ti_framework.models import (
    ALL_SCENARIOS,
    BenchmarkStatus,
    CohortResult,
    Country,
    DataTier,
    EngineConfig,
    Powertrain,
    RunResult,
    Scenario,
    SupportParams,
    Vehicle,
    Volume,
)

__version__ = "0.1.0"

__all__ = [
    "run",
    "run_sensitivity",
    "placements_from_volumes",
    "decomposition_identity_holds",
    "Placement",
    "EngineConfig",
    "Scenario",
    "ALL_SCENARIOS",
    "Powertrain",
    "DataTier",
    "BenchmarkStatus",
    "Country",
    "Vehicle",
    "Volume",
    "SupportParams",
    "CohortResult",
    "RunResult",
]
