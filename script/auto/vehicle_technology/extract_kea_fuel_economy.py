"""KEA label fuel economy -> vehicle_technology_kr_kea.csv (per company x model x powertrain).

Input   raw/kea_vehicle_fuel_economy_labels.csv   one row per certified trim on sale (Korea)
        method/kr_model_map.csv                   KEA base name as published -> company and
                                                  English model name
        method/fuel_carbon_factors.csv            gCO2 per litre by fuel
Output  processed/vehicle_technology_kr_kea.csv
        company, model, powertrain, tailpipe_gco2_km, energy_wh_km, n_trims, test_cycle,
        source_id, source_file

Algorithm
    $$ I_{tailpipe} = \\frac{f_{fuel}}{FE},\\qquad \\eta = \\frac{1000}{FE_{el}} $$
    ASCII: tailpipe gCO2/km = fuel factor (gCO2/L) / label km per L;
           BEV Wh/km = 1000 / label km per kWh. Trim mean over the model x powertrain.
    f_fuel   carbon content of the fuel burned (gCO2/L), method/fuel_carbon_factors.csv
    FE       label combined fuel economy (km/L), 5-cycle corrected
    FE_el    label combined electric efficiency (km/kWh)

The KEA label value is 5-cycle corrected (Korea adopted the US 5-cycle method in 2012), so it
is the sibling of the EPA label and carries ``test_cycle = KR_5CYCLE`` with a real-world factor
of 1.0 in method/real_world_correction.csv. Deriving CO2 from the label fuel economy gives the
label-basis figure, not the 2-cycle regulatory CO2 Korean compliance documents show.

Powertrain and fuel are parsed from the trim string, because the file has no fuel column:
a plug-in marker or PHEV makes it a plug-in hybrid, a hybrid marker or HEV a hybrid, the NEXO
nameplate a fuel-cell vehicle (hydrogen, km/kg), a single-charge range with none of the above a
battery-electric vehicle, and anything else combustion. Fuel follows the same reading: a diesel
marker gives diesel, LPG or LPI gives LPG, otherwise petrol. Converter-built rows are excluded.
The keyword literals are in ``POWERTRAIN_WORDS`` and ``FUEL_WORDS`` below: they are join keys
against the published trim string, not prose.

Run from the repository root:
    .venv/bin/python script/auto/vehicle_technology/extract_kea_fuel_economy.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "vehicle_technology"
RAW = DATA / "raw" / "kea_vehicle_fuel_economy_labels.csv"
MAP = DATA / "method" / "kr_model_map.csv"
FUEL = DATA / "method" / "fuel_carbon_factors.csv"
OUT = DATA / "processed" / "vehicle_technology_kr_kea.csv"
SOURCE_ID = "kea_fuel_economy_labels"
TEST_CYCLE = "KR_5CYCLE"
#: Vehicle class as the file writes it (a join key) -> the project's segment. All three are
#: certified in the same file: passenger car, goods vehicle and bus.
VEHICLE_CLASS = {"승용차": "passenger_car", "화물차": "freight", "승합차": "bus"}
FIELDS = [
    "company",
    "segment",
    "model",
    "powertrain",
    "tailpipe_gco2_km",
    "energy_wh_km",
    "n_trims",
    "test_cycle",
    "source_id",
    "source_file",
]
BASE = re.compile(r"^([^\(\s]+)")
#: Verbatim keywords of the published trim string (join keys), with what each one means.
POWERTRAIN_WORDS = {
    "plug_in": "플러그인",
    "hybrid": "하이브리드",
    "nexo": "넥쏘",
    "electric_word": "일렉트릭",
    "electric": "전기",
}
FUEL_WORDS = {"diesel": "디젤"}
#: Verbatim marker of a converter-built row, excluded from the table.
CONVERSION = "개조차"


def powertrain(name: str, has_range: bool) -> str:
    """Powertrain from the trim string and the presence of an electric range."""
    u = name.upper()
    if POWERTRAIN_WORDS["plug_in"] in name or "PHEV" in u:
        return "PHEV"
    if POWERTRAIN_WORDS["nexo"] in name or "NEXO" in u:
        return "FCEV"
    if POWERTRAIN_WORDS["hybrid"] in name or "HEV" in u:
        return "HEV"
    if (
        has_range
        or POWERTRAIN_WORDS["electric_word"] in name
        or POWERTRAIN_WORDS["electric"] in name
    ):
        return "BEV"
    return "ICE"


def fuel_of(name: str) -> str:
    """Fuel of a combustion trim."""
    u = name.upper()
    if FUEL_WORDS["diesel"] in name or "DIESEL" in u:
        return "diesel"
    if "LPG" in u or "LPI" in u:
        return "lpg"
    return "gasoline"


def main() -> None:
    """Build the technology table for every model in the Korea model map."""
    raw = pd.read_csv(RAW, encoding="utf-8-sig")
    mapping = pd.read_csv(MAP)
    factors = {r["fuel"]: float(r["gco2_per_litre"]) for r in csv.DictReader(FUEL.open())}
    df = raw[
        raw["차종"].isin(VEHICLE_CLASS) & ~raw["모델명"].str.contains(CONVERSION, na=False)
    ].copy()
    df["segment"] = df["차종"].map(VEHICLE_CLASS)
    df["kea_base"] = df["모델명"].str.extract(BASE)[0]
    df = df.merge(
        mapping,
        how="inner",
        left_on=["제조(수입사)", "kea_base"],
        right_on=["kea_make", "kea_base"],
    )
    df["fe"] = pd.to_numeric(df["복합_연비"], errors="coerce")
    df["has_range"] = pd.to_numeric(df["1회충전주행거리"], errors="coerce").notna()
    df["powertrain"] = [
        powertrain(n, r) for n, r in zip(df["모델명"], df["has_range"], strict=True)
    ]
    df = df[df["fe"].notna() & (df["fe"] > 0)]

    def tailpipe(row: pd.Series) -> float | None:
        if row["powertrain"] in ("BEV", "FCEV"):
            return None
        if row["powertrain"] == "PHEV":
            return None  # combined label value needs a utility factor; withheld downstream
        return factors[fuel_of(row["모델명"])] / row["fe"]

    df["tailpipe"] = df.apply(tailpipe, axis=1)
    df["wh_km"] = df.apply(lambda r: 1000.0 / r["fe"] if r["powertrain"] == "BEV" else None, axis=1)
    grp = df.groupby(["company", "segment", "model_en", "powertrain"], as_index=False).agg(
        tailpipe_gco2_km=("tailpipe", "mean"),
        energy_wh_km=("wh_km", "mean"),
        n_trims=("모델명", "size"),
    )
    rows = []
    for r in grp.sort_values(["company", "model_en", "powertrain"]).to_dict("records"):
        rows.append(
            {
                "company": r["company"],
                "segment": r["segment"],
                "model": r["model_en"],
                "powertrain": r["powertrain"],
                "tailpipe_gco2_km": ""
                if pd.isna(r["tailpipe_gco2_km"])
                else round(r["tailpipe_gco2_km"], 2),
                "energy_wh_km": "" if pd.isna(r["energy_wh_km"]) else round(r["energy_wh_km"], 2),
                "n_trims": int(r["n_trims"]),
                "test_cycle": TEST_CYCLE,
                "source_id": SOURCE_ID,
                "source_file": RAW.name,
            }
        )
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    unmapped = sorted(
        set(
            raw[raw["차종"].isin(VEHICLE_CLASS) & raw["제조(수입사)"].isin({"현대", "기아"})][
                "모델명"
            ]
            .str.extract(BASE)[0]
            .dropna()
        )
        - set(mapping["kea_base"])
    )
    print(
        f"{OUT.relative_to(REPO)}: {len(rows)} rows from {len(df)} trims; "
        f"unmapped Hyundai/Kia base names: {unmapped or 'none'}"
    )


if __name__ == "__main__":
    main()
