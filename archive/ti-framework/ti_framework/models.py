# SPDX-License-Identifier: GPL-3.0-or-later
# Trade Impact (TI) Framework — calculation engine
# Copyright (C) 2026 PLANiT Institute
"""Typed data models for the TI Framework engine.

These dataclasses are the validated internal representation the rest of the engine
computes on. They are deliberately tolerant of missing data: every input that the
workbook may leave as "TO COLLECT" / "FLAG" is ``Optional`` and defaults to ``None``,
never to a fabricated value (see NOTES.md §5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Scenario(StrEnum):
    """The three mandatory scenarios (Guideline §4.7). Never report S2 alone."""

    # The labels name the *ambition level*, not a particular publisher's scenario. Which
    # pathway fills each level is a per-run sourcing decision, recorded in
    # DataQuality.scenario_sources — hard-coding "STEPS" or "NZE" here would mislabel a run
    # that sourced its rates from national inventories or an EU pathway instead.
    S1 = "S1"  # Low — the trajectory currently being realised
    S2 = "S2"  # Central — the trajectory that has been committed to
    S3 = "S3"  # High — a 1.5C-aligned trajectory

    @property
    def label(self) -> str:
        return {
            "S1": "Low (current trajectory)",
            "S2": "Central (committed policy)",
            "S3": "High (1.5°C aligned)",
        }[self.value]


ALL_SCENARIOS: tuple[Scenario, ...] = (Scenario.S1, Scenario.S2, Scenario.S3)


class Powertrain(StrEnum):
    ICE = "ICE"
    HEV = "HEV"  # non-plug-in hybrid — treated identically to ICE (fixed sale-year emissions)
    BEV = "BEV"
    PHEV = "PHEV"

    @property
    def is_fixed(self) -> bool:
        """True for powertrains with emissions fixed at sale-year efficiency."""
        return self in (Powertrain.ICE, Powertrain.HEV)


class DataTier(StrEnum):
    """Three-tier data quality hierarchy (Whitepaper §5.1)."""

    A = "A"  # primary/official or firm-verified
    B = "B"  # estimated
    C = "C"  # proxy-based fallback
    UNKNOWN = "?"

    @property
    def rank(self) -> int:
        return {"A": 0, "B": 1, "C": 2, "?": 3}[self.value]


class BenchmarkStatus(StrEnum):
    """Whether a country's Layer-1 S2 benchmark is derivable from its NDC."""

    COMPUTED = "COMPUTED"  # clean base->target arithmetic available
    FLAG_NO_BENCHMARK = "FLAG_NO_BENCHMARK"  # e.g. US — no active NDC
    FLAG_INTENSITY = "FLAG_INTENSITY"  # e.g. IN — GDP-intensity target, not absolute
    FLAG_BAU = "FLAG_BAU"  # e.g. ID — target vs BAU projection
    FLAG_NO_BASELINE = "FLAG_NO_BASELINE"  # e.g. SA — absolute avoided, no baseline
    FLAG_PEAK = "FLAG_PEAK"  # e.g. CN — vs undefined peak

    @property
    def is_flag(self) -> bool:
        return self is not BenchmarkStatus.COMPUTED


@dataclass
class ScenarioRate:
    """A reduction rate triple (fractions/yr) for one country, one quantity (fleet or power)."""

    s1: float | None = None
    s2: float | None = None
    s3: float | None = None
    # S2 upper-bound from the conditional NDC target (D2): used as a sensitivity bound only.
    s2_upper: float | None = None

    def get(self, scenario: Scenario) -> float | None:
        return {Scenario.S1: self.s1, Scenario.S2: self.s2, Scenario.S3: self.s3}[scenario]


@dataclass
class Country:
    """Operating-country Layer-1 parameters and benchmark provenance."""

    name: str
    code: str
    grid_intensity: float | None = None  # G_c(0), kgCO2e/kWh (converted on load)
    ndc_headline: str | None = None
    base_year: int | None = None
    target_year: int | None = None
    reduction_low: float | None = None  # fraction, unconditional
    reduction_high: float | None = None  # fraction, conditional
    econ_rate_low: float | None = None  # %/yr -> stored as fraction
    econ_rate_high: float | None = None
    r_fleet: ScenarioRate = field(default_factory=ScenarioRate)
    r_power: ScenarioRate = field(default_factory=ScenarioRate)
    status: BenchmarkStatus = BenchmarkStatus.COMPUTED
    tier: DataTier = DataTier.UNKNOWN
    source: str | None = None
    # base-year fleet-average segment intensity I_fleet,seg,c(0) [kgCO2e/km]
    fleet_intensity_base: float | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_flag(self) -> bool:
        return self.status.is_flag


@dataclass
class Vehicle:
    """A sold-vehicle model's Layer-2 emission parameters (real-world corrected)."""

    brand: str
    model: str | None
    powertrain: Powertrain
    segment: str | None = None
    eta_ev: float | None = None  # kWh/km (BEV)
    ice_intensity: float | None = None  # kgCO2e/km (ICE/HEV), real-world corrected
    uf: float | None = None  # PHEV utility factor, 0..1
    eta_elec: float | None = None  # kWh/km (PHEV EV-mode)
    ice_mode_intensity: float | None = None  # kgCO2e/km (PHEV charge-sustaining)
    realworld_correction: float | None = None  # multiplicative factor already applied if loaded corrected
    tier: DataTier = DataTier.UNKNOWN
    source: str | None = None


