"""Step 3 — destination parameters and the dynamic reference benchmark for the United States.

Same outputs and same columns as ``build_reference.py``, for the single-country US market.
The two differ only in where the observations come from and in how each parameter is tiered.

Inputs (processed datasets)
    vehicle_usage/processed/vehicle_usage_us.csv            light-duty stock and traffic (FHWA)
    vehicle_usage/processed/vehicle_usage_us_lifetime.csv   expected vehicle lifetime (NHTSA)
    country_emissions/processed/country_emissions_us.csv    light-duty CO2 (EPA inventory)
    country_emissions/processed/country_emissions_owid_grid.csv   grid intensity
    emission_targets/processed/emission_targets_us.csv      S1/S2 r_fleet, r_power
Outputs (data/auto/output/)
    destination_parameters_us.csv    one row: the US market
    reference_trajectories_us.csv    market x scenario x t: E_ref(t) and G(t)

Algorithm (whitepaper §3.1, guideline §2.3 Method B — identical to the EU27 builder):
    $$ D = \\frac{\\sum_k V_k \\cdot 10^6}{\\sum_k N_k},\\quad
       I_{fleet}(0) = \\frac{CO2_{LDV}\\cdot 10^9}{\\left(\\sum_k N_k\\right) D},\\quad
       E_{ref}(t) = \\frac{I_{fleet}(0)}{1000}(1-r_{fleet,S})^{t} D,\\quad
       G(t) = \\frac{G(0)}{1000}(1-r_{power,S})^{t} $$
    ASCII: D = sum(traffic_Mvkm)*1e6/sum(stock); I0 = co2_kt*1e9/(stock*D) [gCO2/km];
           E_ref(t) = I0/1000*(1-r_fleet)^t*D [kgCO2e per vehicle-year];
           G(t) = G0/1000*(1-r_power)^t [kgCO2e/kWh]
    k          FHWA wheelbase class: short-wheelbase ("car") and long-wheelbase light duty
    V_k        annual vehicle-kilometres of class k (million vkm/year)
    N_k        registered vehicles of class k (vehicles)
    CO2_LDV    light-duty vehicle CO2 (ktCO2/year, EPA inventory passenger cars + light trucks)
    D          annual distance per light-duty vehicle (km/year)
    r_fleet, r_power  annual fractional decline rates (1/year), t years after the sale year

Scenario coverage: S2 is the NDC the United States communicated on 2024-12-19,
61 % below 2005 net GHG by 2035, applied pro-rata as in every other market. The
country notified withdrawal from the Paris Agreement a month later, so this is
the last pathway its own government stated rather than one in force; the
``target_level`` column carries that. A market whose rate is empty is still
excluded by the generic rule below and published in ``scenarios_excluded``,
never left as a silent gap.

Run from the repository root:  .venv/bin/python script/auto/model/build_reference_us.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from model_io import LIGHT_DUTY, PARAM_FIELDS, REF_FIELDS, latest, read_csv, read_long, write_csv

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
USAGE = DATA / "vehicle_usage" / "processed" / "vehicle_usage_us.csv"
LIFETIME = DATA / "vehicle_usage" / "processed" / "vehicle_usage_us_lifetime.csv"
EMISSIONS = DATA / "country_emissions" / "processed" / "country_emissions_us.csv"
GRID = DATA / "country_emissions" / "processed" / "country_emissions_owid_grid.csv"
TARGETS = DATA / "emission_targets" / "processed" / "emission_targets_us.csv"
OUT_DIR = DATA / "output"
OUT_PARAMS = OUT_DIR / "destination_parameters_us.csv"
OUT_REF = OUT_DIR / "reference_trajectories_us.csv"

MARKET = COUNTRY = "US"
#: FHWA VM-1 wheelbase classes that together are the light-duty fleet the cohorts sell into.
STOCK_SERIES = ("car_stock", "ldv_long_wb_stock")
TRAFFIC_SERIES = ("car_traffic", "ldv_long_wb_traffic")
#: Inventory series for the benchmark numerator, most specific first.
CO2_SERIES = ("ldv_co2", "car_co2")
LIFETIME_SERIES = "car_expected_lifetime_years"
#: Same plausibility band as the EU27 builder: outside it the numerator and the denominator
#: describe different driving populations and the ratio is not a clean national parameter.
FLEET_INTENSITY_MIN, FLEET_INTENSITY_MAX = 80.0, 320.0
#: The operating-life bracket the sensitivity moves, so low/high are set to match it.
LIFETIME_DELTA_Y = 3

VKT_TIER = "B"
GRID_TIER = "A"
VKT_DERIVATION = (
    "FHWA Highway Statistics VM-1 light-duty vehicle-kilometres (short- plus long-wheelbase) "
    "divided by the registered light-duty vehicle count of the same year."
)
WARN_VKT_TIER = (
    "VKT_TIER_B: FHWA VM-1 partitions light-duty vehicles by wheelbase (short and long), not "
    "by body type, so the denominator is all light-duty vehicles rather than passenger cars as "
    "defined in the EU27 series; numerator and denominator are consistent with each other but "
    "the classification is not the registration-based one, hence tier B."
)
WARN_LIFETIME_TIER = (
    "LIFETIME_TIER_C: the operating life is the NHTSA expected-lifetime figure, computed from a "
    "survival schedule fitted to 1977-2002 passenger-car registrations and scrappage, not to the "
    "current fleet; low and high are the central value minus and plus "
    f"{LIFETIME_DELTA_Y} years, the same bracket the lifetime sensitivity moves."
)
WARN_CO2_FALLBACK = (
    "CO2_SERIES_FALLBACK: the light-duty series ldv_co2 is absent from "
    "country_emissions_us.csv; the passenger-car-only series car_co2 was used against a "
    "light-duty stock and distance, which understates the benchmark. Fix the input."
)
SOURCE_IDS = (
    "fhwa_vm1_2023",
    "epa_ghg_inventory_2025",
    "owid_ember_grid_intensity",
    "nhtsa_809952",
)


def summed_series(
    usage: dict[tuple[str, str], dict[int, float]], names: tuple[str, ...], not_after: int
) -> tuple[int, float] | None:
    """Latest year at or before ``not_after`` in which every named series reports, and the sum.

    Args:
        usage: (country, series) -> {year: value} from the processed usage table.
        names: Series to add together (the wheelbase classes of one fleet definition).
        not_after: Highest observation year allowed.

    Returns:
        (year, summed value) or None when no year carries the whole partition.
    """
    per_series = [usage.get((COUNTRY, name), {}) for name in names]
    if any(not s for s in per_series):
        return None
    common = set.intersection(*[{y for y in s if y <= not_after} for s in per_series])
    if not common:
        return None
    year = max(common)
    return year, sum(s[year] for s in per_series)


def co2_observation(
    emissions: dict[tuple[str, str], dict[int, float]], not_after: int
) -> tuple[str, int, float]:
    """Latest light-duty CO2 observation, falling back to the car-only series with a warning."""
    for name in CO2_SERIES:
        found = latest(emissions.get((COUNTRY, name), {}), not_after)
        if found:
            return name, found[0], found[1]
    raise SystemExit(f"none of {CO2_SERIES} is present in {EMISSIONS.relative_to(REPO)}")


def read_rates(path: Path) -> tuple[dict[tuple[str, str], float], dict[str, str]]:
    """Rates per (scenario, rate name) and the exclusion reason of every unrated scenario.

    Args:
        path: Processed emission-targets table for the market.

    Returns:
        rates: (scenario, rate) -> value, for the scenarios that carry a value.
        excluded: scenario -> reason, for the scenarios whose rates are empty.
    """
    rates: dict[tuple[str, str], float] = {}
    excluded: dict[str, str] = {}
    for row in read_csv(path):
        if row["value"]:
            rates[(row["scenario"], row["rate"])] = float(row["value"])
        else:
            excluded[row["scenario"]] = f"{row['target_level']}: {row['derivation']}"
    return rates, excluded


def main() -> None:
    """Build the US destination parameters and the S1/S2 reference trajectories."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--cohort-year",
        type=int,
        default=2025,
        help="earliest sale year the trajectories are applied to (they are indexed on t)",
    )
    parser.add_argument(
        "--observation-cap",
        type=int,
        default=2024,
        help="highest observation year any parameter may be read from",
    )
    args = parser.parse_args()
    year0: int = args.cohort_year
    cap: int = args.observation_cap

    usage = read_long(USAGE)
    emissions = read_long(EMISSIONS)
    grid_series = read_long(GRID)
    lifetime_series = read_long(LIFETIME)
    rates, excluded = read_rates(TARGETS)

    warnings = [WARN_VKT_TIER, WARN_LIFETIME_TIER]

    stock = summed_series(usage, STOCK_SERIES, cap)
    traffic = summed_series(usage, TRAFFIC_SERIES, cap)
    if stock is None or traffic is None:
        raise SystemExit(f"{USAGE.relative_to(REPO)}: no year carries stock and traffic together")
    stock_same_year = summed_series(usage, STOCK_SERIES, traffic[0])
    if stock_same_year is None or stock_same_year[0] != traffic[0]:
        raise SystemExit(f"{USAGE.relative_to(REPO)}: no stock observation for {traffic[0]}")
    vkt = traffic[1] * 1e6 / stock_same_year[1]

    co2_name, co2_year, co2_kt = co2_observation(emissions, cap)
    if co2_name != CO2_SERIES[0]:
        print(f"WARNING  {WARN_CO2_FALLBACK}")
        warnings.append(WARN_CO2_FALLBACK)
    fleet_intensity = co2_kt * 1e9 / (stock_same_year[1] * vkt)
    fleet_tier = VKT_TIER
    if not FLEET_INTENSITY_MIN <= fleet_intensity <= FLEET_INTENSITY_MAX:
        fleet_tier = "C"
        warnings.append(
            f"FLEET_INTENSITY_IMPLAUSIBLE: {fleet_intensity:.0f} gCO2/km outside "
            f"{FLEET_INTENSITY_MIN:.0f}-{FLEET_INTENSITY_MAX:.0f}; inventory and stock cover "
            "different driving populations; tiered down to C."
        )

    grid = latest(grid_series.get((COUNTRY, "grid_intensity"), {}), cap)
    if grid is None:
        raise SystemExit(f"{GRID.relative_to(REPO)}: no US grid intensity at or before {cap}")

    life_observation = latest(lifetime_series.get((COUNTRY, LIFETIME_SERIES), {}), cap)
    if life_observation is None:
        raise SystemExit(f"{LIFETIME.relative_to(REPO)}: no {LIFETIME_SERIES} observation")
    life = round(life_observation[1])

    scenarios = sorted({s for (s, _rate) in rates})
    missing = [s for s in scenarios if (s, "r_fleet") not in rates or (s, "r_power") not in rates]
    if missing:
        raise SystemExit(f"{TARGETS.relative_to(REPO)}: incomplete rate pair for {missing}")

    params = {
        "market": MARKET,
        "country": COUNTRY,
        "segment": LIGHT_DUTY,
        "cohort_year": year0,
        "vkt_km": vkt,
        "vkt_low_km": None,
        "vkt_high_km": None,
        "vkt_tier": VKT_TIER,
        "vkt_year": traffic[0],
        "vkt_derivation": (
            f"{VKT_DERIVATION} Parameters are read from the latest observations at or before "
            f"{cap}; the cohorts they price were sold in {year0} and later, and the "
            "trajectories are indexed on t = years after sale, not on calendar year."
        ),
        "stock": stock_same_year[1],
        "stock_year": stock_same_year[0],
        "co2_kt": co2_kt,
        "co2_year": co2_year,
        "fleet_intensity_gco2_km": fleet_intensity,
        "fleet_intensity_tier": fleet_tier,
        "grid_gco2_kwh": grid[1],
        "grid_year": grid[0],
        "grid_tier": GRID_TIER,
        "mean_age_years": None,
        "mean_age_year": None,
        "mean_age_tier": None,
        "lifetime_years": life,
        "lifetime_low_years": life - LIFETIME_DELTA_Y,
        "lifetime_high_years": life + LIFETIME_DELTA_Y,
        "lifetime_tier": "C",
        "scenarios_excluded": ";".join(sorted(excluded)),
        "scenario_exclusion_reason": " | ".join(f"{s}: {r}" for s, r in sorted(excluded.items())),
        "warnings": " | ".join(warnings),
        "source_ids": ";".join(SOURCE_IDS),
    }
    write_csv(OUT_PARAMS, PARAM_FIELDS, [params])

    ref_rows: list[dict[str, object]] = []
    for scenario in scenarios:
        r_fleet = rates[(scenario, "r_fleet")]
        r_power = rates[(scenario, "r_power")]
        for t in range(int(life + LIFETIME_DELTA_Y)):
            ref_rows.append(
                {
                    "market": MARKET,
                    "country": COUNTRY,
                    "segment": LIGHT_DUTY,
                    "scenario": scenario,
                    "t": t,
                    "calendar_year": year0 + t,
                    "r_fleet": r_fleet,
                    "r_power": r_power,
                    "fleet_intensity_gco2_km": round(fleet_intensity, 6),
                    "e_ref_kgco2_per_vehicle": round(
                        fleet_intensity / 1000 * (1 - r_fleet) ** t * vkt, 6
                    ),
                    "grid_kgco2_per_kwh": round(grid[1] / 1000 * (1 - r_power) ** t, 9),
                }
            )
    write_csv(OUT_REF, REF_FIELDS, ref_rows)

    print(
        f"{OUT_PARAMS.relative_to(REPO)}: 1 market; vkt {vkt:,.0f} km/yr (tier {VKT_TIER}, "
        f"{traffic[0]}), fleet intensity {fleet_intensity:.1f} gCO2/km from {co2_name} "
        f"{co2_year}, grid {grid[1]:.1f} gCO2/kWh ({grid[0]}), T {life} y "
        f"[{life - LIFETIME_DELTA_Y}, {life + LIFETIME_DELTA_Y}]"
    )
    print(
        f"{OUT_REF.relative_to(REPO)}: {len(ref_rows)} rows, scenarios {scenarios}; "
        f"excluded {sorted(excluded) or 'none'}"
    )


if __name__ == "__main__":
    main()
