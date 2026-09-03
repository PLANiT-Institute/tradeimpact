# SPDX-License-Identifier: GPL-3.0-or-later
"""Sector registry for exported-product lifetime impact analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    label: str
    unit: str
    description: str


@dataclass(frozen=True)
class SectorProfile:
    sector_id: str
    name: str
    implementation_status: str
    operating_boundary: str
    activity_basis: str
    direct_metrics: tuple[MetricDefinition, ...]
    descriptive_metrics: tuple[MetricDefinition, ...]
    contextual_pathways: tuple[str, ...]
    required_dimensions: tuple[str, ...]
    boundary_risks: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "sector_id": self.sector_id,
            "name": self.name,
            "implementation_status": self.implementation_status,
            "operating_boundary": self.operating_boundary,
            "activity_basis": self.activity_basis,
            "direct_metrics": [asdict(metric) for metric in self.direct_metrics],
            "descriptive_metrics": [asdict(metric) for metric in self.descriptive_metrics],
            "contextual_pathways": list(self.contextual_pathways),
            "required_dimensions": list(self.required_dimensions),
            "boundary_risks": list(self.boundary_risks),
        }


_COMMON_DIMENSIONS = (
    "company boundary",
    "operating geography",
    "reporting year",
    "activity volume and unit",
    "source and evidence class",
    "mapping status",
)


SECTOR_PROFILES: tuple[SectorProfile, ...] = (
    SectorProfile(
        sector_id="automotive",
        name="Automotive",
        implementation_status="pilot",
        operating_boundary="vehicle registration or use country",
        activity_basis="new vehicle registrations by vehicle class, model, and powertrain",
        direct_metrics=(
            MetricDefinition(
                "zev_sales_share",
                "Policy-eligible ZEV sales share",
                "fraction",
                "Registration-weighted share using each policy's eligibility definition.",
            ),
            MetricDefinition(
                "new_vehicle_tailpipe_intensity",
                "New-vehicle certified tailpipe intensity",
                "gCO2/km",
                "Registration-weighted certified value within one test regime and vehicle class.",
            ),
        ),
        descriptive_metrics=(
            MetricDefinition(
                "new_vehicle_registrations",
                "New passenger-car registrations",
                "registrations",
                "Observed registrations for the exact brand, geography, and reporting year.",
            ),
            MetricDefinition(
                "powertrain_sales_share",
                "Powertrain sales share",
                "fraction",
                "Registration share for one disclosed powertrain classification.",
            ),
        ),
        contextual_pathways=(
            "destination passenger-car or road-transport pathway",
            "destination grid pathway",
            "economy-wide NDC fallback",
        ),
        required_dimensions=_COMMON_DIMENSIONS
        + ("vehicle class", "model", "powertrain", "certification regime"),
        boundary_risks=(
            "manufacturer group versus brand",
            "sales versus registrations",
            "destination registration versus verified export origin",
            "policy-specific PHEV and FCEV eligibility",
        ),
    ),
    SectorProfile(
        sector_id="power",
        name="Power generation",
        implementation_status="pilot",
        operating_boundary="generation country and connected grid; consumption attribution separate",
        activity_basis="net generation by plant, technology, and fuel",
        direct_metrics=(
            MetricDefinition(
                "generation_emissions_intensity",
                "Generation emissions intensity",
                "kgCO2e/MWh",
                "Reported or derived direct intensity on one declared net-generation boundary.",
            ),
            MetricDefinition(
                "clean_generation_share",
                "Policy-defined clean generation share",
                "fraction",
                "Share calculated with the applicable policy's technology eligibility rules.",
            ),
        ),
        descriptive_metrics=(
            MetricDefinition(
                "net_generation",
                "Net generation",
                "MWh",
                "Observed net generation; plant and technology decomposition retained when disclosed.",
            ),
            MetricDefinition(
                "reported_generation",
                "Reported generation",
                "MWh",
                "Observed generation where the source does not identify a gross or net basis.",
            ),
            MetricDefinition(
                "scope1_emissions",
                "Reported Scope 1 emissions",
                "tCO2e",
                "Company-reported direct emissions retained without denominator conversion.",
            ),
            MetricDefinition(
                "scope2_emissions",
                "Reported Scope 2 emissions",
                "tCO2e",
                "Company-reported indirect purchased-energy emissions on its stated method.",
            ),
        ),
        contextual_pathways=("power-sector emissions pathway", "economy-wide NDC"),
        required_dimensions=_COMMON_DIMENSIONS
        + ("plant", "generation technology", "fuel", "net generation MWh"),
        boundary_risks=(
            "generation versus consumption country",
            "cross-border electricity trade",
            "company average masking coal and zero-carbon assets",
        ),
    ),
    SectorProfile(
        sector_id="shipping",
        name="Commercial shipping",
        implementation_status="pilot",
        operating_boundary="voyage and IMO jurisdiction; flag state reported separately",
        activity_basis="transport work by vessel type and fuel",
        direct_metrics=(
            MetricDefinition(
                "shipping_carbon_intensity",
                "Shipping carbon intensity",
                "gCO2e/tonne-nm",
                "Cargo-mass transport intensity only where vessel coverage and accounting boundary match.",
            ),
            MetricDefinition(
                "shipping_eeoi",
                "Energy Efficiency Operational Indicator",
                "gCO2e/ton-mile",
                "Source-defined lifecycle-GHG EEOI; the disclosed ton-mile denominator is preserved.",
            ),
        ),
        descriptive_metrics=(
            MetricDefinition(
                "shipping_transport_work",
                "Shipping transport work",
                "tonne-nm",
                "Observed cargo-mass transport work within the stated voyage boundary.",
            ),
        ),
        contextual_pathways=("IMO GHG strategy", "served-country transport pathways"),
        required_dimensions=_COMMON_DIMENSIONS
        + ("vessel", "vessel type", "fuel", "voyage", "transport work"),
        boundary_risks=(
            "flag state versus voyage geography",
            "tank-to-wake versus well-to-wake",
            "ship-type-specific CII denominators",
        ),
    ),
    SectorProfile(
        sector_id="steel",
        name="Steel",
        implementation_status="planned",
        operating_boundary="production plant country",
        activity_basis="crude steel production by plant and production route",
        direct_metrics=(
            MetricDefinition(
                "steel_emissions_intensity",
                "Crude steel emissions intensity",
                "tCO2e/t_crude_steel",
                "Plant- and route-specific intensity on one declared emissions boundary.",
            ),
        ),
        descriptive_metrics=(
            MetricDefinition(
                "crude_steel_production",
                "Crude steel production",
                "t_crude_steel",
                "Observed plant production retaining production-route detail.",
            ),
        ),
        contextual_pathways=("industry or steel pathway", "economy-wide NDC"),
        required_dimensions=_COMMON_DIMENSIONS
        + ("plant", "production route", "crude steel tonnes", "emissions boundary"),
        boundary_risks=(
            "crude steel versus finished product denominator",
            "Scope 1 versus Scope 1+2",
            "scrap allocation and process-route comparability",
        ),
    ),
    SectorProfile(
        sector_id="petrochemicals",
        name="Petrochemicals",
        implementation_status="planned",
        operating_boundary="production plant country",
        activity_basis="production by plant and chemical product",
        direct_metrics=(
            MetricDefinition(
                "petrochemical_emissions_intensity",
                "Product-specific production intensity",
                "tCO2e/t_product",
                "Intensity is comparable only within the same product and emissions boundary.",
            ),
        ),
        descriptive_metrics=(
            MetricDefinition(
                "chemical_production",
                "Chemical product output",
                "t_product",
                "Observed output for one named chemical product and plant boundary.",
            ),
        ),
        contextual_pathways=("chemicals or industry pathway", "economy-wide NDC"),
        required_dimensions=_COMMON_DIMENSIONS
        + ("plant", "chemical product", "production tonnes", "emissions boundary"),
        boundary_risks=(
            "non-comparable chemical products",
            "feedstock carbon versus energy emissions",
            "joint-product allocation",
        ),
    ),
)


def list_sector_profiles() -> list[dict[str, object]]:
    return [profile.to_dict() for profile in SECTOR_PROFILES]


def get_sector_profile(sector_id: str) -> SectorProfile:
    normalized = sector_id.strip().lower()
    for profile in SECTOR_PROFILES:
        if profile.sector_id == normalized:
            return profile
    raise KeyError(f"unknown sector: {sector_id}")
