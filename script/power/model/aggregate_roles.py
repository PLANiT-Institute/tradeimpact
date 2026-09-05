"""Attribute each unit's trade impact to the companies that held a role on it, role by role.

Inputs
    roles/processed/project_roles.csv      company x unit (or plant) x role, phase, share
    output/ti_power_by_unit.csv            unit x scenario lifetime results
Outputs
    output/ti_power_by_role.csv            one row per role row x unit x scenario: the unit's full
                                           figure and the share-weighted figure side by side
    output/ti_power_company.csv            company x role x scenario totals, both weightings

Attribution rule (project lead, 2026-09-05): every role is attributed separately. A company's
rows of different roles are never added together, and the share stays a column, so the weighting
can be changed later without re-collecting. A plant-level role (gem_location_id, no unit id)
applies to every unit at that location.

Run from the repository root:  .venv/bin/python script/power/model/aggregate_roles.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from power_io import DATA, OUT, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

ROLES = DATA / "roles" / "processed" / "project_roles.csv"
BY_UNIT = OUT / "ti_power_by_unit.csv"
BY_ROLE = OUT / "ti_power_by_role.csv"
COMPANY = OUT / "ti_power_company.csv"
ROLE_FIELDS = [
    "company_id",
    "company_name",
    "company_country",
    "role",
    "phase",
    "share",
    "share_basis",
    "gem_unit_id",
    "gem_location_id",
    "plant_name",
    "country",
    "fuel_type",
    "status",
    "capacity_mw",
    "start_year",
    "scenario",
    "ti_lifetime_full_tco2",
    "ti_lifetime_weighted_tco2",
    "ti_remaining_full_tco2",
    "ti_remaining_weighted_tco2",
    "direction",
    "tier",
    "latitude",
    "longitude",
    "source_url",
]
COMPANY_FIELDS = [
    "company_id",
    "company_name",
    "company_country",
    "role",
    "phase",
    "scenario",
    "units",
    "units_with_share",
    "capacity_mw",
    "ti_lifetime_full_tco2",
    "ti_lifetime_weighted_tco2",
    "ti_remaining_full_tco2",
    "ti_remaining_weighted_tco2",
    "direction_full",
]


def weighted(value: float, share: float | None) -> float | str:
    """Share-weighted figure, blank when the share is not on file."""
    return round(value * share, 3) if share is not None else ""


def attribute(roles: list[dict[str, str]], units: list[dict[str, str]]) -> list[dict[str, object]]:
    """Join role rows to unit results by unit id, or by location id for plant-wide roles."""
    by_unit: dict[str, list[dict[str, str]]] = {}
    by_location: dict[str, list[dict[str, str]]] = {}
    for u in units:
        by_unit.setdefault(u["gem_unit_id"], []).append(u)
        if u["gem_location_id"]:
            by_location.setdefault(u["gem_location_id"], []).append(u)
    out: list[dict[str, object]] = []
    for r in roles:
        targets = by_unit.get(r["gem_unit_id"], []) if r["gem_unit_id"] else []
        if not targets and r["gem_location_id"]:
            targets = by_location.get(r["gem_location_id"], [])
        share = num(r["share"])
        for u in targets:
            full = float(u["ti_lifetime_tco2"])
            remaining = float(u["ti_remaining_tco2"])
            out.append(
                {
                    "company_id": r["company_id"],
                    "company_name": r["company_name"],
                    "company_country": r["company_country"],
                    "role": r["role"],
                    "phase": r["phase"],
                    "share": share if share is not None else "",
                    "share_basis": r["share_basis"],
                    "gem_unit_id": u["gem_unit_id"],
                    "gem_location_id": u["gem_location_id"],
                    "plant_name": u["plant_name"],
                    "country": u["country"],
                    "fuel_type": u["fuel_type"],
                    "status": u["status"],
                    "capacity_mw": u["capacity_mw"],
                    "start_year": u["start_year"],
                    "scenario": u["scenario"],
                    "ti_lifetime_full_tco2": round(full, 3),
                    "ti_lifetime_weighted_tco2": weighted(full, share),
                    "ti_remaining_full_tco2": round(remaining, 3),
                    "ti_remaining_weighted_tco2": weighted(remaining, share),
                    "direction": u["direction"],
                    "tier": u["tier"],
                    "latitude": u["latitude"],
                    "longitude": u["longitude"],
                    "source_url": r["source_url"],
                }
            )
    return out


def company_totals(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Sums per company x role x scenario; roles are never added to each other."""
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for r in rows:
        key = (str(r["company_id"]), str(r["role"]), str(r["scenario"]))
        groups.setdefault(key, []).append(r)
    out: list[dict[str, object]] = []
    for (cid, role, scenario), rs in sorted(groups.items()):
        full = sum(float(r["ti_lifetime_full_tco2"]) for r in rs)
        with_share = [r for r in rs if r["share"] != ""]
        out.append(
            {
                "company_id": cid,
                "company_name": rs[0]["company_name"],
                "company_country": rs[0]["company_country"],
                "role": role,
                "phase": rs[0]["phase"],
                "scenario": scenario,
                "units": len({str(r["gem_unit_id"]) for r in rs}),
                "units_with_share": len({str(r["gem_unit_id"]) for r in with_share}),
                "capacity_mw": round(sum(float(r["capacity_mw"]) for r in rs), 1),
                "ti_lifetime_full_tco2": round(full, 3),
                "ti_lifetime_weighted_tco2": round(
                    sum(float(r["ti_lifetime_weighted_tco2"]) for r in with_share), 3
                ),
                "ti_remaining_full_tco2": round(
                    sum(float(r["ti_remaining_full_tco2"]) for r in rs), 3
                ),
                "ti_remaining_weighted_tco2": round(
                    sum(float(r["ti_remaining_weighted_tco2"]) for r in with_share), 3
                ),
                "direction_full": "liability"
                if full > 0
                else ("contribution" if full < 0 else "neutral"),
            }
        )
    return out


def main() -> None:
    """Write the role-level and company x role tables."""
    if not ROLES.exists():
        hand_file_required(ROLES, "run script/power/roles/extract_roles.py")
    if not BY_UNIT.exists():
        hand_file_required(BY_UNIT, "run script/power/model/build_ti_power.py")
    rows = attribute(read_csv(ROLES), read_csv(BY_UNIT))
    write_csv(BY_ROLE, ROLE_FIELDS, rows)
    totals = company_totals(rows)
    write_csv(COMPANY, COMPANY_FIELDS, totals)
    print(
        f"{BY_ROLE.relative_to(REPO)}: {len(rows)} role x unit x scenario rows; "
        f"{COMPANY.name}: {len(totals)} company x role x scenario rows"
    )


if __name__ == "__main__":
    main()
