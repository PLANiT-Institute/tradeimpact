"""Step 3 — destination parameters and reference benchmarks for Japan, one per vehicle segment.

Japan is the only market in the project where distance and stock come from a single table at a
single date: the 自動車燃料消費量調査 prints total vehicle-kilometres and kilometres per vehicle
per calendar day on the same row, so the stock behind a segment is implied rather than joined
from a registration file published at another date. It is also the only market with a published
expected vehicle life (AIRIA 平均使用年数), so the lifetime horizon is sourced rather than
derived from mean age.

Inputs (processed datasets)
    vehicle_usage/processed/vehicle_usage_jp.csv            traffic_, distance_, stock_<segment>
    vehicle_usage/processed/vehicle_usage_jp_lifetime.csv   mean_age_, mean_use_years_<segment>
    country_emissions/processed/country_emissions_jp.csv    co2_<segment> (GIO/NIES sheet 3)
    country_emissions/processed/country_emissions_owid_grid.csv   grid intensity (Ember)
    emission_targets/processed/emission_targets_jp.csv      S1/S2 r_fleet, r_power
Outputs (data/auto/output/)
    destination_parameters_jp.csv    one row per segment
    reference_trajectories_jp.csv    segment x scenario x t: E_ref(t) and G(t)

Algorithm (whitepaper §3.1, guideline §2.3 Method B), per segment:
    $$ I_{fleet}(0) = \\frac{CO2 \\cdot 10^9}{V \\cdot 10^6},\\quad
       E_{ref}(t) = \\frac{I_{fleet}(0)}{1000}(1-r_{fleet,S})^{t} D,\\quad
       G(t) = \\frac{G(0)}{1000}(1-r_{power,S})^{t} $$
    ASCII: I0 = co2_kt*1e9/(traffic_Mvkm*1e6); E_ref(t) = I0/1000*(1-r_fleet)^t*D;
           G(t) = G0/1000*(1-r_power)^t
    V     that segment's vehicle-kilometres (million vkm/fiscal year)
    D     that segment's annual distance per vehicle (km/year, from the same table)
    CO2   that segment's CO2 (ktCO2/fiscal year), published by vehicle type — no proxy needed

Segments. 乗用車 and 貨物車 are built. Buses are not: the survey separates diesel buses but
bundles petrol buses into the car and special-vehicle rows, so a bus denominator would be
diesel-only against an all-bus numerator and the intensity would be biased high. The bus rows are
still published in vehicle_usage_jp.csv, and no company in scope sells buses in Japan.

Tiers. The numerator is tier A — Japan publishes road CO2 split by vehicle type, which Korea does
not. Distance is tier B: the survey covers fuel-burning vehicles, so battery-electric kilometres
are missing from the denominator and the fleet intensity is a combustion-fleet intensity, biased
high by roughly the battery-electric share of vehicle-kilometres (about 1 % of the Japanese car
fleet). The lifetime is tier B: AIRIA publishes it, but counts a temporary deregistration as an
ending, so it is a floor. Fiscal years throughout (April to March); grid intensity is calendar.

Run from the repository root:  .venv/bin/python script/auto/model/build_reference_jp.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from model_io import (
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
USAGE = DATA / "vehicle_usage" / "processed" / "vehicle_usage_jp.csv"
LIFETIME = DATA / "vehicle_usage" / "processed" / "vehicle_usage_jp_lifetime.csv"
EMISSIONS = DATA / "country_emissions" / "processed" / "country_emissions_jp.csv"
GRID = DATA / "country_emissions" / "processed" / "country_emissions_owid_grid.csv"
TARGETS = DATA / "emission_targets" / "processed" / "emission_targets_jp.csv"
OUT_DIR = DATA / "output"
OUT_PARAMS = OUT_DIR / "destination_parameters_jp.csv"
OUT_REF = OUT_DIR / "reference_trajectories_jp.csv"

MARKET = COUNTRY = "JP"
BUILT_SEGMENTS = (PASSENGER_CAR, FREIGHT)
LIFETIME_MIN_Y, LIFETIME_MAX_Y = 10, 25
LIFETIME_BRACKET_Y = 3
VKT_TIER = "B"
GRID_TIER = "A"
FLEET_TIER = "A"
AGE_TIER = "A"
LIFETIME_TIER = "B"
WARN_VKT_TIER = (
    "VKT_TIER_B: the 自動車燃料消費量調査 covers vehicles that burn fuel, so battery-electric "
    "kilometres are absent from both the distance and the implied stock. The fleet intensity is "
    "therefore a combustion-fleet intensity, biased high by roughly the battery-electric share "
    "of vehicle-kilometres (about 1 % of Japanese cars), and the implied stock lands 1-2 % below "
    "the registered fleet AIRIA publishes."
)
WARN_LIFETIME_TIER = (
    "LIFETIME_TIER_B: AIRIA's 平均使用年数 counts a 一時抹消登録 (temporary deregistration) as "
    "an ending, so the published life is a floor on years to scrappage; it is bracketed "
    f"+/-{LIFETIME_BRACKET_Y} years."
)
WARN_FISCAL = (
    "FISCAL_YEAR: the emissions numerator and the distance denominator are Japanese fiscal years "
    "(April to March) and are matched to each other; grid intensity is calendar, which shifts the "
    "power leg by a quarter."
)
WARN_KEI = (
    "KEI_IN_BENCHMARK: the car benchmark covers the whole national fleet including 軽自動車, "
    "which are lower-emitting than registered cars, while the cohort is registration-statistics "
    "(non-kei). The segment ratio stays 1.0, so a kei-heavy fleet average makes the benchmark "
    "harder for a registered car to beat."
)
SOURCE_IDS = (
    "mlit_fuel_consumption_survey",
    "airia_vehicle_age",
    "gio_nies_inventory",
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
    """Build one destination-parameter row and one trajectory set per Japanese segment."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cohort-year", type=int, default=2024)
    parser.add_argument("--observation-cap", type=int, default=2024)
    args = parser.parse_args()
    year0, cap = args.cohort_year, args.observation_cap

    usage = read_long(USAGE)
    lifetime = read_long(LIFETIME)
    emissions = read_long(EMISSIONS)
    grid_series = read_long(GRID)
    rates, excluded = read_rates(TARGETS)

    grid = latest(grid_series.get((COUNTRY, "grid_intensity"), {}), cap)
    if grid is None:
        raise SystemExit(f"{GRID.relative_to(REPO)}: no JP grid intensity at or before {cap}")
    scenarios = sorted({s for (s, _rate) in rates})
    missing = [s for s in scenarios if (s, "r_fleet") not in rates or (s, "r_power") not in rates]
    if missing:
        raise SystemExit(f"{TARGETS.relative_to(REPO)}: incomplete rate pair for {missing}")

    params: list[dict[str, object]] = []
    ref_rows: list[dict[str, object]] = []
    for segment in BUILT_SEGMENTS:
        co2 = latest(emissions.get((COUNTRY, f"co2_{segment}"), {}), cap)
        if co2 is None:
            raise SystemExit(f"{EMISSIONS.name}: no co2_{segment} at or before {cap}")
        # Numerator and denominator are the same fiscal year by construction, not by luck.
        traffic = usage.get((COUNTRY, f"traffic_{segment}"), {}).get(co2[0])
        vkt = usage.get((COUNTRY, f"distance_{segment}"), {}).get(co2[0])
        stock = usage.get((COUNTRY, f"stock_{segment}"), {}).get(co2[0])
        if traffic is None or vkt is None or stock is None:
            raise SystemExit(f"{USAGE.name}: no {segment} distance for the CO2 year {co2[0]}")
        intensity = co2[1] * 1e9 / (traffic * 1e6)

        age = latest(lifetime.get((COUNTRY, f"mean_age_{segment}"), {}), max(cap, year0) + 2)
        life_years = latest(
            lifetime.get((COUNTRY, f"mean_use_years_{segment}"), {}), max(cap, year0) + 2
        )
        if age is None or life_years is None:
            raise SystemExit(f"{LIFETIME.name}: no age or use-years for {segment}")
        life = clamp_life(life_years[1])

        warnings = [WARN_VKT_TIER, WARN_LIFETIME_TIER, WARN_FISCAL]
        if segment == PASSENGER_CAR:
            warnings.append(WARN_KEI)
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
                "vkt_year": co2[0],
                "vkt_derivation": (
                    "自動車燃料消費量調査 第１表: １日１車当たり走行キロ x 365 per row, "
                    "traffic-weighted over the rows the segment map assigns to this segment; the "
                    "implied stock is that segment's 走行キロ divided by the same figure. "
                    f"Fiscal {co2[0]}, matched to the emissions year rather than taken as the "
                    "latest observation."
                ),
                "stock": stock,
                "stock_year": co2[0],
                "co2_kt": co2[1],
                "co2_year": co2[0],
                "fleet_intensity_gco2_km": intensity,
                "fleet_intensity_tier": FLEET_TIER,
                "grid_gco2_kwh": grid[1],
                "grid_year": grid[0],
                "grid_tier": GRID_TIER,
                "mean_age_years": age[1],
                "mean_age_year": age[0],
                "mean_age_tier": AGE_TIER,
                "lifetime_years": life,
                "lifetime_low_years": clamp_life(life_years[1] - LIFETIME_BRACKET_Y),
                "lifetime_high_years": clamp_life(life_years[1] + LIFETIME_BRACKET_Y),
                "lifetime_tier": LIFETIME_TIER,
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
            for t in range(clamp_life(life_years[1] + LIFETIME_BRACKET_Y)):
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
            f"{float(str(r['mean_age_years'])):.2f} y, published life "
            f"{r['lifetime_years']} y"
        )
    print(f"{OUT_REF.relative_to(REPO)}: {len(ref_rows)} rows, scenarios {scenarios}")


if __name__ == "__main__":
    main()
