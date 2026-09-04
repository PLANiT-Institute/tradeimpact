"""Derive S1 and S2 annual decline rates per EU27 market (whitepaper §3.1, guideline §2.3 B).

Inputs
    data/auto/emission_targets/raw/eu_climate_targets.csv   EU policy anchors (hand-transcribed
                                                            from legislation; links in method.md)
    data/auto/country_emissions/processed/country_emissions_eu27.csv
    data/auto/vehicle_usage/processed/vehicle_usage_eu27.csv
Output
    data/auto/emission_targets/processed/emission_targets_eu27.csv

Scenarios
    S1 current trajectory   log-linear trend of observed per-car CO2 (fleet) and of grid
                            intensity (power) over the trend window, pandemic years excluded.
    S2 committed policy     EU-wide pro-rata against the European Climate Law's furthest
                            target, 90% below 1990 by 2040: transport from its 2023 level, and
                            public electricity CO2 from its latest observation. The 2040 anchor
                            is used rather than the 2030 one so that a car's whole operating life
                            (up to 25 years) sits inside the target horizon. Where the power rate
                            comes out negative (target already met) it is floored at each
                            market's observed S1 grid trend and flagged: committed policy is
                            never read as less ambitious than the current trajectory.

Algorithm:
    $$ r = 1 - \\left(\\frac{V_{target}}{V_{base}}\\right)^{1/(y_{target}-y_{base})} $$
    ASCII: r = 1 - (V_target / V_base) ** (1 / (y_target - y_base))
    where V are emissions in the same unit and y are calendar years; the S1 trend fits
    ln V = a + b*y and reports r = 1 - exp(b). r > 0 means decline, r in 1/year.

Run from the repository root:
    .venv/bin/python script/auto/emission_targets/derive_eu27_rates.py
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "emission_targets"
TARGETS = DATASET / "raw" / "eu_climate_targets.csv"
EMISSIONS = (
    REPO / "data" / "auto" / "country_emissions" / "processed" / "country_emissions_eu27.csv"
)
USAGE = REPO / "data" / "auto" / "vehicle_usage" / "processed" / "vehicle_usage_eu27.csv"
OUT = DATASET / "processed" / "emission_targets_eu27.csv"

EU = "EU27"
# Trend window: pandemic mobility and generation are not a policy trend.
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


def read_long(path: Path) -> dict[tuple[str, str], dict[int, float]]:
    """(country, series) -> {year: value} from a long-format CSV."""
    out: dict[tuple[str, str], dict[int, float]] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            out.setdefault((row["country"], row["series"]), {})[int(row["year"])] = float(
                row["value"]
            )
    return out


def latest(series: dict[int, float], not_after: int) -> tuple[int, float] | None:
    """Most recent (year, value) at or before ``not_after``."""
    pairs = [(y, v) for y, v in series.items() if y <= not_after]
    return max(pairs) if pairs else None


def cagr_decline(base: float, target: float, years: int) -> float:
    """Annual decline fraction taking ``base`` to ``target`` over ``years`` (1/year)."""
    if base <= 0 or target <= 0 or years <= 0:
        raise ValueError("cannot derive a decline rate from non-positive values")
    return 1.0 - (target / base) ** (1.0 / years)


def log_linear_rate(series: dict[int, float], not_after: int) -> tuple[float, int, int] | None:
    """Fit ln(value) = a + b*year; return (1 - exp(b), first year, last year) or None."""
    points = [
        (y, v)
        for y, v in series.items()
        if TREND_START <= y <= not_after and y not in TREND_EXCLUDE and v > 0
    ]
    if len(points) < 4:
        return None
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(math.log(v) for _, v in points) / n
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    if sxx == 0:
        return None
    sxy = sum((x - mean_x) * (math.log(v) - mean_y) for x, v in points)
    return 1.0 - math.exp(sxy / sxx), min(x for x, _ in points), max(x for x, _ in points)


def main() -> None:
    """Write one row per country x scenario x rate (r_fleet, r_power)."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cohort-year", type=int, default=2024, help="analysis (sale) year")
    args = parser.parse_args()
    cohort_year: int = args.cohort_year

    targets = {row["target_id"]: row for row in csv.DictReader(TARGETS.open(newline=""))}
    emissions = read_long(EMISSIONS)
    usage = read_long(USAGE)

    transport_1990 = emissions[(EU, "transport_ghg")][1990]
    power = emissions[(EU, "power_co2")]
    power_1990 = power[1990]
    power_year, power_now = latest(power, cohort_year) or (None, None)
    if power_year is None:
        raise SystemExit("EU27 power_co2 has no observation at or before the cohort year")

    t40, tr = targets["eu_2040_economy"], targets["eu_2030_transport"]
    # The committed pathway is taken to the furthest year the European Climate Law sets, so a
    # car's whole operating life sits inside the target horizon instead of extrapolating a
    # seven-year window over two decades.
    r_fleet_s2 = cagr_decline(
        float(tr["base_value"]),
        transport_1990 * (1.0 - float(t40["reduction_vs_base"])),
        int(t40["target_year"]) - int(tr["base_year"]),
    )
    r_power_s2_raw = cagr_decline(
        power_now,
        power_1990 * (1.0 - float(t40["reduction_vs_base"])),
        int(t40["target_year"]) - power_year,
    )
    power_flag = ""
    r_power_s2 = r_power_s2_raw
    if r_power_s2_raw <= 0:
        r_power_s2 = 0.0
        power_flag = (
            f" PATHWAY_ALREADY_MET: EU public electricity CO2 in {power_year} "
            f"({power_now / 1000:.0f} Mt) is below the pro-rata 2040 level "
            f"({power_1990 * (1 - float(t40['reduction_vs_base'])) / 1000:.0f} Mt); implied rate "
            f"{r_power_s2_raw:+.4f}/yr. Committed policy cannot be less ambitious than the "
            "current trajectory, so S2 power is floored at each market's observed S1 grid trend."
        )

    eu_rows = [
        (
            "S2",
            "r_fleet",
            r_fleet_s2,
            int(tr["base_year"]),
            int(t40["target_year"]),
            "EU transport 2023 level to 10% of its 1990 level by 2040 (the European Climate Law's "
            "furthest target, 90% below 1990, applied pro-rata to transport), compound annual "
            "decline applied to every member state's car fleet.",
            f"{t40['source_id']};eurostat_env_air_gge_crf1a3",
        ),
        (
            "S2",
            "r_power",
            r_power_s2,
            power_year,
            int(t40["target_year"]),
            "EU public electricity and heat CO2 from its latest observation to 10% of 1990 by "
            "2040, compound annual decline." + power_flag,
            f"{t40['source_id']};eurostat_env_air_gge_crf1a1a",
        ),
    ]

    countries = sorted({c for (c, s) in emissions if s == "car_co2" and c != EU})
    out: list[dict[str, object]] = []
    skipped: list[str] = []
    for country in countries:
        co2 = emissions.get((country, "car_co2"), {})
        stock = usage.get((country, "car_stock"), {})
        per_car = {y: v * 1e9 / stock[y] for y, v in co2.items() if stock.get(y)}
        fleet_trend = log_linear_rate(per_car, cohort_year)
        grid_trend = log_linear_rate(emissions.get((country, "grid_intensity"), {}), cohort_year)
        if fleet_trend is None or grid_trend is None:
            skipped.append(country)
            continue
        for rate, (value, y0, y1), what, source_id in (
            (
                "r_fleet",
                fleet_trend,
                "observed CO2 per registered car (inventory CRF 1.A.3.b.i / car stock)",
                "eurostat_env_air_gge_crf1a3b1;eurostat_road_eqs_carpda",
            ),
            ("r_power", grid_trend, "observed grid carbon intensity", "owid_ember_grid_intensity"),
        ):
            derivation = (
                f"Log-linear trend of {what}, {y0}-{y1} excluding "
                f"{TREND_EXCLUDE[0]}-{TREND_EXCLUDE[1]}."
            )
            if value < 0:
                derivation += (
                    f" OBSERVED_INCREASE: the series is rising ({value:+.4f}/yr), so the S1 "
                    "benchmark grows over the lifetime and no crossover can occur."
                )
            out.append(
                {
                    "country": country,
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
        for scenario, rate, value, y0, y1, derivation, source_id in eu_rows:
            target_level = "ndc_prorata"
            if scenario == "S2" and rate == "r_power" and power_flag:
                value = max(grid_trend[0], 0.0)
                target_level = "ndc_prorata_s1_floor"
                derivation += (
                    f" Applied here as the observed grid trend {value:+.4f}/yr "
                    f"({grid_trend[1]}-{grid_trend[2]})."
                )
            out.append(
                {
                    "country": country,
                    "scenario": scenario,
                    "rate": rate,
                    "value": round(value, 9),
                    "target_level": target_level,
                    "base_year": y0,
                    "target_year": y1,
                    "derivation": derivation,
                    "source_id": source_id,
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out)
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rows, {len(countries) - len(skipped)} countries; "
        f"r_fleet S2 {r_fleet_s2:.4f}; r_power S2 {r_power_s2:.4f}"
        + (f"; skipped (no trend): {skipped}" if skipped else "")
    )


if __name__ == "__main__":
    main()
