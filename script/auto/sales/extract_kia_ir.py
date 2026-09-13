"""Extract Kia IR retail sales by model and market into the sales schema.

Reads every ``data/auto/sales/raw/kia_<year>_retail_sales_by_model_market.xlsx`` (Kia IR,
"Retail Sales by Country", sheet ``Total`` = year-to-date sum of the monthly sheets) and
writes one ``data/auto/sales/processed/sales_kia_ir_<year>.csv`` per workbook.

The sheet lists models in blocks by production plant; a block ends with a subtotal row
whose label sits in column B (e.g. ``Korea Plants``). Market columns are Kia's IR regions,
so ``destination_level`` is ``region`` for Europe, Eastern Europe, Latin America, Middle
East, Africa and Asia Pacific. Labels are resolved through ``method/kia_labels.csv``; the
labels drift between editions (the 2024 workbook writes ``K5 / Optima`` where later editions
write ``K5``), so the map carries both spellings.

A cell can be negative when returns in the period exceed sales of a model the market no longer
takes; those cells are dropped rather than carried as volume, and the count is printed.

Kia's 2024 node was never refreshed past October, so that workbook is ten months. The missing
months are estimated rather than left as a hole: each cell is grown by the ratio the same
destination showed between the same months and the full year in the next year's workbook — Kia's
own monthly sheets, not an outside assumption. The estimate is written as separate rows carrying
``basis = retail_sales_estimated`` and the months they stand for, so it is visible in every table
and can be dropped by anyone who would rather have the hole. As a check on the method, the
2025 whole-company factor is 1.200 against a flat twelve-tenths of 1.200, and Korea's is 1.204.

Run from the repository root:  .venv/bin/python script/auto/sales/extract_kia_ir.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import load_workbook

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "sales"
RAW_DIR = DATASET / "raw"
RAW_GLOB = "kia_*_retail_sales_by_model_market.xlsx"
LABELS = DATASET / "method" / "kia_labels.csv"
PROCESSED = DATASET / "processed"

COMPANY = "kia"
BASIS = "retail_sales"
BASIS_ESTIMATED = "retail_sales_estimated"
HEADER_ROW = 4
FIRST_MARKET_COL = 7  # column H; column G is the derived "Total"
TOTAL_COL = 6  # column G
MODEL_COL = 4  # column E
BLOCK_COL = 1  # column B
TOTAL_SHEET = "Total"

FIELDS = [
    "company",
    "destination",
    "destination_level",
    "origin",
    "cohort_year",
    "period",
    "model",
    "powertrain",
    "units",
    "basis",
    "source_file",
]


def load_labels() -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """Return (market label -> (code, level), plant label -> origin code)."""
    markets: dict[str, tuple[str, str]] = {}
    plants: dict[str, str] = {}
    with LABELS.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["kind"] == "market":
                markets[row["label"]] = (row["code"], row["level"])
            else:
                plants[row["label"]] = row["code"]
    return markets, plants


def clean(label: object) -> str:
    """Normalise a header or row label: collapse whitespace, drop line breaks."""
    return " ".join(str(label).split())


def months_with_data(wb) -> list[int]:  # noqa: ANN001 - openpyxl workbook
    """Month numbers whose sheet carries a non-zero grand total.

    The monthly sheets follow the ``Total`` sheet in calendar order, but their names are not
    stable between editions (``Jun`` in the 2024 workbook, ``June`` from 2025), so the position
    governs and the name is not matched.
    """
    found = []
    for i, name in enumerate(wb.sheetnames[1:13], start=1):
        for row in wb[name].iter_rows(values_only=True):
            if row[BLOCK_COL] and clean(row[BLOCK_COL]).lower() == "total":
                if row[TOTAL_COL]:
                    found.append(i)
                break
    return found


def completion_factors(reference: Path, observed_months: int) -> dict[str, float]:
    """Per-destination ratio of a full year to its first ``observed_months``, from one workbook.

    Args:
        reference: A retail workbook that does cover twelve months.
        observed_months: How many months the workbook being completed carries.

    Returns:
        {market label: full-year units / units of the first ``observed_months``}. A destination
        the reference year records no volume for is absent, and the caller falls back.
    """
    wb = load_workbook(reference, data_only=True, read_only=True)
    header = list(wb[TOTAL_SHEET].iter_rows(values_only=True))[HEADER_ROW - 1]
    columns = {
        col: clean(header[col]) for col in range(FIRST_MARKET_COL, len(header)) if header[col]
    }
    early: dict[int, float] = dict.fromkeys(columns, 0.0)
    whole: dict[int, float] = dict.fromkeys(columns, 0.0)
    for i, sheet in enumerate(wb.sheetnames[1:13], start=1):
        for row in wb[sheet].iter_rows(values_only=True):
            if row[BLOCK_COL] and clean(row[BLOCK_COL]).lower() == "total":
                for col in columns:
                    value = row[col] if isinstance(row[col], int | float) else 0.0
                    whole[col] += value
                    if i <= observed_months:
                        early[col] += value
                break
    wb.close()
    return {
        columns[col]: whole[col] / early[col]
        for col in columns
        if early[col] > 0 and whole[col] > 0
    }


def extract(path: Path, markets: dict[str, tuple[str, str]], plants: dict[str, str]) -> Path:
    """Flatten one workbook's Total sheet to one row per model x market with units > 0.

    Args:
        path: Raw workbook in data/auto/sales/raw.
        markets: Market label -> (destination code, destination level).
        plants: Plant block label -> origin code.

    Returns:
        The processed CSV written.
    """
    wb = load_workbook(path, data_only=True, read_only=True)
    if wb.sheetnames[0] != TOTAL_SHEET:
        raise SystemExit(f"{path.name}: first sheet is {wb.sheetnames[0]!r}, not {TOTAL_SHEET!r}")
    ws = wb[TOTAL_SHEET]
    rows = list(ws.iter_rows(values_only=True))

    header = rows[HEADER_ROW - 1]
    title = clean(rows[0][16])  # "Total. 2026, Kia ..." carries the year
    year = int(next(tok.strip(",") for tok in title.split() if tok.strip(",").isdigit()))
    if f"kia_{year}_" not in path.name:
        raise SystemExit(f"{path.name}: the Total sheet is titled {title!r}")
    months = months_with_data(wb)
    period = f"{year}-{months[0]:02d}..{year}-{months[-1]:02d}"

    market_cols: list[tuple[int, str, str]] = []
    for col in range(FIRST_MARKET_COL, len(header)):
        if header[col] is None:
            break
        label = clean(header[col])
        if label not in markets:
            raise SystemExit(f"unmapped market label {label!r}: add it to {LABELS.name}")
        code, level = markets[label]
        market_cols.append((col, code, level))

    out: list[dict[str, object]] = []
    labels: list[str] = []  # the market label of out[i], for the completion step
    returns = 0
    pending: list[tuple[str, list[object]]] = []
    for row in rows[HEADER_ROW:]:
        block = clean(row[BLOCK_COL]) if row[BLOCK_COL] else ""
        model = clean(row[MODEL_COL]) if row[MODEL_COL] else ""
        if block.lower() == "total":
            break
        if block:
            if block not in plants:
                raise SystemExit(f"unmapped plant label {block!r}: add it to {LABELS.name}")
            origin = plants[block]
            for pending_model, values in pending:
                for col, code, level in market_cols:
                    units = values[col]
                    if units in (None, "", 0):
                        continue
                    if int(units) < 0:
                        returns += 1
                        continue
                    labels.append(clean(header[col]))
                    out.append(
                        {
                            "company": COMPANY,
                            "destination": code,
                            "destination_level": level,
                            "origin": origin,
                            "cohort_year": year,
                            "period": period,
                            "model": pending_model,
                            "powertrain": "",
                            "units": int(units),
                            "basis": BASIS,
                            "source_file": path.name,
                        }
                    )
            pending = []
        elif model and row[TOTAL_COL] is not None:
            pending.append((model, list(row)))

    if pending:
        raise SystemExit(f"{len(pending)} model rows without a closing plant subtotal")

    estimated = complete_the_year(path, out, labels, year, months)
    out = out + estimated
    out.sort(
        key=lambda r: (str(r["basis"]), str(r["origin"]), str(r["model"]), str(r["destination"]))
    )
    dest = PROCESSED / f"sales_kia_ir_{year}.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out)

    total = sum(int(r["units"]) for r in out)
    tail = f", {returns} net-negative cell(s) dropped" if returns else ""
    if estimated:
        share = sum(int(r["units"]) for r in estimated) / total
        tail += f"; {len(estimated)} estimated row(s), {share:.1%} of the units"
    print(f"{dest.relative_to(REPO)}: {len(out)} rows, {total:,} units, period {period}{tail}")
    return dest


def complete_the_year(
    path: Path,
    observed: list[dict[str, object]],
    labels: list[str],
    year: int,
    months: list[int],
) -> list[dict[str, object]]:
    """Rows standing for the months a truncated workbook never received.

    Kia overwrites one node per year, so a year whose node stopped early is never completed at
    the source. A year with no later workbook beside it is still running and is left alone.
    Each observed cell is grown by the ratio the same destination showed between the same months
    and the full year in the next year's workbook; where that year records no volume for the
    destination, the whole-company ratio stands in.

    Args:
        path: The workbook being completed.
        observed: The rows already extracted from it.
        labels: The market label of each observed row, aligned with it.
        year: The workbook's calendar year.
        months: Month numbers the workbook carries.

    Returns:
        One row per observed cell with a non-zero estimate, carrying ``retail_sales_estimated``
        and the months it stands for. Empty when the workbook is a full year.
    """
    if months == list(range(1, 13)):
        return []
    # A later year's workbook on disk is the evidence that this year is over and was abandoned
    # short. Without one the year is simply still running, and its missing months have not
    # happened yet: a year to date is completed by waiting, never by estimating.
    reference = RAW_DIR / f"kia_{year + 1}_retail_sales_by_model_market.xlsx"
    if not reference.exists():
        print(f"  {path.name}: {len(months)} months, year still in progress; not completed")
        return []
    factors = completion_factors(reference, len(months))
    default = 12.0 / len(months)
    period = f"{year}-{months[-1] + 1:02d}..{year}-12"
    estimated: list[dict[str, object]] = []
    for row, label in zip(observed, labels, strict=True):
        units = int(round(int(str(row["units"])) * (factors.get(label, default) - 1.0)))
        if units <= 0:
            continue
        estimated.append({**row, "period": period, "units": units, "basis": BASIS_ESTIMATED})
    return estimated


def main() -> None:
    """Extract every retail workbook on disk, one processed file per year."""
    markets, plants = load_labels()
    paths = sorted(RAW_DIR.glob(RAW_GLOB))
    if not paths:
        raise SystemExit(f"no workbook matching {RAW_GLOB} in {RAW_DIR}")
    for path in paths:
        extract(path, markets, plants)


if __name__ == "__main__":
    main()
