"""EPA Automotive Trends MY2024 carline file -> powertrain shares per US nameplate.

Input   data/auto/vehicle_technology/raw/epa_automotive_trends_my2024.csv
        data/auto/vehicle_technology/method/epa_carline_map.csv (make, carline_name ->
        base_model; the nameplate the company sales releases use)
Output  data/auto/vehicle_technology/processed/epa_trends_powertrain_share_my2024.csv
        one row per (make, base_model, powertrain): certification production volume and the
        share of the base model's volume, plus the volume-weighted label combined MPG
        (5-cycle adjusted; the certified values used for pricing stay in
        vehicle_technology_us_epa.csv).

Rows duplicate in the raw file (the same model type appears in several compliance groups); they
are deduplicated on (CAFE Mfr Code, DIVISION_CD, CARLINE_CODE, MODEL_TYPE_INDEX) before summing.

Powertrain classification (guideline: mild hybrids count as ICE):
    FUEL_USAGE_DESC == Electricity                 -> BEV
    FUEL_USAGE_DESC == Hydrogen                    -> FCEV
    PHEV_COMPOSITE_COMB_MPGE present or 'Plug-in'  -> PHEV
    HYBRID_YN == Y and not 'MHEV' in the name      -> HEV
    otherwise                                      -> ICE

Basis caveat: production for US sale in model year 2024, not calendar-year sales. The shares
are applied to the companies' calendar-year volumes as a numbered assumption; the volumes
themselves are never used as a cohort.

Run from the repository root:  .venv/bin/python script/auto/vehicle_technology/extract_epa_trends.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto" / "vehicle_technology"
RAW = DATA / "raw" / "epa_automotive_trends_my2024.csv"
MAP = DATA / "method" / "epa_carline_map.csv"
OUT = DATA / "processed" / "epa_trends_powertrain_share_my2024.csv"
SOURCE_ID = "epa_automotive_trends_my2024"
KEY = ["CAFE Mfr Code", "DIVISION_CD", "CARLINE_CODE", "MODEL_TYPE_INDEX"]
MPG = "RND_5C_ADJ_MT_COMB_FE"  # label combined fuel economy, 5-cycle adjusted, rounded
FIELDS = [
    "make",
    "base_model",
    "powertrain",
    "model_year",
    "production_volume",
    "share",
    "label_comb_mpg_weighted",
    "carlines",
    "source_id",
    "source_file",
]


def classify(row: pd.Series) -> str:
    """Powertrain of one model type."""
    fuel = str(row["FUEL_USAGE_DESC"])
    name = str(row["CARLINE_NAME"])
    if fuel.startswith("Electricity"):
        return "BEV"
    if fuel.startswith("Hydrogen"):
        return "FCEV"
    if pd.notna(row.get("PHEV_COMPOSITE_COMB_MPGE")) or "Plug-in" in name:
        return "PHEV"
    if str(row["HYBRID_YN"]) == "Y" and "MHEV" not in name.upper():
        return "HEV"
    return "ICE"


def main() -> None:
    """Build the share table for every make in the carline map."""
    raw = pd.read_csv(RAW, low_memory=False)
    carline_map = pd.read_csv(MAP)
    makes = set(carline_map["make"])
    df = raw[raw["MFR_DIVISION_SHORT_NM"].str.upper().isin(makes)].copy()
    df["make"] = df["MFR_DIVISION_SHORT_NM"].str.upper()
    df = df.drop_duplicates(subset=KEY)
    df = df.merge(
        carline_map, how="left", left_on=["make", "CARLINE_NAME"], right_on=["make", "carline_name"]
    )
    unmapped = sorted(df.loc[df["base_model"].isna(), "CARLINE_NAME"].unique())
    if unmapped:
        raise SystemExit(f"carlines missing from {MAP.name}: {unmapped}")
    df["powertrain"] = df.apply(classify, axis=1)
    df["vol"] = (
        pd.to_numeric(df["Model_Type_Actual_Prod_Vol"], errors="coerce").fillna(0).astype(int)
    )
    df["mpg"] = pd.to_numeric(df[MPG], errors="coerce")
    df["mpg_x_vol"] = df["mpg"] * df["vol"]
    grp = df.groupby(["make", "base_model", "powertrain"], as_index=False).agg(
        production_volume=("vol", "sum"),
        mpg_x_vol=("mpg_x_vol", "sum"),
        carlines=("CARLINE_NAME", lambda s: "; ".join(sorted(set(s)))),
    )
    base_total = grp.groupby(["make", "base_model"])["production_volume"].transform("sum")
    grp["share"] = (grp["production_volume"] / base_total.where(base_total > 0)).round(6)
    grp["label_comb_mpg_weighted"] = (
        grp["mpg_x_vol"] / grp["production_volume"].where(grp["production_volume"] > 0)
    ).round(1)
    grp["model_year"] = int(df["MODEL_YEAR"].iloc[0])
    grp["source_id"] = SOURCE_ID
    grp["source_file"] = RAW.name
    grp = grp.sort_values(["make", "base_model", "powertrain"])
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in grp.to_dict("records"):
            w.writerow({k: r.get(k, "") for k in FIELDS})
    mixed = grp.groupby(["make", "base_model"]).size()
    print(
        f"{OUT.relative_to(REPO)}: {len(grp)} rows, {len(mixed)} base models, "
        f"{(mixed > 1).sum()} with more than one powertrain; {len(df)} model types after dedup"
    )


if __name__ == "__main__":
    main()
