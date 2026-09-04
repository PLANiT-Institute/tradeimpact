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
    S2 committed policy     the 2050 Carbon Neutrality Scenarios (2021), the government's own
                            pathway to net zero: transport 98.1 -> 2.8 MtCO2e (scenario A) for
                            the fleet; power 269.6 -> 20.7 MtCO2e (scenario B) for the grid,
                            because the scenario-A power endpoint
                            is zero and a compound decline cannot reach zero. The 2030 NDC waypoint
                            is not used to set the rate: a vehicle sold today is driven for 11 to
                            25 years, so a rate fitted to a 7-year window and then extrapolated
                            over a lifetime would describe a policy nobody stated. Floored at the
                            observed S1 grid trend where that trend is already steeper (committed
                            policy is never read as less ambitious than what is observed, the same
                            rule as the EU27 build).

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

    for rate, key, label, note_extra in (
        (
            "r_fleet",
            "kr_2050_transport_a",
            "transport, scenario A",
            "The transport sector covers road, domestic aviation, rail and navigation, not "
            "cars alone.",
        ),
        (
            "r_power",
            "kr_2050_power_b",
            "power sector, scenario B",
            "Scenario B anchors the power rate because the scenario-A endpoint is zero.",
        ),
    ):
        t = targets[key]
        value = cagr_decline(
            float(t["base_value"]),
            float(t["target_value"]),
            int(t["target_year"]) - int(t["base_year"]),
        )
        level, floor_note = "net_zero_2050", ""
        if rate == "r_power" and s1["r_power"] > value:
            level = "net_zero_2050_s1_floor"
            floor_note = (
                f" PATHWAY_ALREADY_MET: the pathway power rate {value:.4f}/yr is below the "
                f"observed S1 grid trend {s1['r_power']:.4f}/yr, so S2 power is floored at the "
                "S1 trend."
            )
            value = s1["r_power"]
        out.append(
            {
                "country": COUNTRY,
                "scenario": "S2",
                "rate": rate,
                "value": round(value, 9),
                "target_level": level,
                "base_year": t["base_year"],
                "target_year": t["target_year"],
                "derivation": (
                    f"2050 Carbon Neutrality Scenarios (2021) {label} {t['base_value']} -> "
                    f"{t['target_value']} MtCO2e ({t['base_year']}-{t['target_year']}), compound "
                    "annual decline applied pro-rata over the whole vehicle-lifetime horizon. "
                    + note_extra
                    + floor_note
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
