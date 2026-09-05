"""Build the CO2 emission-factor table: national factors first, IPCC 2006 defaults otherwise.

Inputs
    emission_factors/method/ipcc_2006_table_2_2.csv     hand transcription of IPCC Table 2.2
    emission_factors/raw/ipcc_2006_v2_ch2_stationary_combustion.pdf   the chapter, for checking
    emission_factors/raw/national_emission_factors.csv  HAND-GATHERED: a country's own implied
                                                        factor per fuel (national inventory,
                                                        CRT table 1.A(a)) with a link per row
Output
    emission_factors/processed/emission_factors.csv
        country ('' = default for any country), fuel_id, ef_kgco2_per_tj, ef_low, ef_high,
        basis (national | ipcc_default), biogenic, source_id, source_url, tier

Rule (project lead, 2026-09-05): a unit's factor is the destination country's own fuel-specific
factor where one is on file, and the IPCC 2006 default otherwise. The model resolves that order;
this table carries both with the basis and tier that say which is which.

Verification: every default and bound in the transcription must occur in the PDF's own text
(thousands written with a space, comma or nothing), or the extractor stops. That is the check
that the hand-typed numbers are the published ones.

Run from the repository root:
    .venv/bin/python script/power/emission_factors/extract_emission_factors.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

DATASET = DATA / "emission_factors"
TABLE = DATASET / "method" / "ipcc_2006_table_2_2.csv"
PDF = DATASET / "raw" / "ipcc_2006_v2_ch2_stationary_combustion.pdf"
NATIONAL = DATASET / "raw" / "national_emission_factors.csv"
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
    for r in national:
        if r["fuel_id"] not in fuels:
            raise SystemExit(f"national factor names an unknown fuel_id: {r}")
        if not r["source_url"].startswith("http"):
            raise SystemExit(f"national factor without a source link: {r}")
        value = num(r["ef_kgco2_per_tj"])
        if value is None:
            raise SystemExit(f"national factor without a value: {r}")
        out.append(
            {
                "country": r["country"],
                "fuel_id": r["fuel_id"],
                "ef_kgco2_per_tj": value,
                "ef_low_kgco2_per_tj": "",
                "ef_high_kgco2_per_tj": "",
                "basis": "national",
                "biogenic": fuels[r["fuel_id"]]["biogenic"],
                "source_id": r["source_id"],
                "source_url": r["source_url"],
                "tier": "A",
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
