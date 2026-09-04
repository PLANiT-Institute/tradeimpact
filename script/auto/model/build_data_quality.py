"""Step 5b — the data-quality declaration that must accompany every cohort result.

Guideline §5.3: a published TI figure carries its analysis level, benchmark method, the tier
of every input behind it, the share of affected units resting on tier-C (proxied) inputs, and
whether that share is high enough that only the direction — not the magnitude — is published.
One declaration per company **x market**: the two markets rest on different sales bases and
different input tiers, so one shared declaration would hide both.

Inputs   output/ti_by_model.csv, output/ti_withheld.csv, output/ti_exclusions.csv,
         output/destination_parameters_*.csv
Output   output/ti_data_quality.csv   one row per company x market

Algorithm:
    tier_c_share = units in markets whose distance tier is C / covered units;
    directional_only = tier_c_share > 0.5 (guideline §5.3 tier-C suppression rule);
    lifetime_T_central = units-weighted mean of the per-market operating life, rounded.

Run from the repository root:  .venv/bin/python script/auto/model/build_data_quality.py
"""

from __future__ import annotations

from collections import Counter, defaultdict

from model_io import OUT_DIR, REPO, load_cohorts, load_params, read_csv, write_csv

CELLS = OUT_DIR / "ti_by_model.csv"
WITHHELD = OUT_DIR / "ti_withheld.csv"
EXCLUSIONS = OUT_DIR / "ti_exclusions.csv"
OUT = OUT_DIR / "ti_data_quality.csv"

# Guideline §5.3: above this tier-C unit share only the direction is published.
TIER_C_THRESHOLD = 0.5
ANALYSIS_LEVEL = "Level 1 (destination cohort; production origin not established)"
LAYER1_METHOD = "B (NDC pro-rata exponential decline)"
#: Withheld reasons are free text; these powertrain labels are the standing categories.
PRICED_POWERTRAIN_REASONS = ("PHEV", "FCEV")
OTHER_REASON = "no_certified_value"

FIELDS = [
    "company",
    "market",
    "cohort_year",
    "analysis_level",
    "layer1_method",
    "sales_basis",
    "test_cycles",
    "covered_units",
    "withheld_units",
    "covered_share",
    "tier_c_units",
    "tier_c_share",
    "directional_only",
    "lifetime_t_central_years",
    "scenarios_reported",
    "scenarios_excluded",
    "markets_covered",
    "markets_vkt_tier_a",
    "markets_vkt_tier_b",
    "markets_vkt_tier_c",
    "markets_fleet_tier_c",
    "withheld_reasons",
    "coverage_notes",
    "warnings",
]


def main() -> None:
    """Write one declaration row per company x market."""
    cells = read_csv(CELLS)
    withheld = read_csv(WITHHELD)
    exclusions = read_csv(EXCLUSIONS)
    params = load_params()
    cohorts = load_cohorts()

    rows: list[dict[str, object]] = []
    for company, market in sorted({(c["company"], c["market"]) for c in cells}):
        theirs = [c for c in cells if c["company"] == company and c["market"] == market]
        scenarios = sorted({c["scenario"] for c in theirs})
        # Units are scenario-invariant; count them once.
        mine = [c for c in theirs if c["scenario"] == scenarios[0]]
        covered = sum(int(c["units"]) for c in mine)
        held = [w for w in withheld if w["company"] == company and w["market"] == market]
        held_units = sum(int(w["units"]) for w in held)
        tier_c = sum(int(c["units"]) for c in mine if c["vkt_tier"] == "C")
        life_weighted = sum(int(c["units"]) * int(c["lifetime_years"]) for c in mine)
        countries = {c["destination"] for c in mine}
        vkt_tiers = Counter(params[(market, m)]["vkt_tier"] for m in countries)
        fleet_c = sum(1 for m in countries if params[(market, m)]["fleet_intensity_tier"] == "C")
        reasons: dict[str, int] = defaultdict(int)
        for w in held:
            key = w["powertrain"] if w["powertrain"] in PRICED_POWERTRAIN_REASONS else OTHER_REASON
            reasons[key] += int(w["units"])
        notes = sorted(
            {
                c["coverage_note"]
                for c in cohorts
                if c["company"] == company and c["market"] == market and c["coverage_note"]
            }
            | {w["coverage_note"] for w in held if w["coverage_note"]}
        )
        market_warnings = sorted(
            {
                w.split(":")[0]
                for (m, _c), p in params.items()
                if m == market
                for w in p["warnings"].split(" | ")
                if w
            }
        )
        rows.append(
            {
                "company": company,
                "market": market,
                "cohort_year": min(int(c["cohort_year"]) for c in mine),
                "analysis_level": ANALYSIS_LEVEL,
                "layer1_method": LAYER1_METHOD,
                "sales_basis": ";".join(
                    sorted(
                        {
                            c["basis"]
                            for c in cohorts
                            if c["company"] == company and c["market"] == market
                        }
                    )
                ),
                "test_cycles": ";".join(sorted({c["test_cycle"] for c in mine})),
                "covered_units": covered,
                "withheld_units": held_units,
                "covered_share": round(covered / (covered + held_units), 6)
                if covered + held_units
                else None,
                "tier_c_units": tier_c,
                "tier_c_share": round(tier_c / covered, 6) if covered else None,
                "directional_only": covered > 0 and tier_c / covered > TIER_C_THRESHOLD,
                "lifetime_t_central_years": round(life_weighted / covered) if covered else None,
                "scenarios_reported": ";".join(scenarios),
                "scenarios_excluded": ";".join(
                    sorted(
                        e["scenario"]
                        for e in exclusions
                        if e["company"] == company and e["market"] == market
                    )
                ),
                "markets_covered": len(countries),
                "markets_vkt_tier_a": vkt_tiers.get("A", 0),
                "markets_vkt_tier_b": vkt_tiers.get("B", 0),
                "markets_vkt_tier_c": vkt_tiers.get("C", 0),
                "markets_fleet_tier_c": fleet_c,
                "withheld_reasons": "; ".join(f"{k} {v:,}" for k, v in sorted(reasons.items())),
                "coverage_notes": " | ".join(notes),
                "warnings": "; ".join(market_warnings),
            }
        )

    write_csv(OUT, FIELDS, rows)
    for r in rows:
        print(
            f"{r['company']} {r['market']}: tier-C share {float(r['tier_c_share']):.1%}, "  # type: ignore[arg-type]
            f"directional_only={r['directional_only']}, T central "
            f"{r['lifetime_t_central_years']} y, excluded [{r['scenarios_excluded']}]"
        )
    print(f"{OUT.relative_to(REPO)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
