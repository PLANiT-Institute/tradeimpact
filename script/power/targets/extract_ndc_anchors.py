"""Read each destination's committed target out of the Climate Watch NDC content.

Inputs
    targets/raw/climatewatch_ndc_content.json    GHG target text, type and target year per country
                                                 and per NDC submission (fetch_climatewatch_ndc.py)
    targets/raw/ndc_anchors_power.csv            HAND overrides: rows that replace or add a country
    projects/processed/projects_gem.csv          the destinations that need an anchor
    geography/processed/country_codes.csv        alpha-2 <-> alpha-3
Output
    targets/processed/ndc_anchors_power.csv      one row per destination with the anchor the S2
                                                 rate is read from, its parse status and the
                                                 target text it came from

Rule: the latest submission on file for the country is used (third NDC over second over updated
first over first over INDC). A **base-year target** ("61-66 percent below 2005 levels by 2035")
is machine-read into reduction, base year and target year: the unconditional figure where the
text distinguishes one, otherwise the lower bound of a range (recorded as ``reduction`` with the
upper bound in ``reduction_upper``), and the furthest target year the text states (the project
lead's rule: the pathway runs to the government's furthest stated year). A **baseline-scenario**
(BAU) target has no absolute level and is recorded as not usable; a **GDP-intensity** target
likewise; **fixed-level** and **trajectory** targets need the base-year emissions the text does
not carry and are recorded as ``needs_review`` for a hand row. A hand row in
raw/ndc_anchors_power.csv replaces the parsed row for its country.

Run from the repository root:  .venv/bin/python script/power/targets/extract_ndc_anchors.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, read_csv, write_csv  # noqa: E402

RAW = DATA / "targets" / "raw" / "climatewatch_ndc_content.json"
HAND = DATA / "targets" / "raw" / "ndc_anchors_power.csv"
PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
CODES = DATA / "geography" / "processed" / "country_codes.csv"
SOURCES = DATA / "registry" / "sources.csv"
OUT = DATA / "targets" / "processed" / "ndc_anchors_power.csv"
SOURCE_ID = "climatewatch_ndc_content"
DOCUMENT_ORDER = ["indc", "first_ndc", "revised_first_ndc", "second_ndc", "third_ndc"]
FIELDS = [
    "country",
    "iso3",
    "anchor_id",
    "scope",
    "target_type",
    "base_year",
    "base_value",
    "base_unit",
    "target_year",
    "target_value",
    "reduction",
    "reduction_upper",
    "conditional",
    "communicated",
    "document",
    "source_url",
    "source_id",
    "verified",
    "parse_status",
    "target_text",
    "origin",
    "note",
]
PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*(?:(?:-|to)\s*(\d+(?:\.\d+)?)\s*)?%")
YEAR = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
BASE_WORDS = ("below", "compar", "relative", "from", "than", "against", "base")
FIRST_TARGET_YEAR = 2026
TEXT_LIMIT = 300


def clean(text: str) -> str:
    """Target text without markup, with one spelling of percent and of the dash."""
    t = re.sub(r"<[^>]+>", " ", text or "")
    t = t.replace("–", "-").replace("—", "-").replace("−", "-")
    t = re.sub(r"\bper\s?cent\b|\bpercent\b", "%", t, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", t).strip()


def latest(values: list[dict[str, str]]) -> dict[str, str] | None:
    """The value from the most recent submission type."""
    ranked = sorted(
        values,
        key=lambda v: (
            DOCUMENT_ORDER.index(v["document_slug"]) if v["document_slug"] in DOCUMENT_ORDER else -1
        ),
    )
    return ranked[-1] if ranked else None


def base_year_of(text: str) -> int | None:
    """The year the reduction is measured against (a comparison word before it or 'level' after)."""
    for m in YEAR.finditer(text):
        before = text[max(0, m.start() - 40) : m.start()].lower()
        after = text[m.end() : m.end() + 14].lower()
        year = int(m.group(1))
        if year <= FIRST_TARGET_YEAR and (
            any(w in before for w in BASE_WORDS) or "level" in after or "base" in after
        ):
            return year
    return None


def parse_base_year_target(text: str, fallback_years: list[int]) -> dict[str, object] | None:
    """Reduction, upper bound, base year and target year from a base-year target sentence."""
    pcts = [
        (m.start(), float(m.group(1)), float(m.group(2)) if m.group(2) else None)
        for m in PERCENT.finditer(text)
    ]
    if not pcts:
        return None
    lower = text.lower()

    def following_year(pos: int) -> int | None:
        window = text[pos : pos + 45]
        years = [int(y) for y in YEAR.findall(window) if int(y) >= FIRST_TARGET_YEAR]
        return years[0] if years else None

    chosen = None
    unconditional = [m.start() for m in re.finditer(r"unconditional", lower)]
    if unconditional:
        near = [(min(abs(p - u) for u in unconditional), p, lo, hi) for p, lo, hi in pcts]
        near = [n for n in near if n[0] <= 80]
        if near:
            _, p, lo, hi = min(near)
            chosen = (p, lo, hi)
    if chosen is None:
        paired = [(following_year(p) or 0, p, lo, hi) for p, lo, hi in pcts]
        if any(y for y, *_ in paired):
            _, p, lo, hi = max(paired)
            chosen = (p, lo, hi)
        else:
            chosen = pcts[0]
    p, lo, hi = chosen
    target_year = following_year(p) or (max(fallback_years) if fallback_years else None)
    base_year = base_year_of(text)
    if target_year is None or base_year is None or lo >= 100:
        return None
    return {
        "reduction": round(lo / 100, 6),
        "reduction_upper": round(hi / 100, 6) if hi is not None else "",
        "base_year": base_year,
        "target_year": target_year,
    }


def years_in(text: str) -> list[int]:
    """Every four-digit year in a target-year field such as '2030 and 2035'."""
    return [int(y) for y in YEAR.findall(text or "")]


def classify(target_type: str) -> str:
    """Our target_type from Climate Watch's type label."""
    t = (target_type or "").lower()
    if "base year" in t:
        return "reduction_from_base"
    if "baseline" in t:
        return "bau_reduction"
    if "intensity" in t:
        return "gdp_intensity"
    if "fixed" in t:
        return "fixed_level"
    if "trajectory" in t:
        return "trajectory"
    if "not applicable" in t or not t:
        return "none"
    return "other"


