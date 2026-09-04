"""Step 3 — destination parameters and the dynamic reference benchmark for Korea.

Same outputs and columns as ``build_reference.py`` (EU27) and ``build_reference_us.py``, for the
single-country KR market.

Inputs (processed datasets)
    vehicle_usage/processed/vehicle_usage_kr.csv           승용 stock (MOLIT) and mean age
    vehicle_usage/processed/vehicle_usage_kr_traffic.csv   승용차 vehicle-kilometres (KOTSA)
    country_emissions/processed/country_emissions_kr.csv   car_co2 = GIR road CO2 x KOTSA share
    country_emissions/processed/country_emissions_owid_grid.csv   grid intensity (Ember)
    emission_targets/processed/emission_targets_kr.csv     S1/S2/S3 r_fleet, r_power
Outputs (data/auto/output/)
    destination_parameters_kr.csv    one row: the KR market
    reference_trajectories_kr.csv    market x scenario x t: E_ref(t) and G(t)

Algorithm (whitepaper §3.1, guideline §2.3 Method B — identical to the EU27 builder):
    $$ D = \\frac{V \\cdot 10^6}{N},\\quad I_{fleet}(0) = \\frac{CO2_{car}\\cdot 10^9}{N D},\\quad
       E_{ref}(t) = \\frac{I_{fleet}(0)}{1000}(1-r_{fleet,S})^{t} D,\\quad
       G(t) = \\frac{G(0)}{1000}(1-r_{power,S})^{t} $$
    ASCII: D = traffic_Mvkm*1e6/stock; I0 = co2_kt*1e9/(stock*D); E_ref(t) = I0/1000*(1-r)^t*D;
           G(t) = G0/1000*(1-r_power)^t
    V        승용차 vehicle-kilometres (million vkm/year, inspection odometers grossed up)
    N        registered 승용 vehicles at year end (vehicles)
    CO2_car  passenger-car CO2 (ktCO2/year): GIR 1.A.3.b road CO2 x KOTSA passenger-car share
    D        annual distance per car (km/year)

Tiers. Distance is tier A (odometer-based, same 승용 population as the stock). The benchmark
numerator is tier C: the national inventory publishes no vehicle-type split and the share comes
from a bottom-up local inventory whose level disagrees with the national one by 13-26 %. The
lifetime follows the EU27 rule (1.5 x mean age, clamped to 10-25 years, low = mean age, high =
2 x mean age) on a mean age biased low by the open-ended oldest model-year band, so it is tier C.

Run from the repository root:  .venv/bin/python script/auto/model/build_reference_kr.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from model_io import PARAM_FIELDS, REF_FIELDS, latest, read_csv, read_long, write_csv

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
FLEET_INTENSITY_MIN, FLEET_INTENSITY_MAX = 80.0, 320.0
LIFETIME_MIN_Y, LIFETIME_MAX_Y = 10, 25
LIFETIME_CENTRAL_MULTIPLE = 1.5
VKT_TIER = "A"
GRID_TIER = "A"
FLEET_TIER = "C"
AGE_TIER = "C"
VKT_DERIVATION = (
    "KOTSA TMACS 승용차 annual vehicle-kilometres (inspection odometer readings grossed up to "
    "the registered fleet) divided by the MOLIT year-end 승용 stock of the same year."
)
WARN_FLEET_TIER = (
    "FLEET_INTENSITY_TIER_C: the national inventory (GIR) publishes road-transport CO2 without a "
    "vehicle-type split; the passenger-car share is taken from the KOTSA bottom-up local "
    "inventory, whose national level sits 13-26 % below the GIR road total. Share applied to the "
    "GIR level; both sources carried."
)
WARN_AGE_TIER = (
    "MEAN_AGE_TIER_C: the MOLIT model-year distribution has an open-ended oldest band (2005 and "
    "earlier) counted at its nominal age, so the mean age is biased low and the derived "
    "lifetime with it."
)
WARN_VKT_BREAK = (
    "VKT_SERIES_BREAK_2021: KOTSA per-vehicle distance shows an 11 % discontinuity in 2021 (total "
    "row relabelled 평균 -> 계); the latest year is used and the S1 trend excludes 2020-2021."
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
    """Build the KR destination parameters and the reference trajectories."""
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
    warnings = [WARN_FLEET_TIER, WARN_AGE_TIER, WARN_VKT_BREAK]

    traffic = latest(traffic_series.get((COUNTRY, "car_traffic"), {}), cap)
    if traffic is None:
        raise SystemExit(f"{TRAFFIC.relative_to(REPO)}: no car_traffic at or before {cap}")
    stock_year, stock = traffic[0], usage.get((COUNTRY, "car_stock"), {}).get(traffic[0])
    if stock is None:
        raise SystemExit(f"{USAGE.relative_to(REPO)}: no car_stock for {traffic[0]}")
    vkt = traffic[1] * 1e6 / stock

    co2 = latest(emissions.get((COUNTRY, "car_co2"), {}), cap)
    if co2 is None:
        raise SystemExit(f"{EMISSIONS.relative_to(REPO)}: no car_co2 at or before {cap}")
    co2_stock = usage.get((COUNTRY, "car_stock"), {}).get(co2[0])
    co2_traffic = traffic_series.get((COUNTRY, "car_traffic"), {}).get(co2[0])
    if co2_stock is None or co2_traffic is None:
        raise SystemExit(f"no stock and traffic observation for the CO2 year {co2[0]}")
    fleet_intensity = co2[1] * 1e9 / (co2_traffic * 1e6)
    fleet_tier = FLEET_TIER
    if not FLEET_INTENSITY_MIN <= fleet_intensity <= FLEET_INTENSITY_MAX:
        warnings.append(
            f"FLEET_INTENSITY_IMPLAUSIBLE: {fleet_intensity:.0f} gCO2/km outside "
            f"{FLEET_INTENSITY_MIN:.0f}-{FLEET_INTENSITY_MAX:.0f}."
        )

    grid = latest(grid_series.get((COUNTRY, "grid_intensity"), {}), cap)
    if grid is None:
        raise SystemExit(f"{GRID.relative_to(REPO)}: no KR grid intensity at or before {cap}")

    age = latest(usage.get((COUNTRY, "car_mean_age_years"), {}), max(cap, year0))
    if age is None:
        raise SystemExit(f"{USAGE.relative_to(REPO)}: no car_mean_age_years")
    mean_age = age[1]

    scenarios = sorted({s for (s, _rate) in rates})
    missing = [s for s in scenarios if (s, "r_fleet") not in rates or (s, "r_power") not in rates]
    if missing:
        raise SystemExit(f"{TARGETS.relative_to(REPO)}: incomplete rate pair for {missing}")

    life = clamp_life(LIFETIME_CENTRAL_MULTIPLE * mean_age)
    params = {
        "market": MARKET,
        "country": COUNTRY,
        "cohort_year": year0,
        "vkt_km": vkt,
        "vkt_low_km": None,
        "vkt_high_km": None,
        "vkt_tier": VKT_TIER,
        "vkt_year": stock_year,
        "vkt_derivation": (
            f"{VKT_DERIVATION} Parameters are read from the latest observations at or before "
            f"{cap}; trajectories are indexed on t = years after sale."
        ),
        "car_stock": stock,
        "car_stock_year": stock_year,
        "car_co2_kt": co2[1],
        "car_co2_year": co2[0],
        "fleet_intensity_gco2_km": fleet_intensity,
        "fleet_intensity_tier": fleet_tier,
        "grid_gco2_kwh": grid[1],
        "grid_year": grid[0],
        "grid_tier": GRID_TIER,
        "mean_car_age_years": mean_age,
        "mean_car_age_year": age[0],
        "mean_car_age_tier": AGE_TIER,
        "lifetime_years": life,
        "lifetime_low_years": clamp_life(mean_age),
        "lifetime_high_years": clamp_life(2 * mean_age),
        "lifetime_tier": "C",
        "scenarios_excluded": ";".join(sorted(excluded)),
        "scenario_exclusion_reason": " | ".join(f"{s}: {r}" for s, r in sorted(excluded.items())),
        "warnings": " | ".join(warnings),
        "source_ids": ";".join(SOURCE_IDS),
    }
    write_csv(OUT_PARAMS, PARAM_FIELDS, [params])

    ref_rows: list[dict[str, object]] = []
    for scenario in scenarios:
        r_fleet, r_power = rates[(scenario, "r_fleet")], rates[(scenario, "r_power")]
        for t in range(int(params["lifetime_high_years"])):
            ref_rows.append(
                {
                    "market": MARKET,
                    "country": COUNTRY,
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
        f"{OUT_PARAMS.relative_to(REPO)}: 1 market; vkt {vkt:,.0f} km/yr ({stock_year}), fleet "
        f"intensity {fleet_intensity:.1f} gCO2/km ({co2[0]}, tier C), grid {grid[1]:.1f} gCO2/kWh "
        f"({grid[0]}), mean age {mean_age:.2f} y -> T {life} y [{params['lifetime_low_years']}, "
        f"{params['lifetime_high_years']}]"
    )
    print(f"{OUT_REF.relative_to(REPO)}: {len(ref_rows)} rows, scenarios {scenarios}")


if __name__ == "__main__":
    main()
