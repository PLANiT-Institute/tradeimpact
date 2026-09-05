"""Derive the S1 and S2 annual decline rates of grid intensity for every destination in scope.

Inputs
    grid/processed/grid_intensity.csv           observed gCO2/kWh by country and year
    projects/processed/projects_gem.csv         the destinations that need a pathway
    targets/processed/ndc_anchors_power.csv     committed targets read from Climate Watch's NDC
                                                content, hand rows on top (extract_ndc_anchors.py)
Outputs
    targets/processed/emission_targets_power.csv
    targets/processed/emission_targets_power_exclusions.csv

Algorithm
    S1  $$ \\ln g_y = a + b\\,y \\;\\Rightarrow\\; r = 1 - e^{b} $$  over 2015..latest, excluding
        2020-2021;  ASCII: ln g = a + b*y, r = 1 - exp(b)
    S2  $$ r = 1 - \\left(\\frac{g_{target}}{g_{latest}}\\right)^{1/(y_{target}-y_{latest})} $$
        ASCII: r = 1 - (g_target / g_latest) ** (1 / (y_target - y_latest))
        g_target = g(base) * (1 - reduction)                (reduction_from_base)
                 = g(base) * target_value / base_value      (absolute_level)
                 = target_value                             (intensity_target)
        floored at S1 where S1 is steeper or the target level is already met.
    g   grid carbon intensity, gCO2/kWh;  r  annual fractional decline, 1/year

Run from the repository root:  .venv/bin/python script/power/targets/derive_power_rates.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

GRID = DATA / "grid" / "processed" / "grid_intensity.csv"
PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
ANCHORS = DATA / "targets" / "processed" / "ndc_anchors_power.csv"
OUT = DATA / "targets" / "processed" / "emission_targets_power.csv"
EXCLUDED = DATA / "targets" / "processed" / "emission_targets_power_exclusions.csv"
TREND_START = 2015
TREND_EXCLUDE = (2020, 2021)
MIN_POINTS = 3
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
EXCLUDED_FIELDS = ["country", "scenario", "reason"]
USABLE_TYPES = ("reduction_from_base", "absolute_level", "intensity_target")


def log_linear_rate(series: dict[int, float]) -> tuple[float, int, int] | None:
    """Annual decline from a log-linear fit over TREND_START.. excluding the gap years."""
    pts = [
        (y, math.log(v))
        for y, v in sorted(series.items())
        if y >= TREND_START and y not in TREND_EXCLUDE and v > 0
    ]
    if len(pts) < MIN_POINTS:
        return None
    n = len(pts)
    mx = sum(y for y, _ in pts) / n
    my = sum(v for _, v in pts) / n
    b = sum((y - mx) * (v - my) for y, v in pts) / sum((y - mx) ** 2 for y, _ in pts)
    return 1 - math.exp(b), pts[0][0], pts[-1][0]


def target_level(anchor: dict[str, str], series: dict[int, float]) -> tuple[float, str] | None:
    """Grid-intensity level the anchor commits to at its target year, and how it was read."""
    base_year = int(anchor["base_year"]) if anchor["base_year"] else None
    if anchor["target_type"] == "intensity_target":
        value = num(anchor["target_value"])
        return (value, "intensity target as stated") if value else None
    if base_year is None:
        return None
    if base_year in series:
        g_base, base_note = series[base_year], f"g({base_year})"
    else:
        first = min(series)
        g_base, base_note = series[first], f"g({first}) standing in for g({base_year})"
    if anchor["target_type"] == "reduction_from_base":
        reduction = num(anchor["reduction"])
        if reduction is None:
            return None
        return g_base * (1 - reduction), f"{base_note} x (1 - {reduction})"
    if anchor["target_type"] == "absolute_level":
        base_value, target_value = num(anchor["base_value"]), num(anchor["target_value"])
        if not base_value or target_value is None:
            return None
        return g_base * target_value / base_value, f"{base_note} x {target_value}/{base_value}"
    return None


def main() -> None:
    """Write the rate table and the exclusion list."""
    if not PROJECTS.exists():
        hand_file_required(PROJECTS, "run script/power/projects/extract_gem_tracker.py")
    if not ANCHORS.exists():
        hand_file_required(ANCHORS, "run script/power/targets/extract_ndc_anchors.py")
    grid: dict[str, dict[int, float]] = {}
    for r in read_csv(GRID):
        grid.setdefault(r["country"], {})[int(r["year"])] = float(r["value"])
    destinations = sorted({r["country"] for r in read_csv(PROJECTS)})
    anchors = {a["country"]: a for a in read_csv(ANCHORS)}
    out: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    for c in destinations:
        series = grid.get(c, {})
        fit = log_linear_rate(series)
        if fit is None:
            reason = f"fewer than {MIN_POINTS} grid observations since {TREND_START}"
            excluded.append({"country": c, "scenario": "S1", "reason": reason})
            excluded.append({"country": c, "scenario": "S2", "reason": reason + " (no start)"})
            continue
        s1, y0, y1 = fit
        derivation = f"Log-linear trend of observed grid intensity, {y0}-{y1} excluding 2020-2021."
        if s1 < 0:
            derivation += f" OBSERVED_INCREASE: series rising ({s1:+.4f}/yr)."
        out.append(
            {
                "country": c,
                "scenario": "S1",
                "rate": "r_power",
                "value": round(s1, 9),
                "target_level": "observed_trend",
                "base_year": y0,
                "target_year": y1,
                "derivation": derivation,
                "source_id": "owid_ember_grid_intensity",
            }
        )
        anchor = anchors.get(c)
        if anchor is None:
            excluded.append(
                {
                    "country": c,
                    "scenario": "S2",
                    "reason": "no NDC target on file for this destination",
                }
            )
            continue
        status = anchor.get("parse_status", "")
        if anchor["target_type"] not in USABLE_TYPES or status not in ("parsed", "hand"):
            excluded.append(
                {
                    "country": c,
                    "scenario": "S2",
                    "reason": (
                        f"{anchor['target_type']} ({status}) in {anchor.get('document', '')}: "
                        f"{anchor.get('target_text', '')[:140]}"
                    ),
                }
            )
            continue
        level = target_level(anchor, series)
        if level is None:
            excluded.append(
                {
                    "country": c,
                    "scenario": "S2",
                    "reason": f"anchor {anchor['anchor_id']} lacks the fields its type needs",
                }
            )
            continue
        g_target, how = level
        g_latest = series[y1]
        years = int(anchor["target_year"]) - y1
        if years <= 0:
            excluded.append(
                {
                    "country": c,
                    "scenario": "S2",
                    "reason": f"anchor {anchor['anchor_id']} target year not after {y1}",
                }
            )
            continue
        level_name = f"{anchor['scope']}_prorata"
        note = ""
        if g_target >= g_latest:
            value, level_name = s1, level_name + "_s1_floor"
            note = (
                f" PATHWAY_ALREADY_MET: target level {g_target:.1f} gCO2/kWh is at or above the "
                f"latest observation {g_latest:.1f}; S2 floored at the S1 trend."
            )
        else:
            value = 1 - (g_target / g_latest) ** (1 / years)
            if s1 > value:
                note = (
                    f" S1_STEEPER: pro-rata rate {value:.4f}/yr is below the observed trend "
                    f"{s1:.4f}/yr; S2 floored at S1."
                )
                value, level_name = s1, level_name + "_s1_floor"
        out.append(
            {
                "country": c,
                "scenario": "S2",
                "rate": "r_power",
                "value": round(value, 9),
                "target_level": level_name,
                "base_year": anchor["base_year"] or y1,
                "target_year": anchor["target_year"],
                "derivation": (
                    f"{anchor['anchor_id']} ({anchor['target_type']}, {anchor['scope']}, "
                    f"{anchor.get('document') or anchor['communicated']}): target level {how} = "
                    f"{g_target:.1f} gCO2/kWh at {anchor['target_year']}, compound decline from "
                    f"{g_latest:.1f} at {y1}." + note
                ),
                "source_id": anchor["source_id"],
            }
        )
    write_csv(OUT, FIELDS, out)
    write_csv(EXCLUDED, EXCLUDED_FIELDS, excluded)
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rates for {len(destinations)} destinations; "
        f"{len(excluded)} exclusions -> {EXCLUDED.name}"
    )


if __name__ == "__main__":
    main()
