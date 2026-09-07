"""Attribute each unit's trade impact to the companies that held a role on it, role by role.

Inputs
    roles/processed/project_roles.csv      hand register: company x unit x role, phase, share
    roles/processed/company_ir_roles.csv   company disclosures and project pages, each row citing
                                           the page on disk that states the role or the share
    roles/processed/gem_tracker_roles.csv  investment and operation rows from the tracker's own
                                           Owner / Parent / Operator fields
    roles/processed/gem_wiki_roles.csv     development, construction and finance rows from the
                                           wiki pages
    companies/method/companies.csv         names and HQ for the tracker-derived rows
    output/ti_power_by_unit.csv            unit x scenario lifetime results
Outputs
    output/ti_power_by_role.csv            one row per role row x unit x scenario: the unit's full
                                           figure and the share-weighted figure side by side
    output/ti_power_company.csv            company x role x scenario totals, both weightings

Attribution rule (project lead, 2026-09-05): every role is attributed separately. A company's
rows of different roles are never added together, and the share stays a column, so the weighting
can be changed later without re-collecting. A plant-level role (gem_location_id, no unit id)
applies to every unit at that location. Rows come from two origins, kept in the ``origin``
column: ``register`` (hand-gathered, any role), ``company_ir`` (read from a company disclosure or
project page that is on disk and hash-recorded), ``gem`` (investment and operation rows from the
tracker's own fields) and ``gem_wiki`` (development, construction and finance rows read from the
wiki pages). Precedence is register, then company_ir, then tracker, then wiki, per company x plant
x role, so a sourced reading always replaces a machine one of the same role. A row whose company is
headquartered in the unit's country is a domestic role, not a trade, and is dropped and counted.

The five phases are separate and never pooled: **development**, **construction** (EPC and
equipment), **investment** (equity), **operation** (O&M) and **finance** (debt and cover). A
utility that both owns and operates a plant carries two rows, one in each phase.

Run from the repository root:  .venv/bin/python script/power/model/aggregate_roles.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from power_io import DATA, OUT, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

ROLES = DATA / "roles" / "processed" / "project_roles.csv"
GEM_TRACKER = DATA / "roles" / "processed" / "gem_tracker_roles.csv"
GEM_WIKI = DATA / "roles" / "processed" / "gem_wiki_roles.csv"
COMPANIES = DATA / "companies" / "method" / "companies.csv"
COMPANY_IR = DATA / "roles" / "processed" / "company_ir_roles.csv"
VOCAB = DATA / "roles" / "method" / "roles.csv"
SCOPE = DATA / "registry" / "scope.csv"
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
    "origin",
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
    "units_from_register",
    "units_from_company_ir",
    "units_from_gem",
    "units_from_wiki",
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
                    "origin": r.get("origin", "register"),
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
                "units_from_register": len(
                    {str(r["gem_unit_id"]) for r in rs if r["origin"] == "register"}
                ),
                "units_from_company_ir": len(
                    {str(r["gem_unit_id"]) for r in rs if r["origin"] == "company_ir"}
                ),
                "units_from_gem": len({str(r["gem_unit_id"]) for r in rs if r["origin"] == "gem"}),
                "units_from_wiki": len(
                    {str(r["gem_unit_id"]) for r in rs if r["origin"] == "gem_wiki"}
                ),
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


def merge_registers(
    register: list[dict[str, str]],
    tracker: list[dict[str, str]],
    wiki: list[dict[str, str]],
    companies: dict[str, dict[str, str]],
    vocab: dict[str, dict[str, str]],
    exclude_home: bool = True,
    company_ir: list[dict[str, str]] | None = None,
) -> tuple[list[dict[str, str]], int]:
    """Register rows, then tracker rows, then wiki rows, one per company x plant x role.

    Domestic rows (the company's own country) are dropped and counted. A machine-read row is
    skipped where a source of higher standing already states that company's role on that plant.
    """
    out: list[dict[str, str]] = []
    domestic = 0
    seen: set[tuple[str, str, str]] = set()

    def keys(company: str, unit: str, location: str, role: str) -> list[tuple[str, str, str]]:
        return [(company, place, role) for place in (unit, location) if place]

    for origin, rows in (("register", register), ("company_ir", company_ir or [])):
        for r in rows:
            if exclude_home and r["country"] and r["company_country"] == r["country"]:
                domestic += 1
                continue
            candidate = keys(r["company_id"], r["gem_unit_id"], r["gem_location_id"], r["role"])
            if any(k in seen for k in candidate):
                continue
            out.append({**r, "origin": origin})
            seen.update(candidate)
    for origin, rows in (("gem", tracker), ("gem_wiki", wiki)):
        for g in rows:
            c = companies[g["company_id"]]
            if exclude_home and c["country"] == g["country"]:
                domestic += 1
                continue
            unit = g.get("gem_unit_id", "")
            candidate = keys(g["company_id"], unit, g["gem_location_id"], g["role"])
            if any(k in seen for k in candidate):
                continue
            seen.update(candidate)
            note = (
                f"tracker {g['level']} field: {g['entity']}"
                if origin == "gem"
                else f"GEM wiki sentence: {g.get('sentence', '')[:200]}"
            )
            out.append(
                {
                    "company_id": g["company_id"],
                    "company_name": c["name_en"],
                    "company_country": c["country"],
                    "company_type": c["type"],
                    "gem_unit_id": unit,
                    "gem_location_id": g["gem_location_id"] if not unit else "",
                    "plant_name": g["plant_name"],
                    "country": g["country"],
                    "role": g["role"],
                    "phase": vocab[g["role"]]["phase"],
                    "share": g["share"],
                    "share_basis": vocab[g["role"]]["share_basis"],
                    "from_year": "",
                    "to_year": "",
                    "source_url": g["source_url"],
                    "source_note": note,
                    "accessed_date": "",
                    "origin": origin,
                }
            )
    return out, domestic


def main() -> None:
    """Write the role-level and company x role tables."""
    if not ROLES.exists():
        hand_file_required(ROLES, "run script/power/roles/extract_roles.py")
    if not GEM_TRACKER.exists():
        hand_file_required(GEM_TRACKER, "run script/power/roles/extract_gem_roles.py")
    if not BY_UNIT.exists():
        hand_file_required(BY_UNIT, "run script/power/model/build_ti_power.py")
    companies = {c["company_id"]: c for c in read_csv(COMPANIES)}
    scope = {r["setting"]: r["value"].strip() for r in read_csv(SCOPE)} if SCOPE.exists() else {}
    merged, domestic = merge_registers(
        read_csv(ROLES),
        read_csv(GEM_TRACKER),
        read_csv(GEM_WIKI) if GEM_WIKI.exists() else [],
        companies,
        {v["role"]: v for v in read_csv(VOCAB)},
        exclude_home=scope.get("exclude_home_country", "yes") == "yes",
        company_ir=read_csv(COMPANY_IR) if COMPANY_IR.exists() else [],
    )
    rows = attribute(merged, read_csv(BY_UNIT))
    write_csv(BY_ROLE, ROLE_FIELDS, rows)
    totals = company_totals(rows)
    write_csv(COMPANY, COMPANY_FIELDS, totals)
    print(
        f"{BY_ROLE.relative_to(REPO)}: {len(rows)} role x unit x scenario rows from "
        f"{len(merged)} role rows ({domestic} domestic dropped); {COMPANY.name}: {len(totals)} "
        "company x role x scenario rows"
    )


if __name__ == "__main__":
    main()
