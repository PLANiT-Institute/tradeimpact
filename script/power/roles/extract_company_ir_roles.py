"""Validate the company-disclosure role register and join it to the company table.

Input   roles/raw/company_ir_roles.csv          the register: one row per company x plant x role,
                                                read by hand from a page that is on disk
        roles/raw/company_ir/index.csv          the pages, with their URLs and SHA-256
        roles/method/roles.csv                  role vocabulary: phase and share basis
        companies/method/companies.csv
Output  roles/processed/company_ir_roles.csv

Every row must name a known company and role, carry a share in (0, 1] or blank, at least one
tracker id, and — the point of this register — a ``role_source_key`` that exists in the fetched
page index whose URL matches the row's ``role_source_url``; the same for ``share_source_key``
wherever a share is stated. A row that cites a page not on disk is rejected, so no role and no
share can enter the model without a page a reader can open.

This register outranks the machine readings (tracker fields, wiki sentences) in
``aggregate_roles.py``: a company's own words, or a project page quoted with its sentence, beat a
keyword match — and it is the only source that can name a **specific** tier-2 scope (boiler
supply, civil works, a buyer's credit) rather than the ``*_unspecified`` role a keyword read
gives. The unit ids here also bring their units into scope in
``projects/extract_gem_tracker.py``, which is how projects the tracker's owner field misses — the
Korean and Japanese sponsors of Vung Ang 2 and Jawa 9-10, for instance — enter the result set.

Run from the repository root:  .venv/bin/python script/power/roles/extract_company_ir_roles.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, num, read_csv, write_csv  # noqa: E402

DATASET = DATA / "roles"
RAW = DATASET / "raw" / "company_ir_roles.csv"
PAGES = DATASET / "raw" / "company_ir" / "index.csv"
VOCAB = DATASET / "method" / "roles.csv"
COMPANIES = DATA / "companies" / "method" / "companies.csv"
OUT = DATASET / "processed" / "company_ir_roles.csv"
FIELDS = [
    "company_id",
    "company_name",
    "company_country",
    "company_type",
    "gem_unit_id",
    "gem_location_id",
    "plant_name",
    "country",
    "role_tier1",
    "role_tier2",
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
    pages: dict[str, dict[str, str]],
) -> list[str]:
    """Problems found in the register, one message per failing row and check."""
    problems = []
    for i, r in enumerate(rows, start=2):
        where = f"row {i} ({r.get('company_id')} / {r.get('plant_name')} / {r.get('role_tier2')})"
        if r["company_id"] not in companies:
            problems.append(f"{where}: unknown company_id")
        if r["role_tier2"] not in vocab:
            problems.append(f"{where}: unknown role_tier2 (see method/roles.csv)")
        share = num(r["share"])
        if r["share"] and (share is None or not 0 < share <= 1):
            problems.append(f"{where}: share must be blank or in (0, 1]")
        if not r["gem_unit_id"] and not r["gem_location_id"]:
            problems.append(f"{where}: needs gem_unit_id or gem_location_id")
        if not DATE.match(r["accessed_date"]):
            problems.append(f"{where}: accessed_date must be YYYY-MM-DD")
        for kind in ("role", "share"):
            key, url = r[f"{kind}_source_key"], r[f"{kind}_source_url"]
            if kind == "share" and not r["share"]:
                if key or url:
                    problems.append(f"{where}: share source given without a share")
                continue
            if not key:
                problems.append(f"{where}: {kind}_source_key is required")
                continue
            page = pages.get(key)
            if page is None:
                problems.append(f"{where}: {kind}_source_key {key!r} is not in the page index")
            elif page["url"] != url:
                problems.append(f"{where}: {kind}_source_url does not match the page index")
            if not r[f"{kind}_quote"].strip():
                problems.append(f"{where}: {kind}_quote is required (the sentence read)")
    return problems


def main() -> None:
    """Validate and write the register."""
    if not RAW.exists():
        write_csv(OUT, FIELDS, [])
        print(f"no company register on file ({RAW.relative_to(REPO)}); wrote an empty table")
        return
    rows = read_csv(RAW)
    pages = {p["source_key"]: p for p in read_csv(PAGES)} if PAGES.exists() else {}
    vocab = {v["role_tier2"]: v for v in read_csv(VOCAB)}
    companies = {c["company_id"]: c for c in read_csv(COMPANIES)}
    problems = validate(rows, vocab, companies, pages)
    if problems:
        raise SystemExit("company register rejected:\n  " + "\n  ".join(problems))
    out: list[dict[str, object]] = []
    for r in rows:
        c = companies[r["company_id"]]
        note = f"{r['role_as_stated']} — “{r['role_quote']}” ({r['role_source_url']})"
        if r["share"]:
            note += f"; share from {r['share_source_url']}: “{r['share_quote']}”"
        if r["note"]:
            note += f"; {r['note']}"
        out.append(
            {
                "company_id": r["company_id"],
                "company_name": c["name_en"],
                "company_country": c["country"],
                "company_type": c["type"],
                "gem_unit_id": r["gem_unit_id"],
                "gem_location_id": r["gem_location_id"],
                "plant_name": r["plant_name"],
                "country": r["country"],
                "role_tier1": vocab[r["role_tier2"]]["role_tier1"],
                "role_tier2": r["role_tier2"],
                "phase": vocab[r["role_tier2"]]["phase"],
                "share": r["share"],
                "share_basis": vocab[r["role_tier2"]]["share_basis"],
                "from_year": r["from_year"],
                "to_year": r["to_year"],
                "source_url": r["role_source_url"],
                "source_note": note,
                "accessed_date": r["accessed_date"],
            }
        )
    write_csv(OUT, FIELDS, out)
    by_role: dict[str, int] = {}
    for r in out:
        key = f"{r['role_tier1']}/{r['role_tier2']}"
        by_role[key] = by_role.get(key, 0) + 1
    companies_named = {str(r["company_id"]) for r in out}
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rows for {len(companies_named)} companies from "
        f"{len(pages)} pages on disk; by role {dict(sorted(by_role.items()))}"
    )


if __name__ == "__main__":
    main()