@dataclass
class Volume:
    """Registrations V_c,v — vehicles of a powertrain in an operating country in cohort Y0."""

    country_code: str
    year: int
    brand: str | None
    model: str | None
    powertrain: Powertrain
    units: float | None
    segment: str | None = None
    source: str | None = None
    tier: DataTier = DataTier.UNKNOWN


@dataclass
class SupportParams:
    """Sector-wide support parameters and sensitivity bands (Support_params sheet).

    Method A (Weibull) and Method C (renewal/scrappage) inputs are passed directly to
    their benchmark classes (layer1/automotive.py) — no loader collects them yet, so
    they deliberately have no fields here until a data path exists.
    """

    lifetime_T: int | None = None  # central T
    lifetime_sens: int = 3  # +/- years
    vkt: dict[str, float] = field(default_factory=dict)  # D_c per country code [km/yr]
    # Per-destination operating lifetime. A fleet that is scrapped at 12 years and one scrapped
    # at 25 do not share a horizon, so a country value overrides the central T where sourced.
    lifetime_by_country: dict[str, int] = field(default_factory=dict)
    uf_band: float = 0.15  # +/- UF sensitivity
    realworld_range: tuple[float, float] | None = None

    def vkt_for(self, code: str) -> float | None:
        return self.vkt.get(code)

    def lifetime_for(self, code: str) -> int | None:
        return self.lifetime_by_country.get(code, self.lifetime_T)

    def with_lifetime(self, central: int) -> SupportParams:
        """Move the central lifetime, carrying every per-country value by the same shift.

        Sensitivity sweeps vary one horizon; without the shift they would silently discard the
        per-country lifetimes and sweep only the countries that never had one.
        """
        from dataclasses import replace

        delta = 0 if self.lifetime_T is None else central - self.lifetime_T
        return replace(
            self,
            lifetime_T=central,
            lifetime_by_country={
                code: max(1, years + delta) for code, years in self.lifetime_by_country.items()
            },
        )


@dataclass
class EngineConfig:
    """Run-level configuration and the optional methodological switches (NOTES.md §3)."""

    scenarios: tuple[Scenario, ...] = ALL_SCENARIOS
    flag_market_rule: str = "exclude"  # "exclude" | "iea_proxy"
    # sector-split correction factors (default 1.0 = off). Applied to economy-wide rate.
    sector_split_fleet: float = 1.0
    sector_split_power: float = 1.0
    sector_split_enabled: bool = False
    s_curve: bool = False
    s_curve_k: float = 0.4  # logistic steepness if s_curve enabled
    monte_carlo: bool = False
    mc_draws: int = 2000
    mc_seed: int = 12345
    tier_c_threshold: float = 0.5  # Tier-C volume share above which only directional label emitted


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class VehicleResult:
    """Per-vehicle cumulative TI and annual gap series for one (country, vehicle, scenario)."""

    country_code: str
    powertrain: Powertrain
    scenario: Scenario
    gap_series: list[float]  # kgCO2e/vehicle/yr, t=0..T-1
    cumulative: float  # kgCO2e/vehicle over lifetime
    crossover_year: float | None  # t* (years since sale) or None
    crossover_reason: str | None = None


@dataclass
class CellTotal:
    """One (destination, powertrain) cell of the decomposition, with the volume behind it.

    ``by_country`` and ``by_powertrain`` are the two margins the Guideline requires. The
    margins alone cannot say whether a market looks bad because of where it is or because
    of what was sold into it — that needs the joint, and the per-vehicle figure needs the
    units, so both travel together.
    """

    country_code: str
    powertrain: Powertrain
    ti_tco2e: float
    units: float

    @property
    def ti_per_vehicle_kg(self) -> float | None:
        """Cumulative lifetime TI per vehicle in this cell, kgCO2e. None when unpopulated."""
        return self.ti_tco2e * 1000.0 / self.units if self.units else None


@dataclass
class CohortResult:
    """Single-cohort firm-level TI for one scenario, with mandatory decomposition."""

    firm: str
    cohort_year: int
    scenario: Scenario
    total: float  # tCO2e
    by_country: dict[str, float]  # tCO2e
    by_powertrain: dict[str, float]  # tCO2e
    annual: list[float]  # TI_annual time-series, tCO2e/yr, t=0..T-1
    by_cell: list[CellTotal] = field(default_factory=list)  # joint of the two margins
    excluded_flag_markets: dict[str, str] = field(default_factory=dict)  # code -> reason
    warnings: list[str] = field(default_factory=list)
    directional_only: bool = False  # set when Tier-C share exceeds threshold


@dataclass
class DataQuality:
    """Data-quality declaration payload (Guideline §5.3)."""

    firm: str
    cohort_year: int
    analysis_level: str
    layer1_method: str
    benchmark_tiers: dict[str, str]
    layer2_tiers: dict[str, str]
    volume_tiers: dict[str, str]
    lifetime_T: int | None
    lifetime_sens: int
    scenario_sources: dict[str, str]
    missing_inputs: list[str]
    warnings: list[str]
    flag_markets: dict[str, str]


@dataclass
class RunResult:
    """Top-level engine output bundling all required outputs across scenarios."""

    firm: str
    cohort_year: int
    cohorts: dict[Scenario, CohortResult]  # single-cohort TI per scenario
    vehicle_results: list[VehicleResult]
    data_quality: DataQuality
    config: EngineConfig
    # optional extras populated by downstream steps
    portfolio: dict[Scenario, list[float]] = field(default_factory=dict)
    sensitivity: dict[str, object] = field(default_factory=dict)
