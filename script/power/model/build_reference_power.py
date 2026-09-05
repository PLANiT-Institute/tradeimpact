"""Build the benchmark grid-intensity path per destination and scenario, observed then projected.

Inputs
    grid/processed/grid_intensity.csv                observed gCO2/kWh
    targets/processed/emission_targets_power.csv     r_power per country and scenario
    projects/processed/projects_gem.csv              sets the horizon (latest end of life)
    projects/method/technology_defaults.csv          lifetimes for the horizon
Output
    output/reference_power.csv
        country, scenario, calendar_year, grid_gco2_per_kwh, basis (observed | pathway), r_power

Algorithm
    $$ g_c^{s}(y) = g_c(y_{obs}) \\,(1 - r_c^{s})^{\\,y - y_{obs}} \\quad (y > y_{obs}) $$
    ASCII: g(y) = g(y_obs) * (1 - r) ** (y - y_obs) for years after the latest observation;
    observed values are used as they are for years up to y_obs, identically in both scenarios.
    g  grid carbon intensity, gCO2/kWh;  r  annual fractional decline, 1/year

Run from the repository root:  .venv/bin/python script/power/model/build_reference_power.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from power_io import DATA, OUT, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

GRID = DATA / "grid" / "processed" / "grid_intensity.csv"
RATES = DATA / "targets" / "processed" / "emission_targets_power.csv"
PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
DEFAULTS = DATA / "projects" / "method" / "technology_defaults.csv"
REFERENCE = OUT / "reference_power.csv"
HORIZON_CAP = 2100
FIELDS = ["country", "scenario", "calendar_year", "grid_gco2_per_kwh", "basis", "r_power"]


def lifetime_for(unit: dict[str, str], defaults: list[dict[str, str]]) -> int | None:
    """Longest default lifetime of a unit (the sensitivity's high variant), for the horizon."""
    for d in defaults:
        if d["fuel_type"] != unit["fuel_type"]:
            continue
        if re.search(d["technology_pattern"], unit.get("technology", "") or "", re.IGNORECASE):
            return int(d.get("lifetime_high_years") or d["lifetime_years"])
    return None


def horizon(projects: list[dict[str, str]], defaults: list[dict[str, str]]) -> int:
    """Latest calendar year any unit in scope may still operate, capped."""
    end = 0
    for u in projects:
        start = num(u["start_year"])
        if start is None:
            continue
        retired = num(u["retired_year"])
        life = lifetime_for(u, defaults)
        last = int(retired) if retired else (int(start) + (life or 0) - 1)
        end = max(end, last)
    return min(end, HORIZON_CAP)


def pathway(series: dict[int, float], rate: float, until: int) -> list[tuple[int, float, str]]:
    """Observed values then the compound path from the latest observation to ``until``."""
    latest = max(series)
    out = [(y, v, "observed") for y, v in sorted(series.items())]
    g = series[latest]
    for y in range(latest + 1, until + 1):
        g *= 1 - rate
        out.append((y, g, "pathway"))
    return out


def main() -> None:
    """Write the reference path for every destination x scenario with a rate."""
    for path, how in (
        (PROJECTS, "run script/power/projects/extract_gem_tracker.py"),
        (RATES, "run script/power/targets/derive_power_rates.py"),
    ):
        if not path.exists():
            hand_file_required(path, how)
    grid: dict[str, dict[int, float]] = {}
    for r in read_csv(GRID):
        grid.setdefault(r["country"], {})[int(r["year"])] = float(r["value"])
    projects = read_csv(PROJECTS)
    until = horizon(projects, read_csv(DEFAULTS))
    rows: list[dict[str, object]] = []
    for rate in read_csv(RATES):
        c, s, r = rate["country"], rate["scenario"], float(rate["value"])
        for y, g, basis in pathway(grid[c], r, until):
            rows.append(
                {
                    "country": c,
                    "scenario": s,
                    "calendar_year": y,
                    "grid_gco2_per_kwh": round(g, 4),
                    "basis": basis,
                    "r_power": r,
                }
            )
    write_csv(REFERENCE, FIELDS, rows)
    pairs = {(str(r["country"]), str(r["scenario"])) for r in rows}
    print(
        f"{REFERENCE.relative_to(REPO)}: {len(rows)} rows, {len(pairs)} country x scenario, "
        f"to {until}"
    )


if __name__ == "__main__":
    main()
