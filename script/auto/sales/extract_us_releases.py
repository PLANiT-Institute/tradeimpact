"""US sales releases -> sales_toyota_us.csv, sales_nissan_us.csv and the Nissan origin split.

Inputs (data/auto/sales/raw/, written by fetch_us_releases.py)
    tmna_us_sales_<year>.csv     Toyota Motor North America: models by division, and a second
                                 table giving model x powertrain
    nissan_us_sales_<year>.csv   Nissan Group: Nissan and Infiniti models, and Nissan Division
                                 volumes split into North American production and imports

Outputs (data/auto/sales/processed/)
    sales_toyota_us.csv          company x model x powertrain x cohort year
    sales_nissan_us.csv          company x model x cohort year (the release states no powertrain)
    us_release_origin_split.csv  company x cohort year x origin: the published split of US
                                 volumes into North American production and imports

Toyota's powertrain, and the subtraction it needs. The electrified table is an overlay on the
model table, not a second set of rows: the Camry appears in both because every Camry sold is a
hybrid. Combustion volume is therefore the model total minus its electrified rows, never a sum
of the two tables. Rows in the electrified table are read from their suffix (HYBRID, PLUG-IN
HYBRID, BEV); the nameplates that are electrified without carrying a suffix are listed in
ELECTRIFIED_WITHOUT_SUFFIX so that an unknown label fails loudly instead of defaulting.

Division. Toyota's table groups models under subtotals, and a group belongs to the division its
subtotal names, so the Lexus models land under ``lexus`` and Toyota's under ``toyota``. Both
companies' totals are checked against the published division totals. Nissan's Infiniti models
land under ``infiniti``. ``companies.csv`` decides which of those is in scope.

Run from the repository root:  .venv/bin/python script/auto/sales/extract_us_releases.py
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "sales"
RAW = DATASET / "raw"
OUT_TOYOTA = DATASET / "processed" / "sales_toyota_us.csv"
OUT_NISSAN = DATASET / "processed" / "sales_nissan_us.csv"
OUT_ORIGIN = DATASET / "processed" / "us_release_origin_split.csv"

SALES_FIELDS = [
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
    "source_id",
    "source_file",
]
ORIGIN_FIELDS = [
    "company",
    "cohort_year",
    "origin",
    "body",
    "units",
    "source_id",
    "source_file",
]
#: Electrified rows whose label states no powertrain: these nameplates are sold in one form only.
ELECTRIFIED_WITHOUT_SUFFIX = {
    "MIRAI": "FCEV",
    "CROWN": "HEV",
    "CROWN SIGNIA": "HEV",
}
#: Nissan nameplates that are battery-electric; the rest of its US line-up is combustion only.
NISSAN_BEV = {"LEAF", "ARIYA"}
NISSAN_NOT_A_MODEL = {
    "Nissan Division Total",
    "Infiniti Division Total",
    "TOTAL VEHICLE",
    "Total Car",
    "Total Truck",
    "North American produced",
    "Import",
    "Car",
    "Truck",
    "Selling days",
}
DIVISION_SUBTOTAL = re.compile(r"^TOTAL (TOYOTA|LEXUS) DIV\.\s+(CAR|SUV|PICKUP|TRUCK)$")
#: Toyota prints both blocks inside one table; this heading starts the second one.
ELECTRIFIED_HEADING = "ELECTRIFIED VEHICLE SALES SUMMARY"
#: What a division total exceeds the printed model rows by is kept as its own row rather than
#: dropped, so a cohort still sums to the figure the company published.
RESIDUAL_MODEL = "OTHER (NOT PRINTED AS A MODEL ROW)"


def read_raw(path: Path) -> list[dict[str, str]]:
    """Rows of one raw release CSV."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def units(value: str) -> int | None:
    """'248,088' -> 248088; blanks, percentages and dashes -> None."""
    text = value.replace(",", "").replace("‑", "-").strip()
    if not text or "%" in text or text in {"-", "--"}:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def years_of(path: Path) -> tuple[int, int]:
    """(release year, comparison year) from the file name."""
    year = int(path.stem.rsplit("_", 1)[1])
    return year, year - 1


def sales_row(
    company: str, year: int, model: str, powertrain: str, value: int, path: Path, source_id: str
) -> dict[str, object]:
    """One processed sales row."""
    return {
        "company": company,
        "destination": "US",
        "destination_level": "country",
        "origin": "",
        "cohort_year": year,
        "period": f"{year}-01..{year}-12",
        "model": model,
        "powertrain": powertrain,
        "units": value,
        "basis": "brand_total_sales",
        "source_id": source_id,
        "source_file": path.name,
    }


