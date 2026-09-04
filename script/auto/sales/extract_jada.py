"""JADA workbooks -> Japan registrations by nameplate, by maker and fuel, and by brand.

Inputs (data/auto/sales/raw/, fetched by fetch_jada.py)
    jada_model_ranking_<year>.xlsx        nameplate ranking, annual sheet, top 50
    jada_fuel_by_maker_<year>.xlsx        maker x fuel, one sheet per month
    jada_brand_registrations_<year>.xls   brand x vehicle class, one sheet per month
    ../method/jada_brands.csv             brand name as the workbook writes it -> company
    ../method/jp_model_names.csv          nameplate as the workbook writes it -> English name

Outputs (data/auto/sales/processed/)
    sales_jada_jp.csv              company x model x cohort year: Japan registrations, the
                                   companies in scope only, basis ``registrations``. ``model`` is
                                   the English nameplate and ``source_label`` the string the
                                   workbook prints, so the table joins in English and still says
                                   what it was read from.
    jada_fuel_mix_jp.csv           company x cohort year x powertrain: registrations and share,
                                   summed over the twelve monthly sheets, every maker
    jada_brand_registrations_jp.csv  company x cohort year: passenger-car registrations and the
                                   part of them built outside Japan (JADA's imported row)

Boundaries that travel with these tables. The nameplate ranking excludes kei cars and foreign
brands and is cut at the top 50, so it is a subset of a company's Japanese sales, not all of it;
the brand table is the complete figure to compare against. The fuel table excludes kei cars,
folds Lexus into Toyota, and counts Japanese-brand cars built abroad as imports, so it does not
reconcile with the brand table at brand level. No JADA table crosses model with fuel.

Run from the repository root:  .venv/bin/python script/auto/sales/extract_jada.py
"""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "sales"
RAW = DATASET / "raw"
BRANDS = DATASET / "method" / "jada_brands.csv"
MODEL_NAMES = DATASET / "method" / "jp_model_names.csv"
SCOPE = DATASET / "method" / "companies.csv"
OUT_SALES = DATASET / "processed" / "sales_jada_jp.csv"
OUT_FUEL = DATASET / "processed" / "jada_fuel_mix_jp.csv"
OUT_BRAND = DATASET / "processed" / "jada_brand_registrations_jp.csv"
SOURCE_ID = "jada_registration_statistics"

SALES_FIELDS = [
    "company",
    "destination",
    "destination_level",
    "origin",
    "cohort_year",
    "period",
    "model",
    "source_label",
    "powertrain",
    "units",
    "basis",
    "source_id",
    "source_file",
]
FUEL_FIELDS = [
    "company",
    "cohort_year",
    "fuel",
    "powertrain",
    "units",
    "share",
    "months",
    "source_id",
    "source_file",
]
BRAND_FIELDS = [
    "company",
    "cohort_year",
    "units",
    "units_imported",
    "imported_share",
    "months",
    "source_id",
    "source_file",
]
#: JADA fuel headings (written full width in the workbook, compared after normalising) ->
#: the label kept as published and the powertrain vocabulary used everywhere else here.
FUEL_POWERTRAIN = {
    "ガソリン": ("petrol", "ICE"),
    "HV": ("hybrid", "HEV"),
    "PHV": ("plug-in hybrid", "PHEV"),
    "ディーゼル": ("diesel", "ICE"),
    "EV": ("battery electric", "BEV"),
    "FCV": ("fuel cell", "FCEV"),
    "その他": ("other (mainly LPG)", "OTHER"),
}
#: An annual sheet is labelled January to December in the workbook's own characters; the
#: two editions on hand write the months and the tilde differently.
#: Verbatim header and label strings of the source workbooks (join keys, not prose). In
#: English they read: nameplate, brand, petrol, passenger car, total, grand total, and the
#: imported-of-which row.
NAMEPLATE_HEADER = "ブランド通称名"
BRAND_HEADER = "ブランド名"
PETROL_LABEL = "ガソリン"
PASSENGER_CAR_LABEL = "乗用車"
TOTAL_LABEL = "計"
GRAND_TOTAL_LABEL = "合計"
IMPORTED_LABEL = "内輸入"
ANNUAL_SHEET = re.compile(r"1\s*月?\s*[~～-]\s*12\s*月")


def normalise(value: object) -> str:
    """Full-width text to a comparable string (JADA mixes both widths)."""
    return unicodedata.normalize("NFKC", str(value)).replace(" ", "").replace("　", "").strip()


