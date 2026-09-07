"""Compute each country's own capacity factor per fuel from published capacity and generation.

Inputs  utilisation/raw/ember/ember_yearly_fuel.csv capacity in GW and generation in TWh per
                                                    country, fuel and year (Ember)
        utilisation/method/fuel_map.csv             Ember's fuel names -> this model's fuel_type
        geography/processed/country_codes.csv       alpha-3 -> alpha-2
Output  utilisation/processed/capacity_factors_country.csv
        one row per destination x fuel: the latest year with both figures, its implied capacity
        factor, and the low and high of the last few years as the sensitivity band

Why: the August 2026 tracker publishes no unit-level capacity factor, and a single global default
per technology is the weakest input in the model. A country's own utilisation is published, and
Global Energy Monitor itself moved to country-level factors for its lifetime CO2 estimates on
exactly this pair of series. A unit still falls back on the technology default where its
destination and fuel have no usable pair.

Algorithm:
    $$ CF_{c,f,y} = \\frac{G_{c,f,y}\\,[\\mathrm{TWh}] \\cdot 10^{6}}
                          {P_{c,f,y}\\,[\\mathrm{GW}] \\cdot 10^{3} \\cdot 8760} $$
    ASCII: cf = generation_twh * 1e6 / (capacity_gw * 1e3 * 8760)
    G generation in TWh, P installed capacity in GW, 8760 hours in a year. A pair is used only
    where the capacity is at least MIN_CAPACITY_GW and the result lands in (0, 1]: a fleet of a
    few tens of MW, or a country whose capacity series lags a new plant, produces a factor above
    one and is dropped rather than clipped.

Run from the repository root:
    .venv/bin/python script/power/utilisation/extract_capacity_factors.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

DATASET = DATA / "utilisation"
RAW = DATASET / "raw" / "ember" / "ember_yearly_fuel.csv"
FUEL_MAP = DATASET / "method" / "fuel_map.csv"
CODES = DATA / "geography" / "processed" / "country_codes.csv"
OUT = DATASET / "processed" / "capacity_factors_country.csv"
SOURCE_ID = "ember_yearly_electricity"
HOURS = 8760
#: A fleet smaller than this is too small for its generation and capacity series to line up.
MIN_CAPACITY_GW = 0.05
#: Years of history the low-high band is taken from, ending at the latest usable year.
BAND_YEARS = 5
FIELDS = [
    "country",
    "iso3",
    "fuel_type",
    "year",
    "capacity_gw",
    "generation_twh",
    "capacity_factor",
    "cf_low",
    "cf_high",
    "years_used",
    "proxy_fuel",
    "source_id",
    "note",
]


def capacity_factor(generation_twh: float, capacity_gw: float) -> float | None:
    """Implied capacity factor, or None where the pair cannot support one."""
    if capacity_gw < MIN_CAPACITY_GW:
        return None
    cf = generation_twh * 1e6 / (capacity_gw * 1e3 * HOURS)
    return cf if 0 < cf <= 1 else None


def series(rows: list[dict[str, str]], fuels: dict[str, dict[str, str]]) -> dict:
    """(iso3, fuel_type) -> {year: {"capacity": GW, "generation": TWh}} from the Ember subset."""
    out: dict[tuple[str, str], dict[int, dict[str, float]]] = {}
    for r in rows:
        fuel = fuels.get(r["Variable"])
        value, year = num(r["Value"]), num(r["Year"])
        if fuel is None or value is None or year is None or not r["ISO 3 code"]:
            continue
        if r["Category"] == "Capacity" and r["Unit"] == "GW":
            field = "capacity"
        elif r["Category"] == "Electricity generation" and r["Unit"] == "TWh":
            field = "generation"
        else:
            continue
        out.setdefault((r["ISO 3 code"], fuel["fuel_type"]), {}).setdefault(int(year), {})[
            field
        ] = value
    return out


def main() -> None:
    """Write one capacity factor per destination and fuel, with its band."""
    if not RAW.exists():
        hand_file_required(RAW, "run script/power/utilisation/fetch_ember_yearly.py")
    fuels = {r["ember_variable"]: r for r in read_csv(FUEL_MAP)}
    by_iso = {r["alpha3"]: r for r in read_csv(CODES) if r["alpha3"]}
    grouped = series(read_csv(RAW), fuels)
    proxy = {r["fuel_type"]: r for r in fuels.values() if r["proxy"] == "yes"}
    out: list[dict[str, object]] = []
    for (iso3, fuel_type), years in sorted(grouped.items()):
        code = by_iso.get(iso3)
        if code is None or not code["alpha2"]:
            continue
        usable = {
            y: cf
            for y, v in sorted(years.items())
            if "capacity" in v
            and "generation" in v
            and (cf := capacity_factor(v["generation"], v["capacity"])) is not None
        }
        if not usable:
            continue
        latest = max(usable)
        band = {y: cf for y, cf in usable.items() if y > latest - BAND_YEARS}
        note = "implied by the country's own published capacity and generation for that fuel"
        if fuel_type in proxy:
            note += f"; {proxy[fuel_type]['note']}"
        out.append(
            {
                "country": code["alpha2"],
                "iso3": iso3,
                "fuel_type": fuel_type,
                "year": latest,
                "capacity_gw": round(years[latest]["capacity"], 4),
                "generation_twh": round(years[latest]["generation"], 4),
                "capacity_factor": round(usable[latest], 4),
                "cf_low": round(min(band.values()), 4),
                "cf_high": round(max(band.values()), 4),
                "years_used": len(band),
                "proxy_fuel": "yes" if fuel_type in proxy else "no",
                "source_id": SOURCE_ID,
                "note": note,
            }
        )
    write_csv(OUT, FIELDS, out)
    fuel_counts: dict[str, int] = {}
    for r in out:
        fuel_counts[str(r["fuel_type"])] = fuel_counts.get(str(r["fuel_type"]), 0) + 1
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} country x fuel factors for "
        f"{len({r['country'] for r in out})} countries; by fuel {dict(sorted(fuel_counts.items()))}"
    )


if __name__ == "__main__":
    main()
