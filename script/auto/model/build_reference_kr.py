"""Step 3 — destination parameters and reference benchmarks for Korea, one per vehicle segment.

Korea publishes emissions, stock, distance and vehicle age under the same four registration
classes (passenger car, bus, goods, special), so a benchmark can be built for each one
against exactly the
population it prices. That is what lets a Porter or a Bongo be measured against Korean goods
vehicles instead of against cars.

Inputs (processed datasets)
    vehicle_usage/processed/vehicle_usage_kr.csv           stock_<segment>, mean_age_<segment>
    vehicle_usage/processed/vehicle_usage_kr_traffic.csv   traffic_<segment> (KOTSA odometers)
    country_emissions/processed/country_emissions_kr.csv   co2_<segment> (GIR road CO2 x share)
    country_emissions/processed/country_emissions_owid_grid.csv   grid intensity (Ember)
    emission_targets/processed/emission_targets_kr.csv     S1/S2 r_fleet, r_power
Outputs (data/auto/output/)
    destination_parameters_kr.csv    one row per segment
    reference_trajectories_kr.csv    segment x scenario x t: E_ref(t) and G(t)

Algorithm (whitepaper §3.1, guideline §2.3 Method B), per segment:
    $$ D = \\frac{V \\cdot 10^6}{N},\\quad I_{fleet}(0) = \\frac{CO2 \\cdot 10^9}{V \\cdot 10^6},
       \\quad E_{ref}(t) = \\frac{I_{fleet}(0)}{1000}(1-r_{fleet,S})^{t} D $$
    ASCII: D = traffic_Mvkm*1e6/stock; I0 = co2_kt*1e9/(traffic_Mvkm*1e6);
           E_ref(t) = I0/1000*(1-r_fleet)^t*D;  G(t) = G0/1000*(1-r_power)^t
    V     that class's vehicle-kilometres (million vkm/year, inspection odometers)
    N     that class's registered vehicles at year end
    CO2   that class's CO2 (ktCO2/year): GIR road CO2 x the class's KOTSA share

The scenario rates are national and are applied to every segment pro-rata: Korea's climate plan
sets a target for transport as a whole (1.A.3), not one per vehicle class.

Tiers. Distance is tier A for every segment (odometer-based, same class as the stock). The
numerator is tier C throughout: the national inventory has no vehicle-class split and the share
comes from a bottom-up local inventory whose level sits 13-26 % below the national road total.
Mean age is tier C (the oldest model-year band is open-ended, biasing the mean low).

Run from the repository root:  .venv/bin/python script/auto/model/build_reference_kr.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from model_io import (
    BUS,
    FREIGHT,
    INTENSITY_BAND,
    PARAM_FIELDS,
    PASSENGER_CAR,
    REF_FIELDS,
    latest,
    read_csv,
    read_long,
    write_csv,
)

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
USAGE = DATA / "vehicle_usage" / "processed" / "vehicle_usage_kr.csv"
TRAFFIC = DATA / "vehicle_usage" / "processed" / "vehicle_usage_kr_traffic.csv"
EMISSIONS = DATA / "country_emissions" / "processed" / "country_emissions_kr.csv"
GRID = DATA / "country_emissions" / "processed" / "country_emissions_owid_grid.csv"
TARGETS = DATA / "emission_targets" / "processed" / "emission_targets_kr.csv"
OUT_DIR = DATA / "output"
OUT_PARAMS = OUT_DIR / "destination_parameters_kr.csv"
OUT_REF = OUT_DIR / "reference_trajectories_kr.csv"

MARKET = COUNTRY = "KR"
#: The segments Korean statistics support, in reporting order. Special vehicles are left
#: out: no company in scope sells them and they are 0.7 % of the road fleet.
BUILT_SEGMENTS = (PASSENGER_CAR, FREIGHT, BUS)
LIFETIME_MIN_Y, LIFETIME_MAX_Y = 10, 25
LIFETIME_CENTRAL_MULTIPLE = 1.5
VKT_TIER = "A"
GRID_TIER = "A"
FLEET_TIER = "C"
AGE_TIER = "C"
WARN_FLEET_TIER = (
    "FLEET_INTENSITY_TIER_C: the national inventory (GIR) publishes road-transport CO2 without "
    "a vehicle-class split; the class share is taken from the KOTSA bottom-up local inventory, "
    "whose national level sits 13-26 % below the GIR road total. Share applied to the GIR "
    "level; both sources carried."
)
WARN_AGE_TIER = (
    "MEAN_AGE_TIER_C: the MOLIT model-year distribution has an open-ended oldest band (2005 and "
    "earlier) counted at its nominal age, so the mean age is biased low and the derived lifetime "
    "with it."
)
WARN_VKT_BREAK = (
    "VKT_SERIES_BREAK_2021: KOTSA per-vehicle distance shows an 11 % discontinuity in 2021 "
    "(the total row is relabelled from mean to sum); the latest year is used and the S1 "
    "trend excludes "
    "2020-2021."
)
SOURCE_IDS = (
    "molit_vehicle_registration",
    "kotsa_tmacs_vkm",
    "gir_inventory_co2",
    "kotsa_road_ghg_vehicle_type",
    "owid_ember_grid_intensity",
)


def clamp_life(years: float) -> int:
    """Round and clamp a lifetime to the plausible band."""
    return int(min(LIFETIME_MAX_Y, max(LIFETIME_MIN_Y, round(years))))


def read_rates(path: Path) -> tuple[dict[tuple[str, str], float], dict[str, str]]:
    """Rates per (scenario, rate name) and the exclusion reason of every unrated scenario."""
    rates: dict[tuple[str, str], float] = {}
    excluded: dict[str, str] = {}
    for row in read_csv(path):
        if row["value"]:
            rates[(row["scenario"], row["rate"])] = float(row["value"])
        else:
            excluded[row["scenario"]] = f"{row['target_level']}: {row['derivation']}"
    return rates, excluded


def main() -> None:
    """Build one destination-parameter row and one trajectory set per Korean segment."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cohort-year", type=int, default=2024)
    parser.add_argument("--observation-cap", type=int, default=2024)
    args = parser.parse_args()
    year0, cap = args.cohort_year, args.observation_cap

    usage = read_long(USAGE)
    traffic_series = read_long(TRAFFIC)
    emissions = read_long(EMISSIONS)
    grid_series = read_long(GRID)
    rates, excluded = read_rates(TARGETS)

    grid = latest(grid_series.get((COUNTRY, "grid_intensity"), {}), cap)
    if grid is None:
        raise SystemExit(f"{GRID.relative_to(REPO)}: no KR grid intensity at or before {cap}")
    scenarios = sorted({s for (s, _rate) in rates})
    missing = [s for s in scenarios if (s, "r_fleet") not in rates or (s, "r_power") not in rates]
    if missing:
        raise SystemExit(f"{TARGETS.relative_to(REPO)}: incomplete rate pair for {missing}")

    params: list[dict[str, object]] = []
    ref_rows: list[dict[str, object]] = []
    for segment in BUILT_SEGMENTS:
        traffic = latest(traffic_series.get((COUNTRY, f"traffic_{segment}"), {}), cap)
        if traffic is None:
            raise SystemExit(f"{TRAFFIC.name}: no traffic_{segment} at or before {cap}")
        stock = usage.get((COUNTRY, f"stock_{segment}"), {}).get(traffic[0])
        if stock is None:
            raise SystemExit(f"{USAGE.name}: no stock_{segment} for {traffic[0]}")
        vkt = traffic[1] * 1e6 / stock

        co2 = latest(emissions.get((COUNTRY, f"co2_{segment}"), {}), cap)
        if co2 is None:
            raise SystemExit(f"{EMISSIONS.name}: no co2_{segment} at or before {cap}")
        co2_traffic = traffic_series.get((COUNTRY, f"traffic_{segment}"), {}).get(co2[0])
        if co2_traffic is None:
            raise SystemExit(f"{TRAFFIC.name}: no traffic_{segment} for the CO2 year {co2[0]}")
        intensity = co2[1] * 1e9 / (co2_traffic * 1e6)

        age = latest(usage.get((COUNTRY, f"mean_age_{segment}"), {}), max(cap, year0))
        if age is None:
            raise SystemExit(f"{USAGE.name}: no mean_age_{segment}")
        mean_age = age[1]
        life = clamp_life(LIFETIME_CENTRAL_MULTIPLE * mean_age)

        warnings = [WARN_FLEET_TIER, WARN_AGE_TIER, WARN_VKT_BREAK]
        low, high = INTENSITY_BAND[segment]
        if not low <= intensity <= high:
            warnings.append(
                f"FLEET_INTENSITY_IMPLAUSIBLE: {intensity:.0f} gCO2/km outside the {segment} "
                f"band {low:.0f}-{high:.0f}."
            )
        params.append(
            {
                "market": MARKET,
                "country": COUNTRY,
                "segment": segment,
                "cohort_year": year0,
                "vkt_km": vkt,
                "vkt_low_km": None,
                "vkt_high_km": None,
                "vkt_tier": VKT_TIER,
                "vkt_year": traffic[0],
                "vkt_derivation": (
                    f"KOTSA TMACS {segment} annual vehicle-kilometres (inspection odometer "
                    "readings grossed up to the registered fleet) divided by the MOLIT year-end "
                    f"stock of the same class. Parameters are read from the latest observations "
                    f"at or before {cap}; trajectories are indexed on t = years after sale."
                ),
                "stock": stock,
                "stock_year": traffic[0],
                "co2_kt": co2[1],
                "co2_year": co2[0],
                "fleet_intensity_gco2_km": intensity,
                "fleet_intensity_tier": FLEET_TIER,
                "grid_gco2_kwh": grid[1],
                "grid_year": grid[0],
                "grid_tier": GRID_TIER,
                "mean_age_years": mean_age,
                "mean_age_year": age[0],
                "mean_age_tier": AGE_TIER,
                "lifetime_years": life,
                "lifetime_low_years": clamp_life(mean_age),
                "lifetime_high_years": clamp_life(2 * mean_age),
                "lifetime_tier": "C",
                "scenarios_excluded": ";".join(sorted(excluded)),
                "scenario_exclusion_reason": " | ".join(
                    f"{s}: {r}" for s, r in sorted(excluded.items())
                ),
                "warnings": " | ".join(warnings),
                "source_ids": ";".join(SOURCE_IDS),
            }
        )
        for scenario in scenarios:
            r_fleet, r_power = rates[(scenario, "r_fleet")], rates[(scenario, "r_power")]
            for t in range(clamp_life(2 * mean_age)):
                ref_rows.append(
                    {
                        "market": MARKET,
                        "country": COUNTRY,
                        "segment": segment,
                        "scenario": scenario,
                        "t": t,
                        "calendar_year": year0 + t,
                        "r_fleet": r_fleet,
                        "r_power": r_power,
                        "fleet_intensity_gco2_km": round(intensity, 6),
                        "e_ref_kgco2_per_vehicle": round(
                            intensity / 1000 * (1 - r_fleet) ** t * vkt, 6
                        ),
                        "grid_kgco2_per_kwh": round(grid[1] / 1000 * (1 - r_power) ** t, 9),
                    }
                )

    write_csv(OUT_PARAMS, PARAM_FIELDS, params)
    write_csv(OUT_REF, REF_FIELDS, ref_rows)
    for r in params:
        print(
            f"{r['segment']:14s} vkt {float(str(r['vkt_km'])):>7,.0f} km/yr, intensity "
            f"{float(str(r['fleet_intensity_gco2_km'])):>6.1f} gCO2/km, mean age "
            f"{float(str(r['mean_age_years'])):.2f} y -> T {r['lifetime_years']} y"
        )
    print(f"{OUT_REF.relative_to(REPO)}: {len(ref_rows)} rows, scenarios {scenarios}")


if __name__ == "__main__":
    main()
