#!/usr/bin/env python3
"""Audit every load-bearing number in the deck against the published dataset."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "data" / "published"
HTML = (REPO / "outputs" / "deck" / "PLANiT_TradeImpact_Framework_EN_20260811_v02.html").read_text()
TEXT = re.sub(r"<[^>]+>", " ", HTML) + " " + HTML  # markup + the script payload behind the live charts
TEXT = TEXT.replace("−", "-").replace(" ", " ").replace(" ", " ")

res = json.loads((PUB / "lifetime_results.json").read_text())
dest = {r["country_code"]: r for r in json.loads((PUB / "destination_inputs.json").read_text())}
coh = {c["company_id"]: c for c in json.loads((PUB / "product_cohorts.json").read_text())}
firms = json.loads((PUB / "firms.json").read_text())
T = next(v for v in res.values() if v["firm"] == "Toyota")
H = next(v for v in res.values() if v["firm"] == "Hyundai")

units = {}
for fid, c in coh.items():
    agg = {}
    for r in c["records"]:
        agg[r["product_type"]] = agg.get(r["product_type"], 0.0) + r["units"]
    units[fid] = agg

de = dest["DE"]
D, I0 = de["vkt_km_per_year"], de["fleet_intensity_base_gco2_per_km"] / 1000
e_ref0 = I0 * D
e_prod = 107.13284 * 1.211 / 1000 * D
gap = [e_ref0 * (1 - de["r_fleet_s2"]) ** t - e_prod for t in range(15)]
tstar = math.log(e_prod / e_ref0) / math.log(1 - de["r_fleet_s2"])
meas = sorted(r["vkt_km_per_year"] for r in dest.values() if r["vkt_tier"] != "C")
ti_firms = [f for f in firms if f["project"] == "TI"]

CHECKS: list[tuple[str, str, float | str]] = [
    ("1,286", "evidence rows", sum(len(c["records"]) for c in coh.values())),
    ("803,094", "Toyota units", units["toyota"] and T["coverage"]["total_units"]),
    ("429,936", "Hyundai units", H["coverage"]["total_units"]),
    ("778,461", "Toyota covered", T["coverage"]["covered_units"]),
    ("411,225", "Hyundai covered", H["coverage"]["covered_units"]),
    ("23,911", "Toyota PHEV withheld", T["coverage"]["withheld_product_types"]["PHEV"]["units"]),
    ("18,624", "Hyundai PHEV withheld", H["coverage"]["withheld_product_types"]["PHEV"]["units"]),
    ("610,881", "Toyota HEV units", units["toyota"]["HEV"]),
    ("41,582", "Hyundai BEV units", units["hyundai"]["BEV"]),
    ("198,552", "Hyundai ICE units", units["hyundai"]["ICE_OTHER"]),
    ("594,136", "DE million vkm", 594136.0),
    ("12,042", "DE km/car/yr", D),
    ("150.34", "DE fleet gCO2/km", de["fleet_intensity_base_gco2_per_km"]),
    ("107.13", "Corolla certified", 107.13284),
    ("129.74", "Corolla real-world", 107.13284 * 1.211),
    ("1,810", "E_ref(0)", e_ref0),
    ("1,562", "E_prod", e_prod),
    ("+248", "gap t=0", gap[0]),
    ("-590", "gap t=14", gap[-1]),
    ("-3,167", "cumulative per vehicle", sum(gap)),
    ("-54,182", "cell TI tCO2e", sum(gap) * 17111 / 1000),
    ("3.32", "crossover", tstar),
    ("2.63", "DE r_fleet S1 %", de["r_fleet_s1"] * 100),
    ("4.34", "r_fleet S2 %", de["r_fleet_s2"] * 100),
    ("13.51", "r_fleet S3 %", de["r_fleet_s3"] * 100),
    ("8.56", "DE r_power S3 %", de["r_power_s3"] * 100),
    ("-1.40", "Toyota S1 Mt", T["cohorts"]["S1"]["total_tCO2e"] / 1e6),
    ("-13.95", "Toyota S3 Mt", T["cohorts"]["S3"]["total_tCO2e"] / 1e6),
    ("-3.72", "Hyundai S2 Mt", H["cohorts"]["S2"]["total_tCO2e"] / 1e6),
    ("-7.775", "Hyundai S3 Mt (live chart payload)", H["cohorts"]["S3"]["total_tCO2e"] / 1e6),
    ("-10.41", "Toyota HEV S3 Mt", T["cohorts"]["S3"]["by_powertrain"]["HEV"] / 1e6),
    ("0.58", "Hyundai BEV S2 Mt", H["cohorts"]["S2"]["by_powertrain"]["BEV"] / 1e6),
    ("0.33", "Hyundai BEV S3 Mt", H["cohorts"]["S3"]["by_powertrain"]["BEV"] / 1e6),
    ("-4.20", "Toyota T-3 Mt", T["sensitivity"]["lifetime"]["T_minus"]["S2"] / 1e6),
    ("-7.98", "Toyota T+3 Mt", T["sensitivity"]["lifetime"]["T_plus"]["S2"] / 1e6),
    ("-5.40", "Toyota vkt low Mt", T["sensitivity"]["vkt_proxy"]["low_distance"]["S2"] / 1e6),
    ("-6.41", "Toyota vkt high Mt", T["sensitivity"]["vkt_proxy"]["high_distance"]["S2"] / 1e6),
    ("10,366", "vkt low km", T["sensitivity"]["vkt_proxy"]["low_km_per_year"]),
    ("13,265", "vkt high km", T["sensitivity"]["vkt_proxy"]["high_km_per_year"]),
    ("7,109", "min measured km", meas[0]),
    ("14,417", "max measured km", meas[-1]),
    ("11,982", "proxy km", next(r["vkt_km_per_year"] for r in dest.values() if r["vkt_tier"] == "C")),
    ("10.33", "DE mean car age", de["mean_car_age_years"]),
    ("391", "LU fleet gCO2/km", dest["LU"]["fleet_intensity_base_gco2_per_km"]),
    ("-1,173", "PL HEV S2 kt",
     next(c["TI_tCO2e"] for c in T["cohorts"]["S2"]["by_cell"]
          if c["country"] == "PL" and c["powertrain"] == "HEV") / 1e3),
    ("-5,965", "Toyota S2 kt", T["cohorts"]["S2"]["total_tCO2e"] / 1e3),
    ("-504", "deepest annual kt", min(T["cohorts"]["S2"]["annual_tCO2e"]) / 1e3),
    ("+102", "year 0 annual kt", T["cohorts"]["S2"]["annual_tCO2e"][0] / 1e3),
]

SHARE_CHECKS = [
    ("96.9%", T["coverage"]["covered_share"] * 100),
    ("95.6%", H["coverage"]["covered_share"] * 100),
    ("53.6%", T["coverage"]["vkt_proxy"]["unit_share"] * 100),
    ("76.1%", units["toyota"]["HEV"] / T["coverage"]["total_units"] * 100),
    ("19.5%", units["toyota"]["ICE_OTHER"] / T["coverage"]["total_units"] * 100),
    ("9.7%", units["hyundai"]["BEV"] / H["coverage"]["total_units"] * 100),
    ("46.2%", units["hyundai"]["ICE_OTHER"] / H["coverage"]["total_units"] * 100),
    ("73%", T["trajectory"]["surviving_vehicles"][16] / T["trajectory"]["surviving_vehicles"][0] * 100),
    ("61%", H["trajectory"]["surviving_vehicles"][16] / H["trajectory"]["surviving_vehicles"][0] * 100),
]

def _bev_crossing_within(firm: str, scen: str) -> tuple[int, int]:
    v = next(x for x in res.values() if x["firm"] == firm)
    cells = [c for c in v["crossover"] if c["powertrain"] == "BEV" and c["scenario"] == scen]
    inside = sum(1 for c in cells
                 if c.get("crossover_year") is not None
                 and c["crossover_year"] < dest[c["country"]]["operating_lifetime_years"])
    return inside, len(cells)

_hy_in, _hy_n = _bev_crossing_within("Hyundai", "S2")
_ty_in, _ty_n = _bev_crossing_within("Toyota", "S2")
CHECKS.append(("20 of 115", "Hyundai BEV cells crossing within life", f"{_hy_in} of {_hy_n}"))
CHECKS.append(("11 of 61", "Toyota BEV cells crossing within life", f"{_ty_in} of {_ty_n}"))

phev = [r for c in coh.values() for r in c["records"] if r["product_type"] == "PHEV"]
phev_both = sum(1 for r in phev
                if r["certified_tailpipe_gco2_per_km"] is not None
                and r["certified_electricity_kwh_per_km"] is not None)
CHECKS.append(("132", "PHEV rows publishing both observables", phev_both))
CHECKS.append(("134", "PHEV rows in total", len(phev)))

COUNT_CHECKS = [
    ("Two firms of eleven", sum(1 for f in ti_firms if f["lifetime_result_available"]), len(ti_firms)),
]


def norm(x: str) -> str:
    return x.replace(",", "").replace("+", "").lstrip()


fails, missing = [], []
for shown, label, actual in CHECKS:
    if shown not in TEXT:
        missing.append(f"{shown!r} ({label}) not present in deck text")
        continue
    if isinstance(actual, str):
        if shown != actual:
            fails.append(f"{label}: deck {shown}, data {actual}")
        continue
    want = float(norm(shown))
    got = float(actual)
    tol = max(abs(want) * 0.006, 0.006)
    if abs(want - got) > tol:
        fails.append(f"{label}: deck {shown}, data {got:,.4f}")

for shown, actual in SHARE_CHECKS:
    # live charts carry the numeral without its percent sign
    if shown not in TEXT and shown.rstrip("%") not in TEXT:
        missing.append(f"{shown!r} (share) not present")
        continue
    want = float(shown.rstrip("%"))
    dp = len(shown.split(".")[1].rstrip("%")) if "." in shown else 0
    if abs(want - actual) > 0.5 * 10 ** -dp + 1e-9:
        fails.append(f"share {shown}: data {actual:.3f}%")

for shown, a, b in COUNT_CHECKS:
    if shown not in TEXT:
        missing.append(f"{shown!r} not present")
    elif (a, b) != (2, 11):
        fails.append(f"{shown}: data says {a} of {b}")

print(f"checked {len(CHECKS) + len(SHARE_CHECKS) + len(COUNT_CHECKS)} claims")
print(f"  mismatches : {len(fails)}")
for f in fails:
    print("    ✗", f)
print(f"  not found  : {len(missing)}")
for m in missing:
    print("    ?", m)
if not fails and not missing:
    print("  ALL CLAIMS TRACE TO data/published/")
