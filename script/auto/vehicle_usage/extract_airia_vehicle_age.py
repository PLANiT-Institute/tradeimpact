"""AIRIA age releases -> vehicle_usage_jp_lifetime.csv (mean age and published vehicle life).

Input   raw/airia_mean_age_2025.pdf        平均車齢
        raw/airia_mean_use_years_2025.pdf  平均使用年数
Output  processed/vehicle_usage_jp_lifetime.csv
        mean_age_<segment>         years since first registration, fleet mean
        mean_use_years_<segment>   years from first registration to deregistration

Both releases are prose, not tables: each states its headline as 「乗用車は 13.35 年」 with the
per-body-type breakdown 「普通乗用車は 12.74 年」 following in the same paragraph. The reader
normalises the page text, then takes the headline figure for each of the three vehicle classes it
needs, refusing a match that is preceded by 普通, 小型, 軽 or 大型 so a body-type line cannot be
read as the class total.

平均使用年数 is the expected vehicle life the lifetime horizon needs, published rather than
derived — but AIRIA's own note says the figure counts a 一時抹消登録 (temporary deregistration)
as an ending, so it is a little shorter than years-to-scrappage. That makes it a floor on the
operating life, and the reference builder brackets it.

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
#: AIRIA vehicle class -> the project's segment name.
CLASSES = {
    "乗用車": "passenger_car",
    "貨物車": "freight",
    "乗合車": "bus",
}
#: file -> (series prefix, what it measures)
RELEASES = {
    "airia_mean_age_2025.pdf": ("mean_age", "平均車齢"),
    "airia_mean_use_years_2025.pdf": ("mean_use_years", "平均使用年数"),
}
#: a class total is never preceded by a body-size prefix (普通/小型/軽/大型).
PREFIX = "(?<![通型軽大])"


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
            found = re.search(rf"{PREFIX}{label}は([0-9.]+)年", text)
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
