"""Read construction, equipment, finance, operation and ownership roles from the GEM wiki pages.

Input   roles/raw/gem_wiki/*.txt               one readable page file per plant, wikitext under a
                                               provenance header (fetch_gem_wiki.py)
        roles/raw/gem_wiki/index.csv           file -> page title, URL, SHA-256, fetch date
        projects/processed/projects_gem.csv    page -> units / locations
        companies/method/companies.csv         patterns, HQ and type per company
        roles/method/roles.csv                 role vocabulary: phase and share basis
Output  roles/processed/gem_wiki_roles.csv
        one row per company x plant location x role, with the sentence it was read from

Method: the page text (markup, references, templates and tables removed) is split into sentences;
a sentence that names an in-scope company is classified by the company's type and the role words
it contains — EPC / turnkey / contractor for a builder, boiler / turbine / supply for an equipment
maker, loan / debt / financing for a lender, insurance / guarantee for export-credit cover,
"operation and maintenance" for an operator, stake / equity / consortium for an owner. Sentences
about intentions, protests, scandals, memoranda or quotations are skipped. The developer role is
read only from an explicit development statement ("developed the project", "project developer",
"the sponsors are"), never from a proposal or a short-list. A share
stated as a percentage within the same sentence after the company name is kept. Every row carries
the sentence, so the reading can be checked; the rows are tier C (a keyword reading of narrative
text, unverified) and a hand row in raw/project_roles.csv replaces them.

Run from the repository root:  .venv/bin/python script/power/roles/extract_wiki_roles.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, read_csv, write_csv  # noqa: E402

RAW_DIR = DATA / "roles" / "raw" / "gem_wiki"
INDEX = RAW_DIR / "index.csv"
#: The header line each page file puts before the wikitext.
MARKER = "--- wikitext as returned by the API ---"
PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
COMPANIES = DATA / "companies" / "method" / "companies.csv"
VOCAB = DATA / "roles" / "method" / "roles.csv"
OUT = DATA / "roles" / "processed" / "gem_wiki_roles.csv"
SOURCE_ID = "gem_wiki"
FIELDS = [
    "company_id",
    "gem_location_id",
    "plant_name",
    "country",
    "role",
    "phase",
    "share",
    "share_basis",
    "sentence",
    "source_url",
    "source_id",
]
#: Role words by role; the company's type decides which roles a sentence may support.
WORDS = {
    "epc_contractor": re.compile(
        r"\bEPC\b|engineering, procurement|turnkey|contractor|construction contract|"
        r"\b(?:build|built|construct(?:ed|ing)?) (?:the|a) (?:plant|project|station|units?)|"
        r"awarded",
        re.IGNORECASE,
    ),
    "equipment_supplier": re.compile(
        r"boiler|turbine|generator|equipment|suppl(?:y|ied|ier)|shipped|technology|manufactur",
        re.IGNORECASE,
    ),
    "lender": re.compile(
        r"\bloans?\b|lend|debt|financ(?:e|ed|ing)\b|funding|credit facility", re.IGNORECASE
    ),
    "eca_cover": re.compile(r"insur|guarantee|cover(?:age)?\b|export credit", re.IGNORECASE),
    "om_contractor": re.compile(
        r"operation and maintenance|O&M|\boperator\b|operated by", re.IGNORECASE
    ),
    "equity_owner": re.compile(
        r"\bstakes?\b|equity|sharehold|owner|owned|acquir|consortium|sponsor|joint venture|"
        r"\bpartner|\bsold\b|\bbought\b|\bshares?\b",
        re.IGNORECASE,
    ),
    "developer": re.compile(
        r"develop(?:ed|ing) (?:the|this) (?:plant|project|station)|"
        r"\bdeveloper of\b|project developer|co-?developer|sponsors? (?:of|are|include)",
        re.IGNORECASE,
    ),
}
#: Roles a company of each type may be read into, in order of preference.
ROLES_BY_TYPE = {
    "eca_bank": ["lender", "eca_cover"],
    "eca_insurer": ["eca_cover", "lender"],
    "epc_contractor": ["epc_contractor", "equipment_supplier", "equity_owner"],
    "equipment_supplier": ["equipment_supplier", "epc_contractor", "equity_owner"],
    "utility": ["equity_owner", "om_contractor", "developer"],
    "genco": ["equity_owner", "om_contractor", "developer"],
    "trading_house": ["equity_owner", "om_contractor", "developer"],
    "developer": ["equity_owner", "om_contractor", "developer"],
}
NOISE = re.compile(
    r"consider|protest|demand|object|withdr|pull(?:ed|ing)? (?:out|their)|cancel|bribe|scandal|"
    r"alleg|lawsuit|court|activist|oppos|reportedly (?:in talks|interested)|may |might |could |"
    r"memorandum|\bMoU\b|short-?list|would not|unclear|not available|no longer|abandon|"
    r"[\"\u201c\u201d]",
    re.IGNORECASE,
)
SHARE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*(?:%|percent\b)")


def clean(wikitext: str) -> str:
    """Page text without comments, references, templates, tables, links and markup."""
    t = re.sub(r"<!--.*?-->", " ", wikitext, flags=re.S)
    t = re.sub(r"<ref[^>]*/>", " ", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", " ", t, flags=re.S)
    for _ in range(3):
        t = re.sub(r"\{\{[^{}]*\}\}", " ", t)
    t = re.sub(r"\{\|.*?\|\}", " ", t, flags=re.S)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", t)
    t = re.sub(r"'{2,}|={2,}|<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def sentences(text: str) -> list[str]:
    """Sentences of the cleaned page text."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"“])", text) if len(s.strip()) > 25]


