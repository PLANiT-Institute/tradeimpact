"""AIRIA age releases -> vehicle_usage_jp_lifetime.csv (mean age and published vehicle life).

Input   raw/airia_mean_age_2025.pdf        mean vehicle age
        raw/airia_mean_use_years_2025.pdf  mean years of use
Output  processed/vehicle_usage_jp_lifetime.csv
        mean_age_<segment>         years since first registration, fleet mean
        mean_use_years_<segment>   years from first registration to deregistration

Both releases are prose, not tables: each states its headline as "passenger cars are 13.35
years" with the per-body-type breakdown ("standard passenger cars are 12.74 years") following in
the same paragraph. The reader normalises the page text, then takes the headline figure for each
of the three vehicle classes it needs, refusing a match preceded by a body-size prefix
(standard, small, kei, large) so a body-type line cannot be read as the class total.

Mean years of use is the expected vehicle life the lifetime horizon needs, published rather than
derived — but AIRIA's own note says the figure counts a temporary deregistration as an ending,
so it is a little shorter than years-to-scrappage. That makes it a floor on the operating life,
and the reference builder brackets it.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_usage/extract_airia_vehicle_age.py
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import pypdf

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "vehicle_usage"
RAW = DATA / "raw"
OUT = DATA / "processed" / "vehicle_usage_jp_lifetime.csv"
SOURCE_ID = "airia_vehicle_age"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]
#: Vehicle class as the release writes it (a join key, matched against the PDF text) -> the
#: project's segment name. In English the three read "passenger car", "goods vehicle" and "bus".
CLASSES = {
    "乗用車": "passenger_car",
    "貨物車": "freight",
    "乗合車": "bus",
}
#: file -> (series prefix, what it measures)
RELEASES = {
    "airia_mean_age_2025.pdf": ("mean_age", "mean vehicle age"),
    "airia_mean_use_years_2025.pdf": ("mean_use_years", "mean years of use"),
}
#: A class total is never preceded by a body-size prefix; these four characters end the words
#: for standard, small, kei and large, so the lookbehind rejects a body-type line.
PREFIX = "(?<![通型軽大])"
#: Verbatim sentence frame of the released figure: "<class> is <number> years".
SENTENCE = "は([0-9.]+)年"


def page_text(path: Path) -> str:
    """Normalised text of the release's first page."""
    reader = pypdf.PdfReader(path)
    text = "".join(page.extract_text() or "" for page in reader.pages[:1])
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def main() -> None:
    """One row per release and segment."""
    rows: list[dict[str, object]] = []
    for name, (prefix, what) in sorted(RELEASES.items()):
        path = RAW / name
        year = int(name.rsplit("_", 1)[1].split(".")[0])
        text = page_text(path)
        for label, segment in CLASSES.items():
            found = re.search(rf"{PREFIX}{label}{SENTENCE}", text)
            if found is None:
                raise SystemExit(f"{name}: no {what} headline for {label}")
            rows.append(
                {
                    "country": "JP",
                    "series": f"{prefix}_{segment}",
                    "year": year,
                    "value": float(found.group(1)),
                    "unit": "years",
                    "source_id": SOURCE_ID,
                    "source_file": name,
                }
            )
    rows.sort(key=lambda r: (str(r["series"]), int(str(r["year"]))))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; "
        + ", ".join(f"{r['series']} {r['value']}" for r in rows)
    )


if __name__ == "__main__":
    main()
