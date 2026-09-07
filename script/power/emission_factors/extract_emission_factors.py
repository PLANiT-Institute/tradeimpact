"""Build the CO2 emission-factor table: national factors first, IPCC 2006 defaults otherwise.

Inputs
    emission_factors/method/ipcc_2006_table_2_2.csv     hand transcription of IPCC Table 2.2
    emission_factors/raw/ipcc_2006_v2_ch2_stationary_combustion.pdf   the chapter, for checking
    emission_factors/raw/national_emission_factors.csv  HAND-READ: a destination's own factor
                                                        per fuel, one row per country x fuel,
                                                        citing the document and quoting its line
    emission_factors/raw/national_documents/index.csv   the inventory documents, with URL,
                                                        SHA-256 and licence per document
Output
    emission_factors/processed/emission_factors.csv
        country ('' = default for any country), fuel_id, ef_kgco2_per_tj, ef_low, ef_high,
        basis (national | national_adopted | ipcc_default), biogenic, source_id, source_url, tier

Rule (project lead, 2026-09-05): a unit's factor is the destination country's own fuel-specific
factor where one is on file, and the IPCC 2006 default otherwise. Three bases, in that order:

    national          the country measured it and publishes it as country-specific (tier A)
    national_adopted  the country's own instrument publishes the IPCC value as its factor, so the
                      number is the default but the provenance is national (tier B)
    ipcc_default      the country states none and the IPCC default stands in (tier C)

Verification, both ways. Every IPCC default and bound in the transcription must occur in the
chapter PDF's own text (thousands written with a space, comma or nothing). Every national row must
cite a ``source_key`` in the fetched document index whose URL matches the row, and its ``quote``
must appear in that document's own text, with the factor's digits inside the quote. A row whose
document is not on disk, or whose quote is not the document's words, is rejected.

Run from the repository root:
    .venv/bin/python script/power/emission_factors/extract_emission_factors.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402
from provenance import normalise, page_text, quote_is_on_the_page  # noqa: E402

DATASET = DATA / "emission_factors"
TABLE = DATASET / "method" / "ipcc_2006_table_2_2.csv"
PDF = DATASET / "raw" / "ipcc_2006_v2_ch2_stationary_combustion.pdf"
NATIONAL = DATASET / "raw" / "national_emission_factors.csv"
DOCUMENTS = DATASET / "raw" / "national_documents"
DOCUMENT_INDEX = DOCUMENTS / "index.csv"
#: A national row's basis and the tier it carries.
NATIONAL_BASES = {"national": "A", "national_adopted": "B"}
#: How a document's printed number becomes kg CO2 per TJ. Every national row names one, and the
#: extractor re-does the arithmetic: the row's factor has to follow from the number in the quote.
#:     kg_co2_per_tj  already in kg CO2/TJ, however the document punctuates thousands
#:     t_co2_per_tj   tonnes CO2/TJ (x 1000)
#:     tc_per_tj      tonnes of carbon per TJ, the Chinese guideline's unit (x 44/12 x 1000)
CONVERSIONS = {
    "kg_co2_per_tj": lambda v: v,
    "t_co2_per_tj": lambda v: v * 1e3,
    "tc_per_tj": lambda v: v * (44 / 12) * 1e3,
}
#: Tolerance on re-doing that arithmetic, in kg CO2/TJ: the documents round to whole numbers.
CONVERSION_TOLERANCE = 1.0
OUT = DATASET / "processed" / "emission_factors.csv"
IPCC_SOURCE_ID = "ipcc_2006_v2_ch2"
FIELDS = [
    "country",
    "fuel_id",
    "ef_kgco2_per_tj",
    "ef_low_kgco2_per_tj",
    "ef_high_kgco2_per_tj",
    "basis",
    "biogenic",
    "source_id",
    "source_url",
    "tier",
]


def number_pattern(value: float) -> re.Pattern[str]:
    """Regex matching an integer factor as the PDF may render it: 98 300, 98,300 or 98300."""
    digits = str(int(round(value)))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        return re.compile(rf"(?<!\d){head}[ , ]?{tail}(?!\d)")
    return re.compile(rf"(?<!\d){digits}(?!\d)")


def verify_transcription(rows: list[dict[str, str]], pdf_text: str) -> list[str]:
    """Return the (fuel, column) pairs whose number is not in the chapter text."""
    missing = []
    for r in rows:
        for column in ("ef_kgco2_per_tj", "ef_low_kgco2_per_tj", "ef_high_kgco2_per_tj"):
            value = num(r[column])
            if value is None or not number_pattern(value).search(pdf_text):
                missing.append(f"{r['fuel_id']}.{column}={r[column]}")
    return missing


def validate_national(
    rows: list[dict[str, str]],
    fuels: dict[str, dict[str, str]],
    documents: dict[str, dict[str, str]],
) -> list[str]:
    """Problems in the national register, one message per failing row and check."""
    problems: list[str] = []
    texts: dict[str, str] = {}
    for i, r in enumerate(rows, start=2):
        where = f"row {i} ({r.get('country')} / {r.get('fuel_id')})"
        if r["fuel_id"] not in fuels:
            problems.append(f"{where}: unknown fuel_id")
        if r["basis"] not in NATIONAL_BASES:
            problems.append(f"{where}: basis must be one of {sorted(NATIONAL_BASES)}")
        value = num(r["ef_kgco2_per_tj"])
        if value is None or value <= 0:
            problems.append(f"{where}: needs a positive factor in kg CO2 per TJ")
        document = documents.get(r["source_key"])
        if document is None:
            problems.append(f"{where}: source_key {r['source_key']!r} is not in the document index")
            continue
        if document["url"] != r["source_url"]:
            problems.append(f"{where}: source_url does not match the document index")
        if document["country"] != r["country"]:
            problems.append(
                f"{where}: the document is {document['country']}'s, so it cannot state "
                f"{r['country']}'s factor"
            )
        path = DOCUMENTS / document["file"]
        if not path.exists():
            problems.append(f"{where}: {document['file']} is not on disk")
            continue
        if r["source_key"] not in texts:
            texts[r["source_key"]] = page_text(path)
        if not r["quote"].strip():
            problems.append(f"{where}: quote is required (the document's own table line)")
            continue
        if not quote_is_on_the_page(r["quote"], texts[r["source_key"]]):
            problems.append(f"{where}: quote is not in {document['file']}")
            continue
        problems.extend(check_derivation(where, r, value))
    return problems


def check_derivation(where: str, row: dict[str, str], value: float | None) -> list[str]:
    """The printed number must be in the quote and must give the row's factor once converted."""
    printed = row["document_value"].strip()
    conversion = CONVERSIONS.get(row["conversion"])
    if not printed:
        return [f"{where}: document_value is required (the number as the document prints it)"]
    if conversion is None:
        return [f"{where}: conversion must be one of {sorted(CONVERSIONS)}"]
    if printed not in normalise(row["quote"]):
        return [f"{where}: document_value {printed!r} is not in the quote"]
    parsed = num(printed.replace(" ", "").replace(",", "." if printed.count(",") == 1 else ""))
    if parsed is None:
        return [f"{where}: document_value {printed!r} is not a number"]
    if row["conversion"] == "kg_co2_per_tj":
        parsed = num(re.sub(r"[ ,.]", "", printed))
    if parsed is None or value is None:
        return [f"{where}: cannot check the derivation"]
    derived = conversion(parsed)
    if abs(derived - value) > CONVERSION_TOLERANCE:
        return [
            f"{where}: {printed} {row['conversion']} gives {derived:,.0f} kg CO2/TJ, "
            f"not the {value:,.0f} on the row"
        ]
    return []