def brand_map() -> dict[str, str]:
    """JADA brand name -> company slug."""
    with BRANDS.open(newline="") as f:
        return {normalise(r["jada_brand"]): r["company"] for r in csv.DictReader(f)}


def in_scope() -> set[str]:
    """Companies flagged in scope."""
    with SCOPE.open(newline="") as f:
        return {r["company"] for r in csv.DictReader(f) if r["in_scope"] == "yes"}


def number(value: object) -> int | None:
    """A JADA cell as an integer, or None when it is blank or a marker."""
    text = normalise(value).replace(",", "")
    if text in {"", "nan", "-", "--", "―", "△", "▲"}:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def model_rows(
    path: Path,
    year: int,
    companies: set[str],
    brands: dict[str, str],
    names: dict[str, str],
) -> list[dict]:
    """Nameplate rows of one annual ranking workbook."""
    book = pd.ExcelFile(path)
    sheets = [s for s in book.sheet_names if ANNUAL_SHEET.search(normalise(s))]
    if not sheets:
        raise SystemExit(
            f"{path.name}: no annual (January to December) sheet in {book.sheet_names}"
        )
    df = book.parse(sheets[0], header=None)
    # The title row also contains the words, so match a cell that IS the heading.
    header = [
        i
        for i in range(len(df))
        if any(normalise(v) == NAMEPLATE_HEADER for v in df.iloc[i].tolist())
    ]
    if not header:
        raise SystemExit(f"{path.name}: no header row carrying the nameplate column")
    start = header[0]
    columns = {normalise(v): i for i, v in enumerate(df.iloc[start]) if normalise(v) != "nan"}
    name_col, brand_col = columns[NAMEPLATE_HEADER], columns[BRAND_HEADER]
    # The volume column is headed "units" in some editions and by the period itself in
    # others, so it is taken by position: the column right of the brand.
    units_col = brand_col + 1
    rows, skipped = [], defaultdict(int)
    for i in range(start + 1, len(df)):
        model, brand = normalise(df.iat[i, name_col]), normalise(df.iat[i, brand_col])
        units = number(df.iat[i, units_col])
        if model in {"nan", ""} or units is None:
            continue
        company = brands.get(brand)
        if company is None:
            raise SystemExit(f"{path.name}: brand {brand!r} is not in {BRANDS.name}")
        if company not in companies:
            skipped[company] += units
            continue
        label = str(df.iat[i, name_col]).strip()
        model_en = names.get(normalise(label))
        if model_en is None:
            raise SystemExit(f"{path.name}: nameplate {label!r} is not in {MODEL_NAMES.name}")
        rows.append(
            {
                "company": company,
                "destination": "JP",
                "destination_level": "country",
                "origin": "",
                "cohort_year": year,
                "period": f"{year}-01..{year}-12",
                "model": model_en,
                "source_label": label,
                "powertrain": "",
                "units": units,
                "basis": "registrations",
                "source_id": SOURCE_ID,
                "source_file": path.name,
            }
        )
    if skipped:
        out = ", ".join(f"{c} {v:,}" for c, v in sorted(skipped.items()))
        print(f"  {path.name}: out of scope, not written: {out}")
    return rows


def fuel_rows(path: Path, year: int, brands: dict[str, str]) -> list[dict]:
    """Maker x fuel registrations, summed over the monthly sheets of one workbook."""
    book = pd.ExcelFile(path)
    totals: dict[tuple[str, str, str], int] = defaultdict(int)
    months: dict[str, int] = defaultdict(int)
    for sheet in book.sheet_names:
        df = book.parse(sheet, header=None)
        head = df.index[df.apply(lambda r: PETROL_LABEL in normalise(r.to_string()), axis=1)]
        if not len(head):
            continue
        row0 = int(head[0])
        fuel_col = {}
        for i, v in enumerate(df.iloc[row0]):
            key = normalise(v).rstrip("(*)").rstrip("（*）")
            if key in FUEL_POWERTRAIN:
                fuel_col[FUEL_POWERTRAIN[key]] = i
        if len(fuel_col) < len(FUEL_POWERTRAIN):
            raise SystemExit(
                f"{path.name} {sheet}: only found {sorted(f for f, _ in fuel_col)} of the "
                f"{len(FUEL_POWERTRAIN)} fuel columns"
            )
        for i in range(row0 + 1, len(df)):
            brand = normalise(df.iat[i, 1])
            company = brands.get(brand)
            if company is None:
                continue
            months[company] += 1
            for (fuel, powertrain), col in fuel_col.items():
                value = number(df.iat[i, col])
                if value is not None:
                    totals[(company, fuel, powertrain)] += value
    by_company: dict[str, int] = defaultdict(int)
    for (company, _fuel, _pt), value in totals.items():
        by_company[company] += value
    return [
        {
            "company": company,
            "cohort_year": year,
            "fuel": fuel,
            "powertrain": powertrain,
            "units": value,
            "share": round(value / by_company[company], 6) if by_company[company] else None,
            "months": months[company],
            "source_id": SOURCE_ID,
            "source_file": path.name,
        }
        for (company, fuel, powertrain), value in sorted(totals.items())
    ]


