"""Check the transcribed technology defaults against the documents they are cited from.

Input   projects/method/technology_defaults.csv        the transcribed lifetime, capacity factor
                                                       and thermal efficiency per technology
        projects/method/technology_document_values.csv  which document number each row is checked
                                                        against, and on which heating value
        projects/raw/technology_documents/*.pdf|.html   the documents themselves
Output  projects/processed/technology_defaults_check.csv
        one row per default, with the document's own number beside the transcribed one

Why this exists: the efficiency, capacity factor and lifetime a unit falls back on when the
tracker publishes none are hand-transcribed numbers, and a hand-transcribed number is only as good
as the document a reader can open. The check reads the heat rate straight out of the EIA report's
text, converts it to a net-calorific-value efficiency, and reports the gap against the
transcription.

Algorithm:
    A heat rate in Btu per kWh on a higher-heating-value basis is a thermal efficiency
    $$ \\eta_{HHV} = \\frac{3412.14}{HR_{Btu/kWh}}, \\qquad
       \\eta_{LHV} = \\eta_{HHV} \\cdot \\frac{HHV}{LHV} $$
    ASCII: eta_hhv = 3412.14 / heat_rate_btu_per_kwh; eta_lhv = eta_hhv * hhv_to_lhv_ratio
    3412.14 Btu is one kWh of electricity. The IPCC 2006 emission factors this model multiplies
    by are stated per TJ of net calorific value, so the efficiency has to be on the same basis;
    the ratio comes from the method file, per fuel.

Run from the repository root:
    .venv/bin/python script/power/projects/verify_technology_defaults.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

DATASET = DATA / "projects"
DEFAULTS = DATASET / "method" / "technology_defaults.csv"
DOCUMENT_VALUES = DATASET / "method" / "technology_document_values.csv"
RAW_DIR = DATASET / "raw" / "technology_documents"
INDEX = RAW_DIR / "index.csv"
OUT = DATASET / "processed" / "technology_defaults_check.csv"
#: Btu of electricity in one kWh (exact by definition of the Btu and the kWh).
BTU_PER_KWH = 3412.14
#: A thermal plant's heat rate sits in this range; a capacity in MW is below it and a capital
#: cost in $/kW above the first of them, which is what makes the table line unambiguous.
MIN_HEAT_RATE, MAX_HEAT_RATE = 4000.0, 20000.0
#: A transcription this far from the document's own number, relatively, is reported as a gap.
TOLERANCE = 0.10
FIELDS = [
    "fuel_type",
    "technology_pattern",
    "parameter",
    "transcribed",
    "document_value",
    "document_unit",
    "document_technology",
    "document_derived",
    "relative_gap",
    "verdict",
    "source_key",
    "source_url",
    "note",
]


def heat_rates(pdf: Path) -> dict[str, float]:
    """Technology -> nominal heat rate in Btu/kWh, as the report's Table 1 prints it.

    A table line reads ``Ultra Supercritical Coal (USC)10 650 8,800 3,636 42.1 4.6 N``: the name,
    an optional footnote number, the nominal capacity in MW, the heat rate, then costs. The heat
    rate is taken as the first number on the line inside the plausible range for a thermal plant,
    which is unambiguous because a capacity in MW sits below it and the capital cost in $/kW sits
    after it. Lines whose heat rate the report prints as ``N/A`` (nuclear, wind, solar, storage)
    are skipped rather than read as their capital cost.
    """
    reader = PdfReader(pdf)
    number = re.compile(r"\d[\d,]*(?:\.\d+)?")
    out: dict[str, float] = {}
    for page in reader.pages:
        text = page.extract_text() or ""
        if "Heat Rate" not in text:
            continue
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if "N/A" in line or not line[:1].isalpha():
                continue
            tokens = list(number.finditer(line))
            if len(tokens) < 4:
                continue
            name = re.sub(r"\s+", " ", line[: tokens[0].start()]).strip()
            rate = next(
                (
                    value
                    for t in tokens
                    if MIN_HEAT_RATE
                    <= (value := float(t.group(0).replace(",", "")))
                    <= MAX_HEAT_RATE
                ),
                None,
            )
            if name and rate is not None:
                out.setdefault(name, rate)
    return out


def efficiency_from_heat_rate(heat_rate_btu_per_kwh: float, hhv_to_lhv_ratio: float) -> float:
    """Net-calorific-value thermal efficiency implied by a higher-heating-value heat rate."""
    return BTU_PER_KWH / heat_rate_btu_per_kwh * hhv_to_lhv_ratio


def verdict(transcribed: float | None, derived: float | None) -> tuple[str, float | str]:
    """Verdict and relative gap for one comparison."""
    if transcribed is None or derived is None:
        return "no_document_value", ""
    gap = (transcribed - derived) / derived
    return ("agrees" if abs(gap) <= TOLERANCE else "differs"), round(gap, 4)


def main() -> None:
    """Compare every transcribed default with its document and write the check table."""
    if not INDEX.exists():
        hand_file_required(INDEX, "run script/power/projects/fetch_technology_documents.py")
    index = {r["source_key"]: r for r in read_csv(INDEX)}
    mapped = {(r["fuel_type"], r["technology_pattern"]): r for r in read_csv(DOCUMENT_VALUES)}
    rates: dict[str, dict[str, float]] = {}
    out: list[dict[str, object]] = []
    for d in read_csv(DEFAULTS):
        key = (d["fuel_type"], d["technology_pattern"])
        m = mapped.get(key)
        transcribed = num(d["efficiency_lhv"])
        document_value: float | None = None
        derived: float | None = None
        source_key = m["source_key"] if m else ""
        if m:
            entry = index[source_key]
            if source_key not in rates:
                rates[source_key] = heat_rates(RAW_DIR / entry["file"])
            document_value = rates[source_key].get(m["document_technology"])
            if document_value is not None:
                derived = efficiency_from_heat_rate(document_value, float(m["hhv_to_lhv_ratio"]))
        result, gap = verdict(transcribed, derived)
        out.append(
            {
                "fuel_type": d["fuel_type"],
                "technology_pattern": d["technology_pattern"],
                "parameter": "efficiency_lhv",
                "transcribed": transcribed if transcribed is not None else "",
                "document_value": document_value if document_value is not None else "",
                "document_unit": "Btu/kWh (HHV)" if document_value is not None else "",
                "document_technology": m["document_technology"] if m else "",
                "document_derived": round(derived, 4) if derived is not None else "",
                "relative_gap": gap,
                "verdict": result,
                "source_key": source_key,
                "source_url": index[source_key]["url"] if source_key else d["source_url"],
                "note": m["note"]
                if m
                else "no heat rate for this technology class in the "
                "documents on file; the transcription stands on its own citation",
            }
        )
    write_csv(OUT, FIELDS, out)
    counts: dict[str, int] = {}
    for r in out:
        counts[str(r["verdict"])] = counts.get(str(r["verdict"]), 0) + 1
    gaps = [r for r in out if r["verdict"] == "differs"]
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} defaults checked, {dict(sorted(counts.items()))}"
        + (
            "; gaps: "
            + ", ".join(
                f"{r['fuel_type']}/{r['document_technology']} {r['relative_gap']:+}" for r in gaps
            )
            if gaps
            else ""
        )
    )


if __name__ == "__main__":
    main()
