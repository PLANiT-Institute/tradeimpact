"""Step 5b — the data-quality declaration that must accompany every cohort result.

Guideline §5.3: a published TI figure carries its analysis level, benchmark method, the tier
of every input behind it, the share of affected units resting on tier-C (proxied) inputs, and
whether that share is high enough that only the direction — not the magnitude — is published.

Inputs   output/ti_by_model_eu27.csv, output/ti_withheld_eu27.csv,
         output/destination_parameters_eu27.csv
Output   output/ti_data_quality_eu27.csv   one row per company

Algorithm:
    tier_c_share = units in markets whose distance tier is C / covered units;
    directional_only = tier_c_share > 0.5 (guideline §5.3 tier-C suppression rule);
    lifetime_T_central = units-weighted mean of the per-market operating life, rounded.

Run from the repository root:  .venv/bin/python script/auto/model/build_data_quality.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "data" / "auto" / "output"
CELLS = OUT_DIR / "ti_by_model_eu27.csv"
WITHHELD = OUT_DIR / "ti_withheld_eu27.csv"
PARAMS = OUT_DIR / "destination_parameters_eu27.csv"
OUT = OUT_DIR / "ti_data_quality_eu27.csv"

# Guideline §5.3: above this tier-C unit share only the direction is published.
TIER_C_THRESHOLD = 0.5
ANALYSIS_LEVEL = "Level 1 (destination cohort; production origin not established)"
LAYER1_METHOD = "B (NDC pro-rata exponential decline)"

FIELDS = [
    "company",
    "cohort_year",
    "analysis_level",
    "layer1_method",
    "covered_units",
    "withheld_units",
    "covered_share",
    "tier_c_units",
    "tier_c_share",
    "directional_only",
    "lifetime_t_central_years",
    "markets_covered",
    "markets_vkt_tier_a",
    "markets_vkt_tier_b",
    "markets_vkt_tier_c",
    "markets_fleet_tier_c",
    "withheld_reasons",
    "warnings",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    """Write one declaration row per company."""
    cells = [c for c in read_csv(CELLS) if c["scenario"] == "S1"]  # units are scenario-invariant
    withheld = read_csv(WITHHELD)
    params = {p["country"]: p for p in read_csv(PARAMS)}
    warnings = sorted(
        {w.split(":")[0] for p in params.values() for w in p["warnings"].split(" | ") if w}
    )

    rows: list[dict[str, object]] = []
    for company in sorted({c["company"] for c in cells}):
        mine = [c for c in cells if c["company"] == company]
        covered = sum(int(c["units"]) for c in mine)
        held = [w for w in withheld if w["company"] == company]
        held_units = sum(int(w["units"]) for w in held)
        tier_c = sum(int(c["units"]) for c in mine if c["vkt_tier"] == "C")
        life_weighted = sum(int(c["units"]) * int(c["lifetime_years"]) for c in mine)
        markets = {c["destination"] for c in mine}
        vkt_tiers = Counter(params[m]["vkt_tier"] for m in markets)
        fleet_c = sum(1 for m in markets if params[m]["fleet_intensity_tier"] == "C")
        reasons: dict[str, int] = defaultdict(int)
        for w in held:
            reasons[
                w["powertrain"] if w["powertrain"] in ("PHEV", "FCEV") else "no_certified_value"
            ] += int(w["units"])
        rows.append(
            {
                "company": company,
                "cohort_year": mine[0]["cohort_year"],
                "analysis_level": ANALYSIS_LEVEL,
                "layer1_method": LAYER1_METHOD,
                "covered_units": covered,
                "withheld_units": held_units,
                "covered_share": round(covered / (covered + held_units), 6),
                "tier_c_units": tier_c,
                "tier_c_share": round(tier_c / covered, 6) if covered else None,
                "directional_only": covered > 0 and tier_c / covered > TIER_C_THRESHOLD,
                "lifetime_t_central_years": round(life_weighted / covered) if covered else None,
                "markets_covered": len(markets),
                "markets_vkt_tier_a": vkt_tiers.get("A", 0),
                "markets_vkt_tier_b": vkt_tiers.get("B", 0),
                "markets_vkt_tier_c": vkt_tiers.get("C", 0),
                "markets_fleet_tier_c": fleet_c,
                "withheld_reasons": "; ".join(f"{k} {v:,}" for k, v in sorted(reasons.items())),
                "warnings": "; ".join(warnings),
            }
        )

    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(
            f"{r['company']}: tier-C share {float(r['tier_c_share']):.1%}, "  # type: ignore[arg-type]
            f"directional_only={r['directional_only']}, T central {r['lifetime_t_central_years']} y"
        )
    print(f"{OUT.relative_to(REPO)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
