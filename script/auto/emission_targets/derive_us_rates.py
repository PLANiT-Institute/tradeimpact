"""Derive S1/S2/S3 annual decline rates for the United States (whitepaper §3.1, guideline §2.3).

Inputs
    country_emissions/processed/country_emissions_us.csv         car_ghg_co2e annual series
    country_emissions/processed/country_emissions_owid_grid.csv  US grid intensity
    emission_targets/raw/ndc_anchors.csv                         NDC status (FLAG market)
    emission_targets/raw/iea_weo_2024_world_co2.csv              IEA WEO world scenario anchors
Output
    emission_targets/processed/emission_targets_us.csv

Scenarios
    S1 current trajectory   log-linear trend of observed passenger-car GHG (fleet) and grid
                            intensity (power), same window and exclusions as the EU27 derivation.
    S2 committed policy     the US has no NDC in force -> FLAG market (guideline): no rate; the
                            row records the reason so S2 is excluded from the headline, not zeroed.
    S3 1.5C-aligned         world NZE pro-rata (IEA WEO 2024 Table A.4c): compound annual decline
                            of world passenger-car CO2 (fleet) and of world electricity-and-heat CO2
                            (power) from 2023 to 2040. Disclosed as ``world_prorata`` — a regional
                            NZE path for the US is not published in the report on hand.

Algorithm:
    $$ r = 1 - \\left(\\frac{V_{2040}}{V_{2023}}\\right)^{1/17} $$   (S3)
    ASCII: r = 1 - (V_2040 / V_2023) ** (1/17); S1: ln V = a + b y, r = 1 - exp(b)
    V in MtCO2 (world) or ktCO2e / gCO2 per kWh (US observed); r in 1/year, positive = decline.

Run from the repository root:  .venv/bin/python script/auto/emission_targets/derive_us_rates.py
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
EMISSIONS_US = DATA / "country_emissions" / "processed" / "country_emissions_us.csv"
GRID = DATA / "country_emissions" / "processed" / "country_emissions_owid_grid.csv"
NDC = DATA / "emission_targets" / "raw" / "ndc_anchors.csv"
WEO = DATA / "emission_targets" / "raw" / "iea_weo_2024_world_co2.csv"
OUT = DATA / "emission_targets" / "processed" / "emission_targets_us.csv"

COUNTRY = "US"
TREND_START = 2015
TREND_EXCLUDE = (2020, 2021)
S3_BASE_YEAR, S3_TARGET_YEAR = 2023, 2040
S3_SCENARIO = "NZE"

FIELDS = [
    "country",
    "scenario",
    "rate",
    "value",
    "target_level",
    "base_year",
    "target_year",
    "derivation",
    "source_id",
]


def read_series(path: Path, country: str, series: str) -> dict[int, float]:
    """{year: value} for one country x series from a long-format CSV."""
    with path.open(newline="") as f:
        return {
            int(r["year"]): float(r["value"])
            for r in csv.DictReader(f)
            if r["country"] == country and r["series"] == series
        }


def log_linear_rate(series: dict[int, float], not_after: int) -> tuple[float, int, int]:
    """Fit ln(value) = a + b*year in the trend window; return (1 - exp(b), first, last year)."""
    points = [
        (y, v)
        for y, v in series.items()
        if TREND_START <= y <= not_after and y not in TREND_EXCLUDE and v > 0
    ]
    if len(points) < 4:
        raise SystemExit(f"only {len(points)} usable trend points; four are required")
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(math.log(v) for _, v in points) / n
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    sxy = sum((x - mean_x) * (math.log(v) - mean_y) for x, v in points)
    return 1.0 - math.exp(sxy / sxx), min(x for x, _ in points), max(x for x, _ in points)


def cagr_decline(base: float, target: float, years: int) -> float:
    """Annual decline fraction taking ``base`` to ``target`` over ``years``."""
    if base <= 0 or target <= 0 or years <= 0:
        raise SystemExit("cannot derive a decline rate from non-positive values")
    return 1.0 - (target / base) ** (1.0 / years)


def main() -> None:
    """Write the US rate table."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cohort-year", type=int, default=2024, help="analysis (sale) year")
    year0: int = parser.parse_args().cohort_year

    ndc = next(r for r in csv.DictReader(NDC.open(newline="")) if r["country"] == COUNTRY)
    weo: dict[tuple[str, str, int], float] = {}
    weo_source = ""
    for r in csv.DictReader(WEO.open(newline="")):
        weo[(r["scenario"], r["sector"], int(r["year"]))] = float(r["value_mtco2"])
        weo_source = r["source_id"]

    out: list[dict[str, object]] = []
    fleet = read_series(EMISSIONS_US, COUNTRY, "car_ghg_co2e")
    grid = read_series(GRID, COUNTRY, "grid_intensity")
    for rate, series, what, source_id in (
        (
            "r_fleet",
            fleet,
            "observed passenger-car GHG (EPA inventory Table A-91)",
            "epa_ghg_inventory_2025_annexes",
        ),
        ("r_power", grid, "observed grid carbon intensity", "owid_ember_grid_intensity"),
    ):
        value, y0, y1 = log_linear_rate(series, year0)
        derivation = (
            f"Log-linear trend of {what}, {y0}-{y1} excluding "
            f"{TREND_EXCLUDE[0]}-{TREND_EXCLUDE[1]}."
        )
        if value < 0:
            derivation += f" OBSERVED_INCREASE: series rising ({value:+.4f}/yr)."
        out.append(
            {
                "country": COUNTRY,
                "scenario": "S1",
                "rate": rate,
                "value": round(value, 9),
                "target_level": "observed_trend",
                "base_year": y0,
                "target_year": y1,
                "derivation": derivation,
                "source_id": source_id,
            }
        )

    for rate in ("r_fleet", "r_power"):
        out.append(
            {
                "country": COUNTRY,
                "scenario": "S2",
                "rate": rate,
                "value": None,
                "target_level": "flag_no_ndc",
                "base_year": None,
                "target_year": None,
                "derivation": (
                    f"FLAG market: {ndc['note']} S2 is excluded from the headline and reported "
                    f"separately. Anchor verified: {ndc['verified']}."
                ),
                "source_id": ndc["source_id"],
            }
        )

    for rate, sector in (("r_fleet", "passenger_cars"), ("r_power", "electricity_heat")):
        base = weo[(S3_SCENARIO, sector, S3_BASE_YEAR)]
        target = weo[(S3_SCENARIO, sector, S3_TARGET_YEAR)]
        value = cagr_decline(base, target, S3_TARGET_YEAR - S3_BASE_YEAR)
        out.append(
            {
                "country": COUNTRY,
                "scenario": "S3",
                "rate": rate,
                "value": round(value, 9),
                "target_level": "world_prorata",
                "base_year": S3_BASE_YEAR,
                "target_year": S3_TARGET_YEAR,
                "derivation": (
                    f"IEA WEO 2024 {S3_SCENARIO} world {sector.replace('_', ' ')} CO2 "
                    f"{base:,.0f} -> {target:,.0f} Mt ({S3_BASE_YEAR}-{S3_TARGET_YEAR}), "
                    "compound annual decline applied pro-rata; no US-specific NZE path in the "
                    "report on hand."
                ),
                "source_id": weo_source,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    summary = ", ".join(
        f"{r['scenario']} {r['rate']} {r['value']}" for r in out if r["value"] is not None
    )
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows; {summary}; S2 flagged (no NDC in force)")


if __name__ == "__main__":
    main()
