"""Step 3 — destination parameters and the dynamic reference benchmark per EU27 market.

Inputs (processed datasets)
    vehicle_usage/processed/vehicle_usage_eu27.csv          stock, traffic, age bands
    country_emissions/processed/country_emissions_eu27.csv  car CO2, grid intensity
    emission_targets/processed/emission_targets_eu27.csv    S1/S2/S3 r_fleet, r_power
Outputs (data/auto/output/)
    destination_parameters_eu27.csv   per market: distance, fleet intensity base, grid, lifetime,
                                      each with tier, reference year, derivation and warnings
    reference_trajectories_eu27.csv   per market x scenario x year: E_ref(t) and G(t)

Algorithm (whitepaper §3.1, guideline §2.3 Method B):
    $$ I_{fleet,c}(0) = \\frac{CO2_{cars,c}}{N_c \\cdot D_c},\\quad
       E_{ref,c}(t) = I_{fleet,c}(0)\\,(1-r_{fleet,c,S})^{t}\\, D_c,\\quad
       G_c(t) = G_c(0)\\,(1-r_{power,c,S})^{t} $$
    ASCII: I0 = co2_kt*1e9/(stock*vkt) [gCO2/km]; E_ref(t) = I0/1000*(1-r_fleet)^t*vkt
           [kgCO2e per vehicle-year]; G(t) = G0/1000*(1-r_power)^t [kgCO2e/kWh]
    CO2_cars,c  national passenger-car CO2 (ktCO2, inventory CRF 1.A.3.b.i)
    N_c         registered passenger-car stock (vehicles)
    D_c         annual distance per car (km/year), t years after the sale year

Run from the repository root:  .venv/bin/python script/auto/model/build_reference.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
USAGE = DATA / "vehicle_usage" / "processed" / "vehicle_usage_eu27.csv"
EMISSIONS = DATA / "country_emissions" / "processed" / "country_emissions_eu27.csv"
TARGETS = DATA / "emission_targets" / "processed" / "emission_targets_eu27.csv"
OUT_DIR = DATA / "output"
OUT_PARAMS = OUT_DIR / "destination_parameters_eu27.csv"
OUT_REF = OUT_DIR / "reference_trajectories_eu27.csv"

EU = "EU27"
SCENARIOS = ("S1", "S2", "S3")
# Plausibility bands: outside them the traffic/stock or inventory/stock series describe
# different populations, so the value is not published as a clean national parameter.
VKT_MIN_KM, VKT_MAX_KM = 3_000.0, 30_000.0
FLEET_INTENSITY_MIN, FLEET_INTENSITY_MAX = 80.0, 320.0
# Operating life bracketed by the stock-weighted mean age: at least the mean age (exponential
# scrappage), at most twice it (single retirement age); central = midpoint.
LIFETIME_MIN_Y, LIFETIME_MAX_Y = 10, 25
LIFETIME_CENTRAL_MULTIPLE = 1.5
# Eurostat age-band midpoints (years); the open top band is closed at 25.
AGE_BAND_MIDPOINT = {
    "car_stock_age_y_lt2": 1.0,
    "car_stock_age_y2-5": 3.5,
    "car_stock_age_y5-10": 7.5,
    "car_stock_age_y10-20": 15.0,
    "car_stock_age_y_gt20": 25.0,
}
POOLED_MIN_CONTRIBUTORS = 15

PARAM_FIELDS = [
    "country",
    "cohort_year",
    "vkt_km",
    "vkt_low_km",
    "vkt_high_km",
    "vkt_tier",
    "vkt_year",
    "vkt_derivation",
    "car_stock",
    "car_stock_year",
    "car_co2_kt",
    "car_co2_year",
    "fleet_intensity_gco2_km",
    "fleet_intensity_tier",
    "grid_gco2_kwh",
    "grid_year",
    "grid_tier",
    "mean_car_age_years",
    "mean_car_age_year",
    "mean_car_age_tier",
    "lifetime_years",
    "lifetime_low_years",
    "lifetime_high_years",
    "warnings",
    "source_ids",
]
REF_FIELDS = [
    "country",
    "scenario",
    "t",
    "calendar_year",
    "r_fleet",
    "r_power",
    "fleet_intensity_gco2_km",
    "e_ref_kgco2_per_vehicle",
    "grid_kgco2_per_kwh",
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


def clamp_life(years: float) -> int:
    """Round and clamp a lifetime to the plausible band."""
    return int(min(LIFETIME_MAX_Y, max(LIFETIME_MIN_Y, round(years))))


def age_bands_by_year(
    usage: dict[tuple[str, str], dict[int, float]], country: str
) -> dict[int, dict[str, float]]:
    """{year: {band: stock}} restricted to years reporting the whole partition."""
    by_year: dict[int, dict[str, float]] = {}
    for band in AGE_BAND_MIDPOINT:
        for year, value in usage.get((country, band), {}).items():
            by_year.setdefault(year, {})[band] = value
    return {y: b for y, b in by_year.items() if AGE_BAND_MIDPOINT.keys() <= b.keys()}


def mean_age(by_year: dict[int, dict[str, float]], not_after: int) -> tuple[float, int] | None:
    """Stock-weighted mean age from the latest complete year (stock is published a year ahead)."""
    for year in sorted(by_year, reverse=True):
        if year > not_after + 1:
            continue
        bands = by_year[year]
        total = sum(bands.values())
        if total > 0:
            return sum(m * bands[b] for b, m in AGE_BAND_MIDPOINT.items()) / total, year
    return None


def pooled_age_bands(
    usage: dict[tuple[str, str], dict[int, float]], countries: list[str], not_after: int
) -> dict[int, dict[str, float]]:
    """Sum the complete age partitions of the member states that report them."""
    per_year: dict[int, dict[str, float]] = {}
    contributors: dict[int, int] = {}
    for country in countries:
        for year, bands in age_bands_by_year(usage, country).items():
            if year > not_after + 1:
                continue
            bucket = per_year.setdefault(year, dict.fromkeys(AGE_BAND_MIDPOINT, 0.0))
            for band in AGE_BAND_MIDPOINT:
                bucket[band] += bands[band]
            contributors[year] = contributors.get(year, 0) + 1
    usable = [y for y, n in contributors.items() if n >= POOLED_MIN_CONTRIBUTORS]
    return {max(usable): per_year[max(usable)]} if usable else {}


def quantile(values: list[float], q: float) -> float:
    """Linear-interpolated quantile of a sorted list."""
    position = q * (len(values) - 1)
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def main() -> None:
    """Build destination parameters and reference trajectories for every EU27 market."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cohort-year", type=int, default=2024, help="analysis (sale) year")
    args = parser.parse_args()
    year0: int = args.cohort_year

    usage = read_long(USAGE)
    emissions = read_long(EMISSIONS)
    rates: dict[tuple[str, str, str], float] = {}
    with TARGETS.open(newline="") as f:
        for row in csv.DictReader(f):
            rates[(row["country"], row["scenario"], row["rate"])] = float(row["value"])

    countries = sorted({c for (c, s) in emissions if s == "car_co2" and c != EU})
    pooled = pooled_age_bands(usage, countries, year0)

    rows: list[dict[str, object]] = []
    for c in countries:
        stock = latest(usage.get((c, "car_stock"), {}), year0)
        traffic = latest(usage.get((c, "car_traffic"), {}), year0)
        co2 = latest(emissions.get((c, "car_co2"), {}), year0)
        grid = latest(emissions.get((c, "grid_intensity"), {}), year0)
        warnings: list[str] = []
        sources = [
            "eurostat_road_eqs_carpda",
            "eurostat_env_air_gge_crf1a3b1",
            "owid_ember_grid_intensity",
            "eurostat_road_eqs_carage",
        ]

        vkt = vkt_year = vkt_tier = None
        vkt_derivation = ""
        if stock and traffic:
            candidate = traffic[1] * 1e6 / stock[1]
            if VKT_MIN_KM <= candidate <= VKT_MAX_KM:
                vkt, vkt_year = candidate, traffic[0]
                vkt_tier = "A" if traffic[0] >= year0 - 2 else "B"
                vkt_derivation = (
                    "Eurostat road_tf_veh (TER_REGNAT) car vehicle-kilometres divided by the "
                    "registered car stock."
                )
                sources.insert(0, "eurostat_road_tf_veh")

        age = mean_age(age_bands_by_year(usage, c), year0)
        age_tier = "A"
        if age is None and pooled:
            age, age_tier = mean_age(pooled, year0), "C"
        elif age is not None and age[1] < year0 - 2:
            age_tier = "B"

        rows.append(
            {
                "country": c,
                "cohort_year": year0,
                "vkt_km": vkt,
                "vkt_low_km": None,
                "vkt_high_km": None,
                "vkt_tier": vkt_tier,
                "vkt_year": vkt_year,
                "vkt_derivation": vkt_derivation,
                "car_stock": stock[1] if stock else None,
                "car_stock_year": stock[0] if stock else None,
                "car_co2_kt": co2[1] if co2 else None,
                "car_co2_year": co2[0] if co2 else None,
                "grid_gco2_kwh": grid[1] if grid else None,
                "grid_year": grid[0] if grid else None,
                "grid_tier": "A" if grid else None,
                "mean_car_age_years": age[0] if age else None,
                "mean_car_age_year": age[1] if age else None,
                "mean_car_age_tier": age_tier if age else None,
                "_warnings": warnings,
                "_sources": sources,
            }
        )

    # EU-average distance (stock-weighted over measured markets) stands in for the rest.
    measured = [r for r in rows if r["vkt_km"] and r["car_stock"]]
    if measured:
        fallback = sum(r["vkt_km"] * r["car_stock"] for r in measured) / sum(  # type: ignore[operator]
            r["car_stock"]
            for r in measured  # type: ignore[misc]
        )
        sorted_vkt = sorted(float(r["vkt_km"]) for r in measured)  # type: ignore[arg-type]
        band: tuple[float | None, float | None] = (None, None)
        if len(sorted_vkt) >= 4:
            band = (quantile(sorted_vkt, 0.25), quantile(sorted_vkt, 0.75))
        for r in rows:
            if r["vkt_km"] is None:
                r["vkt_km"], r["vkt_tier"], r["vkt_year"] = fallback, "C", year0
                r["vkt_low_km"], r["vkt_high_km"] = band
                r["vkt_derivation"] = (
                    "EU average distance per registered car, stock-weighted over member states "
                    "that publish a matching traffic series; no national series is available."
                )
                r["_warnings"].append(  # type: ignore[union-attr]
                    "VKT_PROXY: EU average distance per car used; the benchmark side is "
                    "unaffected (distance cancels in CO2 per car), the product side scales with it."
                )

    for r in rows:
        stock_v, vkt_v, co2_v = r["car_stock"], r["vkt_km"], r["car_co2_kt"]
        fleet = co2_v * 1e9 / (stock_v * vkt_v) if stock_v and vkt_v and co2_v is not None else None  # type: ignore[operator]
        fleet_tier = "A" if r["vkt_tier"] == "A" else (r["vkt_tier"] or "C")
        if fleet is not None and not FLEET_INTENSITY_MIN <= fleet <= FLEET_INTENSITY_MAX:
            fleet_tier = "C"
            r["_warnings"].append(  # type: ignore[union-attr]
                f"FLEET_INTENSITY_IMPLAUSIBLE: {fleet:.0f} gCO2/km outside "
                f"{FLEET_INTENSITY_MIN:.0f}-{FLEET_INTENSITY_MAX:.0f}; inventory and stock "
                "cover different driving populations (cross-border refuelling); tiered down to C."
            )
        r["fleet_intensity_gco2_km"] = fleet
        r["fleet_intensity_tier"] = fleet_tier if fleet is not None else None
        mean = r["mean_car_age_years"]
        r["lifetime_years"] = clamp_life(LIFETIME_CENTRAL_MULTIPLE * mean) if mean else None  # type: ignore[operator]
        r["lifetime_low_years"] = clamp_life(mean) if mean else None  # type: ignore[arg-type]
        r["lifetime_high_years"] = clamp_life(2 * mean) if mean else None  # type: ignore[operator]
        r["warnings"] = " | ".join(r.pop("_warnings"))  # type: ignore[arg-type]
        r["source_ids"] = ";".join(r.pop("_sources"))  # type: ignore[arg-type]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_PARAMS.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PARAM_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    ref_rows: list[dict[str, object]] = []
    incomplete: list[str] = []
    for r in rows:
        c = str(r["country"])
        fleet, grid0 = r["fleet_intensity_gco2_km"], r["grid_gco2_kwh"]
        life = r["lifetime_high_years"]
        if fleet is None or grid0 is None or life is None or r["vkt_km"] is None:
            incomplete.append(c)
            continue
        for s in SCENARIOS:
            rf, rp = rates.get((c, s, "r_fleet")), rates.get((c, s, "r_power"))
            if rf is None or rp is None:
                incomplete.append(f"{c}/{s}")
                continue
            for t in range(int(life)):
                ref_rows.append(
                    {
                        "country": c,
                        "scenario": s,
                        "t": t,
                        "calendar_year": year0 + t,
                        "r_fleet": rf,
                        "r_power": rp,
                        "fleet_intensity_gco2_km": round(fleet, 6),  # type: ignore[arg-type]
                        "e_ref_kgco2_per_vehicle": round(
                            fleet / 1000 * (1 - rf) ** t * r["vkt_km"], 6
                        ),  # type: ignore[operator]
                        "grid_kgco2_per_kwh": round(grid0 / 1000 * (1 - rp) ** t, 9),  # type: ignore[operator]
                    }
                )
    with OUT_REF.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REF_FIELDS)
        writer.writeheader()
        writer.writerows(ref_rows)

    tiers = {t: sum(1 for r in rows if r["vkt_tier"] == t) for t in ("A", "B", "C")}
    print(f"{OUT_PARAMS.relative_to(REPO)}: {len(rows)} markets; vkt tiers {tiers}")
    note = f"; incomplete: {incomplete}" if incomplete else ""
    print(f"{OUT_REF.relative_to(REPO)}: {len(ref_rows)} rows{note}")


if __name__ == "__main__":
    main()
