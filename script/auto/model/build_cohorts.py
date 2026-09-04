"""Step 3a — the market-neutral cohort table: sales joined to product technology.

One row per market x company x destination x model x powertrain x cohort_year, carrying the
volume and the certified product parameters the impact step needs. Every market is joined by
its own rule; downstream steps read only this table and never a market-specific sales file.

Inputs
    sales/method/companies.csv                                     exporters in scope
    sales/method/us_model_map.csv                                  IR model name -> EPA base model
    sales/processed/sales_eea_eu27_2024.csv                        EU27 registrations
    sales/processed/sales_kia_ir_2026.csv                          Kia IR retail sales
    sales/processed/sales_hyundai_plant_2025.csv                   Hyundai IR plant sales
    vehicle_technology/processed/vehicle_technology_eea_2024.csv   certified WLTP values
    vehicle_technology/processed/vehicle_technology_us_epa.csv     EPA label values
Outputs (data/auto/output/)
    cohorts.csv            the joined cohort rows, one per cell, plus the sensitivity variants
    cohorts_withheld.csv   volumes that cannot enter a result and the reason

Algorithm:
    EU27 — the registration dataset already states the powertrain, so the join is the identity
    $$ (company, destination, model, powertrain) \\rightarrow (I_{cert}, \\eta_{cert}) $$
    on the EEA certified table; test cycle WLTP.

    US — the IR files publish a commercial model name and no powertrain. The name is resolved
    through ``us_model_map.csv`` to an EPA ``base_model`` and a powertrain, then the EPA label
    values of that base model are pooled over the trim-level EPA model names of the most
    recent model year at or before the cohort year:
    $$ I_{cert} = \\frac{\\sum_m n_m\\,I_m}{\\sum_m n_m},\\qquad
       \\eta_{cert} = \\frac{\\sum_m n_m\\,\\eta_m}{\\sum_m n_m} $$
    ASCII: cert = sum(n_trims * value) / sum(n_trims) over the EPA models of one
           (company, model_year, base_model, powertrain).
    n_m      number of certified trims behind EPA model name m (-)
    I_m      EPA label tailpipe intensity of model m (gCO2/km)
    eta_m    EPA label electric consumption of model m (Wh/km)
    Where the IR name covers several powertrains (``powertrain_rule = mixed_central_ice``) the
    central case takes the rule's powertrain and a second row is written under
    ``variant = all_hev`` with the hybrid technology of the same base model, so the sensitivity
    step can price the upper bound without repeating this join.

Run from the repository root:  .venv/bin/python script/auto/model/build_cohorts.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
COMPANIES = DATA / "sales" / "method" / "companies.csv"
US_MODEL_MAP = DATA / "sales" / "method" / "us_model_map.csv"
SALES_EU27 = DATA / "sales" / "processed" / "sales_eea_eu27_2024.csv"
SALES_US = (
    DATA / "sales" / "processed" / "sales_kia_ir_2026.csv",
    DATA / "sales" / "processed" / "sales_hyundai_plant_2025.csv",
)
TECH_EU27 = DATA / "vehicle_technology" / "processed" / "vehicle_technology_eea_2024.csv"
TECH_US = DATA / "vehicle_technology" / "processed" / "vehicle_technology_us_epa.csv"
OUT_DIR = DATA / "output"
OUT_COHORTS = OUT_DIR / "cohorts.csv"
OUT_WITHHELD = OUT_DIR / "cohorts_withheld.csv"

EU27, US = "EU27", "US"
CENTRAL, ALL_HEV = "central", "all_hev"
MIXED_RULE = "mixed_central_ice"
HEV = "HEV"

#: Powertrains that carry no defensible product intensity anywhere yet (guideline A-06).
WITHHELD_POWERTRAIN = {
    "PHEV": "no sourced utility factor: the sales data publish only combined values",
    "FCEV": "no sourced hydrogen supply emissions intensity for the destination",
}
NO_CERTIFIED_EU27 = "the registration dataset reports no certified intensity for this cell"
NO_MAP_ROW = (
    "no row in sales/method/us_model_map.csv: the IR model name is not resolved to an EPA "
    "base model, so no certified intensity can be attached"
)

COHORT_FIELDS = [
    "market",
    "company",
    "destination",
    "cohort_year",
    "period",
    "model",
    "powertrain",
    "units",
    "basis",
    "tailpipe_gco2_km",
    "energy_wh_km",
    "test_cycle",
    "technology_source",
    "sales_source_file",
    "powertrain_rule",
    "coverage_note",
    "variant",
]
WITHHELD_FIELDS = [
    "market",
    "company",
    "destination",
    "cohort_year",
    "model",
    "powertrain",
    "units",
    "reason",
    "coverage_note",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    """All rows of a CSV as dicts."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def in_scope_companies() -> set[str]:
    """Exporter names flagged in scope in the companies lookup."""
    return {r["company"] for r in read_csv(COMPANIES) if r["in_scope"] == "yes"}


