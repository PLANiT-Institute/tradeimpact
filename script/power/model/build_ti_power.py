"""Compute the trade impact of every generating unit in scope, year by year and over its life.

Inputs
    projects/processed/projects_gem.csv
    projects/method/technology_defaults.csv      lifetime, capacity factor, efficiency (tier C)
    emission_factors/processed/emission_factors.csv
    output/reference_power.csv                   destination grid path per scenario
Outputs
    output/ti_power_annual.csv       unit x scenario x calendar year, both sides of the comparison
    output/ti_power_by_unit.csv      unit x scenario lifetime totals, inputs, tiers, coordinates
    output/ti_power_excluded.csv     units with no result and the reason

Algorithm (whitepaper sign convention: positive = emissions added)
    generation      $$ G = P \\cdot 8760 \\cdot CF \\cdot 10^{3} $$   kWh/year
                    ASCII: G = P_MW * 8760 * CF * 1000
    unit intensity  $$ I = HR \\cdot EF \\cdot 10^{-3} $$   gCO2/kWh, HR in MJ/kWh, EF in kgCO2/TJ
                    ASCII: I = HR * EF / 1000   (zero for nuclear, hydro, wind, solar, geothermal)
    per year        $$ E_{prod}(y) = G\\,I,\\quad E_{ref}(y) = G\\,g_c^{s}(y),\\quad
                       TI(y) = E_{prod}(y) - E_{ref}(y) $$   tCO2 after /10^6
    lifetime        $$ TI = \\sum_{y=y_0}^{y_0+L-1} TI(y) $$
    P capacity (MW); CF capacity factor; HR heat rate (MJ/kWh); EF emission factor (kgCO2/TJ);
    g grid intensity of destination c under scenario s (gCO2/kWh); L lifetime (years).

The order of inputs: the tracker's own capacity factor and heat rate where published, the
technology default otherwise; the destination's national emission factor where on file, the
IPCC default otherwise. Every choice is a column on the result row with its tier.

Run from the repository root:  .venv/bin/python script/power/model/build_ti_power.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from power_io import DATA, OUT, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
DEFAULTS = DATA / "projects" / "method" / "technology_defaults.csv"
FACTORS = DATA / "emission_factors" / "processed" / "emission_factors.csv"
REFERENCE = OUT / "reference_power.csv"
ANNUAL = OUT / "ti_power_annual.csv"
BY_UNIT = OUT / "ti_power_by_unit.csv"
EXCLUDED = OUT / "ti_power_excluded.csv"
HOURS = 8760
MJ_PER_KWH = 3.6
ZERO_STACK = {"nuclear", "hydro", "wind", "solar", "geothermal"}
EXCLUDED_STATUS = re.compile(r"cancel|shelv")
TIER_ORDER = {"A": 0, "B": 1, "C": 2}
ANNUAL_FIELDS = [
    "gem_unit_id",
    "scenario",
    "t",
    "calendar_year",
    "generation_gwh",
    "grid_gco2_per_kwh",
    "grid_basis",
    "e_prod_tco2",
    "e_ref_tco2",
    "ti_tco2",
    "cumulative_ti_tco2",
]
UNIT_FIELDS = [
    "gem_unit_id",
    "gem_location_id",
    "country",
    "plant_name",
    "unit_name",
    "fuel_type",
    "fuel_id",
    "technology",
    "status",
    "capacity_mw",
    "start_year",
    "end_year",
    "lifetime_years",
    "lifetime_source",
    "capacity_factor",
    "cf_source",
    "heat_rate_mj_per_kwh",
    "heat_rate_source",
    "ef_kgco2_per_tj",
    "ef_basis",
    "intensity_gco2_per_kwh",
    "biogenic",
    "scenario",
    "years_counted",
    "years_dropped",
    "e_prod_lifetime_tco2",
    "e_ref_lifetime_tco2",
    "ti_lifetime_tco2",
    "ti_remaining_tco2",
    "analysis_year",
    "crossover_year",
    "direction",
    "layer1_tier",
    "layer2_tier",
    "tier",
    "latitude",
    "longitude",
    "matched_companies",
    "wiki_url",
]
EXCLUDED_FIELDS = ["gem_unit_id", "plant_name", "country", "fuel_type", "status", "reason"]


def intensity_gco2_per_kwh(heat_rate_mj_per_kwh: float, ef_kgco2_per_tj: float) -> float:
    """Stack CO2 per kWh from heat rate (MJ/kWh) and fuel factor (kgCO2/TJ)."""
    return heat_rate_mj_per_kwh * ef_kgco2_per_tj * 1e-3


def unit_flow(
    generation_kwh: float,
    intensity: float,
    grid: dict[int, tuple[float, str]],
    years: list[int],
) -> list[dict[str, object]]:
    """Per-year product and benchmark emissions (tCO2) for the years the grid path covers."""
    rows: list[dict[str, object]] = []
    cumulative = 0.0
    for t, y in enumerate(years):
        if y not in grid:
            continue
        g, basis = grid[y]
        e_prod = generation_kwh * intensity / 1e6
        e_ref = generation_kwh * g / 1e6
        cumulative += e_prod - e_ref
        rows.append(
            {
                "t": t,
                "calendar_year": y,
                "generation_gwh": round(generation_kwh / 1e6, 3),
                "grid_gco2_per_kwh": round(g, 3),
                "grid_basis": basis,
                "e_prod_tco2": round(e_prod, 3),
                "e_ref_tco2": round(e_ref, 3),
                "ti_tco2": round(e_prod - e_ref, 3),
                "cumulative_ti_tco2": round(cumulative, 3),
            }
        )
    return rows


def default_for(unit: dict[str, str], defaults: list[dict[str, str]]) -> dict[str, str] | None:
    """First technology_defaults row whose fuel and technology pattern match the unit."""
    tech = unit.get("technology", "") or ""
    for d in defaults:
        if d["fuel_type"] == unit["fuel_type"] and re.search(
            d["technology_pattern"], tech, re.IGNORECASE
        ):
            return d
    return None


def factor_for(
    unit: dict[str, str], factors: list[dict[str, str]]
) -> tuple[dict[str, str] | None, str]:
    """(factor row, fuel_id): the destination's national row first, else the IPCC default."""
    text = f"{unit.get('fuel_detail', '')} {unit['fuel_type']}".strip().lower()
    defaults = [f for f in factors if f["basis"] == "ipcc_default"]
    fuel_id = ""
    for f in defaults:
        pattern = f.get("gem_fuel_pattern") or ""
        if pattern and re.search(pattern, text, re.IGNORECASE):
            fuel_id = f["fuel_id"]
            break
    if not fuel_id:
        return None, ""
    for f in factors:
        if f["basis"] == "national" and f["country"] == unit["country"] and f["fuel_id"] == fuel_id:
            return f, fuel_id
    return next(f for f in defaults if f["fuel_id"] == fuel_id), fuel_id


