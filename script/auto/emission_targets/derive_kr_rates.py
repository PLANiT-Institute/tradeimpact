"""Derive S1/S2/S3 annual decline rates for Korea (whitepaper §3.1, guideline §2.3).

Inputs
    country_emissions/processed/country_emissions_kr.csv        car_co2 (derived, tier C)
    country_emissions/processed/country_emissions_owid_grid.csv grid_intensity (KR)
    emission_targets/raw/kr_climate_targets.csv                 hand-transcribed policy anchors
Output
    emission_targets/processed/emission_targets_kr.csv

Scenarios
    S1 current trajectory   log-linear trend of observed road-transport CO2 (GIR 1.A.3.b) and of
                            grid intensity, 2015 onward excluding 2020-2021; the KOTSA car share is
                            not used for the trend because it drifts over time
    S2 committed policy     1st National Carbon Neutrality Basic Plan (2023): transport (1.A.3)
                            annual path 2023 -> 2030 (93.7 -> 61.0 MtCO2e) for the fleet; power
                            sector 2018 -> 2030 (269.6 -> 145.9 MtCO2e) for the grid, floored at
                            the observed S1 grid trend where that trend is already steeper
                            (committed policy is never read as less ambitious than what is
                            observed, the same rule as the EU27 build)
    S3 1.5C-aligned         2050 carbon-neutral scenarios (2021): transport 98.1 -> 2.8 MtCO2e
                            (A안) for the fleet; power 269.6 -> 20.7 (B안) for the grid, because
                            the A안 power endpoint is zero and a compound decline cannot reach it

Algorithm
    $$ r = 1 - \\left(\\frac{V_{target}}{V_{base}}\\right)^{1/(y_{target}-y_{base})} $$
    ASCII: r = 1 - (V_target / V_base) ** (1 / years); S1: ln V = a + b y, r = 1 - exp(b)
    V_base, V_target   sector emissions at the base and target year (MtCO2e)
    r                  annual fractional decline (1/year)

Run from the repository root:  .venv/bin/python script/auto/emission_targets/derive_kr_rates.py
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
EMISSIONS = DATA / "country_emissions" / "processed" / "country_emissions_kr.csv"
GRID = DATA / "country_emissions" / "processed" / "country_emissions_owid_grid.csv"
TARGETS = DATA / "emission_targets" / "raw" / "kr_climate_targets.csv"
OUT = DATA / "emission_targets" / "processed" / "emission_targets_kr.csv"

COUNTRY = "KR"
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
    """{year: value} of one series."""
    out: dict[int, float] = {}
    for r in csv.DictReader(path.open(newline="")):
        if r["country"] == country and r["series"] == series and r["value"]:
            out[int(r["year"])] = float(r["value"])
    return out


def log_linear_rate(series: dict[int, float], not_after: int) -> tuple[float, int, int]:
    """Annual decline from a log-linear fit over TREND_START..not_after excluding the gap years."""
    pts = [
        (y, math.log(v))
        for y, v in sorted(series.items())
        if TREND_START <= y <= not_after and y not in TREND_EXCLUDE and v > 0
    ]
    if len(pts) < 3:
        raise SystemExit(f"fewer than 3 observations for the trend: {pts}")
    n = len(pts)
    mx = sum(y for y, _ in pts) / n
    my = sum(v for _, v in pts) / n
    b = sum((y - mx) * (v - my) for y, v in pts) / sum((y - mx) ** 2 for y, _ in pts)
    return 1 - math.exp(b), pts[0][0], pts[-1][0]


def cagr_decline(base: float, target: float, years: int) -> float:
    """Compound annual decline from base to target over ``years``."""
    return 1 - (target / base) ** (1 / years)


def main() -> None:
    """Write the Korean rate table."""
    targets = {r["target_id"]: r for r in csv.DictReader(TARGETS.open(newline=""))}
    road = read_series(EMISSIONS, COUNTRY, "road_co2")
    grid = read_series(GRID, COUNTRY, "grid_intensity")
    out: list[dict[str, object]] = []

    s1: dict[str, float] = {}
    for rate, series, what, source in (
        (
            "r_fleet",
            road,
            "road-transport CO2 (GIR 1.A.3.b; the KOTSA passenger-car share drifts from 0.49 to "
            "0.58 over 2018-2024 and is not a stable observation, so the national road series "
            "carries the trend)",
            "gir_inventory_co2",
        ),
        ("r_power", grid, "grid carbon intensity", "owid_ember_grid_intensity"),
    ):
        value, y0, y1 = log_linear_rate(series, 2024)
        s1[rate] = value
        derivation = f"Log-linear trend of observed {what}, {y0}-{y1} excluding 2020-2021."
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
                "source_id": source,
            }
        )

    path = targets["kr_2030_transport_path"]
    fleet_s2 = cagr_decline(
        float(path["base_value"]),
        float(path["target_value"]),
        int(path["target_year"]) - int(path["base_year"]),
    )
    out.append(
        {
            "country": COUNTRY,
            "scenario": "S2",
            "rate": "r_fleet",
            "value": round(fleet_s2, 9),
            "target_level": "ndc_prorata",
            "base_year": path["base_year"],
            "target_year": path["target_year"],
            "derivation": (
                "1st National Carbon Neutrality Basic Plan (2023) transport (1.A.3) annual path "
                f"{path['base_value']} -> {path['target_value']} MtCO2e "
                f"({path['base_year']}-{path['target_year']}), "
                "compound annual decline applied pro-rata to passenger cars; 수송 covers road, "
                "domestic aviation, rail and navigation, not cars alone."
            ),
            "source_id": path["source_id"],
        }
    )
    power = targets["kr_2030_power"]
    power_s2 = cagr_decline(
        float(power["base_value"]),
        float(power["target_value"]),
        int(power["target_year"]) - int(power["base_year"]),
    )
    level, note = "ndc_prorata", ""
    if s1["r_power"] > power_s2:
        level = "ndc_prorata_s1_floor"
        note = (
            f" PATHWAY_ALREADY_MET: the pro-rata power rate {power_s2:.4f}/yr is below the "
            "observed "
            f"S1 grid trend {s1['r_power']:.4f}/yr, so S2 power is floored at the S1 trend."
        )
        power_s2 = s1["r_power"]
    out.append(
        {
            "country": COUNTRY,
            "scenario": "S2",
            "rate": "r_power",
            "value": round(power_s2, 9),
            "target_level": level,
            "base_year": power["base_year"],
            "target_year": power["target_year"],
            "derivation": (
                "1st National Carbon Neutrality Basic Plan (2023) power sector (전환) "
                f"{power['base_value']} -> {power['target_value']} MtCO2e "
                f"({power['base_year']}-{power['target_year']}), "
                "compound annual decline applied to grid intensity." + note
            ),
            "source_id": power["source_id"],
        }
    )

    for rate, key, label in (
        ("r_fleet", "kr_2050_transport_a", "transport (1.A.3) A안"),
        ("r_power", "kr_2050_power_b", "power sector (전환) B안"),
    ):
        t = targets[key]
        value = cagr_decline(
            float(t["base_value"]),
            float(t["target_value"]),
            int(t["target_year"]) - int(t["base_year"]),
        )
        out.append(
            {
                "country": COUNTRY,
                "scenario": "S3",
                "rate": rate,
                "value": round(value, 9),
                "target_level": "1p5c_prorata",
                "base_year": t["base_year"],
                "target_year": t["target_year"],
                "derivation": (
                    f"2050 carbon-neutral scenarios (2021) {label} {t['base_value']} -> "
                    f"{t['target_value']} "
                    f"MtCO2e ({t['base_year']}-{t['target_year']}), compound annual decline "
                    "applied pro-rata. "
                    + (
                        "B안 anchors the power rate because the A안 endpoint is zero."
                        if rate == "r_power"
                        else "B안 (9.2 MtCO2e) is the published upper end of the range."
                    )
                ),
                "source_id": t["source_id"],
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rows; "
        + ", ".join(f"{r['scenario']} {r['rate']} {r['value']}" for r in out)
    )


if __name__ == "__main__":
    main()
