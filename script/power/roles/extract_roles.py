"""Validate the hand-gathered role register and join it to the company table.

Input   data/power/roles/raw/project_roles.csv         HAND-GATHERED (see method.md)
        data/power/roles/method/roles.csv              role vocabulary: phase and share basis
        data/power/companies/method/companies.csv
Output  data/power/roles/processed/project_roles.csv

Every row must name a known company and role, carry the role's phase and share basis, a share in
(0, 1] or blank, at least one tracker id, and a source link. A failing row stops the extractor
by name: a role that cannot be traced is not attributed. A header-only register is reported as
pending and yields a header-only output, so the pipeline runs on the tracker's equity rows alone.

Run from the repository root:  .venv/bin/python script/power/roles/extract_roles.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

DATASET = DATA / "roles"
RAW = DATASET / "raw" / "project_roles.csv"
VOCAB = DATASET / "method" / "roles.csv"
COMPANIES = DATA / "companies" / "method" / "companies.csv"
OUT = DATASET / "processed" / "project_roles.csv"
FIELDS = [
    "company_id",
    "company_name",
    "company_country",
    "company_type",
    "gem_unit_id",
    "gem_location_id",
    "plant_name",
    "country",
    "role",
    "phase",
    "share",
    "share_basis",
    "from_year",
    "to_year",
    "source_url",
    "source_note",
    "accessed_date",
]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(
    rows: list[dict[str, str]],
    vocab: dict[str, dict[str, str]],
    companies: dict[str, dict[str, str]],
) -> list[str]:
    """Problems found in the register, one message per failing row and check."""
    problems = []
    for i, r in enumerate(rows, start=2):
        where = f"row {i} ({r.get('company_id')} / {r.get('plant_name')} / {r.get('role')})"
        if r["company_id"] not in companies:
            problems.append(f"{where}: unknown company_id")
        role = vocab.get(r["role"])
        if role is None:
            problems.append(f"{where}: unknown role")
        else:
            if r["phase"] != role["phase"]:
                problems.append(f"{where}: phase must be {role['phase']}")
            if r["share_basis"] != role["share_basis"]:
                problems.append(f"{where}: share_basis must be {role['share_basis']}")
        share = num(r["share"])
        if r["share"] and (share is None or not 0 < share <= 1):
            problems.append(f"{where}: share must be blank or in (0, 1]")
        if not r["gem_unit_id"] and not r["gem_location_id"]:
            problems.append(f"{where}: needs gem_unit_id or gem_location_id")
        if not r["source_url"].startswith("http"):
            problems.append(f"{where}: source_url must be a link")
        if not DATE.match(r["accessed_date"]):
            problems.append(f"{where}: accessed_date must be YYYY-MM-DD")
    return problems


def main() -> None:
    """Validate and write the register."""
    if not RAW.exists():
        hand_file_required(RAW, "create the register with the header in method.md")
    rows = read_csv(RAW)
    if not rows:
        write_csv(OUT, FIELDS, [])
        print(
            f"HAND FILE PENDING (header-only): {RAW.relative_to(REPO)} - construction, "
            "equipment, O&M and finance roles are not attributed until it is filled; equity "
            "roles come from the tracker's owner shares (roles/processed/gem_ownership.csv)"
        )
        return
    vocab = {v["role"]: v for v in read_csv(VOCAB)}
    companies = {c["company_id"]: c for c in read_csv(COMPANIES)}
    problems = validate(rows, vocab, companies)
    if problems:
        raise SystemExit("role register rejected:\n  " + "\n  ".join(problems))
    out: list[dict[str, object]] = []
    for r in rows:
        c = companies[r["company_id"]]
        out.append(
            {
                **{k: r.get(k, "") for k in FIELDS},
                "company_name": c["name_en"],
                "company_country": c["country"],
                "company_type": c["type"],
            }
        )
    write_csv(OUT, FIELDS, out)
    roles = {}
    for r in out:
        roles[str(r["role"])] = roles.get(str(r["role"]), 0) + 1
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows; by role {dict(sorted(roles.items()))}")


if __name__ == "__main__":
    main()