def worst(*tiers: str) -> str:
    """Worst tier of those given."""
    return max(tiers, key=lambda t: TIER_ORDER.get(t, 2))


def main() -> None:
    """Assess every unit in scope under every scenario its destination has a path for."""
    for path, how in (
        (PROJECTS, "run script/power/projects/extract_gem_tracker.py"),
        (REFERENCE, "run script/power/model/build_reference_power.py"),
    ):
        if not path.exists():
            hand_file_required(path, how)
    defaults = read_csv(DEFAULTS)
    # The IPCC method table carries the fuel patterns; join them onto the processed factors.
    patterns = {
        r["fuel_id"]: r["gem_fuel_pattern"]
        for r in read_csv(DATA / "emission_factors" / "method" / "ipcc_2006_table_2_2.csv")
    }
    factors = read_csv(FACTORS)
    for f in factors:
        f["gem_fuel_pattern"] = patterns.get(f["fuel_id"], "")
    reference: dict[tuple[str, str], dict[int, tuple[float, str]]] = {}
    for r in read_csv(REFERENCE):
        reference.setdefault((r["country"], r["scenario"]), {})[int(r["calendar_year"])] = (
            float(r["grid_gco2_per_kwh"]),
            r["basis"],
        )
    observed_latest = max(
        y for path in reference.values() for y, (_, basis) in path.items() if basis == "observed"
    )
    analysis_year = observed_latest + 1
    annual: list[dict[str, object]] = []
    by_unit: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []

    def drop(u: dict[str, str], reason: str) -> None:
        excluded.append({k: u.get(k, "") for k in EXCLUDED_FIELDS[:-1]} | {"reason": reason})

    for u in read_csv(PROJECTS):
        if EXCLUDED_STATUS.search(u["status"]):
            drop(u, f"status {u['status']}: never built")
            continue
        start = num(u["start_year"])
        capacity = num(u["capacity_mw"])
        if start is None or capacity is None:
            drop(u, "no start year or capacity in the tracker")
            continue
        d = default_for(u, defaults)
        if d is None:
            drop(u, f"no technology default for fuel_type {u['fuel_type']!r}")
            continue
        cf = num(u["capacity_factor"])
        cf_source = "gem" if cf is not None else "default"
        cf = cf if cf is not None else float(d["capacity_factor"])
        zero = u["fuel_type"] in ZERO_STACK
        heat = num(u["heat_rate_mj_per_kwh"])
        heat_source, ef_row, fuel_id, biogenic = "", None, "", "no"
        if zero:
            intensity, heat, heat_source, ef_basis = 0.0, "", "not_applicable", "not_applicable"
        else:
            if heat is None:
                eff = num(d["efficiency_lhv"])
                if eff is None:
                    drop(u, f"no heat rate and no default efficiency for {u['fuel_type']}")
                    continue
                heat, heat_source = MJ_PER_KWH / eff, "default"
            else:
                heat_source = "gem"
            ef_row, fuel_id = factor_for(u, factors)
            if ef_row is None:
                fuel_text = f"{u.get('fuel_detail')!r}/{u['fuel_type']}"
                drop(u, f"no emission factor matches fuel {fuel_text}")
                continue
            ef_basis = ef_row["basis"]
            biogenic = ef_row["biogenic"]
            intensity = intensity_gco2_per_kwh(heat, float(ef_row["ef_kgco2_per_tj"]))
        retired = num(u["retired_year"])
        life = int(d["lifetime_years"])
        end_year = int(retired) if retired else int(start) + life - 1
        lifetime_source = "retired_year" if retired else "default"
        years = list(range(int(start), end_year + 1))
        generation = capacity * HOURS * cf * 1e3
        layer2 = worst(
            "A",
            "B" if cf_source == "gem" else "C",
            "not_applicable" if zero else ("B" if heat_source == "gem" else "C"),
            "A" if ef_basis == "national" else ("A" if zero else "C"),
        )
        layer2 = "A" if zero and cf_source == "gem" else layer2
        assessed = False
        for scenario in ("S1", "S2"):
            path = reference.get((u["country"], scenario))
            if path is None:
                continue
            flow = unit_flow(generation, intensity, path, years)
            if not flow:
                continue
            assessed = True
            for row in flow:
                annual.append({"gem_unit_id": u["gem_unit_id"], "scenario": scenario, **row})
            ti_total = sum(float(r["ti_tco2"]) for r in flow)
            remaining = sum(
                float(r["ti_tco2"]) for r in flow if int(r["calendar_year"]) >= analysis_year
            )
            crossover = next((r["calendar_year"] for r in flow if float(r["ti_tco2"]) > 0), "")
            by_unit.append(
                {
                    "gem_unit_id": u["gem_unit_id"],
                    "gem_location_id": u["gem_location_id"],
                    "country": u["country"],
                    "plant_name": u["plant_name"],
                    "unit_name": u["unit_name"],
                    "fuel_type": u["fuel_type"],
                    "fuel_id": fuel_id,
                    "technology": u["technology"],
                    "status": u["status"],
                    "capacity_mw": capacity,
                    "start_year": int(start),
                    "end_year": end_year,
                    "lifetime_years": len(years),
                    "lifetime_source": lifetime_source,
                    "capacity_factor": cf,
                    "cf_source": cf_source,
                    "heat_rate_mj_per_kwh": round(heat, 4) if isinstance(heat, float) else heat,
                    "heat_rate_source": heat_source,
                    "ef_kgco2_per_tj": ef_row["ef_kgco2_per_tj"] if ef_row else "",
                    "ef_basis": ef_basis,
                    "intensity_gco2_per_kwh": round(intensity, 3),
                    "biogenic": biogenic,
                    "scenario": scenario,
                    "years_counted": len(flow),
                    "years_dropped": len(years) - len(flow),
                    "e_prod_lifetime_tco2": round(sum(float(r["e_prod_tco2"]) for r in flow), 3),
                    "e_ref_lifetime_tco2": round(sum(float(r["e_ref_tco2"]) for r in flow), 3),
                    "ti_lifetime_tco2": round(ti_total, 3),
                    "ti_remaining_tco2": round(remaining, 3),
                    "analysis_year": analysis_year,
                    "crossover_year": crossover,
                    "direction": "liability"
                    if ti_total > 0
                    else ("contribution" if ti_total < 0 else "neutral"),
                    "layer1_tier": "A",
                    "layer2_tier": layer2,
                    "tier": worst("A", layer2),
                    "latitude": u["latitude"],
                    "longitude": u["longitude"],
                    "matched_companies": u["matched_companies"],
                    "wiki_url": u["wiki_url"],
                }
            )
        if not assessed:
            drop(u, f"no grid path for destination {u['country']} (see targets exclusions)")
    write_csv(ANNUAL, ANNUAL_FIELDS, annual)
    write_csv(BY_UNIT, UNIT_FIELDS, by_unit)
    write_csv(EXCLUDED, EXCLUDED_FIELDS, excluded)
    units = {str(r["gem_unit_id"]) for r in by_unit}
    print(
        f"{BY_UNIT.relative_to(REPO)}: {len(by_unit)} unit x scenario rows, {len(units)} units; "
        f"{ANNUAL.name}: {len(annual)} rows; {EXCLUDED.name}: {len(excluded)}; analysis year "
        f"{analysis_year}"
    )


if __name__ == "__main__":
    main()
