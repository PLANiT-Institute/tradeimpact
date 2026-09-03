"""Step 4 — lifetime trade impact per company x destination x model x powertrain x scenario.

Inputs
    sales/processed/sales_eea_eu27_2024.csv                        volumes (registrations)
    vehicle_technology/processed/vehicle_technology_eea_2024.csv   certified WLTP values
    vehicle_technology/method/real_world_correction.csv            factor per powertrain
    output/destination_parameters_eu27.csv                         distance, lifetime per market
    output/reference_trajectories_eu27.csv                         E_ref(t), G(t) per scenario
Outputs (data/auto/output/)
    ti_by_model_eu27.csv    one row per cell x scenario: units, per-vehicle and total TI
    ti_annual_eu27.csv      annual TI flow per company x scenario over the cohort horizon
    ti_withheld_eu27.csv    units that carry no result and why (PHEV, FCEV, no certified value)

Algorithm (whitepaper §3.2-3.5, guideline §3.3-3.4, §4):
    $$ E_{prod}(t) = \\begin{cases} I_{cert}\\,f_{rw}\\,D_c & \\text{ICE, HEV}\\\\
       \\eta_{cert}\\, G_c(t)\\, D_c & \\text{BEV} \\end{cases},\\qquad
       TI_{v} = \\sum_{t=0}^{T_c-1}\\big(E_{ref,c}(t)-E_{prod}(t)\\big),\\qquad
       TI_{cell} = TI_v \\cdot N / 1000 $$
    ASCII: E_prod = tailpipe_gco2_km*factor/1000*vkt [kgCO2e/vehicle-yr] for ICE/HEV;
           E_prod(t) = energy_wh_km/1000 * G(t) * vkt for BEV (G in kgCO2e/kWh);
           TI_v = sum_{t=0}^{T-1} (E_ref(t) - E_prod(t)) [kgCO2e/vehicle]; TI = TI_v*units/1000 [t]
    I_cert  certified tailpipe intensity (gCO2/km), f_rw real-world factor (-), D_c annual
    distance (km/yr), eta_cert certified consumption (Wh/km), T_c operating life (years).
    Positive TI = contribution below the destination benchmark; negative = lock-in liability.

Run from the repository root:  .venv/bin/python script/auto/model/build_ti.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
SALES = DATA / "sales" / "processed" / "sales_eea_eu27_2024.csv"
TECH = DATA / "vehicle_technology" / "processed" / "vehicle_technology_eea_2024.csv"
CORRECTION = DATA / "vehicle_technology" / "method" / "real_world_correction.csv"
PARAMS = DATA / "output" / "destination_parameters_eu27.csv"
REFERENCE = DATA / "output" / "reference_trajectories_eu27.csv"
OUT_CELLS = DATA / "output" / "ti_by_model_eu27.csv"
OUT_ANNUAL = DATA / "output" / "ti_annual_eu27.csv"
OUT_WITHHELD = DATA / "output" / "ti_withheld_eu27.csv"

WITHHELD_REASON = {
    "PHEV": "no sourced utility factor: the registration data publish only combined values",
    "FCEV": "no sourced hydrogen supply emissions intensity for the destination",
}
NO_CERTIFIED = "the registration dataset reports no certified intensity for this cell"

CELL_FIELDS = [
    "company",
    "destination",
    "model",
    "powertrain",
    "scenario",
    "cohort_year",
    "units",
    "lifetime_years",
    "vkt_km",
    "vkt_tier",
    "real_world_factor",
    "e_prod_year0_kgco2e",
    "e_ref_year0_kgco2e",
    "ti_per_vehicle_kgco2e",
    "ti_tco2e",
]
ANNUAL_FIELDS = ["company", "scenario", "t", "calendar_year", "surviving_vehicles", "ti_tco2e"]
WITHHELD_FIELDS = ["company", "destination", "model", "powertrain", "units", "reason"]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    """Compute the per-cell lifetime TI and the cohort annual flow for every scenario."""
    tech = {
        (r["company"], r["destination"], r["model"], r["powertrain"]): r for r in read_csv(TECH)
    }
    factor = {r["powertrain"]: float(r["factor"]) for r in read_csv(CORRECTION)}
    params = {r["country"]: r for r in read_csv(PARAMS)}
    reference: dict[tuple[str, str], dict[int, tuple[float, float]]] = defaultdict(dict)
    for r in read_csv(REFERENCE):
        reference[(r["country"], r["scenario"])][int(r["t"])] = (
            float(r["e_ref_kgco2_per_vehicle"]),
            float(r["grid_kgco2_per_kwh"]),
        )
    scenarios = sorted({s for (_, s) in reference})

    cells: list[dict[str, object]] = []
    withheld: list[dict[str, object]] = []
    annual: dict[tuple[str, str], dict[int, float]] = defaultdict(lambda: defaultdict(float))
    surviving: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))

    for s in read_csv(SALES):
        key = (s["company"], s["destination"], s["model"], s["powertrain"])
        units = int(s["units"])
        pt = s["powertrain"]
        base = {"company": key[0], "destination": key[1], "model": key[2], "powertrain": pt}
        if pt in WITHHELD_REASON:
            withheld.append({**base, "units": units, "reason": WITHHELD_REASON[pt]})
            continue
        t_row = tech.get(key)
        cert = None
        if t_row is not None:
            cert = t_row["energy_wh_km"] if pt == "BEV" else t_row["tailpipe_gco2_km"]
        if not cert:
            withheld.append({**base, "units": units, "reason": NO_CERTIFIED})
            continue
        p = params[key[1]]
        vkt, life = float(p["vkt_km"]), int(p["lifetime_years"])
        rw = factor[pt]
        for t in range(life):
            surviving[key[0]][t] += units
        for sc in scenarios:
            ref = reference[(key[1], sc)]
            cumulative = 0.0
            e_prod0 = 0.0
            for t in range(life):
                e_ref, grid = ref[t]
                if pt == "BEV":
                    e_prod = float(cert) / 1000.0 * rw * grid * vkt
                else:
                    e_prod = float(cert) * rw / 1000.0 * vkt
                if t == 0:
                    e_prod0 = e_prod
                gap = e_ref - e_prod
                cumulative += gap
                annual[(key[0], sc)][t] += gap * units / 1000.0
            cells.append(
                {
                    **base,
                    "scenario": sc,
                    "cohort_year": int(s["cohort_year"]),
                    "units": units,
                    "lifetime_years": life,
                    "vkt_km": round(vkt, 3),
                    "vkt_tier": p["vkt_tier"],
                    "real_world_factor": rw,
                    "e_prod_year0_kgco2e": round(e_prod0, 4),
                    "e_ref_year0_kgco2e": round(ref[0][0], 4),
                    "ti_per_vehicle_kgco2e": round(cumulative, 4),
                    "ti_tco2e": round(cumulative * units / 1000.0, 4),
                }
            )

    cells.sort(
        key=lambda r: tuple(
            str(r[k]) for k in ("company", "scenario", "destination", "model", "powertrain")
        )
    )
    with OUT_CELLS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CELL_FIELDS)
        w.writeheader()
        w.writerows(cells)

    year0 = int(cells[0]["cohort_year"]) if cells else 0
    annual_rows = [
        {
            "company": c,
            "scenario": sc,
            "t": t,
            "calendar_year": year0 + t,
            "surviving_vehicles": int(surviving[c][t]),
            "ti_tco2e": round(v, 4),
        }
        for (c, sc), series in sorted(annual.items())
        for t, v in sorted(series.items())
    ]
    with OUT_ANNUAL.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ANNUAL_FIELDS)
        w.writeheader()
        w.writerows(annual_rows)

    withheld.sort(
        key=lambda r: tuple(str(r[k]) for k in ("company", "powertrain", "destination", "model"))
    )
    with OUT_WITHHELD.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=WITHHELD_FIELDS)
        w.writeheader()
        w.writerows(withheld)

    for c in sorted({str(r["company"]) for r in cells}):
        mine = [r for r in cells if r["company"] == c]
        totals = {
            sc: sum(float(r["ti_tco2e"]) for r in mine if r["scenario"] == sc) for sc in scenarios
        }
        covered = sum(int(r["units"]) for r in mine if r["scenario"] == scenarios[0])
        held = sum(int(r["units"]) for r in withheld if r["company"] == c)
        print(
            f"{c}: covered {covered:,} units, withheld {held:,}; TI tCO2e "
            + ", ".join(f"{sc} {v:,.0f}" for sc, v in totals.items())
        )
    print(
        f"{OUT_CELLS.relative_to(REPO)}: {len(cells)} rows; {OUT_ANNUAL.name}: "
        f"{len(annual_rows)}; {OUT_WITHHELD.name}: {len(withheld)}"
    )


if __name__ == "__main__":
    main()