def coverage_note(basis: str, period: str) -> str:
    """Sourcing caveat that travels with every row of a sales file.

    The note is derived from the row itself — the reporting basis and the months covered —
    so a new sales file inherits the right caveat without a per-file branch.

    Args:
        basis: `registrations`, `retail_sales` or `plant_sales`.
        period: Months covered, e.g. `2026-01..2026-06`.

    Returns:
        Human-readable caveat, empty when the row needs none.
    """
    notes: list[str] = []
    if basis == "plant_sales":
        notes.append(
            "production-side plant sales: covers only vehicles built at the destination's own "
            "plants; units imported from other plants are not in the source"
        )
    if basis == "retail_sales":
        notes.append("retail sales as published by the exporter's investor-relations release")
    months = [p for p in period.split("..") if p]
    if len(months) == 2 and not (months[0].endswith("-01") and months[1].endswith("-12")):
        notes.append(f"partial year: the source covers {period} only, not the full cohort year")
    return "; ".join(notes)


def aggregate_units(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Sum ``units`` over rows that share every non-volume field.

    The IR files split one destination cohort across production origins; origin is not part of
    the cohort grain (analysis Level 1 does not establish production origin), so the volumes
    are pooled.

    Args:
        rows: Cohort rows carrying an integer ``units`` value.

    Returns:
        One row per distinct set of non-volume fields, units summed, deterministically ordered.
    """
    pooled: dict[tuple[object, ...], dict[str, object]] = {}
    for row in rows:
        key = tuple(v for k, v in sorted(row.items()) if k != "units")
        if key in pooled:
            pooled[key]["units"] = int(str(pooled[key]["units"])) + int(str(row["units"]))
        else:
            pooled[key] = dict(row)
    return list(pooled.values())


def build_eu27(companies: set[str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Join the EU27 registrations to the EEA certified values.

    Args:
        companies: Exporters in scope.

    Returns:
        cohorts: Central-variant cohort rows for the EU27 market.
        withheld: Volumes that carry no certified value or no priceable powertrain.
    """
    tech = {
        (r["company"], r["destination"], r["model"], r["powertrain"]): r
        for r in read_csv(TECH_EU27)
    }
    cohorts: list[dict[str, object]] = []
    withheld: list[dict[str, object]] = []
    for s in read_csv(SALES_EU27):
        if s["company"] not in companies:
            continue
        note = coverage_note(s["basis"], s["period"])
        identity = {
            "market": EU27,
            "company": s["company"],
            "destination": s["destination"],
            "cohort_year": int(s["cohort_year"]),
            "model": s["model"],
            "powertrain": s["powertrain"],
        }
        units = int(s["units"])
        if s["powertrain"] in WITHHELD_POWERTRAIN:
            withheld.append(
                {
                    **identity,
                    "units": units,
                    "reason": WITHHELD_POWERTRAIN[s["powertrain"]],
                    "coverage_note": note,
                }
            )
            continue
        t = tech.get((s["company"], s["destination"], s["model"], s["powertrain"]))
        tailpipe = t["tailpipe_gco2_km"] if t else ""
        energy = t["energy_wh_km"] if t else ""
        certified = energy if s["powertrain"] == "BEV" else tailpipe
        if t is None or not certified:
            withheld.append(
                {**identity, "units": units, "reason": NO_CERTIFIED_EU27, "coverage_note": note}
            )
            continue
        cohorts.append(
            {
                **identity,
                "period": s["period"],
                "units": units,
                "basis": s["basis"],
                "tailpipe_gco2_km": tailpipe,
                "energy_wh_km": energy,
                "test_cycle": t["test_cycle"],
                "technology_source": f"{t['source_id']} ({t['source_file']})",
                "sales_source_file": s["source_file"],
                "powertrain_rule": "explicit",
                "coverage_note": note,
                "variant": CENTRAL,
            }
        )
    return cohorts, withheld


def epa_technology(
    tech: list[dict[str, str]],
) -> dict[tuple[str, str, str], dict[int, dict[str, object]]]:
    """Pool the EPA label values of every (company, base_model, powertrain) by model year.

    Args:
        tech: Rows of the processed EPA technology table.

    Returns:
        {(company, base_model, powertrain): {model_year: pooled values}} where the pooled
        values carry ``tailpipe_gco2_km``, ``energy_wh_km``, ``n_models``, ``n_trims`` and
        ``test_cycle``.
    """
    buckets: dict[tuple[str, str, str, int], list[dict[str, str]]] = defaultdict(list)
    for r in tech:
        buckets[(r["company"], r["base_model"], r["powertrain"], int(r["model_year"]))].append(r)
    pooled: dict[tuple[str, str, str], dict[int, dict[str, object]]] = defaultdict(dict)
    for (company, base, pt, year), group in buckets.items():
        weights = [int(r["n_trims"]) for r in group]
        total = sum(weights)
        pooled[(company, base, pt)][year] = {
            "tailpipe_gco2_km": weighted_mean(group, weights, "tailpipe_gco2_km"),
            "energy_wh_km": weighted_mean(group, weights, "energy_wh_km"),
            "n_models": len(group),
            "n_trims": total,
            "test_cycle": group[0]["test_cycle"],
            "source_id": group[0]["source_id"],
            "source_file": group[0]["source_file"],
        }
    return pooled


def weighted_mean(rows: list[dict[str, str]], weights: list[int], field: str) -> float | None:
    """Trim-weighted mean of one numeric field over the rows that report it.

    Args:
        rows: EPA rows of one (company, model_year, base_model, powertrain).
        weights: Trim counts, aligned with ``rows``.
        field: Column to average.

    Returns:
        The weighted mean, or None when no row reports the field.
    """
    pairs = [(w, float(r[field])) for r, w in zip(rows, weights, strict=True) if r[field]]
    total = sum(w for w, _ in pairs)
    return sum(w * v for w, v in pairs) / total if total else None


def pick_model_year(
    by_year: dict[int, dict[str, object]], cohort_year: int
) -> tuple[int, dict[str, object]]:
    """Most recent model year at or before the cohort year, else the most recent available."""
    eligible = [y for y in by_year if y <= cohort_year]
    year = max(eligible) if eligible else max(by_year)
    return year, by_year[year]


def build_us(companies: set[str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Join the US IR sales to the EPA label values through the US model map.

    Args:
        companies: Exporters in scope.

    Returns:
        cohorts: Central-variant rows plus the ``all_hev`` variant of every mixed cohort.
        withheld: Volumes with no map row, no EPA technology or an unpriceable powertrain.
    """
    mapping = {(r["company"], r["ir_model"]): r for r in read_csv(US_MODEL_MAP)}
    pooled = epa_technology(read_csv(TECH_US))
    central: list[dict[str, object]] = []
    variants: list[dict[str, object]] = []
    withheld: list[dict[str, object]] = []

    for path in SALES_US:
        for s in read_csv(path):
            if s["company"] not in companies or s["destination"] != US:
                continue
            note = coverage_note(s["basis"], s["period"])
            cohort_year = int(s["cohort_year"])
            m = mapping.get((s["company"], s["model"]))
            identity = {
                "market": US,
                "company": s["company"],
                "destination": US,
                "cohort_year": cohort_year,
                "model": s["model"],
                "powertrain": (m or {}).get("powertrain", ""),
            }
            units = int(s["units"])
            if m is None:
                withheld.append(
                    {**identity, "units": units, "reason": NO_MAP_ROW, "coverage_note": note}
                )
                continue
            pt, rule = m["powertrain"], m["powertrain_rule"]
            if not pt:
                withheld.append(
                    {
                        **identity,
                        "units": units,
                        "reason": f"{rule}: {m['note']}",
                        "coverage_note": note,
                    }
                )
                continue
            if pt in WITHHELD_POWERTRAIN:
                withheld.append(
                    {
                        **identity,
                        "units": units,
                        "reason": WITHHELD_POWERTRAIN[pt],
                        "coverage_note": note,
                    }
                )
                continue
            row = us_cohort_row(s, m, pt, pooled, note)
            if row is None:
                withheld.append(
                    {
                        **identity,
                        "units": units,
                        "reason": (
                            f"no EPA technology row for {m['epa_base_model']} {pt} at or before "
                            f"model year {cohort_year} in vehicle_technology_us_epa.csv"
                        ),
                        "coverage_note": note,
                    }
                )
                continue
            central.append(row)
            if rule == MIXED_RULE:
                variants.append(all_hev_variant(s, m, pt, pooled, note, row))

    return aggregate_units(central) + aggregate_units(variants), withheld


def us_cohort_row(
    s: dict[str, str],
    m: dict[str, str],
    powertrain: str,
    pooled: dict[tuple[str, str, str], dict[int, dict[str, object]]],
    note: str,
    variant: str = CENTRAL,
) -> dict[str, object] | None:
    """One US cohort row, or None when the base model has no EPA technology at all."""
    by_year = pooled.get((s["company"], m["epa_base_model"], powertrain))
    if not by_year:
        return None
    cohort_year = int(s["cohort_year"])
    year, values = pick_model_year(by_year, cohort_year)
    certified = values["energy_wh_km"] if powertrain == "BEV" else values["tailpipe_gco2_km"]
    if certified is None:
        return None
    return {
        "market": US,
        "company": s["company"],
        "destination": US,
        "cohort_year": cohort_year,
        "period": s["period"],
        "model": s["model"],
        "powertrain": powertrain,
        "units": int(s["units"]),
        "basis": s["basis"],
        "tailpipe_gco2_km": round_or_blank(values["tailpipe_gco2_km"]),
        "energy_wh_km": round_or_blank(values["energy_wh_km"]),
        "test_cycle": values["test_cycle"],
        "technology_source": (
            f"{values['source_id']} ({values['source_file']}): {m['epa_base_model']} "
            f"{powertrain} model year {year}, {values['n_models']} EPA model name(s), "
            f"{values['n_trims']} trims, trim-weighted mean"
        ),
        "sales_source_file": s["source_file"],
        "powertrain_rule": m["powertrain_rule"],
        "coverage_note": note,
        "variant": variant,
    }


def all_hev_variant(
    s: dict[str, str],
    m: dict[str, str],
    powertrain: str,
    pooled: dict[tuple[str, str, str], dict[int, dict[str, object]]],
    note: str,
    central_row: dict[str, object],
) -> dict[str, object]:
    """The all-hybrid bound of a mixed cohort row.

    Falls back to the central row when the base model has no hybrid on the EPA table; the
    fallback is named in ``powertrain_rule`` so the bound is never silently the central case.
    """
    row = us_cohort_row(s, m, HEV, pooled, note, variant=ALL_HEV)
    if row is not None:
        return row
    fallback = dict(central_row)
    fallback["variant"] = ALL_HEV
    fallback["powertrain_rule"] = f"{MIXED_RULE}_no_hev_on_epa_table"
    return fallback


def round_or_blank(value: object) -> object:
    """Round a pooled certified value to 2 dp, or return an empty cell when absent."""
    return "" if value is None else round(float(str(value)), 2)


def main() -> None:
    """Build the cohort table and the withheld table for every market in scope."""
    companies = in_scope_companies()
    eu_cohorts, eu_withheld = build_eu27(companies)
    us_cohorts, us_withheld = build_us(companies)
    cohorts = eu_cohorts + us_cohorts
    withheld = eu_withheld + us_withheld

    order = ("market", "variant", "company", "destination", "model", "powertrain")
    cohorts.sort(key=lambda r: tuple(str(r[k]) for k in order))
    withheld.sort(
        key=lambda r: tuple(str(r[k]) for k in ("market", "company", "destination", "model"))
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_COHORTS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COHORT_FIELDS)
        w.writeheader()
        w.writerows(cohorts)
    with OUT_WITHHELD.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=WITHHELD_FIELDS)
        w.writeheader()
        w.writerows(withheld)

    markets = {str(r["market"]) for r in cohorts} | {str(r["market"]) for r in withheld}
    for market in sorted(markets):
        for company in sorted(companies):
            covered = sum(
                int(str(r["units"]))
                for r in cohorts
                if r["market"] == market and r["company"] == company and r["variant"] == CENTRAL
            )
            held = sum(
                int(str(r["units"]))
                for r in withheld
                if r["market"] == market and r["company"] == company
            )
            if covered or held:
                print(f"{market} {company}: {covered:,} units joined, {held:,} withheld")
    print(
        f"{OUT_COHORTS.relative_to(REPO)}: {len(cohorts)} rows; "
        f"{OUT_WITHHELD.name}: {len(withheld)} rows"
    )


if __name__ == "__main__":
    main()
