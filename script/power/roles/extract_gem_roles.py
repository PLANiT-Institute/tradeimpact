"""Read the investment and operation roles out of the tracker's own Owner, Parent and Operator text.

Input   data/power/projects/processed/projects_gem.csv    owner / parent / operator text per unit
        data/power/companies/method/companies.csv         patterns and HQ per company
        data/power/roles/method/roles.csv                 role vocabulary: phase and share basis
Output  data/power/roles/processed/gem_tracker_roles.csv
        one row per company x unit x role: the level it was read at, the entity as written, the
        share (fraction or blank), the unit's wiki page as source

The tracker states two of the five project roles itself:

    Owner(s) / Parent(s)  ->  equity_owner   (investment phase), with the share it prints in
                              brackets: ``Marubeni Corp [50.0%]; Chubu Electric [50.0%]``
    Operator(s)           ->  om_contractor  (operation phase); the tracker prints no share here

Both are a third party's compilation of company disclosures, so both are tier B and need no hand
transcription. Development, construction (EPC and equipment) and finance are not in the tracker:
those come from the wiki pages (``extract_wiki_roles.py``) or the hand register. Where the same
company appears at both owner and parent level the direct (owner) row is kept; a company whose HQ
is the unit's country is skipped (a domestic holding or a domestic operator is not a trade).

Run from the repository root:  .venv/bin/python script/power/roles/extract_gem_roles.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, read_csv, write_csv  # noqa: E402

PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
COMPANIES = DATA / "companies" / "method" / "companies.csv"
VOCAB = DATA / "roles" / "method" / "roles.csv"
OUT = DATA / "roles" / "processed" / "gem_tracker_roles.csv"
SOURCE_ID = "gem_global_integrated_power_tracker"
TOKEN = re.compile(r"^\s*(?P<name>.*?)\s*(?:\[(?P<share>[\d.]+)\s*%\])?\s*$")
#: Tracker column -> the role it states, in the order a company's rows are preferred.
LEVEL_ROLES = (("owner", "equity_owner"), ("parent", "equity_owner"), ("operator", "om_contractor"))
FIELDS = [
    "company_id",
    "gem_unit_id",
    "gem_location_id",
    "plant_name",
    "country",
    "role",
    "phase",
    "level",
    "entity",
    "share",
    "share_basis",
    "source_url",
    "source_id",
]


def parse_entities(text: str) -> list[tuple[str, float | None]]:
    """(entity name, share fraction or None) for each '; '-separated token of a tracker field."""
    out: list[tuple[str, float | None]] = []
    for token in (text or "").split(";"):
        m = TOKEN.match(token)
        if not m or not m.group("name"):
            continue
        share = m.group("share")
        out.append((m.group("name"), float(share) / 100 if share else None))
    return out


def tracker_rows(
    units: list[dict[str, str]],
    companies: list[dict[str, str]],
    vocab: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    """Investment and operation rows for every in-scope company the tracker names on a unit."""
    matchers = [
        (c["company_id"], c["country"], re.compile(c["gem_owner_pattern"], re.IGNORECASE))
        for c in companies
        if c["in_scope"] == "yes" and c["gem_owner_pattern"]
    ]
    out: list[dict[str, object]] = []
    for u in units:
        found: dict[tuple[str, str], dict[str, object]] = {}
        for level, role in LEVEL_ROLES:
            for entity, share in parse_entities(u.get(level, "")):
                for cid, home, pattern in matchers:
                    key = (cid, role)
                    if home == u["country"] or not pattern.search(entity) or key in found:
                        continue
                    found[key] = {
                        "company_id": cid,
                        "gem_unit_id": u["gem_unit_id"],
                        "gem_location_id": u["gem_location_id"],
                        "plant_name": u["plant_name"],
                        "country": u["country"],
                        "role": role,
                        "phase": vocab[role]["phase"],
                        "level": level,
                        "entity": entity,
                        "share": share if share is not None else "",
                        "share_basis": vocab[role]["share_basis"],
                        "source_url": u.get("wiki_url", ""),
                        "source_id": SOURCE_ID,
                    }
        out.extend(found.values())
    return out


def main() -> None:
    """Write the tracker-derived investment and operation register."""
    if not PROJECTS.exists():
        hand_file_required(PROJECTS, "run script/power/projects/extract_gem_tracker.py")
    vocab = {v["role"]: v for v in read_csv(VOCAB)}
    rows = tracker_rows(read_csv(PROJECTS), read_csv(COMPANIES), vocab)
    write_csv(OUT, FIELDS, rows)
    by_role: dict[str, int] = {}
    for r in rows:
        by_role[str(r["role"])] = by_role.get(str(r["role"]), 0) + 1
    with_share = sum(1 for r in rows if r["share"] != "")
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} company x unit x role rows, {with_share} with a "
        f"stated share; by role {dict(sorted(by_role.items()))}"
    )


if __name__ == "__main__":
    main()