def anchor_for(
    alpha2: str, iso3: str, values: dict[str, list[dict[str, str]]]
) -> dict[str, object]:
    """The parsed anchor row for one destination."""
    target = latest(values.get("ghg_target", []))
    row: dict[str, object] = {k: "" for k in FIELDS}
    row.update(
        {
            "country": alpha2,
            "iso3": iso3,
            "scope": "economy",
            "conditional": "no",
            "source_url": f"https://www.climatewatchdata.org/ndcs/country/{iso3}",
            "source_id": SOURCE_ID,
            "verified": "no",
            "origin": "climatewatch",
        }
    )
    if target is None:
        row.update({"target_type": "none", "parse_status": "no_ndc_target_on_file"})
        return row
    doc = target["document_slug"]
    same_doc = lambda slug: [v for v in values.get(slug, []) if v["document_slug"] == doc]  # noqa: E731
    type_value = (latest(same_doc("ghg_target_type")) or {}).get("value", "")
    year_value = (latest(same_doc("time_target_year")) or {}).get("value", "")
    text = clean(target["value"])
    kind = classify(type_value)
    row.update(
        {
            "anchor_id": f"{alpha2.lower()}_{doc}",
            "target_type": kind,
            "communicated": doc,
            "document": doc,
            "target_text": text[:TEXT_LIMIT],
            "note": f"Climate Watch type: {type_value}; target year field: {clean(year_value)}",
        }
    )
    if kind == "reduction_from_base":
        parsed = parse_base_year_target(text, years_in(year_value))
        if parsed:
            row.update(parsed)
            row["parse_status"] = "parsed"
        else:
            row["parse_status"] = "needs_review"
    elif kind in ("bau_reduction", "gdp_intensity"):
        row["parse_status"] = "not_usable"
    elif kind == "none":
        row["parse_status"] = "no_ndc_target_on_file"
    else:
        row["parse_status"] = "needs_review"
    return row


def main() -> None:
    """Write the anchor table: parsed rows, hand rows on top."""
    if not RAW.exists():
        hand_file_required(RAW, "run script/power/targets/fetch_climatewatch_ndc.py")
    if not PROJECTS.exists():
        hand_file_required(PROJECTS, "run script/power/projects/extract_gem_tracker.py")
    payload = json.loads(RAW.read_text(encoding="utf-8"))
    by_slug = {i["slug"]: i["locations"] for i in payload["indicators"]}
    codes = {r["alpha2"]: r["alpha3"] for r in read_csv(CODES)}
    destinations = sorted({r["country"] for r in read_csv(PROJECTS)})
    rows: list[dict[str, object]] = []
    for a2 in destinations:
        iso3 = codes.get(a2, "")
        values = {slug: locs.get(iso3, []) for slug, locs in by_slug.items()}
        rows.append(anchor_for(a2, iso3, values))
    hand = read_csv(HAND) if HAND.exists() else []
    known_sources = {r["source_id"] for r in read_csv(SOURCES)}
    for h in hand:
        if h["country"] not in destinations:
            continue
        if h["source_id"] not in known_sources:
            raise SystemExit(
                f"hand anchor {h['anchor_id']} cites source_id {h['source_id']!r}, "
                "which is not in registry/sources.csv"
            )
        rows = [r for r in rows if r["country"] != h["country"]]
        rows.append({**{k: "" for k in FIELDS}, **h, "parse_status": "hand", "origin": "hand"})
    rows.sort(key=lambda r: str(r["country"]))
    write_csv(OUT, FIELDS, rows)
    status = {}
    for r in rows:
        status[str(r["parse_status"])] = status.get(str(r["parse_status"]), 0) + 1
    print(f"{OUT.relative_to(REPO)}: {len(rows)} destinations; {dict(sorted(status.items()))}")


if __name__ == "__main__":
    main()
