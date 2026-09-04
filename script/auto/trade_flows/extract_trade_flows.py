"""Extract passenger-car trade flows by exporter, importer, year and powertrain class.

Inputs (all fetched directly from their sources of truth; links and hashes in raw_files.csv)
    trade_flows/raw/comext_imports_<partner>.json    Eurostat Comext ds-045409: EU member-state
        imports from KR / JP, HS 8703 six-digit, units (SUPPLEMENTARY_QUANTITY) and euros
    trade_flows/raw/comtrade_<rep>_<flow>_<partner>_<year>.json   UN Comtrade: exporter-reported
        exports (X) and importer-reported imports (M) between KR/JP and US/AU, units and USD
    trade_flows/method/hs_passenger_cars.csv          HS6 -> powertrain class
Output  trade_flows/processed/trade_flows.csv — long format, one row per
        reporter x flow x exporter x importer x hs6 x year, with the powertrain class.

Units are vehicles ("number of items"); Comtrade rows flagged ``isQtyEstimated`` are kept with
``quantity_flag = estimated``. Values are in the source currency (EUR for Comext, USD for
Comtrade). Nothing is netted or mirrored here: both sides of a flow are published so the
reconciliation stays visible.

Run from the repository root:  .venv/bin/python script/auto/trade_flows/extract_trade_flows.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "trade_flows"
RAW = DATASET / "raw"
HS_TABLE = DATASET / "method" / "hs_passenger_cars.csv"
OUT = DATASET / "processed" / "trade_flows.csv"

GEO_RECODE = {"EL": "GR"}
EU27 = {
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
}
EU_AGGREGATE = "EU27_2020"
COMTRADE_UNITS = {5: "vehicles"}
FIELDS = [
    "reporter",
    "flow",
    "exporter",
    "importer",
    "year",
    "hs6",
    "powertrain_class",
    "units",
    "quantity_flag",
    "value",
    "currency",
    "source_id",
    "source_file",
]


def flatten(payload: dict) -> list[tuple[dict[str, str], float]]:
    """JSON-stat 2.0 cube -> [({dimension: category}, value)]."""
    ids, sizes = payload["id"], payload["size"]
    lookup = [
        {pos: key for key, pos in payload["dimension"][n]["category"]["index"].items()} for n in ids
    ]
    out = []
    for position, value in payload["value"].items():
        remainder = int(position)
        cats: list[str] = []
        for size, table in zip(reversed(sizes), reversed(lookup), strict=True):
            cats.append(table[remainder % size])
            remainder //= size
        out.append((dict(zip(ids, reversed(cats), strict=True)), float(value)))
    return out


def comext_rows(path: Path, classes: dict[str, str]) -> list[dict[str, object]]:
    """EU member-state imports: one row per reporter x hs6 x year with units and euros."""
    snap = json.loads(path.read_text())
    cells: dict[tuple[str, str, int], dict[str, float]] = {}
    for indicator, payload in snap["responses"].items():
        for cats, value in flatten(payload):
            code = GEO_RECODE.get(cats["reporter"], cats["reporter"])
            if code not in EU27:
                continue  # the EU aggregate carries no supplementary quantity: summed below
            cells.setdefault((code, cats["product"], int(cats["time"])), {})[indicator] = value
    rows = []
    totals: dict[tuple[str, int], dict[str, float]] = {}
    for (importer, hs6, year), ind in sorted(cells.items()):
        units = ind.get("SUPPLEMENTARY_QUANTITY")
        rows.append(
            {
                "reporter": importer,
                "flow": "imports",
                "exporter": snap["partner"],
                "importer": importer,
                "year": year,
                "hs6": hs6,
                "powertrain_class": classes[hs6],
                "units": None if units is None else round(units),
                "quantity_flag": "reported" if units is not None else "not_reported",
                "value": ind.get("VALUE_IN_EUROS"),
                "currency": "EUR",
                "source_id": snap["source_id"],
                "source_file": path.name,
            }
        )
        total = totals.setdefault((hs6, year), {"units": 0.0, "value": 0.0, "n": 0})
        if units is not None:
            total["units"] += units
            total["n"] += 1
        total["value"] += ind.get("VALUE_IN_EUROS") or 0.0
    for (hs6, year), total in sorted(totals.items()):
        rows.append(
            {
                "reporter": "EU27",
                "flow": "imports",
                "exporter": snap["partner"],
                "importer": "EU27",
                "year": year,
                "hs6": hs6,
                "powertrain_class": classes[hs6],
                "units": round(total["units"]) if total["n"] else None,
                "quantity_flag": "member_state_sum" if total["n"] else "not_reported",
                "value": round(total["value"], 2),
                "currency": "EUR",
                "source_id": snap["source_id"],
                "source_file": path.name,
            }
        )
    return rows


def comtrade_rows(path: Path, classes: dict[str, str]) -> list[dict[str, object]]:
    """Comtrade records: exporter-reported exports or importer-reported imports."""
    snap = json.loads(path.read_text())
    flow = "exports" if snap["flow"] == "X" else "imports"
    exporter = snap["reporter"] if flow == "exports" else snap["partner"]
    importer = snap["partner"] if flow == "exports" else snap["reporter"]
    rows = []
    for r in snap["response"]["data"]:
        units = r["qty"] if r["qtyUnitCode"] == 5 and r["qty"] not in (None, 0) else None
        flag = "estimated" if r.get("isQtyEstimated") else "reported"
        if units is None:
            flag = "not_reported"
        rows.append(
            {
                "reporter": snap["reporter"],
                "flow": flow,
                "exporter": exporter,
                "importer": importer,
                "year": int(r["refYear"]),
                "hs6": r["cmdCode"],
                "powertrain_class": classes[r["cmdCode"]],
                "units": None if units is None else round(units),
                "quantity_flag": flag,
                "value": r.get("primaryValue"),
                "currency": "USD",
                "source_id": snap["source_id"],
                "source_file": path.name,
            }
        )
    return rows


def main() -> None:
    """Combine every pinned raw file into one long table."""
    classes = {r["hs6"]: r["powertrain_class"] for r in csv.DictReader(HS_TABLE.open(newline=""))}
    out: list[dict[str, object]] = []
    for path in sorted(RAW.glob("comext_imports_*.json")):
        out.extend(comext_rows(path, classes))
    for path in sorted(RAW.glob("comtrade_*.json")):
        out.extend(comtrade_rows(path, classes))
    out.sort(
        key=lambda r: tuple(
            str(r[k]) for k in ("exporter", "importer", "reporter", "flow", "year", "hs6")
        )
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    summary: dict[tuple[str, str, str], float] = {}
    for r in out:
        if (
            r["year"] == 2024
            and r["units"]
            and r["importer"] in ("EU27", "US", "AU")
            and r["flow"] == "imports"
        ):
            k = (str(r["exporter"]), str(r["importer"]), str(r["powertrain_class"]))
            summary[k] = summary.get(k, 0.0) + float(str(r["units"]))
    for k in sorted(summary):
        print(f"2024 imports {k[0]} -> {k[1]} {k[2]}: {summary[k]:,.0f} vehicles")
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows")


if __name__ == "__main__":
    main()
