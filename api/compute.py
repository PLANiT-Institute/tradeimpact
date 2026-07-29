# SPDX-License-Identifier: GPL-3.0-or-later
"""Thin service layer over the engine: fixture-shaped inputs in, result JSON out.

The single compute entry point for anything outside the engine (the Vercel calculator
function, scripts). All numbers originate in ti_framework — no arithmetic here.
"""

from __future__ import annotations

import math

from ti_framework.core.scenarios import run
from ti_framework.io.fixtures import parse_fixture
from ti_framework.report.outputs import to_json_dict

MAX_REQUEST_BYTES = 1_000_000
MAX_COUNTRIES = 50
MAX_PLACEMENTS = 500
MAX_LIFETIME_YEARS = 50


def _finite_number(
    value: object,
    field: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    integer: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    if integer and not number.is_integer():
        raise ValueError(f"{field} must be an integer")
    if minimum is not None and number < minimum:
        raise ValueError(f"{field} must be at least {minimum:g}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{field} must be at most {maximum:g}")
    return number


def _validate_optional_numbers(
    values: dict,
    fields: tuple[str, ...],
    path: str,
    *,
    minimum: float,
    maximum: float,
) -> None:
    for field in fields:
        value = values.get(field)
        if value is not None:
            _finite_number(value, f"{path}.{field}", minimum=minimum, maximum=maximum)


def validate_payload(payload: object) -> dict:
    """Reject malformed or computationally unbounded public calculator inputs."""
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")

    firm = payload.get("firm", "Firm")
    if not isinstance(firm, str) or not firm.strip() or len(firm) > 200:
        raise ValueError("firm must be a non-empty string of at most 200 characters")
    _finite_number(
        payload.get("cohort_year", 2024),
        "cohort_year",
        minimum=1900,
        maximum=2200,
        integer=True,
    )

    countries = payload.get("countries")
    if not isinstance(countries, dict) or not 1 <= len(countries) <= MAX_COUNTRIES:
        raise ValueError(f"countries must contain between 1 and {MAX_COUNTRIES} entries")
    for code, country in countries.items():
        if not isinstance(code, str) or not code or len(code) > 12:
            raise ValueError("country codes must be non-empty strings of at most 12 characters")
        if not isinstance(country, dict):
            raise ValueError(f"countries.{code} must be an object")
        _validate_optional_numbers(
            country,
            ("grid_intensity", "fleet_intensity_base"),
            f"countries.{code}",
            minimum=0,
            maximum=10,
        )
        for rate_group in ("r_fleet", "r_power"):
            rates = country.get(rate_group, {})
            if not isinstance(rates, dict):
                raise ValueError(f"countries.{code}.{rate_group} must be an object")
            _validate_optional_numbers(
                rates,
                ("s1", "s2", "s3", "s2_upper"),
                f"countries.{code}.{rate_group}",
                minimum=0,
                maximum=1,
            )

    support = payload.get("support")
    if not isinstance(support, dict):
        raise ValueError("support must be an object")
    _finite_number(
        support.get("lifetime_T"),
        "support.lifetime_T",
        minimum=1,
        maximum=MAX_LIFETIME_YEARS,
        integer=True,
    )
    vkt = support.get("vkt")
    if not isinstance(vkt, dict) or len(vkt) > MAX_COUNTRIES:
        raise ValueError(f"support.vkt must be an object with at most {MAX_COUNTRIES} entries")
    for code, distance in vkt.items():
        _finite_number(distance, f"support.vkt.{code}", minimum=1, maximum=100_000)

    placements = payload.get("placements")
    if not isinstance(placements, list) or not 1 <= len(placements) <= MAX_PLACEMENTS:
        raise ValueError(f"placements must contain between 1 and {MAX_PLACEMENTS} entries")
    for index, placement in enumerate(placements):
        path = f"placements[{index}]"
        if not isinstance(placement, dict):
            raise ValueError(f"{path} must be an object")
        code = placement.get("country")
        if code not in countries:
            raise ValueError(f"{path}.country must reference an included country")
        powertrain = placement.get("powertrain")
        if powertrain not in {"ICE", "HEV", "BEV", "PHEV"}:
            raise ValueError(f"{path}.powertrain is invalid")
        if placement.get("units") is not None:
            _finite_number(
                placement["units"], f"{path}.units", minimum=0, maximum=100_000_000
            )
        _validate_optional_numbers(
            placement,
            (
                "eta_ev",
                "ice_intensity",
                "eta_elec",
                "ice_mode_intensity",
                "realworld_correction",
            ),
            path,
            minimum=0,
            maximum=10,
        )
        if placement.get("uf") is not None:
            _finite_number(placement["uf"], f"{path}.uf", minimum=0, maximum=1)

    config = payload.get("config", {})
    if not isinstance(config, dict):
        raise ValueError("config must be an object")
    scenarios = config.get("scenarios")
    if scenarios is not None and (
        not isinstance(scenarios, list)
        or not 1 <= len(scenarios) <= 3
        or any(scenario not in {"S1", "S2", "S3"} for scenario in scenarios)
        or len(set(scenarios)) != len(scenarios)
    ):
        raise ValueError("config.scenarios must contain one to three valid scenarios")
    if config.get("flag_market_rule", "exclude") not in {"exclude", "iea_proxy"}:
        raise ValueError("config.flag_market_rule must be exclude or iea_proxy")
    for field in ("sector_split_fleet", "sector_split_power"):
        if config.get(field) is not None:
            _finite_number(config[field], f"config.{field}", minimum=0, maximum=10)
    for field in ("sector_split_enabled", "s_curve", "monte_carlo"):
        if config.get(field) is not None and not isinstance(config[field], bool):
            raise ValueError(f"config.{field} must be a boolean")
    if config.get("tier_c_threshold") is not None:
        _finite_number(
            config["tier_c_threshold"],
            "config.tier_c_threshold",
            minimum=0,
            maximum=1,
        )
    return payload


def compute(payload: dict) -> dict:
    """Run the engine on a fixture-shaped payload and return the result JSON dict.

    ``payload`` uses the same schema as ``ti-framework/fixtures/*.json`` (firm,
    cohort_year, countries, support, placements, config). Raises ``KeyError`` /
    ``ValueError`` on malformed input — callers map that to a 400.
    """
    fx = parse_fixture(validate_payload(payload))
    result = run(
        fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config,
        analysis_level=fx.analysis_level, layer1_method=fx.layer1_method,
    )
    return to_json_dict(result)
