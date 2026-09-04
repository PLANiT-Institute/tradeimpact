"""Extract US light-duty emissions from the EPA GHG Inventory transcriptions.

Inputs (hand-checked transcriptions of PDF text; the PDFs are not stored — URLs and SHA-256 in
data/auto/registry/raw_files.csv)
    raw/epa_ghg_inventory_2025_table_3_13.csv   main text Table 3-13: CO2 from fossil fuel
        combustion by fuel and vehicle type (passenger cars, light-duty trucks), MMT CO2 eq.;
        1990, 2005, 2019-2023
    raw/epa_ghg_inventory_2025_table_a_91.csv   Annex Table A-91: passenger-car total GHG by fuel
        (CO2 + CH4 + N2O), MMT CO2 eq.; 1990, 2000, 2010, 2013-2023
    raw/epa_ghg_inventory_2025_table_a_93.csv   Annex Table A-93: light-duty-truck total GHG,
        MMT CO2 eq.; 1990, 2000, 2012-2023
Output  processed/country_emissions_us.csv (long format, ktCO2 / ktCO2e)

Series: ``car_co2``, ``ldt_co2``, ``ldv_co2`` (cars + light-duty trucks; CO2 level series) and
``car_ghg_co2e``, ``ldt_ghg_co2e``, ``ldv_ghg_co2e`` (annual trend series). EPA's "passenger
cars" is a narrower population than FHWA's short-wheelbase light-duty class, so the benchmark
uses the light-duty totals (``ldv_*``), whose population matches FHWA's all-light-duty stock and
distance.

Run from the repository root:
    .venv/bin/python script/auto/country_emissions/extract_epa_inventory.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "country_emissions"
OUT = DATASET / "processed" / "country_emissions_us.csv"
KT_PER_MMT = 1000.0
TYPE_PREFIX = {"passenger_cars": "car", "light_duty_trucks": "ldt"}
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def load(name: str, value_col: str) -> dict[tuple[str, int], tuple[float, str]]:
    """{(vehicle_type, year): (summed value MMT, source_id)} from one transcription."""
    acc: dict[tuple[str, int], float] = defaultdict(float)
    sources: dict[tuple[str, int], str] = {}
    with (DATASET / "raw" / name).open(newline="") as f:
        for r in csv.DictReader(f):
            key = (r["vehicle_type"], int(r["year"]))
            acc[key] += float(r[value_col])
            sources[key] = r["source_id"]
    return {k: (v, sources[k]) for k, v in acc.items()}


def main() -> None:
    """Write per-type and light-duty-total series for CO2 (level) and GHG (trend)."""
    out: list[dict[str, object]] = []
    for suffix, unit, tables in (
        ("co2", "ktCO2", ["epa_ghg_inventory_2025_table_3_13.csv"]),
        (
            "ghg_co2e",
            "ktCO2e",
            ["epa_ghg_inventory_2025_table_a_91.csv", "epa_ghg_inventory_2025_table_a_93.csv"],
        ),
    ):
        data: dict[tuple[str, int], tuple[float, str]] = {}
        files: dict[str, str] = {}
        for t in tables:
            part = load(t, "value_mmt_co2e")
            data.update(part)
            for vtype, _y in part:
                files[vtype] = t
        by_type: dict[str, dict[int, tuple[float, str]]] = defaultdict(dict)
        for (vtype, year), (v, sid) in data.items():
            by_type[vtype][year] = (v, sid)
        for vtype, series in by_type.items():
            for year, (v, sid) in sorted(series.items()):
                out.append(
                    {
                        "country": "US",
                        "series": f"{TYPE_PREFIX[vtype]}_{suffix}",
                        "year": year,
                        "value": round(v * KT_PER_MMT, 1),
                        "unit": unit,
                        "source_id": sid,
                        "source_file": files[vtype],
                    }
                )
        years = set(by_type["passenger_cars"]) & set(by_type["light_duty_trucks"])
        for year in sorted(years):
            v = by_type["passenger_cars"][year][0] + by_type["light_duty_trucks"][year][0]
            sids = sorted(
                {by_type["passenger_cars"][year][1], by_type["light_duty_trucks"][year][1]}
            )
            out.append(
                {
                    "country": "US",
                    "series": f"ldv_{suffix}",
                    "year": year,
                    "value": round(v * KT_PER_MMT, 1),
                    "unit": unit,
                    "source_id": ";".join(sids),
                    "source_file": ";".join(
                        sorted({files["passenger_cars"], files["light_duty_trucks"]})
                    ),
                }
            )
    out.sort(key=lambda r: (str(r["series"]), int(str(r["year"]))))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    for s in ("car_co2", "ldv_co2", "ldv_ghg_co2e"):
        mine = [r for r in out if r["series"] == s]
        mt = float(str(mine[-1]["value"])) / 1000
        print(f"{s}: {len(mine)} years, latest {mine[-1]['year']} = {mt:,.1f} Mt")
    print(f"{OUT.relative_to(REPO)}: {len(out)} rows")


if __name__ == "__main__":
    main()