def main() -> None:
    """Verify the transcription, merge national factors, write the table."""
    if not PDF.exists():
        hand_file_required(PDF, "run script/power/emission_factors/fetch_ipcc_defaults.py")
    table = read_csv(TABLE)
    text = " ".join(page.extract_text() or "" for page in PdfReader(str(PDF)).pages)
    missing = verify_transcription(table, text)
    if missing:
        raise SystemExit(f"transcription not found in the IPCC chapter text: {missing}")
    out: list[dict[str, object]] = []
    for r in table:
        out.append(
            {
                "country": "",
                "fuel_id": r["fuel_id"],
                "ef_kgco2_per_tj": num(r["ef_kgco2_per_tj"]),
                "ef_low_kgco2_per_tj": num(r["ef_low_kgco2_per_tj"]),
                "ef_high_kgco2_per_tj": num(r["ef_high_kgco2_per_tj"]),
                "basis": "ipcc_default",
                "biogenic": r["biogenic"],
                "source_id": IPCC_SOURCE_ID,
                "source_url": "https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol2.html",
                "tier": "C",
            }
        )
    fuels = {r["fuel_id"]: r for r in table}
    national = read_csv(NATIONAL) if NATIONAL.exists() else []
    documents = (
        {r["source_key"]: r for r in read_csv(DOCUMENT_INDEX)} if DOCUMENT_INDEX.exists() else {}
    )
    problems = validate_national(national, fuels, documents)
    if problems:
        raise SystemExit("national factor register rejected:\n  " + "\n  ".join(problems))
    for r in national:
        out.append(
            {
                "country": r["country"],
                "fuel_id": r["fuel_id"],
                "ef_kgco2_per_tj": num(r["ef_kgco2_per_tj"]),
                "ef_low_kgco2_per_tj": "",
                "ef_high_kgco2_per_tj": "",
                "basis": r["basis"],
                "biogenic": fuels[r["fuel_id"]]["biogenic"],
                "source_id": r["source_id"],
                "source_url": r["source_url"],
                "tier": NATIONAL_BASES[r["basis"]],
            }
        )
    write_csv(OUT, FIELDS, out)
    print(
        f"{OUT.relative_to(REPO)}: {len(table)} IPCC defaults verified against the chapter text, "
        f"{len(national)} national factors on file"
        + ("" if national else " (hand file raw/national_emission_factors.csv is header-only)")
    )


if __name__ == "__main__":
    main()
