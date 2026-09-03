"""Step 4b — crossover year per cell and the mandatory sensitivities (guideline §3.3, §5).

Inputs   output/destination_parameters_eu27.csv, output/reference_trajectories_eu27.csv (rates),
         sales/processed/sales_eea_eu27_2024.csv, vehicle_technology/processed/*_eea_2024.csv,
         vehicle_technology/method/real_world_correction.csv
Outputs  output/ti_crossover_eu27.csv     per company x destination x model x powertrain x scenario
         output/ti_sensitivity_eu27.csv   per company x scenario x dimension x variant: total TI

Algorithm:
    Crossover t* is the year the annual gap changes sign (closed form, whitepaper §3.3 note,
    guideline §3.3):
    $$ t^*_{ICE} = \\frac{\\ln\\big(E_{prod}/E_{ref}(0)\\big)}{\\ln(1-r_{fleet})},\\qquad
       t^*_{BEV} = \\frac{\\ln\\big(\\eta G_0 / I_0\\big)}{\\ln\\big((1-r_{fleet})/(1-r_{power})\\big)} $$
    ASCII: t_ice = ln(E_prod/E_ref0)/ln(1-r_fleet); t_bev = ln(eta*G0/I0)/ln((1-r_fleet)/(1-r_power))
    Negative t* means the product is already above (ICE) or below (BEV) the benchmark at sale.
    Sensitivities recompute the cohort total with one input moved at a time:
      lifetime   T_c -/+ 3 years (guideline §5.2; each market's own T, floor 1)
      realworld  ICE and HEV factor set to the low (diesel) and high (petrol) end of the EEA
                 OBFCM gap; BEV stays at 1.0 — the factor REPLACES the central one, it is not
                 applied on top of it
      vkt_proxy  proxied (tier C) markets moved to the lower/upper quartile of measured distances;
                 the benchmark per vehicle is unchanged because distance cancels in CO2 per car
    Symbols: E in kgCO2e per vehicle-year, I0 fleet intensity (kg/km), G0 grid (kg/kWh), eta
    consumption (kWh/km), r in 1/year, T in years.

Run from the repository root:  .venv/bin/python script/auto/model/build_sensitivity.py
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
SALES = DATA / "sales" / "processed" / "sales_eea_eu27_2024.csv"
TECH = DATA / "vehicle_technology" / "processed" / "vehicle_technology_eea_2024.csv"
CORRECTION = DATA / "vehicle_technology" / "method" / "real_world_correction.csv"
PARAMS = DATA / "output" / "destination_parameters_eu27.csv"
REFERENCE = DATA / "output" / "reference_trajectories_eu27.csv"
OUT_CROSS = DATA / "output" / "ti_crossover_eu27.csv"
OUT_SENS = DATA / "output" / "ti_sensitivity_eu27.csv"

LIFETIME_DELTA_Y = 3
RW_RANGE_SOURCE = "eea_obfcm_real_world_2022"

CROSS_FIELDS = [
    "company",
    "destination",
    "model",
    "powertrain",
    "scenario",
    "units",
    "ti_per_vehicle_kgco2e",
    "crossover_year",
    "crossover_calendar_year",
    "reason",
]
SENS_FIELDS = ["company", "scenario", "dimension", "variant", "parameter", "ti_tco2e"]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def crossover(
    pt: str, i0: float, rf: float, rp: float, e_prod0: float, eta_g0: float
) -> tuple[float | None, str | None]:
    """Closed-form t* (years after sale) or (None, reason)."""
    if pt == "BEV":
        a, b = 1.0 - rf, 1.0 - rp
        if eta_g0 <= 0 or i0 <= 0:
            return None, "non-positive intensity"
        if abs(a - b) < 1e-12:
            return None, "r_fleet == r_power: parallel trajectories, no finite crossover"
        t = math.log(eta_g0 / i0) / math.log(a / b)
        return (t, None) if t >= 0 else (None, "crossover before sale year")
    if rf <= 0:
        return None, "r_fleet <= 0: benchmark non-declining, no crossover"
    if e_prod0 <= 0:
        return None, "non-positive emissions ratio"
    t = math.log(e_prod0) / math.log(1.0 - rf)  # e_prod0 is already the ratio E_prod/E_ref(0)
    return (
        (t, None)
        if t >= 0
        else (None, "crossover before sale year (product already above benchmark at t=0)")
    )


def main() -> None:
    """Write crossover years per cell and one-at-a-time sensitivities per company x scenario."""
    tech = {
        (r["company"], r["destination"], r["model"], r["powertrain"]): r for r in read_csv(TECH)
    }
    factor = {r["powertrain"]: float(r["factor"]) for r in read_csv(CORRECTION)}
    rw_low, rw_high = (
        min(v for k, v in factor.items() if k != "BEV"),
        max(v for k, v in factor.items() if k != "BEV"),
    )
    # The two combustion factors are the diesel-midpoint and petrol ends of the OBFCM gap.
    params = {r["country"]: r for r in read_csv(PARAMS)}
    rates: dict[tuple[str, str], tuple[float, float]] = {}
    for r in read_csv(REFERENCE):
        rates[(r["country"], r["scenario"])] = (float(r["r_fleet"]), float(r["r_power"]))
    scenarios = sorted({s for (_, s) in rates})

    # Priced cells only: same rule as build_ti.py.
    cells: list[tuple[dict[str, str], float, str]] = []
    for s in read_csv(SALES):
        pt = s["powertrain"]
        if pt not in factor:
            continue
        t_row = tech.get((s["company"], s["destination"], s["model"], pt))
        cert = (
            None
            if t_row is None
            else (t_row["energy_wh_km"] if pt == "BEV" else t_row["tailpipe_gco2_km"])
        )
        if cert:
            cells.append((s, float(cert), pt))

    def total(
        sc: str, life_delta: int = 0, rw: dict[str, float] | None = None, vkt_key: str | None = None
    ) -> float:
        """Cohort total (tCO2e) for one scenario with one input moved."""
        rw = rw or factor
        out: dict[str, float] = defaultdict(float)
        for s, cert, pt in cells:
            p = params[s["destination"]]
            vkt = float(p["vkt_km"])
            if vkt_key and p["vkt_tier"] == "C" and p[vkt_key]:
                vkt = float(p[vkt_key])
            i0 = float(p["fleet_intensity_gco2_km"]) / 1000.0
            g0 = float(p["grid_gco2_kwh"]) / 1000.0
            e_ref0 = i0 * float(p["vkt_km"])  # benchmark per car: distance cancels
            life = max(1, int(p["lifetime_years"]) + life_delta)
            rf, rp = rates[(s["destination"], sc)]
            cum = 0.0
            for t in range(life):
                e_ref = e_ref0 * (1 - rf) ** t
                e_prod = (
                    (cert / 1000.0 * rw[pt] * g0 * (1 - rp) ** t * vkt)
                    if pt == "BEV"
                    else (cert * rw[pt] / 1000.0 * vkt)
                )
                cum += e_ref - e_prod
            out[s["company"]] += cum * int(s["units"]) / 1000.0
        return out  # type: ignore[return-value]

    cross_rows: list[dict[str, object]] = []
    for s, cert, pt in cells:
        p = params[s["destination"]]
        vkt, i0, g0 = (
            float(p["vkt_km"]),
            float(p["fleet_intensity_gco2_km"]) / 1000.0,
            float(p["grid_gco2_kwh"]) / 1000.0,
        )
        life = int(p["lifetime_years"])
        for sc in scenarios:
            rf, rp = rates[(s["destination"], sc)]
            e_prod_const = cert * factor[pt] / 1000.0 * vkt
            eta_g0 = cert / 1000.0 * factor[pt] * g0
            ratio = e_prod_const / (i0 * vkt) if pt != "BEV" else 0.0
            t_star, reason = crossover(pt, i0, rf, rp, ratio, eta_g0)
            cum = sum(
                i0 * vkt * (1 - rf) ** t
                - ((eta_g0 * (1 - rp) ** t * vkt) if pt == "BEV" else e_prod_const)
                for t in range(life)
            )
            cross_rows.append(
                {
                    "company": s["company"],
                    "destination": s["destination"],
                    "model": s["model"],
                    "powertrain": pt,
                    "scenario": sc,
                    "units": int(s["units"]),
                    "ti_per_vehicle_kgco2e": round(cum, 4),
                    "crossover_year": None if t_star is None else round(t_star, 3),
                    "crossover_calendar_year": None
                    if t_star is None
                    else round(int(s["cohort_year"]) + t_star, 1),
                    "reason": reason or ("within lifetime" if t_star < life else "after lifetime"),  # type: ignore[operator]
                }
            )
    cross_rows.sort(
        key=lambda r: tuple(
            str(r[k]) for k in ("company", "scenario", "destination", "model", "powertrain")
        )
    )
    with OUT_CROSS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CROSS_FIELDS)
        w.writeheader()
        w.writerows(cross_rows)

    variants: list[tuple[str, str, str, dict[str, object]]] = [
        ("lifetime", "central", "T_c", {}),
        ("lifetime", "minus", f"T_c - {LIFETIME_DELTA_Y}", {"life_delta": -LIFETIME_DELTA_Y}),
        ("lifetime", "plus", f"T_c + {LIFETIME_DELTA_Y}", {"life_delta": LIFETIME_DELTA_Y}),
        ("realworld", "central", "ICE 1.191, HEV 1.211, BEV 1.0", {}),
        (
            "realworld",
            "low",
            f"ICE and HEV {rw_low}, BEV 1.0",
            {"rw": {"ICE": rw_low, "HEV": rw_low, "BEV": 1.0}},
        ),
        (
            "realworld",
            "high",
            f"ICE and HEV {rw_high}, BEV 1.0",
            {"rw": {"ICE": rw_high, "HEV": rw_high, "BEV": 1.0}},
        ),
        ("vkt_proxy", "central", "EU stock-weighted mean for tier-C markets", {}),
        ("vkt_proxy", "low", "lower quartile of measured distances", {"vkt_key": "vkt_low_km"}),
        ("vkt_proxy", "high", "upper quartile of measured distances", {"vkt_key": "vkt_high_km"}),
    ]
    sens_rows: list[dict[str, object]] = []
    for dim, var, parameter, kwargs in variants:
        for sc in scenarios:
            for company, value in sorted(total(sc, **kwargs).items()):  # type: ignore[arg-type]
                sens_rows.append(
                    {
                        "company": company,
                        "scenario": sc,
                        "dimension": dim,
                        "variant": var,
                        "parameter": parameter,
                        "ti_tco2e": round(value, 1),
                    }
                )
    sens_rows.sort(
        key=lambda r: tuple(str(r[k]) for k in ("company", "scenario", "dimension", "variant"))
    )
    with OUT_SENS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SENS_FIELDS)
        w.writeheader()
        w.writerows(sens_rows)

    within = sum(1 for r in cross_rows if r["reason"] == "within lifetime")
    print(f"{OUT_CROSS.relative_to(REPO)}: {len(cross_rows)} cells, {within} cross within lifetime")
    for company in sorted({r["company"] for r in sens_rows}):
        for dim in ("lifetime", "realworld", "vkt_proxy"):
            vals = {
                r["variant"]: r["ti_tco2e"]
                for r in sens_rows
                if r["company"] == company and r["scenario"] == "S2" and r["dimension"] == dim
            }
            print(
                f"  {company} S2 {dim}: "
                + ", ".join(f"{k} {float(v):,.0f}" for k, v in vals.items())
            )
    print(f"{OUT_SENS.relative_to(REPO)}: {len(sens_rows)} rows")


if __name__ == "__main__":
    main()