def toyota_rows(path: Path) -> list[dict[str, object]]:
    """Toyota and Lexus models by powertrain, for both years in the release."""
    raw = read_raw(path)
    split = [i for i, r in enumerate(raw) if ELECTRIFIED_HEADING in r["label"].upper()]
    if not split:
        raise SystemExit(f"{path.name}: no {ELECTRIFIED_HEADING!r} heading, so no powertrain block")
    model_block, electrified_block = raw[: split[0]], raw[split[0] :]
    out: list[dict[str, object]] = []
    for year, column in zip(years_of(path), ("units_cy", "units_cy_prior"), strict=True):
        totals: dict[tuple[str, str], int] = {}
        published: dict[str, int] = {}
        buffer: list[tuple[str, int]] = []
        for r in model_block:
            label, value = r["label"].strip(), units(r[column])
            division = DIVISION_SUBTOTAL.match(label)
            if division:
                company = division.group(1).lower()
                for model, model_units in buffer:
                    totals[(company, model)] = model_units
                buffer = []
                continue
            if label in {"TOTAL TOYOTA DIV.", "TOTAL LEXUS DIV."}:
                published[label.split()[1].lower()] = value or 0
                continue
            if label.startswith("TOTAL") or value is None:
                continue
            buffer.append((label, value))

        electrified: dict[tuple[str, str, str], int] = {}
        for r in electrified_block:
            label, value = r["label"].strip(), units(r[column])
            if value is None or label.upper().startswith("TOTAL"):
                continue
            parts = label.split(" ", 1)
            if len(parts) != 2 or parts[0].upper() not in {"TOYOTA", "LEXUS"}:
                continue
            company, rest = parts[0].lower(), parts[1].strip()
            for suffix, powertrain in (
                (" PLUG-IN HYBRID", "PHEV"),
                (" HYBRID", "HEV"),
                (" BEV", "BEV"),
            ):
                if rest.upper().endswith(suffix):
                    electrified[(company, rest[: -len(suffix)].strip(), powertrain)] = value
                    break
            else:
                powertrain = ELECTRIFIED_WITHOUT_SUFFIX.get(rest.upper())
                if powertrain is None:
                    raise SystemExit(
                        f"{path.name}: electrified row {label!r} states no powertrain and is "
                        "not listed in ELECTRIFIED_WITHOUT_SUFFIX"
                    )
                electrified[(company, rest, powertrain)] = value

        for (company, model), total in totals.items():
            mine = {pt: v for (c, m, pt), v in electrified.items() if c == company and m == model}
            combustion = total - sum(mine.values())
            if combustion < 0:
                raise SystemExit(
                    f"{path.name} {year} {company} {model}: electrified rows sum to "
                    f"{sum(mine.values()):,} above the model total {total:,}"
                )
            for powertrain, value in sorted(mine.items()):
                if value:
                    out.append(
                        sales_row(
                            company, year, model, powertrain, value, path, "tmna_us_sales_release"
                        )
                    )
            if combustion:
                out.append(
                    sales_row(
                        company, year, model, "ICE", combustion, path, "tmna_us_sales_release"
                    )
                )
        for company, total in published.items():
            got = sum(
                int(str(r["units"]))
                for r in out
                if r["company"] == company and r["cohort_year"] == year
            )
            if got > total:
                raise SystemExit(
                    f"{path.name} {year}: {company} models sum to {got:,} above the published "
                    f"division total {total:,}"
                )
            if got < total:
                # The release's own division total exceeds the model rows it prints (6 units in
                # 2025). Keep the difference rather than lose it; it carries no powertrain, so
                # the model map withholds it downstream with a stated reason.
                out.append(
                    sales_row(
                        company,
                        year,
                        RESIDUAL_MODEL,
                        "",
                        total - got,
                        path,
                        "tmna_us_sales_release",
                    )
                )
                print(f"  {path.name} {year} {company}: {total - got:,} units not printed by model")
    return out


def nissan_rows(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Nissan and Infiniti models, and the published origin split."""
    raw = read_raw(path)
    sales: list[dict[str, object]] = []
    origin: list[dict[str, object]] = []
    for year, column in zip(years_of(path), ("units_cy", "units_cy_prior"), strict=True):
        for table, company in (("1", "nissan"), ("2", "infiniti")):
            total = None
            got = 0
            block = None
            for r in raw:
                if r["table"] != table:
                    continue
                label, value = r["label"].strip(), units(r[column])
                if label in {"Nissan Division Total", "Infiniti Division Total"}:
                    total = value
                    continue
                if label in {"North American produced", "Import"}:
                    block = "north_american_produced" if label[0] == "N" else "import"
                if label in NISSAN_NOT_A_MODEL:
                    if (
                        block
                        and value is not None
                        and label in {"Car", "Truck", "North American produced", "Import"}
                    ):
                        origin.append(
                            {
                                "company": company,
                                "cohort_year": year,
                                "origin": block,
                                "body": "total"
                                if label in {"North American produced", "Import"}
                                else label.lower(),
                                "units": value,
                                "source_id": "nissan_us_sales_release",
                                "source_file": path.name,
                            }
                        )
                    continue
                if value is None:
                    continue
                model = label.replace("‑", "-")
                powertrain = "BEV" if model.upper() in NISSAN_BEV else ""
                sales.append(
                    sales_row(
                        company, year, model, powertrain, value, path, "nissan_us_sales_release"
                    )
                )
                got += value
            if total is not None and got != total:
                raise SystemExit(
                    f"{path.name} {year}: {company} models sum to {got:,}, "
                    f"the release says {total:,}"
                )
    return sales, origin


def write(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    """Write one processed table."""
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Extract every US release on disk."""
    toyota: list[dict[str, object]] = []
    nissan: list[dict[str, object]] = []
    origin: list[dict[str, object]] = []
    for path in sorted(RAW.glob("tmna_us_sales_*.csv")):
        toyota += toyota_rows(path)
    for path in sorted(RAW.glob("nissan_us_sales_*.csv")):
        rows, split = nissan_rows(path)
        nissan += rows
        origin += split
    write(OUT_TOYOTA, SALES_FIELDS, toyota)
    write(OUT_NISSAN, SALES_FIELDS, nissan)
    write(OUT_ORIGIN, ORIGIN_FIELDS, origin)
    for name, rows in (("toyota", toyota), ("nissan", nissan)):
        per: dict[tuple[str, int], int] = defaultdict(int)
        for r in rows:
            per[(str(r["company"]), int(str(r["cohort_year"])))] += int(str(r["units"]))
        summary = ", ".join(f"{c} {y} {v:,}" for (c, y), v in sorted(per.items()))
        print(f"{name}: {len(rows)} rows; {summary}")
    print(f"{OUT_ORIGIN.relative_to(REPO)}: {len(origin)} rows")


if __name__ == "__main__":
    main()
