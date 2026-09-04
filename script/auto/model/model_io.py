"""Shared readers and output schemas for the model steps.

The model scripts are market-neutral: each one reads *every* destination-parameter and
reference-trajectory file present in ``data/auto/output/`` and keys everything on
(market, country). Adding a market means adding one ``build_reference_<market>.py`` — no
downstream script changes. This module is the single home of the shared field lists and of
the loaders, so the schemas cannot drift between the market-specific reference builders.

Imported by the other scripts in this directory (they run as
``python script/auto/model/<name>.py``, which puts this directory on ``sys.path``).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
OUT_DIR = DATA / "output"
COHORTS = OUT_DIR / "cohorts.csv"
COHORTS_WITHHELD = OUT_DIR / "cohorts_withheld.csv"
REAL_WORLD = DATA / "vehicle_technology" / "method" / "real_world_correction.csv"

#: Vehicle segments. A segment is the population a destination's benchmark describes, named
#: for the class the destination's own statistics use, because a benchmark and the sales it
#: prices must always cover the same population:
#:     passenger_car  cars (EU27 M1, Korea 승용, Japan 乗用車)
#:     light_duty     cars and light trucks together (the United States, where the distance
#:                    statistics split by wheelbase and cannot be cut by body type)
#:     freight        goods vehicles (Korea 화물, N1 to N3)
#:     bus            buses and minibuses (Korea 승합)
PASSENGER_CAR = "passenger_car"
LIGHT_DUTY = "light_duty"
FREIGHT = "freight"
BUS = "bus"
SEGMENTS = (PASSENGER_CAR, LIGHT_DUTY, FREIGHT, BUS)

#: Plausible fleet-intensity band per segment (gCO2/km). Outside it the numerator and the
#: denominator describe different driving populations and the ratio is not a national
#: parameter, so the builder tiers the value down to C and says so. The car band is the one
#: the guideline gives; the others are set from the same reasoning at the scale of the class
#: (a laden truck or a bus burns several times what a car does per kilometre).
INTENSITY_BAND = {
    PASSENGER_CAR: (80.0, 320.0),
    LIGHT_DUTY: (100.0, 400.0),
    FREIGHT: (150.0, 1200.0),
    BUS: (250.0, 1600.0),
}

#: Glob patterns for the per-market reference outputs; one pair per market.
PARAMS_GLOB = "destination_parameters_*.csv"
REFERENCE_GLOB = "reference_trajectories_*.csv"

CENTRAL = "central"
ALL_HEV = "all_hev"

#: Columns of every ``destination_parameters_<market>.csv`` — identical across markets.
PARAM_FIELDS = [
    "market",
    "country",
    "segment",
    "cohort_year",
    "vkt_km",
    "vkt_low_km",
    "vkt_high_km",
    "vkt_tier",
    "vkt_year",
    "vkt_derivation",
    "stock",
    "stock_year",
    "co2_kt",
    "co2_year",
    "fleet_intensity_gco2_km",
    "fleet_intensity_tier",
    "grid_gco2_kwh",
    "grid_year",
    "grid_tier",
    "mean_age_years",
    "mean_age_year",
    "mean_age_tier",
    "lifetime_years",
    "lifetime_low_years",
    "lifetime_high_years",
    "lifetime_tier",
    "scenarios_excluded",
    "scenario_exclusion_reason",
    "warnings",
    "source_ids",
]

#: Columns of every ``reference_trajectories_<market>.csv``.
REF_FIELDS = [
    "market",
    "country",
    "segment",
    "scenario",
    "t",
    "calendar_year",
    "r_fleet",
    "r_power",
    "fleet_intensity_gco2_km",
    "e_ref_kgco2_per_vehicle",
    "grid_kgco2_per_kwh",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_long(path: Path) -> dict[tuple[str, str], dict[int, float]]:
    """(country, series) -> {year: value} from a long-format observation CSV."""
    out: dict[tuple[str, str], dict[int, float]] = {}
    for row in read_csv(path):
        out.setdefault((row["country"], row["series"]), {})[int(row["year"])] = float(row["value"])
    return out


def latest(series: dict[int, float], not_after: int) -> tuple[int, float] | None:
    """Most recent (year, value) at or before ``not_after``, or None when there is none."""
    pairs = [(y, v) for y, v in series.items() if y <= not_after]
    return max(pairs) if pairs else None


def load_params() -> dict[tuple[str, str, str], dict[str, str]]:
    """(market, country, segment) -> destination parameters, pooled over every market file."""
    out: dict[tuple[str, str, str], dict[str, str]] = {}
    for path in sorted(OUT_DIR.glob(PARAMS_GLOB)):
        for row in read_csv(path):
            out[(row["market"], row["country"], row["segment"])] = row
    if not out:
        raise SystemExit(f"no {PARAMS_GLOB} in {OUT_DIR}: run the reference builders first")
    return out


def load_reference() -> dict[tuple[str, str, str, str], dict[int, tuple[float, float]]]:
    """(market, country, segment, scenario) -> {t: (e_ref kgCO2e/vehicle-year, grid kg/kWh)}."""
    out: dict[tuple[str, str, str, str], dict[int, tuple[float, float]]] = defaultdict(dict)
    for path in sorted(OUT_DIR.glob(REFERENCE_GLOB)):
        for row in read_csv(path):
            key = (row["market"], row["country"], row["segment"], row["scenario"])
            out[key][int(row["t"])] = (
                float(row["e_ref_kgco2_per_vehicle"]),
                float(row["grid_kgco2_per_kwh"]),
            )
    if not out:
        raise SystemExit(f"no {REFERENCE_GLOB} in {OUT_DIR}: run the reference builders first")
    return dict(out)


def load_rates() -> dict[tuple[str, str, str, str], tuple[float, float]]:
    """(market, country, segment, scenario) -> (r_fleet, r_power) from the year-0 row."""
    out: dict[tuple[str, str, str, str], tuple[float, float]] = {}
    for path in sorted(OUT_DIR.glob(REFERENCE_GLOB)):
        for row in read_csv(path):
            out[(row["market"], row["country"], row["segment"], row["scenario"])] = (
                float(row["r_fleet"]),
                float(row["r_power"]),
            )
    return out


def scenarios_by_market(keys: Iterable[tuple[str, ...]]) -> dict[str, list[str]]:
    """market -> sorted scenarios that market publishes a trajectory for.

    Args:
        keys: Any iterable whose first element is the market and last the scenario — a loaded
            trajectory or rate mapping iterates as exactly that.

    Returns:
        One sorted scenario list per market.
    """
    out: dict[str, set[str]] = defaultdict(set)
    for key in keys:
        out[key[0]].add(key[-1])
    return {m: sorted(s) for m, s in out.items()}


def load_real_world() -> dict[tuple[str, str], dict[str, float]]:
    """(test_cycle, powertrain) -> {'factor', 'factor_low', 'factor_high'}.

    Keying on the test cycle is what lets one table serve WLTP certified values (which carry
    a published real-world gap) and EPA label values (already 5-cycle adjusted, factor 1.0).
    """
    return {
        (r["test_cycle"], r["powertrain"]): {
            "factor": float(r["factor"]),
            "factor_low": float(r["factor_low"]),
            "factor_high": float(r["factor_high"]),
        }
        for r in read_csv(REAL_WORLD)
    }


def load_cohorts(variant: str | None = CENTRAL) -> list[dict[str, str]]:
    """Cohort rows from ``cohorts.csv``.

    Args:
        variant: Keep only this variant (default the central case); None keeps every row.

    Returns:
        The matching cohort rows, in file order.
    """
    rows = read_csv(COHORTS)
    return rows if variant is None else [r for r in rows if r["variant"] == variant]


def certified(row: dict[str, str]) -> float:
    """Certified product parameter of a cohort row: Wh/km for BEV, else gCO2/km."""
    return float(row["energy_wh_km"] if row["powertrain"] == "BEV" else row["tailpipe_gco2_km"])


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    """Write ``rows`` to ``path`` with a fixed header; deterministic, no timestamps."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