def brand_rows(path: Path, year: int, brands: dict[str, str]) -> list[dict]:
    """Passenger-car registrations and the imported part, summed over the monthly sheets."""
    book = pd.ExcelFile(path)
    total: dict[str, int] = defaultdict(int)
    imported: dict[str, int] = defaultdict(int)
    months: dict[str, int] = defaultdict(int)
    for sheet in book.sheet_names:
        df = book.parse(sheet, header=None)
        head = df.index[df.apply(lambda r: PASSENGER_CAR_LABEL in normalise(r.to_string()), axis=1)]
        if not len(head):
            continue
        row0 = int(head[0])
        labels = [normalise(v) for v in df.iloc[row0 + 1]]
        try:
            car_total_col = labels.index(TOTAL_LABEL)
        except ValueError:
            continue
        company = None
        for i in range(row0 + 2, len(df)):
            name = normalise(df.iat[i, 0])
            if name not in {"", "nan"}:
                # A new block starts here. Foreign brands and total rows are not in the map,
                # and must end the previous brand's block rather than inherit it.
                company = brands.get(name)
                if company is not None:
                    months[company] += 1
            if company is None:
                continue
            kind = normalise(df.iat[i, 1]) + normalise(df.iat[i, 2])
            value = number(df.iat[i, car_total_col])
            if value is None:
                continue
            if GRAND_TOTAL_LABEL in kind:
                total[company] += value
            elif IMPORTED_LABEL in kind:
                imported[company] += value
    return [
        {
            "company": company,
            "cohort_year": year,
            "units": value,
            "units_imported": imported.get(company, 0),
            "imported_share": round(imported.get(company, 0) / value, 6) if value else None,
            "months": months[company],
            "source_id": SOURCE_ID,
            "source_file": path.name,
        }
        for company, value in sorted(total.items())
    ]


def write(path: Path, fields: list[str], rows: list[dict]) -> None:
    """Write one processed table."""
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Extract every JADA workbook on disk."""
    brands, companies = brand_map(), in_scope()
    names = {
        normalise(r["source_label"]): r["model_en"]
        for r in csv.DictReader(MODEL_NAMES.open(newline=""))
    }
    sales: list[dict] = []
    fuel: list[dict] = []
    brand: list[dict] = []
    for path in sorted(RAW.glob("jada_model_ranking_*.xlsx")):
        sales += model_rows(path, int(path.stem.rsplit("_", 1)[1]), companies, brands, names)
    for path in sorted(RAW.glob("jada_fuel_by_maker_*.xlsx")):
        fuel += fuel_rows(path, int(path.stem.rsplit("_", 1)[1]), brands)
    for path in sorted(RAW.glob("jada_brand_registrations_*.xls")):
        brand += brand_rows(path, int(path.stem.rsplit("_", 1)[1]), brands)
    write(OUT_SALES, SALES_FIELDS, sales)
    write(OUT_FUEL, FUEL_FIELDS, fuel)
    write(OUT_BRAND, BRAND_FIELDS, brand)
    per_company: dict[tuple[str, int], int] = defaultdict(int)
    for r in sales:
        per_company[(r["company"], r["cohort_year"])] += int(r["units"])
    print(
        f"{OUT_SALES.relative_to(REPO)}: {len(sales)} nameplate rows; "
        + ", ".join(f"{c} {y} {v:,}" for (c, y), v in sorted(per_company.items()))
    )
    print(f"{OUT_FUEL.relative_to(REPO)}: {len(fuel)} rows")
    print(f"{OUT_BRAND.relative_to(REPO)}: {len(brand)} rows")


if __name__ == "__main__":
    main()
