"""Derive S1 and S2 annual decline rates for the United States (whitepaper §3.1, guideline §2.3).

Inputs
    country_emissions/processed/country_emissions_us.csv         ldv_ghg_co2e, ldv_co2 series
    country_emissions/processed/country_emissions_owid_grid.csv  US grid intensity
    emission_targets/raw/ndc_anchors.csv                         US NDC anchor (61% below 2005 by
                                                                 2035, the last NDC communicated)
Output
    emission_targets/processed/emission_targets_us.csv

Scenarios
    S1 current trajectory   log-linear trend of observed light-duty GHG (fleet) and grid
                            intensity (power), same window and exclusions as the EU27 derivation.
    S2 committed policy     the United States' own NDC applied pro-rata (``ndc_prorata``): each
                            series from its latest observation to (1 - reduction) x its 2005
                            level by 2035, floored at the S1 trend where that level is already
                            met. The country notified withdrawal from the Paris Agreement on
                            2025-01-27, so the anchor is the NDC communicated on 2024-12-19 —
                            the government's own stated pathway, and the only one it has ever
                            stated for 2035. The NDC's own text puts that range "on a straight
                            line or steeper trajectory to net zero emissions by 2050", which is
                            why holding the rate constant past 2035 across a vehicle lifetime is
                            not more ambitious than what was communicated.

Algorithm:
    $$ r = 1 - \\left(\\frac{V_{target}}{V_{base}}\\right)^{1/(y_{target}-y_{base})} $$
    ASCII: r = 1 - (V_target / V_base) ** (1 / (y_target - y_base)); S1: ln V = a + b y,
    r = 1 - exp(b)
    V in ktCO2e / ktCO2 (fleet) or gCO2 per kWh (power); r in 1/year, positive = decline.

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
OUT = DATA / "emission_targets" / "processed" / "emission_targets_us.csv"

COUNTRY = "US"
TREND_START = 2015
TREND_EXCLUDE = (2020, 2021)

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
            if r["country"] == country and r["series"] == series and r["value"]
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
    base_year, target_year = int(ndc["base_year"]), int(ndc["target_year"])
    reduction = float(ndc["reduction_vs_base"])

    out: list[dict[str, object]] = []
    fleet_ghg = read_series(EMISSIONS_US, COUNTRY, "ldv_ghg_co2e")
    fleet_co2 = read_series(EMISSIONS_US, COUNTRY, "ldv_co2")
    grid = read_series(GRID, COUNTRY, "grid_intensity")

    trends: dict[str, float] = {}
    for rate, series, what, source_id in (
        (
            "r_fleet",
            fleet_ghg,
            "observed light-duty vehicle GHG (EPA inventory Tables A-91 and A-93)",
            "epa_ghg_inventory_2025_annexes",
        ),
        ("r_power", grid, "observed grid carbon intensity", "owid_ember_grid_intensity"),
    ):
        value, y0, y1 = log_linear_rate(series, year0)
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

    # The pro-rata anchor needs the 2005 level. EPA prints the CO2e light-duty rows for 1990,
    # 2000 and 2013 onward only, so the ratio of levels is taken from the CO2 row, which is
    # printed for every year; the S1 trend keeps the CO2e series.
    for rate, series, unit, what, source_id in (
        (
            "r_fleet",
            fleet_co2,
            "kt",
            "light-duty vehicle CO2 (EPA inventory Table A-93; the CO2e row does not print 2005)",
            "epa_ghg_inventory_2025_annexes",
        ),
        (
            "r_power",
            grid,
            "gCO2/kWh",
            "grid carbon intensity (the US inventory tables on hand carry no power-sector series, "
            "so the economy-wide reduction is applied to intensity, not to absolute generation "
            "emissions: an intensity-only reading is looser than the absolute target wherever "
            "generation grows)",
            "owid_ember_grid_intensity",
        ),
    ):
        latest_year = max(y for y in series if y <= year0)
        target = series[base_year] * (1.0 - reduction)
        raw = cagr_decline(series[latest_year], target, target_year - latest_year)
        level, value = "ndc_prorata", raw
        text = (
            f"United States NDC communicated {ndc['communicated']}: {reduction:.0%} below "
            f"{base_year} net GHG by {target_year} (the low end of the published "
            f"{reduction:.0%}-{float(ndc['reduction_upper']):.0%} range; the range is not "
            f"propagated), applied pro-rata to {what}: {series[latest_year]:,.1f} {unit} "
            f"({latest_year}) -> {target:,.1f} {unit}, compound annual decline. Anchor "
            f"verified: {ndc['verified']}."
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
                "source_id": f"{ndc['source_id']};{source_id}",
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
