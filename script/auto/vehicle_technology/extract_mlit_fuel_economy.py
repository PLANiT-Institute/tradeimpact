"""MLIT fuel-economy list -> vehicle_technology_jp_mlit.csv (certified gCO2/km per nameplate).

Input   raw/mlit_fuel_economy_petrol_car_wltc_<edition>.xlsx   petrol and petrol-hybrid cars
        raw/mlit_fuel_economy_diesel_car_wltc_<edition>.xlsx   diesel cars
        method/jp_maker_map.csv        make as the workbook writes it -> company, and whether
                                       its sheet is read at all
        ../../sales/method/jp_model_names.csv   nameplate as the workbook writes it -> English
                                       name (one home for the fact, shared with the sales side)
Output  processed/vehicle_technology_jp_mlit.csv
        one row per company x model x powertrain: the mean of that group's grade values, the
        grade count, and the range across grades. ``model`` is the English nameplate and
        ``source_label`` the string the workbook prints.

Only the sheets of makers marked ``read = yes`` are read — the companies in scope and nothing
else — so every nameplate that reaches the output has an English name in the map, and one that
does not stops the extractor rather than passing through in Japanese.

The published quantity is CO2 emissions per kilometre (gCO2/km) on the WLTC cycle, so nothing is
converted: the value that enters the model is the value the certificate carries.

Powertrain comes from the fuel-economy-improvement column, where an H code marks a hybrid. The
engine column is the corroborating signal — a hybrid there prints its engine code, a marker that
it is an internal-combustion engine, and then a motor code — but it is not universal: Daihatsu's
e-SMART grades print one code and carry the H code, so H is the definitive test and an engine
cell that lists two power sources without an H code stops the extractor.

Plug-in hybrids are certified in hybrid mode and the workbook does not separate them, so a
plug-in grade sits inside its nameplate's HEV mean — recorded here, and the cohort's own plug-in
share is withheld rather than assessed, because no utility factor is sourced.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_technology/extract_mlit_fuel_economy.py
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "vehicle_technology"
RAW = DATA / "raw"
MAKERS = DATA / "method" / "jp_maker_map.csv"
MODEL_NAMES = REPO / "data" / "auto" / "sales" / "method" / "jp_model_names.csv"
OUT = DATA / "processed" / "vehicle_technology_jp_mlit.csv"
SOURCE_ID = "mlit_fuel_economy_list"
TEST_CYCLE = "WLTC_JP"
SEGMENT = "passenger_car"
FIELDS = [
    "company",
    "segment",
    "model",
    "source_label",
    "powertrain",
    "tailpipe_gco2_km",
    "tailpipe_low_gco2_km",
    "tailpipe_high_gco2_km",
    "n_trims",
    "edition",
    "test_cycle",
    "source_id",
    "source_file",
]
#: The marks a sheet writes beside a nameplate the maker did not build itself (join keys).
OEM_MARKS = ("※2", "※1", "※")
#: Verbatim header keyword of the source workbook -> the column it marks. These are join keys,
#: not prose; in English they read "make", "nameplate", "engine", "CO2 per kilometre" and
#: "principal fuel-economy improvements".
KEYWORDS = {
    "車名": "make",
    "通称名": "model",
    "原動機": "engine",
    "1km走行": "co2",
    "主要燃費改善": "measures",
}
#: Verbatim marker in the engine cell meaning "internal-combustion engine", printed only where
#: the grade also lists an electric motor.
HYBRID_ENGINE = "内燃機関"
HYBRID_MEASURE = "H"
#: rows the header block occupies in every maker sheet of this edition.
HEADER_ROWS = 8


def norm(value: object) -> str:
    """Text with width, spacing and newlines normalised away."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value)).replace("　", " "))


def nameplates(first: object, second: object) -> list[str]:
    """The nameplates a 通称名 cell pair names.

    Three things happen in these two merged columns. A nameplate can be written in either of
    them. Twins share one block, written as two lines in one cell (Voxy and Noah, Alphard and
    Vellfire), and the block's certified values belong to both. And a nameplate the maker did
    not build itself carries an OEM mark, which sits in the first column with the name in the
    second.
    """
    out: list[str] = []
    for value in (first, second):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        for line in unicodedata.normalize("NFKC", str(value)).splitlines():
            text = line.strip()
            for mark in OEM_MARKS:
                text = text.replace(unicodedata.normalize("NFKC", mark), "")
            text = re.sub(r"\s+", "", text.strip())
            if text:
                out.append(text)
    return out


