"""Reshape the OWID grid-intensity export to the long format the model reads.

Input   data/power/grid/raw/owid_carbon_intensity_electricity.csv
        data/power/geography/processed/country_codes.csv         (alpha-3 -> alpha-2)
Output  data/power/grid/processed/grid_intensity.csv
        country, series, year, value, unit, source_id, source_file — every country with an ISO
        code; OWID's own aggregates (codes starting OWID_) and the World row are dropped.

Run from the repository root:  .venv/bin/python script/power/grid/extract_owid_grid.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, num, read_csv, write_csv  # noqa: E402

RAW = DATA / "grid" / "raw" / "owid_carbon_intensity_electricity.csv"
CODES = DATA / "geography" / "processed" / "country_codes.csv"
OUT = DATA / "grid" / "processed" / "grid_intensity.csv"
SOURCE_ID = "owid_ember_grid_intensity"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]
KEY_COLUMNS = {"Entity", "Code", "Year"}


def value_column(fieldnames: list[str]) -> str:
    """The one data column of a grapher export: whatever is not Entity, Code or Year."""
    rest = [c for c in fieldnames if c not in KEY_COLUMNS]
    if len(rest) != 1:
        raise SystemExit(f"expected one value column in the OWID export, found {rest}")
    return rest[0]


def main() -> None:
    """Write one row per country and year."""
    if not RAW.exists():
        hand_file_required(RAW, "run script/power/grid/fetch_owid_grid.py")
    if not CODES.exists():
        hand_file_required(CODES, "run script/power/geography/extract_country_codes.py")
    alpha2 = {r["alpha3"]: r["alpha2"] for r in read_csv(CODES) if r["alpha3"]}
    raw = read_csv(RAW)
    column = value_column(list(raw[0]))
    out: list[dict[str, object]] = []
    unmapped: set[str] = set()
    for row in raw:
        code = row["Code"]
        if not code or code.startswith("OWID_"):
            continue
        value = num(row[column])
        if value is None:
            continue
        if code not in alpha2:
            unmapped.add(code)
            continue
        out.append(
            {
                "country": alpha2[code],
                "series": "grid_intensity",
                "year": int(row["Year"]),
                "value": value,
                "unit": "gCO2_per_kWh",
                "source_id": SOURCE_ID,
                "source_file": RAW.name,
            }
        )
    out.sort(key=lambda r: (str(r["country"]), int(str(r["year"]))))
    write_csv(OUT, FIELDS, out)
    countries = {str(r["country"]) for r in out}
    print(
        f"{OUT.relative_to(REPO)}: {len(out)} rows, {len(countries)} countries; "
        f"ISO-3 codes without an alpha-2 (dropped): {sorted(unmapped) or 'none'}"
    )


if __name__ == "__main__":
    main()
