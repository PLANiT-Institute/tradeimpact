# SPDX-License-Identifier: GPL-3.0-or-later
"""Thin service layer over the engine: fixture-shaped inputs in, result JSON out.

The single compute entry point for anything outside the engine (the Vercel calculator
function, scripts). All numbers originate in ti_framework — no arithmetic here.
"""

from __future__ import annotations

from ti_framework.core.scenarios import run
from ti_framework.io.fixtures import parse_fixture
from ti_framework.report.outputs import to_json_dict


def compute(payload: dict) -> dict:
    """Run the engine on a fixture-shaped payload and return the result JSON dict.

    ``payload`` uses the same schema as ``ti-framework/fixtures/*.json`` (firm,
    cohort_year, countries, support, placements, config). Raises ``KeyError`` /
    ``ValueError`` on malformed input — callers map that to a 400.
    """
    fx = parse_fixture(payload)
    result = run(
        fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config,
        analysis_level=fx.analysis_level, layer1_method=fx.layer1_method,
    )
    return to_json_dict(result)
