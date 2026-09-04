"""Derive S1 and S2 annual decline rates for Japan (whitepaper §3.1, guideline §2.3).

Inputs
    country_emissions/processed/country_emissions_jp.csv          road CO2 by segment (GIO/NIES)
    country_emissions/processed/country_emissions_owid_grid.csv   JP grid intensity
    emission_targets/raw/jp_climate_targets.csv                   GX / NDC anchors
Output
    emission_targets/processed/emission_targets_jp.csv

Scenarios
    S1 current trajectory   log-linear trend of observed road-transport CO2 (passenger road plus
                            goods vehicles, GIO/NIES sheet 3) and of grid intensity, 2015 onward
                            excluding 2020-2021, the same window as every other market.
    S2 committed policy     the target the cabinet adopted on 2025-02-18 as the GX 2040 Vision and
                            the Plan for Global Warming Countermeasures, and communicated
                            as Japan's NDC: 73 % below
                            FY2013 by FY2040, "on a straight pathway towards the achievement of
                            net zero by 2050". Applied pro-rata: each series runs from its latest
                            observation to 27 % of its FY2013 level by 2040. The 2035 anchor
                            (60 %) is recorded but not used, because 2040 is the further year and
                            a car sold today is driven past 2035.

Two things this build discloses rather than hides. Japan's targets are on FISCAL years (April to
March) and so is the inventory, while grid intensity is calendar — the fiscal label is treated as
the year, which shifts the power leg by a quarter, not by a year. And FY2013 is Japan's
post-Fukushima peak for electricity, every reactor being offline, so a 2013-based pro-rata is
easier on the grid than on any other sector; the S1 floor below keeps S2 from reading as less
ambitious than the observed trend.

Algorithm
    $$ r = 1 - \\left(\\frac{V_{target}}{V_{base}}\\right)^{1/(y_{target}-y_{base})} $$
    ASCII: r = 1 - (V_target / V_base) ** (1 / years); S1: ln V = a + b y, r = 1 - exp(b)
    V in ktCO2 (road) or gCO2 per kWh (grid); r in 1/year, positive = decline.

Run from the repository root:  .venv/bin/python script/auto/emission_targets/derive_jp_rates.py
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
EMISSIONS = DATA / "country_emissions" / "processed" / "country_emissions_jp.csv"
GRID = DATA / "country_emissions" / "processed" / "country_emissions_owid_grid.csv"
TARGETS = DATA / "emission_targets" / "raw" / "jp_climate_targets.csv"
OUT = DATA / "emission_targets" / "processed" / "emission_targets_jp.csv"

COUNTRY = "JP"
TREND_START = 2015
TREND_EXCLUDE = (2020, 2021)
ANCHOR = "jp_2040_economy"
#: the road series the fleet trend and the fleet pro-rata are built from, summed.
ROAD_SERIES = ("road_co2_passenger", "co2_freight")
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
    """{year: value} of one country x series."""
    with path.open(newline="") as f:
        return {
            int(r["year"]): float(r["value"])
            for r in csv.DictReader(f)
            if r["country"] == country and r["series"] == series and r["value"]
        }


def summed(path: Path, country: str, names: tuple[str, ...]) -> dict[int, float]:
    """{year: sum of the named series}, keeping only years every series covers."""
    parts = [read_series(path, country, name) for name in names]
    years = set(parts[0])
    for part in parts[1:]:
        years &= set(part)
    return {y: sum(part[y] for part in parts) for y in sorted(years)}


def log_linear_rate(series: dict[int, float], not_after: int) -> tuple[float, int, int]:
    """Annual decline from a log-linear fit over the trend window."""
    points = [
        (y, math.log(v))
        for y, v in sorted(series.items())
        if TREND_START <= y <= not_after and y not in TREND_EXCLUDE and v > 0
    ]
    if len(points) < 4:
        raise SystemExit(f"only {len(points)} usable trend points; four are required")
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(v for _, v in points) / n
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    sxy = sum((x - mean_x) * (v - mean_y) for x, v in points)
    return 1.0 - math.exp(sxy / sxx), points[0][0], points[-1][0]


def cagr_decline(base: float, target: float, years: int) -> float:
    """Annual decline fraction taking ``base`` to ``target`` over ``years``."""
    if base <= 0 or target <= 0 or years <= 0:
        raise SystemExit("cannot derive a decline rate from non-positive values")
    return 1.0 - (target / base) ** (1.0 / years)


def main() -> None:
    """Write the Japanese rate table."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cohort-year", type=int, default=2024, help="analysis (sale) year")
    year0: int = parser.parse_args().cohort_year

    targets = {r["target_id"]: r for r in csv.DictReader(TARGETS.open(newline=""))}
    anchor = targets[ANCHOR]
    base_year, target_year = int(anchor["base_year"]), int(anchor["target_year"])
    reduction = float(anchor["reduction_vs_base"])

    road = summed(EMISSIONS, COUNTRY, ROAD_SERIES)
    grid = read_series(GRID, COUNTRY, "grid_intensity")

    out: list[dict[str, object]] = []
    trends: dict[str, float] = {}
    for rate, series, what, source_id in (
        (
            "r_fleet",
            road,
            "observed road-transport CO2 (GIO/NIES sheet 3, passenger road plus goods vehicles; "
            "the vehicle-kilometre denominator exists for two fiscal years only, so the national "
            "road series carries the trend, as in the Korean build)",
            "gio_nies_inventory",
        ),
        ("r_power", grid, "observed grid carbon intensity", "owid_ember_grid_intensity"),
    ):
        value, y0, y1 = log_linear_rate(series, year0 + 1)
        trends[rate] = value
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

    for rate, series, unit, what, source_id in (
        ("r_fleet", road, "kt", "road-transport CO2", "gio_nies_inventory"),
        (
            "r_power",
            grid,
            "gCO2/kWh",
            "grid carbon intensity (FY2013 is the post-Fukushima peak, so this leg is the "
            "easiest of the pro-rata legs)",
            "owid_ember_grid_intensity",
        ),
    ):
        latest_year = max(y for y in series if y <= year0 + 1)
        target = series[base_year] * (1.0 - reduction)
        raw = cagr_decline(series[latest_year], target, target_year - latest_year)
        level, value = "gx_2040_prorata", raw
        text = (
            f"Japan {reduction:.0%} below FY{base_year} by FY{target_year} (GX 2040 Vision and "
            "Plan for Global Warming Countermeasures, cabinet decision 2025-02-18, "
            "communicated as Japan's NDC), "
            f"applied pro-rata to {what}: {series[latest_year]:,.1f} {unit} ({latest_year}) -> "
            f"{target:,.1f} {unit}, compound annual decline. Anchor verified: yes."
        )
        if raw <= trends[rate]:
            level, value = "gx_2040_prorata_s1_floor", max(trends[rate], 0.0)
            text += (
                f" PATHWAY_ALREADY_MET (implied {raw:+.4f}/yr): floored at the observed S1 trend "
                f"{value:+.4f}/yr, because committed policy is never read as less ambitious than "
                "what is observed."
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
                "source_id": f"{anchor['source_id']};{source_id}",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    summary = ", ".join(f"{r['scenario']} {r['rate']} {r['value']}" for r in out)
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows; {summary}")


if __name__ == "__main__":
    main()
