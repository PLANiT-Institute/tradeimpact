"""Attribute each unit's trade impact to the companies that held a role on it, role by role.

Inputs
    roles/processed/project_roles.csv      hand register: company x unit x role, phase, share
    roles/processed/company_ir_roles.csv   company disclosures and project pages, each row citing
                                           the page on disk that states the role or the share
    roles/processed/gem_tracker_roles.csv  investment and operation rows from the tracker's own
                                           Owner / Parent / Operator fields
    roles/processed/gem_wiki_roles.csv     development, construction and finance rows from the
                                           wiki pages
    roles/method/roles.csv                 the role vocabulary: tier 2 -> tier 1 -> phase
    companies/method/companies.csv         names and HQ for the tracker-derived rows
    output/ti_power_by_unit.csv            unit x scenario lifetime results
Outputs
    output/ti_power_by_role.csv            one row per company x unit x tier-1 role x scenario:
                                           the unit's full figure and the share-weighted figure
    output/ti_power_company.csv            company x tier-1 role x scenario totals, both weightings

Attribution rule (project lead, 2026-09-05): every role is attributed separately. A company's
rows of different roles are never added together, and the share stays a column, so the weighting
can be changed later without re-collecting. A plant-level role (gem_location_id, no unit id)
applies to every unit at that location.

Roles carry three levels, from ``roles/method/roles.csv``:

    phase       development / construction / investment / operation / finance
    role_tier1  developer, epc_contractor, equipment_supplier, equity_owner, om_contractor,
                lender, eca_cover
    role_tier2  the scope as the source states it: epc_lead, epc_civil_works, boiler_supply,
                equity_direct, buyers_credit, ... or the ``*_unspecified`` key where the source
                names the tier 1 role without saying which scope

**Attribution is at tier 1**: a company holds one epc_contractor role on a unit even where its
own release names two scopes (Sumitomo's civil works and port works at Matarbari, for example),
so the unit's figure is never counted twice. The scopes stay visible in ``role_tier2`` (the most
specific one on file) and ``role_tier2_all`` (every scope that source states, pipe-separated).

Rows come from four origins, kept in the ``origin`` column: ``register`` (hand-gathered, any
role), ``company_ir`` (read from a company disclosure or project page that is on disk and
hash-recorded), ``gem`` (investment and operation rows from the tracker's own fields) and
``gem_wiki`` (development, construction and finance rows read from the wiki pages). Precedence is
register, then company_ir, then tracker, then wiki, per company x plant x tier-1 role, so a
sourced reading always replaces a machine one of the same role; the origins that agree with it are
listed in ``also_stated_by``. A row whose company is headquartered in the unit's country is a
domestic role, not a trade, and is dropped and counted.

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
#: A tier-2 key that says only "this tier 1, scope not stated"; a specific key outranks it.
UNSPECIFIED_SUFFIX = "_unspecified"
ROLE_FIELDS = [
    "company_id",
    "company_name",
    "company_country",
    "phase",
    "role_tier1",
    "role_tier2",
    "role_tier2_all",
    "share",
    "share_basis",
    "origin",
    "also_stated_by",
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
    "phase",
    "role_tier1",
    "role_tier2_all",
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


def is_specific(role_tier2: str) -> bool:
    """Whether the tier-2 key names a scope rather than only its tier-1 group."""
    return not role_tier2.endswith(UNSPECIFIED_SUFFIX)


def attribute(roles: list[dict[str, str]], units: list[dict[str, str]]) -> list[dict[str, object]]:
    """Join role rows to unit results by unit id, or by location id for plant-wide roles."""
    by_unit: dict[str, list[dict[str, str]]] = {}
    by_location: dict[str, list[dict[str, str]]] = {}
    for u in units:
        by_unit.setdefault(u["gem_unit_id"], []).append(u)
        if u["gem_location_id"]:
            by_location.setdefault(u["gem_location_id"], []).append(u)
    out: list[dict[str, object]] = []
    # Guard: one company holds one tier-1 role on a unit once. A register row keyed to a unit and
    # another keyed to its location would otherwise attribute the same unit twice.
    seen: set[tuple[str, str, str, str]] = set()
    for r in roles:
        targets = by_unit.get(r["gem_unit_id"], []) if r["gem_unit_id"] else []
        if not targets and r["gem_location_id"]:
            targets = by_location.get(r["gem_location_id"], [])
        share = num(r["share"])
        for u in targets:
            key = (r["company_id"], r["role_tier1"], u["gem_unit_id"], u["scenario"])
            if key in seen:
                continue
            seen.add(key)
            full = float(u["ti_lifetime_tco2"])
            remaining = float(u["ti_remaining_tco2"])
            out.append(
                {
                    "company_id": r["company_id"],
                    "company_name": r["company_name"],
                    "company_country": r["company_country"],
                    "phase": r["phase"],
                    "role_tier1": r["role_tier1"],
                    "role_tier2": r["role_tier2"],
                    "role_tier2_all": r.get("role_tier2_all", r["role_tier2"]),
                    "share": share if share is not None else "",
                    "share_basis": r["share_basis"],
                    "origin": r.get("origin", "register"),
                    "also_stated_by": r.get("also_stated_by", ""),
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
    """Sums per company x tier-1 role x scenario; roles are never added to each other."""
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for r in rows:
        key = (str(r["company_id"]), str(r["role_tier1"]), str(r["scenario"]))
        groups.setdefault(key, []).append(r)
    out: list[dict[str, object]] = []
    for (cid, tier1, scenario), rs in sorted(groups.items()):
        full = sum(float(r["ti_lifetime_full_tco2"]) for r in rs)
        with_share = [r for r in rs if r["share"] != ""]
        scopes = sorted({s for r in rs for s in str(r["role_tier2_all"]).split("|") if s})
        specific = [s for s in scopes if is_specific(s)]
        out.append(
            {
                "company_id": cid,
                "company_name": rs[0]["company_name"],
                "company_country": rs[0]["company_country"],
                "phase": rs[0]["phase"],
                "role_tier1": tier1,
                "role_tier2_all": "|".join(specific or scopes),
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


def as_role_row(
    row: dict[str, str],
    origin: str,
    companies: dict[str, dict[str, str]],
    vocab: dict[str, dict[str, str]],
) -> dict[str, str]:
    """One source row in the shape ``attribute()`` reads, whichever origin it came from."""
    tier2 = row["role_tier2"]
    tier1 = vocab[tier2]["role_tier1"]
    if origin in ("register", "company_ir"):
        return {
            **row,
            "role_tier1": tier1,
            "role_tier2_all": tier2,
            "origin": origin,
            "also_stated_by": "",
        }
    company = companies[row["company_id"]]
    unit = row.get("gem_unit_id", "")
    note = (
        f"tracker {row['level']} field: {row['entity']}"
        if origin == "gem"
        else f"GEM wiki sentence: {row.get('sentence', '')[:200]}"
    )
    return {
        "company_id": row["company_id"],
        "company_name": company["name_en"],
        "company_country": company["country"],
        "company_type": company["type"],
        "gem_unit_id": unit,
        "gem_location_id": row["gem_location_id"] if not unit else "",
        "plant_name": row["plant_name"],
        "country": row["country"],
        "phase": vocab[tier2]["phase"],
        "role_tier1": tier1,
        "role_tier2": tier2,
        "role_tier2_all": tier2,
        "share": row["share"],
        "share_basis": vocab[tier2]["share_basis"],
        "from_year": "",
        "to_year": "",
        "source_url": row["source_url"],
        "source_note": note,
        "accessed_date": "",
        "origin": origin,
        "also_stated_by": "",
    }


def merge_registers(
    register: list[dict[str, str]],
    tracker: list[dict[str, str]],
    wiki: list[dict[str, str]],
    companies: dict[str, dict[str, str]],
    vocab: dict[str, dict[str, str]],
    exclude_home: bool = True,
    company_ir: list[dict[str, str]] | None = None,
) -> tuple[list[dict[str, str]], int]:
    """One row per company x plant x tier-1 role, from the highest-standing source that states it.

    Sources are read in order of standing: the hand register, then company disclosures, then the
    tracker's own fields, then the wiki sentences. A later source that states a tier-1 role already
    on file does not add a row; it is recorded in ``also_stated_by``. Where the same source names
    several scopes of one tier-1 role, the most specific becomes ``role_tier2`` and all of them are
    kept in ``role_tier2_all``. Domestic rows (the company's own HQ country) are dropped and
    counted.
    """
    groups: list[dict[str, str]] = []
    index: dict[tuple[str, str, str], int] = {}
    domestic = 0

    def keys(row: dict[str, str], tier1: str) -> list[tuple[str, str, str]]:
        places = (row.get("gem_unit_id", ""), row.get("gem_location_id", ""))
        return [(row["company_id"], place, tier1) for place in places if place]

    for origin, rows in (
        ("register", register),
        ("company_ir", company_ir or []),
        ("gem", tracker),
        ("gem_wiki", wiki),
    ):
        for source_row in rows:
            home = companies[source_row["company_id"]]["country"]
            if exclude_home and source_row["country"] and home == source_row["country"]:
                domestic += 1
                continue
            row = as_role_row(source_row, origin, companies, vocab)
            candidate = keys(row, row["role_tier1"])
            hit = next((index[k] for k in candidate if k in index), None)
            if hit is None:
                groups.append(row)
                index.update(dict.fromkeys(candidate, len(groups) - 1))
                continue
            held = groups[hit]
            if held["origin"] != origin:
                stated = [o for o in held["also_stated_by"].split("|") if o]
                if origin not in stated:
                    held["also_stated_by"] = "|".join([*stated, origin])
                continue
            scopes = [s for s in held["role_tier2_all"].split("|") if s]
            if row["role_tier2"] not in scopes:
                scopes.append(row["role_tier2"])
            if is_specific(row["role_tier2"]) and not is_specific(held["role_tier2"]):
                row["also_stated_by"] = held.get("also_stated_by", "")
                groups[hit] = row
                held = groups[hit]
            held["role_tier2_all"] = "|".join(scopes)
    return groups, domestic


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
        {v["role_tier2"]: v for v in read_csv(VOCAB)},
        exclude_home=scope.get("exclude_home_country", "yes") == "yes",
        company_ir=read_csv(COMPANY_IR) if COMPANY_IR.exists() else [],
    )
    rows = attribute(merged, read_csv(BY_UNIT))
    write_csv(BY_ROLE, ROLE_FIELDS, rows)
    totals = company_totals(rows)
    write_csv(COMPANY, COMPANY_FIELDS, totals)
    by_origin: dict[str, int] = {}
    for r in merged:
        by_origin[r["origin"]] = by_origin.get(r["origin"], 0) + 1
    print(
        f"{BY_ROLE.relative_to(REPO)}: {len(rows)} company x unit x tier-1 role x scenario rows "
        f"from {len(merged)} role rows {dict(sorted(by_origin.items()))} "
        f"({domestic} domestic dropped); {COMPANY.name}: {len(totals)} company x role x scenario"
    )


if __name__ == "__main__":
    main()
