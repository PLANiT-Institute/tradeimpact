"""Reduce the world-countries JSON to the code table the other extractors join on.

Input   data/power/geography/raw/world_countries.json
Output  data/power/geography/processed/country_codes.csv
        alpha2, alpha3, iso_numeric, name_common, name_official

Run from the repository root:  .venv/bin/python script/power/geography/extract_country_codes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, write_csv  # noqa: E402

RAW = DATA / "geography" / "raw" / "world_countries.json"
OUT = DATA / "geography" / "processed" / "country_codes.csv"
FIELDS = ["alpha2", "alpha3", "iso_numeric", "name_common", "name_official"]


def main() -> None:
    """Write one row per country with an alpha-2 code."""
    if not RAW.exists():
        hand_file_required(RAW, "run script/power/geography/fetch_country_codes.py")
    rows = []
    for c in json.loads(RAW.read_text(encoding="utf-8")):
        if not c.get("cca2"):
            continue
        rows.append(
            {
                "alpha2": c["cca2"],
                "alpha3": c.get("cca3", ""),
                "iso_numeric": c.get("ccn3", ""),
                "name_common": c["name"]["common"],
                "name_official": c["name"]["official"],
            }
        )
    rows.sort(key=lambda r: str(r["alpha2"]))
    write_csv(OUT, FIELDS, rows)
    print(f"{OUT.relative_to(REPO)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
