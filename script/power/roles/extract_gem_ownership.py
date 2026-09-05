"""Read the equity role out of the tracker's Owner and Parent strings, share included.

Input   data/power/projects/processed/projects_gem.csv    owner / parent text per unit
        data/power/companies/method/companies.csv         patterns and HQ per company
Output  data/power/roles/processed/gem_ownership.csv
        one row per company x unit: level (owner | parent), entity as written, share (fraction or
        blank), the unit's wiki page as source

The tracker writes ownership as entities separated by "; ", each followed by its share in
brackets where known: ``Marubeni Corp [50.0%]; Chubu Electric Power Co Inc [50.0%]``. That is an
equity-owner role with a stated share, published by a third party from company disclosures — so
it seeds the role register (tier B) without hand transcription. Construction, equipment, O&M and
finance roles are not in the tracker and stay hand-gathered. Where the same company appears at
both levels the direct (owner) row is kept; a company whose HQ is the unit's country is skipped
(a domestic holding is not a trade).

Run from the repository root:  .venv/bin/python script/power/roles/extract_gem_ownership.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, read_csv, write_csv  # noqa: E402

PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
COMPANIES = DATA / "companies" / "method" / "companies.csv"
OUT = DATA / "roles" / "processed" / "gem_ownership.csv"
SOURCE_ID = "gem_global_integrated_power_tracker"
TOKEN = re.compile(r"^\s*(?P<name>.*?)\s*(?:\[(?P<share>[\d.]+)\s*%\])?\s*$")
FIELDS = [
    "company_id",
    "gem_unit_id",
    "gem_location_id",
    "plant_name",
    "country",
    "level",
    "entity",
    "share",
    "source_url",
    "source_id",
]


def parse_entities(text: str) -> list[tuple[str, float | None]]:
    """(entity name, share fraction or None) for each '; '-separated token of an owner string."""
    out: list[tuple[str, float | None]] = []
    for token in (text or "").split(";"):
        m = TOKEN.match(token)
        if not m or not m.group("name"):
            continue
        share = m.group("share")
        out.append((m.group("name"), float(share) / 100 if share else None))
    return out


def ownership_rows(
    units: list[dict[str, str]], companies: list[dict[str, str]]
) -> list[dict[str, object]]:
    """Equity rows for every in-scope company named in a unit's owner or parent text."""
    matchers = [
        (c["company_id"], c["country"], re.compile(c["gem_owner_pattern"], re.IGNORECASE))
        for c in companies
        if c["in_scope"] == "yes" and c["gem_owner_pattern"]
    ]
    out: list[dict[str, object]] = []
    for u in units:
        found: dict[str, dict[str, object]] = {}
        for level in ("owner", "parent"):
            for entity, share in parse_entities(u.get(level, "")):
                for cid, home, pattern in matchers:
                    if home == u["country"] or not pattern.search(entity) or cid in found:
                        continue
                    found[cid] = {
                        "company_id": cid,
                        "gem_unit_id": u["gem_unit_id"],
                        "gem_location_id": u["gem_location_id"],
                        "plant_name": u["plant_name"],
                        "country": u["country"],
                        "level": level,
                        "entity": entity,
                        "share": share if share is not None else "",
                        "source_url": u.get("wiki_url", ""),
                        "source_id": SOURCE_ID,
                    }
        out.extend(found.values())
    return out


def main() -> None:
    """Write the tracker-derived equity register."""
    if not PROJECTS.exists():
        hand_file_required(PROJECTS, "run script/power/projects/extract_gem_tracker.py")
    rows = ownership_rows(read_csv(PROJECTS), read_csv(COMPANIES))
    write_csv(OUT, FIELDS, rows)
    with_share = sum(1 for r in rows if r["share"] != "")
    by_company: dict[str, int] = {}
    for r in rows:
        by_company[str(r["company_id"])] = by_company.get(str(r["company_id"]), 0) + 1
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} company x unit equity rows, {with_share} with a "
        f"stated share; by company {dict(sorted(by_company.items(), key=lambda kv: -kv[1]))}"
    )


if __name__ == "__main__":
    main()
