"""Derive S1/S2/S3 annual decline rates for Australia (whitepaper §3.1, guideline §2.3).

Inputs
    country_emissions/processed/country_emissions_au.csv        car_co2, power_co2 (ANGA inventory)
    country_emissions/processed/country_emissions_owid_grid.csv AU grid intensity
    emission_targets/raw/ndc_anchors.csv                        AU NDC anchor (43% below 2005, 2030)
    emission_targets/raw/iea_weo_2024_world_co2.csv             IEA WEO world NZE anchors
Output
    emission_targets/processed/emission_targets_au.csv

Scenarios
    S1  log-linear trend of observed passenger-car CO2 (fleet) and grid intensity (power),
        2015 onward, pandemic years excluded — same window as the EU27 and US derivations.
    S2  economy-wide NDC applied pro-rata (``ndc_prorata``): each sector from its latest
        observation to (1 - reduction) x its 2005 level by the target year; floored at the S1
        trend where the pro-rata level is already met. The anchor row carries ``verified``;
        the value is printed into the derivation so an unverified anchor is visible.
    S3  world NZE pro-rata 2023 -> 2040 (``world_prorata``), as for the United States.

Algorithm:
    $$ r = 1 - \\left(\\frac{V_{target}}{V_{base}}\\right)^{1/(y_{target}-y_{base})} $$
    ASCII: r = 1 - (V_target/V_base) ** (1/(y_target - y_base)); S1: ln V = a + b y, r = 1 - e^b
    V in ktCO2 (AU) or MtCO2 (world), gCO2 per kWh for grid; r in 1/year, positive = decline.

Run from the repository root:  .venv/bin/python script/auto/emission_targets/derive_au_rates.py
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
EMISSIONS = DATA / "country_emissions" / "processed" / "country_emissions_au.csv"
GRID = DATA / "country_emissions" / "processed" / "country_emissions_owid_grid.csv"
NDC = DATA / "emission_targets" / "raw" / "ndc_anchors.csv"
WEO = DATA / "emission_targets" / "raw" / "iea_weo_2024_world_co2.csv"
OUT = DATA / "emission_targets" / "processed" / "emission_targets_au.csv"

COUNTRY = "AU"
TREND_START = 2015
TREND_EXCLUDE = (2020, 2021)
S3_BASE_YEAR, S3_TARGET_YEAR, S3_SCENARIO = 2023, 2040, "NZE"
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


def read_series(path: Path, series: str) -> dict[int, float]:
    """{year: value} for AU x series from a long-format CSV."""
    with path.open(newline="") as f:
        return {
            int(r["year"]): float(r["value"])
            for r in csv.DictReader(f)
            if r["country"] == COUNTRY and r["series"] == series
        }


def log_linear_rate(series: dict[int, float], not_after: int) -> tuple[float, int, int]:
    """Fit ln(value) = a + b*year in the trend window; return (1 - exp(b), first, last)."""
    pts = [
        (y, v)
        for y, v in series.items()
        if TREND_START <= y <= not_after and y not in TREND_EXCLUDE and v > 0
    ]
    if len(pts) < 4:
        raise SystemExit(f"only {len(pts)} usable trend points; four are required")
    n = len(pts)
    mx = sum(x for x, _ in pts) / n
    my = sum(math.log(v) for _, v in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    sxy = sum((x - mx) * (math.log(v) - my) for x, v in pts)
    return 1.0 - math.exp(sxy / sxx), min(x for x, _ in pts), max(x for x, _ in pts)


def cagr_decline(base: float, target: float, years: int) -> float:
    """Annual decline fraction taking ``base`` to ``target`` over ``years``."""
    if base <= 0 or target <= 0 or years <= 0:
        raise SystemExit("cannot derive a decline rate from non-positive values")
    return 1.0 - (target / base) ** (1.0 / years)


def main() -> None:
    """Write the AU rate table."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cohort-year", type=int, default=2024)
    year0: int = parser.parse_args().cohort_year

    ndc = next(r for r in csv.DictReader(NDC.open(newline="")) if r["country"] == COUNTRY)
    weo: dict[tuple[str, str, int], float] = {}
    for r in csv.DictReader(WEO.open(newline="")):
        weo[(r["scenario"], r["sector"], int(r["year"]))] = float(r["value_mtco2"])
    car = read_series(EMISSIONS, "car_co2")
    power = read_series(EMISSIONS, "power_co2")
    grid = read_series(GRID, "grid_intensity")

    out: list[dict[str, object]] = []
    trends = {}
    for rate, series, what, sid in (
        (
            "r_fleet",
            car,
            "observed passenger-car CO2 (ANGA inventory)",
            "anga_odata_paris_inventory",
        ),
        ("r_power", grid, "observed grid carbon intensity", "owid_ember_grid_intensity"),
    ):
        value, y0, y1 = log_linear_rate(series, year0)
        trends[rate] = value
        text = (
            f"Log-linear trend of {what}, {y0}-{y1} excluding "
            f"{TREND_EXCLUDE[0]}-{TREND_EXCLUDE[1]}."
        )
        if value < 0:
            text += f" OBSERVED_INCREASE: series rising ({value:+.4f}/yr)."
        out.append(
            {
                "country": COUNTRY,
                "scenario": "S1",
                "rate": rate,
                "value": round(value, 9),
                "target_level": "observed_trend",
                "base_year": y0,
                "target_year": y1,
                "derivation": text,
                "source_id": sid,
            }
        )

    base_year, target_year = int(ndc["base_year"]), int(ndc["target_year"])
    reduction = float(ndc["reduction_vs_base"])
    for rate, series, sid in (
        ("r_fleet", car, "anga_odata_paris_inventory"),
        ("r_power", power, "anga_odata_paris_inventory"),
    ):
        latest_year = max(y for y in series if y <= year0)
        target = series[base_year] * (1.0 - reduction)
        raw = cagr_decline(series[latest_year], target, target_year - latest_year)
        level, value = "ndc_prorata", raw
        text = (
            f"Australia NDC {reduction:.0%} below {base_year} by {target_year}, applied pro-rata "
            f"to this sector: {series[latest_year]:,.0f} kt ({latest_year}) -> {target:,.0f} kt, "
            f"compound annual decline. Anchor verified: {ndc['verified']}."
        )
        if raw <= 0:
            level, value = "ndc_prorata_s1_floor", max(trends[rate], 0.0)
            text += (
                f" PATHWAY_ALREADY_MET (implied {raw:+.4f}/yr): floored at the observed S1 trend "
                f"{value:+.4f}/yr."
            )
        out.append(
            {
                "country": COUNTRY,
                "scenario": "S2",
                "rate": rate,
                "value": round(value, 9),
                "target_level": level,
                "base_year": latest_year,
                "target_year": target_year,
                "derivation": text,
                "source_id": f"{ndc['source_id']};{sid}",
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
                    "compound annual decline applied pro-rata; no Australia-specific "
                    "NZE path in the report on hand."
                ),
                "source_id": "iea_weo_2024",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print(
        f"{OUT.relative_to(REPO)}: "
        + "; ".join(f"{r['scenario']} {r['rate']} {r['value']}" for r in out)
    )


if __name__ == "__main__":
    main()