def classify(sentence: str, company_type: str, name_span: tuple[int, int] = (0, 0)) -> str | None:
    """The role a sentence supports for a company of this type, or None.

    Role words are looked for outside the company's own name, so "Nippon Export and Investment
    Insurance" is not read as insurance cover by its name alone.
    """
    if NOISE.search(sentence):
        return None
    rest = sentence[: name_span[0]] + " " + sentence[name_span[1] :]
    for role in ROLES_BY_TYPE.get(company_type, ["equity_owner"]):
        if WORDS[role].search(rest):
            return role
    return None


def share_after(sentence: str, name_end: int) -> float | None:
    """A percentage stated within 80 characters after the company name, as a fraction."""
    m = SHARE.search(sentence[name_end : name_end + 80])
    if not m:
        return None
    value = float(m.group(1))
    return value / 100 if 0 < value <= 100 else None


def read_roles(
    pages: dict[str, dict[str, object]],
    units_by_url: dict[str, list[dict[str, str]]],
    companies: list[dict[str, str]],
    vocab: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    """One row per company x location x role, first supporting sentence kept."""
    matchers = [
        (
            c["company_id"],
            c["country"],
            c["type"],
            re.compile(c["gem_owner_pattern"], re.IGNORECASE),
        )
        for c in companies
        if c["in_scope"] == "yes" and c["gem_owner_pattern"]
    ]
    out: dict[tuple[str, str, str], dict[str, object]] = {}
    for url, page in pages.items():
        text = page.get("wikitext")
        units = units_by_url.get(url, [])
        if not text or not units:
            continue
        locations = {(u["gem_location_id"], u["plant_name"], u["country"]) for u in units}
        for s in sentences(clean(str(text))):
            for cid, home, ctype, pattern in matchers:
                m = pattern.search(s)
                if not m:
                    continue
                role = classify(s, ctype, m.span())
                if role is None:
                    continue
                share = share_after(s, m.end())
                for lid, plant, country in locations:
                    if country == home:
                        continue
                    key = (cid, lid, role)
                    if key in out and (share is None or out[key]["share"] != ""):
                        continue
                    out[key] = {
                        "company_id": cid,
                        "gem_location_id": lid,
                        "plant_name": plant,
                        "country": country,
                        "role": role,
                        "phase": vocab[role]["phase"],
                        "share": share if share is not None else "",
                        "share_basis": vocab[role]["share_basis"],
                        "sentence": s[:400],
                        "source_url": url,
                        "source_id": SOURCE_ID,
                    }
    return sorted(
        out.values(), key=lambda r: (str(r["company_id"]), str(r["plant_name"]), str(r["role"]))
    )


def main() -> None:
    """Write the wiki-derived role table."""
    if not INDEX.exists():
        hand_file_required(INDEX, "run script/power/roles/fetch_gem_wiki.py")
    if not PROJECTS.exists():
        hand_file_required(PROJECTS, "run script/power/projects/extract_gem_tracker.py")
    pages: dict[str, dict[str, object]] = {}
    for entry in read_csv(INDEX):
        path = RAW_DIR / entry["file"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        body = text.split(MARKER, 1)[1] if MARKER in text else ""
        if body and "[no wikitext" not in body[:200]:
            pages[entry["url"]] = {"title": entry["page_title"], "wikitext": body}
    units_by_url: dict[str, list[dict[str, str]]] = {}
    for u in read_csv(PROJECTS):
        if u["wiki_url"]:
            units_by_url.setdefault(u["wiki_url"], []).append(u)
    vocab = {v["role"]: v for v in read_csv(VOCAB)}
    rows = read_roles(pages, units_by_url, read_csv(COMPANIES), vocab)
    write_csv(OUT, FIELDS, rows)
    by_role: dict[str, int] = {}
    for r in rows:
        by_role[str(r["role"])] = by_role.get(str(r["role"]), 0) + 1
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} company x location x role rows read from "
        f"{len(pages)} page files; by role {dict(sorted(by_role.items()))}"
    )


if __name__ == "__main__":
    main()
