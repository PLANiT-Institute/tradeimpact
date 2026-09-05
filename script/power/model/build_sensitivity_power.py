"""Vary each unit's least-evidenced inputs one at a time and price the unit again.

Inputs
    output/ti_power_by_unit.csv                  the central inputs of every assessed unit
    output/reference_power.csv                   destination grid path per scenario
    projects/method/technology_defaults.csv      low / high bands for lifetime and capacity factor
    emission_factors/processed/emission_factors.csv   IPCC 95 % bounds per fuel
Output
    output/ti_power_sensitivity.csv
        gem_unit_id, scenario, dimension, variant, parameter, ti_lifetime_tco2, ti_remaining_tco2

Dimensions (guideline v1.0 §5.2), each with a central row identical to the published result:
    lifetime          technology default -> lifetime_low_years / lifetime_high_years
    capacity_factor   technology default -> cf_low / cf_high
    emission_factor   IPCC default -> its lower / upper bound (fossil, non-biogenic units only)
No variant is a new central value; the published table carries the ranges beside the result.

Run from the repository root:  .venv/bin/python script/power/model/build_sensitivity_power.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_ti_power import HOURS, intensity_gco2_per_kwh, unit_flow  # noqa: E402
from power_io import DATA, OUT, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

BY_UNIT = OUT / "ti_power_by_unit.csv"
REFERENCE = OUT / "reference_power.csv"
DEFAULTS = DATA / "projects" / "method" / "technology_defaults.csv"
FACTORS = DATA / "emission_factors" / "processed" / "emission_factors.csv"
SENSITIVITY = OUT / "ti_power_sensitivity.csv"
FIELDS = [
    "gem_unit_id",
    "scenario",
    "dimension",
    "variant",
    "parameter",
    "ti_lifetime_tco2",
    "ti_remaining_tco2",
]
GridPath = dict[int, tuple[float, str]]


def default_for(unit: dict[str, str], defaults: list[dict[str, str]]) -> dict[str, str] | None:
    """First technology_defaults row whose fuel and technology pattern match the unit."""
    for d in defaults:
        if d["fuel_type"] == unit["fuel_type"] and re.search(
            d["technology_pattern"], unit.get("technology", "") or "", re.IGNORECASE
        ):
            return d
    return None


def totals(
    capacity_mw: float,
    cf: float,
    intensity: float,
    path: GridPath,
    years: list[int],
    analysis_year: int,
) -> tuple[float, float]:
    """Lifetime and remaining trade impact (tCO2) for one parameter set."""
    flow = unit_flow(capacity_mw * HOURS * cf * 1e3, intensity, path, years)
    lifetime = sum(float(r["ti_tco2"]) for r in flow)
    remaining = sum(float(r["ti_tco2"]) for r in flow if int(r["calendar_year"]) >= analysis_year)
    return lifetime, remaining


def row(
    u: dict[str, str], dimension: str, variant: str, parameter: object, result: tuple[float, float]
) -> dict[str, object]:
    """One sensitivity row for a unit x scenario."""
    return {
        "gem_unit_id": u["gem_unit_id"],
        "scenario": u["scenario"],
        "dimension": dimension,
        "variant": variant,
        "parameter": parameter,
        "ti_lifetime_tco2": round(result[0], 3),
        "ti_remaining_tco2": round(result[1], 3),
    }


def variants_for(
    u: dict[str, str],
    d: dict[str, str] | None,
    bound: dict[str, str] | None,
    path: GridPath,
) -> list[dict[str, object]]:
    """Central plus low/high rows for every dimension that applies to the unit."""
    capacity, cf = float(u["capacity_mw"]), float(u["capacity_factor"])
    intensity = float(u["intensity_gco2_per_kwh"])
    start, end = int(u["start_year"]), int(u["end_year"])
    analysis_year = int(u["analysis_year"])
    years = list(range(start, end + 1))
    central = totals(capacity, cf, intensity, path, years, analysis_year)
    out: list[dict[str, object]] = []
    # Lifetime: only where the life is a default; a published retirement year is not varied.
    if d and u["lifetime_source"] == "default":
        out.append(row(u, "lifetime", "central", len(years), central))
        for variant, key in (("low", "lifetime_low_years"), ("high", "lifetime_high_years")):
            life = int(d[key])
            alt = list(range(start, start + life))
            result = totals(capacity, cf, intensity, path, alt, analysis_year)
            out.append(row(u, "lifetime", variant, life, result))
    if d and u["cf_source"] == "default":
        out.append(row(u, "capacity_factor", "central", cf, central))
        for variant, key in (("low", "cf_low"), ("high", "cf_high")):
            alt_cf = float(d[key])
            result = totals(capacity, alt_cf, intensity, path, years, analysis_year)
            out.append(row(u, "capacity_factor", variant, alt_cf, result))
    heat = num(u["heat_rate_mj_per_kwh"])
    if bound and heat and u["biogenic"] != "yes":
        out.append(row(u, "emission_factor", "central", float(u["ef_kgco2_per_tj"]), central))
        for variant, key in (("low", "ef_low_kgco2_per_tj"), ("high", "ef_high_kgco2_per_tj")):
            ef = float(bound[key])
            alt_i = intensity_gco2_per_kwh(heat, ef)
            result = totals(capacity, cf, alt_i, path, years, analysis_year)
            out.append(row(u, "emission_factor", variant, ef, result))
    return out


def main() -> None:
    """Write one row per unit x scenario x dimension x variant."""
    for path, how in (
        (BY_UNIT, "run script/power/model/build_ti_power.py"),
        (REFERENCE, "run script/power/model/build_reference_power.py"),
    ):
        if not path.exists():
            hand_file_required(path, how)
    defaults = read_csv(DEFAULTS)
    bounds = {
        f["fuel_id"]: f
        for f in read_csv(FACTORS)
        if f["basis"] == "ipcc_default" and f["ef_low_kgco2_per_tj"] and f["ef_high_kgco2_per_tj"]
    }
    reference: dict[tuple[str, str], GridPath] = {}
    for r in read_csv(REFERENCE):
        reference.setdefault((r["country"], r["scenario"]), {})[int(r["calendar_year"])] = (
            float(r["grid_gco2_per_kwh"]),
            r["basis"],
        )
    out: list[dict[str, object]] = []
    for u in read_csv(BY_UNIT):
        bound = bounds.get(u["fuel_id"]) if u["ef_basis"] == "ipcc_default" else None
        path = reference[(u["country"], u["scenario"])]
        out.extend(variants_for(u, default_for(u, defaults), bound, path))
    write_csv(SENSITIVITY, FIELDS, out)
    dims: dict[str, int] = {}
    for r in out:
        dims[str(r["dimension"])] = dims.get(str(r["dimension"]), 0) + 1
    print(f"{SENSITIVITY.relative_to(REPO)}: {len(out)} rows; by dimension {dims}")


if __name__ == "__main__":
    main()
