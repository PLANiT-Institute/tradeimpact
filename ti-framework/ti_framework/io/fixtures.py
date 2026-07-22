# SPDX-License-Identifier: GPL-3.0-or-later
"""Load a fully-specified run from a JSON fixture.

Unlike the workbook template (mostly empty), a fixture carries every input needed to run the
engine end-to-end. Used for the validation reference cases and the CLI quickstart. Grid
intensity and ICE intensity in fixtures are already in engine units (kgCO2e/kWh, kgCO2e/km).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ti_framework.core.aggregate import Placement
from ti_framework.models import (
    ALL_SCENARIOS,
    BenchmarkStatus,
    Country,
    DataTier,
    EngineConfig,
    Powertrain,
    Scenario,
    ScenarioRate,
    SupportParams,
    Vehicle,
)


@dataclass
class FixtureRun:
    firm: str
    cohort_year: int
    countries: dict[str, Country]
    support: SupportParams
    placements: list[Placement]
    config: EngineConfig
    analysis_level: str = "Level 1"
    layer1_method: str = "B"
    expected: dict | None = None


def _rate(d: dict | None) -> ScenarioRate:
    d = d or {}
    return ScenarioRate(
        s1=d.get("s1"), s2=d.get("s2"), s3=d.get("s3"), s2_upper=d.get("s2_upper")
    )


def _tier(s: str | None) -> DataTier:
    return DataTier(s) if s in ("A", "B", "C") else DataTier.UNKNOWN


def load_fixture(path: str | Path) -> FixtureRun:
    raw = json.loads(Path(path).read_text())

    countries: dict[str, Country] = {}
    for code, c in raw.get("countries", {}).items():
        countries[code] = Country(
            name=c.get("name", code),
            code=code,
            grid_intensity=c.get("grid_intensity"),
            fleet_intensity_base=c.get("fleet_intensity_base"),
            base_year=c.get("base_year"),
            target_year=c.get("target_year"),
            reduction_low=c.get("reduction_low"),
            reduction_high=c.get("reduction_high"),
            econ_rate_low=c.get("econ_rate_low"),
            econ_rate_high=c.get("econ_rate_high"),
            r_fleet=_rate(c.get("r_fleet")),
            r_power=_rate(c.get("r_power")),
            status=BenchmarkStatus(c.get("status", "COMPUTED")),
            tier=_tier(c.get("tier")),
            source=c.get("source"),
            warnings=list(c.get("warnings", [])),
        )

    s = raw.get("support", {})
    rw = s.get("realworld_range")
    support = SupportParams(
        lifetime_T=s.get("lifetime_T"),
        lifetime_sens=s.get("lifetime_sens", 3),
        vkt=dict(s.get("vkt", {})),
        uf_band=s.get("uf_band", 0.15),
        realworld_range=tuple(rw) if rw else None,
    )

    placements: list[Placement] = []
    for p in raw.get("placements", []):
        veh = Vehicle(
            brand=p.get("brand", ""),
            model=p.get("model"),
            powertrain=Powertrain(p["powertrain"]),
            segment=p.get("segment"),
            eta_ev=p.get("eta_ev"),
            ice_intensity=p.get("ice_intensity"),
            uf=p.get("uf"),
            eta_elec=p.get("eta_elec"),
            ice_mode_intensity=p.get("ice_mode_intensity"),
            realworld_correction=p.get("realworld_correction"),
            tier=_tier(p.get("tier")),
            source=p.get("source"),
        )
        placements.append(
            Placement(country_code=p["country"], vehicle=veh, units=p.get("units"))
        )

    cfg = raw.get("config", {})
    scenarios = tuple(Scenario(x) for x in cfg["scenarios"]) if "scenarios" in cfg else ALL_SCENARIOS
    config = EngineConfig(
        scenarios=scenarios,
        flag_market_rule=cfg.get("flag_market_rule", "exclude"),
        sector_split_fleet=cfg.get("sector_split_fleet", 1.0),
        sector_split_power=cfg.get("sector_split_power", 1.0),
        sector_split_enabled=cfg.get("sector_split_enabled", False),
        s_curve=cfg.get("s_curve", False),
        monte_carlo=cfg.get("monte_carlo", False),
        mc_draws=cfg.get("mc_draws", 2000),
        tier_c_threshold=cfg.get("tier_c_threshold", 0.5),
    )

    return FixtureRun(
        firm=raw.get("firm", "Firm"),
        cohort_year=raw.get("cohort_year", 2024),
        countries=countries,
        support=support,
        placements=placements,
        config=config,
        analysis_level=raw.get("analysis_level", "Level 1"),
        layer1_method=raw.get("layer1_method", "B"),
        expected=raw.get("expected"),
    )
