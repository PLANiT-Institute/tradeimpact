"""Step 3z — apply the workbench's reviewed overrides to the built parameters and trajectories.

The workbench queues a correction with a source and a note; this is the step that makes it real.
An override never edits a raw source — it overlays a value the reference builders produced, after
they run and before the cohorts are joined, so the whole result recomputes from the overlaid
number. Every override is applied with its source and note stamped onto the row, and the
trajectories of the cells it touches are recomputed from the overlaid values, so a changed
intensity, distance, grid or scenario rate flows through to the impact.

Input   data/auto/overrides.csv     one reviewed override per row (the workbench writes it)
Patches output/destination_parameters_*.csv   the value, with the override source and note
        output/reference_trajectories_*.csv    e_ref and grid recomputed for the touched cells
        emission_targets/processed/emission_targets_*.csv   a rate value, when a rate is overridden

Two parameter shapes are editable, matching what the workbench exposes:
    "<column> (<segment>)"   a destination-parameter column, e.g. "fleet_intensity_gco2_km (bus)"
    "<rate> (<scenario>)"    a scenario rate, e.g. "r_fleet (S2)"

When overrides.csv is absent or empty the step is a no-op and touches nothing, so a clean build
is unchanged and only a real override produces a diff.

Run from the repository root:  .venv/bin/python script/auto/model/apply_overrides.py
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from model_io import DATA, OUT_DIR, PARAM_FIELDS, REF_FIELDS, read_csv, write_csv

OVERRIDES = DATA / "overrides.csv"
TARGETS_DIR = DATA / "emission_targets" / "processed"
PARAM_DATASETS = {"country_emissions", "vehicle_usage"}
PARAM_RE = re.compile(r"^(.*) \((.*)\)$")
EU27_MEMBERS = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
    "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}  # fmt: skip


def market_of(country: str) -> str:
    """The market whose files carry a country: EU27 for a member state, else the country."""
    return "EU27" if country in EU27_MEMBERS else country


def market_file(prefix: str, market: str, suffix: str = "csv") -> Path:
    """Path to a per-market output file, named lowercase as the builders write it."""
    root = OUT_DIR if prefix.startswith(("destination", "reference")) else TARGETS_DIR
    return root / f"{prefix}_{market.lower()}.{suffix}"


def patch_parameters(rows: list[dict[str, str]]) -> set[tuple[str, str]]:
    """Overlay destination-parameter overrides; return the (market, country) pairs touched."""
    touched: set[tuple[str, str]] = set()
    by_market: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_market[market_of(r["country"])].append(r)
    for market, overrides in by_market.items():
        path = market_file("destination_parameters", market)
        if not path.exists():
            raise SystemExit(f"{path.name} not found for override on {market}")
        params = read_csv(path)
        index = {(p["country"], p["segment"], p["cohort_year"]): p for p in params}
        for o in overrides:
            m = PARAM_RE.match(o["parameter"])
            if not m:
                raise SystemExit(
                    f"override parameter {o['parameter']!r} is not '<column> (<segment>)'"
                )
            column, segment = m.group(1), m.group(2)
            key = (o["country"], segment, o["cohort_year"])
            row = index.get(key)
            if row is None or column not in row:
                raise SystemExit(f"no {column} row for {key} in {path.name}")
            row[column] = o["new_value"]
            row["source_ids"] = ";".join(
                dict.fromkeys([*row["source_ids"].split(";"), o["source_id"]])
            )
            row["warnings"] = " | ".join(
                filter(
                    None, [row["warnings"], f"OVERRIDE {column}: {o['note']} [{o['source_id']}]"]
                )
            )
            touched.add((market, o["country"]))
        write_csv(path, PARAM_FIELDS, params)
    return touched


def patch_targets(rows: list[dict[str, str]]) -> set[tuple[str, str]]:
    """Overlay scenario-rate overrides; return the (market, country) pairs touched."""
    touched: set[tuple[str, str]] = set()
    by_market: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_market[market_of(r["country"])].append(r)
    for market, overrides in by_market.items():
        path = market_file("emission_targets", market)
        if not path.exists():
            raise SystemExit(f"{path.name} not found for rate override on {market}")
        targets = read_csv(path)
        fields = list(targets[0].keys())
        index = {(t["country"], t["scenario"], t["rate"]): t for t in targets}
        for o in overrides:
            m = PARAM_RE.match(o["parameter"])
            if not m:
                raise SystemExit(f"rate override {o['parameter']!r} is not '<rate> (<scenario>)'")
            rate, scenario = m.group(1), m.group(2)
            row = index.get((o["country"], scenario, rate))
            if row is None:
                raise SystemExit(f"no {rate}/{scenario} row for {o['country']} in {path.name}")
            row["value"] = o["new_value"]
            row["derivation"] = f"OVERRIDE: {o['note']} [{o['source_id']}]  ||  {row['derivation']}"
            touched.add((market, o["country"]))
        write_csv(path, fields, targets)
    return touched


def rebuild_trajectories(markets: set[str]) -> None:
    """Recompute e_ref and grid in each touched market's trajectory file from the patched inputs.

    A trajectory value is fully determined by the destination parameters (intensity, distance,
    grid) and the scenario rates, so recomputing it from the patched tables carries an override
    through without duplicating the builders' selection logic. Only the touched markets are
    rewritten, so an unrelated market keeps its bytes.

    Args:
        markets: Market keys whose trajectory files must be recomputed.
    """
    for market in markets:
        params = {
            (p["country"], p["segment"], p["cohort_year"]): p
            for p in read_csv(market_file("destination_parameters", market))
        }
        rates = {
            (t["country"], t["scenario"], t["rate"]): float(t["value"])
            for t in read_csv(market_file("emission_targets", market))
        }
        traj_path = market_file("reference_trajectories", market)
        rows = read_csv(traj_path)
        for row in rows:
            p = params[(row["country"], row["segment"], row["cohort_year"])]
            intensity = float(p["fleet_intensity_gco2_km"])
            vkt, grid0 = float(p["vkt_km"]), float(p["grid_gco2_kwh"])
            r_fleet = rates[(row["country"], row["scenario"], "r_fleet")]
            r_power = rates[(row["country"], row["scenario"], "r_power")]
            t = int(row["t"])
            row["r_fleet"] = r_fleet
            row["r_power"] = r_power
            row["fleet_intensity_gco2_km"] = round(intensity, 6)
            row["e_ref_kgco2_per_vehicle"] = round(intensity / 1000 * (1 - r_fleet) ** t * vkt, 6)
            row["grid_kgco2_per_kwh"] = round(grid0 / 1000 * (1 - r_power) ** t, 9)
        write_csv(traj_path, REF_FIELDS, rows)


def main() -> None:
    """Apply every reviewed override, or do nothing when there are none."""
    if not OVERRIDES.exists():
        print("no overrides.csv: nothing to apply")
        return
    overrides = [r for r in read_csv(OVERRIDES) if r.get("new_value", "").strip()]
    if not overrides:
        print("overrides.csv is empty: nothing to apply")
        return

    params = [o for o in overrides if o["dataset"] in PARAM_DATASETS]
    rates = [o for o in overrides if o["dataset"] == "emission_targets"]
    other = [o for o in overrides if o["dataset"] not in PARAM_DATASETS | {"emission_targets"}]
    if other:
        names = sorted({f"{o['dataset']}/{o['parameter']}" for o in other})
        raise SystemExit(f"overrides for non-editable datasets: {names}")

    touched = patch_parameters(params) | patch_targets(rates)
    rebuild_trajectories({market for market, _country in touched})
    print(
        f"applied {len(overrides)} override(s) across "
        f"{sorted({m for m, _ in touched})}; {len(params)} parameter, {len(rates)} rate"
    )


if __name__ == "__main__":
    main()
