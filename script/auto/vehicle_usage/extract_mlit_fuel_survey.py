"""Fuel Consumption Survey Table 1 -> vehicle_usage_jp.csv (distance and implied stock).

Input   raw/mlit_fuel_survey_fy<year>.xlsx        one workbook per fiscal year
        method/jp_segment_map.csv                 (fuel, operation, use, vehicle type) -> segment
Output  processed/vehicle_usage_jp.csv
        traffic_<segment>    total vehicle-kilometres, million vkm/year
        distance_<segment>   annual distance per vehicle, km/year
        stock_<segment>      vehicles implied by the two above

Two quantities on every row carry the benchmark: total vehicle-kilometres, and kilometres per
vehicle-day, which the survey defines as vehicle-kilometres divided by surveyed vehicles times
*calendar* days — not working days, which the separate working-day-rate column reports. Annual
distance per vehicle is therefore

    D_row = daily_km x 365

and the vehicles behind the row are traffic / D_row. A segment's distance is the traffic-weighted
mean of its rows, which is the same thing as its total traffic over its implied stock — so stock
and distance come from one table at one date, instead of joining a registration series to a
distance series published at another date, as the EU27 and US builds have to. The implied stock
is what confirms the calendar-day reading: it lands within 2 % of the registered fleet AIRIA
publishes for both cars and goods vehicles, where a working-day reading would overstate the
fleet by half.

The column positions move between editions (FY2024 puts vehicle-kilometres in column G, FY2025
in H), so every column is located by its header text. Subtotal rows are skipped; every other row
must appear in the segment map or the extractor stops, so a new vehicle type in a future edition
cannot be silently dropped. Fiscal years: FY2024 is April 2024 to March 2025.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_usage/extract_mlit_fuel_survey.py
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "vehicle_usage"
RAW = DATA / "raw"
MAP = DATA / "method" / "jp_segment_map.csv"
OUT = DATA / "processed" / "vehicle_usage_jp.csv"
SOURCE_ID = "mlit_fuel_consumption_survey"
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]
#: Verbatim header text of the source workbook -> the quantity that column holds. These two
#: strings are join keys, not prose: they must match what the sheet prints. In English they read
#: "vehicle-kilometres" and "kilometres per vehicle per day".
COLUMNS = {
    "走行キロ": "traffic_thousand_km",
    "1日1車当たり走行キロ": "daily_km",
}
#: Verbatim suffix of a subtotal label in the source workbook ("total").
SUBTOTAL_SUFFIX = "計"
#: The traffic column's verbatim header, used in the messages below.
TRAFFIC_HEADER = "走行キロ"
LABEL_COLUMNS = 4
DAYS = 365.0


def norm(value: object) -> str:
    """Label text with width, spacing and newlines normalised away."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value)).replace("　", " "))


def read_table(path: Path) -> list[tuple[tuple[str, ...], dict[str, float]]]:
    """[(label tuple, {quantity: value})] for one fiscal-year workbook."""
    df = pd.read_excel(path, header=None)
    header = None
    for i in range(len(df)):
        cells = [norm(v) for v in df.iloc[i]]
        if any(c.startswith(TRAFFIC_HEADER) for c in cells):
            header, columns = i, cells
            break
    if header is None:
        raise SystemExit(
            f"{path.name}: no header row carrying the vehicle-kilometres column ({TRAFFIC_HEADER})"
        )
    where: dict[str, int] = {}
    for j, cell in enumerate(columns):
        for prefix, quantity in COLUMNS.items():
            if cell.startswith(prefix) and quantity not in where:
                where[quantity] = j
    missing = set(COLUMNS.values()) - set(where)
    if missing:
        raise SystemExit(f"{path.name}: header carries no column for {sorted(missing)}")

    out: list[tuple[tuple[str, ...], dict[str, float]]] = []
    carried = [""] * (LABEL_COLUMNS + 1)
    for i in range(header + 1, len(df)):
        row = [norm(v) for v in df.iloc[i]]
        # Subtotals are written into the operation and use columns (commercial total,
        # private total, petrol total).
        if any(row[j].endswith(SUBTOTAL_SUFFIX) for j in (2, 3) if j < len(row)):
            continue
        labels = []
        for j in range(1, LABEL_COLUMNS + 1):
            cell = row[j] if j < len(row) else ""
            if cell:
                # A merged cell spans downward, so a label present at this level ends whatever
                # the deeper levels were carrying: the LPG block states no use or vehicle
                # type at all.
                carried[j] = cell
                for deeper in range(j + 1, LABEL_COLUMNS + 1):
                    carried[deeper] = ""
            labels.append(cell or carried[j])
        values: dict[str, float] = {}
        for quantity, j in where.items():
            value = pd.to_numeric(df.iat[i, j], errors="coerce")
            if not pd.isna(value):
                values[quantity] = float(value)
        if len(values) == len(COLUMNS):
            out.append((tuple(labels), values))
    return out


def main() -> None:
    """One row per fiscal year, segment and series."""
    segments = {
        (r["fuel"], r["operation"], r["use"], r["vehicle_type"]): r["segment"]
        for r in csv.DictReader(MAP.open(newline=""))
    }
    rows: list[dict[str, object]] = []
    for path in sorted(RAW.glob("mlit_fuel_survey_fy*.xlsx")):
        year = int(path.stem.rsplit("fy", 1)[1])
        traffic: dict[str, float] = {}
        stock: dict[str, float] = {}
        for labels, values in read_table(path):
            segment = segments.get(labels)
            if segment is None:
                raise SystemExit(f"{path.name}: {labels} is not in {MAP.name}")
            km = values["traffic_thousand_km"] * 1000.0
            per_vehicle = values["daily_km"] * DAYS
            if per_vehicle <= 0:
                raise SystemExit(f"{path.name}: {labels} has no working distance")
            traffic[segment] = traffic.get(segment, 0.0) + km
            stock[segment] = stock.get(segment, 0.0) + km / per_vehicle
        for segment in sorted(traffic):
            for series, value, unit in (
                (f"traffic_{segment}", traffic[segment] / 1e6, "million_vkm"),
                (f"distance_{segment}", traffic[segment] / stock[segment], "km_per_year"),
                (f"stock_{segment}", stock[segment], "vehicles"),
            ):
                rows.append(
                    {
                        "country": "JP",
                        "series": series,
                        "year": year,
                        "value": round(value, 3),
                        "unit": unit,
                        "source_id": SOURCE_ID,
                        "source_file": path.name,
                    }
                )
    rows.sort(key=lambda r: (str(r["series"]), int(str(r["year"]))))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    latest = max(int(str(r["year"])) for r in rows)
    shown = {
        str(r["series"]): float(str(r["value"]))
        for r in rows
        if int(str(r["year"])) == latest and str(r["series"]).startswith("distance_")
    }
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows; fiscal {latest} km per vehicle "
        + ", ".join(f"{k[9:]} {v:,.0f}" for k, v in sorted(shown.items()))
    )


if __name__ == "__main__":
    main()