def tokens(value: object) -> set[str]:
    """The codes in a fuel-economy-improvement cell.

    The cell separates its codes with newlines on some sheets and commas on others, so the
    reader splits on anything that is not a letter or digit rather than on one of them. H is a
    code in its own right, and normalising the newlines away would bury it inside a run like
    VIEPHBC.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return set()
    text = unicodedata.normalize("NFKC", str(value)).upper()
    return {t for t in re.split(r"[^A-Z0-9]+", text) if t}


def columns(df: pd.DataFrame, where_from: str) -> dict[str, int]:
    """{role: column index} for one maker sheet.

    A header label is read down a column, not across a row: the Nissan and Honda sheets break
    the fuel-economy-improvement label over three lines in the same column, while every other
    sheet writes it in one cell. Joining the header block down each column reads both. The join
    also picks up the sheet title above the label, so a keyword is searched for anywhere in the
    joined text rather than at its start.
    """
    stacked = ["".join(norm(df.iat[i, j]) for i in range(HEADER_ROWS)) for j in range(df.shape[1])]
    found: dict[str, int] = {}
    for j, text in enumerate(stacked):
        for keyword, role in KEYWORDS.items():
            if keyword in text and role not in found:
                found[role] = j
    missing = set(KEYWORDS.values()) - set(found)
    if missing:
        raise SystemExit(f"{where_from}: header carries no column for {sorted(missing)}")
    for i in range(HEADER_ROWS):
        if not pd.isna(pd.to_numeric(df.iat[i, found["co2"]], errors="coerce")):
            raise SystemExit(
                f"{where_from}: row {i + 1} already carries a CO2 value, so the header block is "
                f"shorter than the {HEADER_ROWS} rows this reader assumes"
            )
    return found


def main() -> None:
    """One row per company, nameplate and powertrain."""
    makers = {
        norm(r["mlit_make"]): r["company"]
        for r in csv.DictReader(MAKERS.open(newline=""))
        if r["read"] == "yes"
    }
    names = {
        norm(r["source_label"]): r["model_en"] for r in csv.DictReader(MODEL_NAMES.open(newline=""))
    }
    groups: dict[tuple[str, str, str, int], list[float]] = {}
    sources: dict[tuple[str, str, str, int], tuple[str, str]] = {}
    for path in sorted(RAW.glob("mlit_fuel_economy_*_wltc_*.xlsx")):
        name = path.name
        edition = int(path.stem.rsplit("_", 1)[1])
        book = pd.ExcelFile(path)
        for sheet in book.sheet_names:
            if "JC08" in norm(sheet).upper():
                continue
            df = pd.read_excel(path, sheet_name=sheet, header=None)
            where = columns(df, f"{name} {sheet}")
            make = ""
            models: list[str] = []
            for i in range(HEADER_ROWS, len(df)):
                row = [norm(v) for v in df.iloc[i]]

                def cell(
                    role: str,
                    row: list[str] = row,
                    where: dict[str, int] = where,
                ) -> str:
                    j = where[role]
                    return row[j] if j < len(row) else ""

                co2 = pd.to_numeric(df.iat[i, where["co2"]], errors="coerce")
                if pd.isna(co2):
                    # Footnotes and the sheet's filling instructions sit below the grades and
                    # must not be carried down as a make or a nameplate.
                    continue
                make = cell("make") or make
                found = nameplates(
                    df.iat[i, where["model"]],
                    df.iat[i, where["model"] + 1] if where["model"] + 1 < df.shape[1] else None,
                )
                models = found or models
                company = makers.get(make)
                if company is None or not models:
                    continue
                engine = cell("engine")
                measures = tokens(df.iat[i, where["measures"]])
                hybrid = HYBRID_MEASURE in measures
                if HYBRID_ENGINE in engine and not hybrid:
                    raise SystemExit(
                        f"{name} {sheet} row {i + 1}: the engine cell marks an "
                        "internal-combustion engine (so the grade has more than one power "
                        f"source) but the improvement codes have no {HYBRID_MEASURE} token "
                        f"({engine!r}, {sorted(measures)})"
                    )
                for model in models:
                    model_en = names.get(model)
                    if model_en is None:
                        raise SystemExit(
                            f"{name} {sheet} row {i + 1}: nameplate {model!r} is not in "
                            f"{MODEL_NAMES.name}"
                        )
                    key = (company, model_en, "HEV" if hybrid else "ICE", edition)
                    groups.setdefault(key, []).append(float(co2))
                    sources[key] = (name, model)

    # A certified value does not change between editions; only the list of what is still
    # type-approved does. So the newest edition that carries a nameplate wins, and an older
    # edition supplies only what the newer one has dropped.
    newest: dict[tuple[str, str, str], int] = {}
    for company, model, powertrain, edition in groups:
        key = (company, model, powertrain)
        newest[key] = max(newest.get(key, 0), edition)
    rows: list[dict[str, object]] = []
    for (company, model, powertrain), edition in sorted(newest.items()):
        values = groups[(company, model, powertrain, edition)]
        source_file, source_label = sources[(company, model, powertrain, edition)]
        rows.append(
            {
                "company": company,
                "segment": SEGMENT,
                "model": model,
                "source_label": source_label,
                "powertrain": powertrain,
                "tailpipe_gco2_km": round(sum(values) / len(values), 3),
                "tailpipe_low_gco2_km": round(min(values), 3),
                "tailpipe_high_gco2_km": round(max(values), 3),
                "n_trims": len(values),
                "edition": edition,
                "test_cycle": TEST_CYCLE,
                "source_id": SOURCE_ID,
                "source_file": source_file,
            }
        )
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    companies = sorted({str(r["company"]) for r in rows})
    trims = sum(int(str(r["n_trims"])) for r in rows)
    print(f"{OUT.relative_to(REPO)}: {len(rows)} rows over {trims} grades, companies {companies}")


if __name__ == "__main__":
    main()
