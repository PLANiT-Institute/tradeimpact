"""Step 5f — what is actually on hand for each sale year, parameter by parameter.

Every other table says what the model computed. This one says what it computed it from, and how
old that was. A sale year is only as good as the observations that existed by then, and the
failure this catches is the quiet one: a 2026 cohort assessed on a 2023 inventory and a 2024
distance survey, with nothing on the face of the result to say so.

One row per sale year x country x dataset x parameter:

    observation_year  the year the value actually comes from, not the year it is used for
    lag_years         sale year minus observation year; 0 means the data had caught up
    status            current / behind / stale / carried_forward / no_observation_year / missing
    tier, source_id   as the parameter itself carries them

``carried_forward`` is the one that matters most: the same observation serving two sale years
means the second year received nothing new. A country whose whole row is carried forward is a
country that has not been updated, however recent the sale year on the report is.

Inputs
    output/destination_parameters_*.csv     distance, stock, intensity, grid, age, lifetime
    output/reference_trajectories_*.csv     the scenario rates actually applied
    output/cohorts.csv                      the sales period behind each cohort
    vehicle_technology/processed/*.csv      the certified values, and the vintage each publishes
    emission_targets/processed/*.csv        the committed path and the target it was read from
    registry/sources.csv                    when each source was last accessed
Output
    output/data_readiness.csv

Run from the repository root:  .venv/bin/python script/auto/model/build_readiness.py
"""

from __future__ import annotations

from collections import defaultdict

from model_io import DATA, OUT_DIR, REPO, read_csv, write_csv

OUT = OUT_DIR / "data_readiness.csv"
TECHNOLOGY = DATA / "vehicle_technology" / "processed"
TARGETS = DATA / "emission_targets" / "processed"
SOURCES = DATA / "registry" / "sources.csv"

#: How far behind the sale year an observation may be before it is called stale.
BEHIND_YEARS = 2
#: Which dataset each destination parameter belongs to, and the column carrying its year.
PARAMETERS = [
    ("vehicle_usage", "vkt_km", "vkt_year", "vkt_tier"),
    ("vehicle_usage", "stock", "stock_year", "vkt_tier"),
    ("vehicle_usage", "mean_age_years", "mean_age_year", "mean_age_tier"),
    ("vehicle_usage", "lifetime_years", "mean_age_year", "lifetime_tier"),
    ("country_emissions", "fleet_intensity_gco2_km", "co2_year", "fleet_intensity_tier"),
    ("country_emissions", "grid_gco2_kwh", "grid_year", "grid_tier"),
]
#: Market -> the technology table its cohorts are joined to, and the column holding its vintage.
TECHNOLOGY_TABLES = {
    "EU27": ("vehicle_technology_eea_2024.csv", "cohort_year"),
    "US": ("vehicle_technology_us_epa.csv", "model_year"),
    "KR": ("vehicle_technology_kr_kea.csv", ""),
    "JP": ("vehicle_technology_jp_mlit.csv", ""),
}

FIELDS = [
    "cohort_year",
    "market",
    "country",
    "dataset",
    "parameter",
    "value",
    "observation_year",
    "lag_years",
    "status",
    "tier",
    "source_id",
    "note",
]


def status_of(cohort_year: int, observation_year: int | None, seen_before: bool) -> str:
    """Name how well the data had caught up with the sale year.

    Args:
        cohort_year: The sale year the value is used for.
        observation_year: The year the value was observed, or None where none is published.
        seen_before: Whether an earlier sale year already used this same observation.

    Returns:
        One of ``current``, ``carried_forward``, ``behind``, ``stale``, ``no_observation_year``.
    """
    if observation_year is None:
        return "no_observation_year"
    if seen_before:
        return "carried_forward"
    lag = cohort_year - observation_year
    if lag <= 0:
        return "current"
    return "behind" if lag <= BEHIND_YEARS else "stale"


def year_of(row: dict[str, str], column: str) -> int | None:
    """The integer year in one column of a parameter row, or None where it is blank."""
    value = row.get(column, "")
    return int(value) if value else None


def parameter_rows() -> list[dict[str, object]]:
    """Readiness rows for every destination parameter, over every sale year built."""
    rows: list[dict[str, object]] = []
    #: (country, parameter) -> the observation years already used by an earlier sale year.
    used: dict[tuple[str, str], set[int]] = defaultdict(set)
    params = []
    for path in sorted(OUT_DIR.glob("destination_parameters_*.csv")):
        params.extend(read_csv(path))
    for p in sorted(params, key=lambda r: (int(r["cohort_year"]), r["country"], r["segment"])):
        cohort_year = int(p["cohort_year"])
        for dataset, value_col, year_col, tier_col in PARAMETERS:
            if not p.get(value_col):
                continue
            observation = year_of(p, year_col)
            key = (p["country"] + "/" + p["segment"], value_col)
            seen = observation is not None and observation in used[key]
            rows.append(
                {
                    "cohort_year": cohort_year,
                    "market": p["market"],
                    "country": p["country"],
                    "dataset": dataset,
                    "parameter": f"{value_col} ({p['segment']})",
                    "value": p[value_col],
                    "observation_year": observation if observation is not None else "",
                    "lag_years": cohort_year - observation if observation is not None else "",
                    "status": status_of(cohort_year, observation, seen),
                    "tier": p.get(tier_col, ""),
                    "source_id": p.get("source_ids", ""),
                    "note": "",
                }
            )
            if observation is not None:
                used[key].add(observation)
    return rows


def target_rows(accessed: dict[str, str]) -> list[dict[str, object]]:
    """Readiness rows for the scenario rates, one per sale year the trajectories carry."""
    markets = {
        "emission_targets_eu27.csv": "EU27",
        "emission_targets_us.csv": "US",
        "emission_targets_kr.csv": "KR",
        "emission_targets_jp.csv": "JP",
    }
    built: dict[str, set[int]] = defaultdict(set)
    for path in sorted(OUT_DIR.glob("reference_trajectories_*.csv")):
        for r in read_csv(path):
            built[r["market"]].add(int(r["cohort_year"]))

    rows: list[dict[str, object]] = []
    used: dict[tuple[str, str, str], set[int]] = defaultdict(set)
    for name, market in markets.items():
        path = TARGETS / name
        if not path.exists():
            continue
        for cohort_year in sorted(built.get(market, set())):
            for t in read_csv(path):
                source = t["source_id"].split(";")[0]
                # The target has no vintage of its own yet, so the nearest honest stand-in is
                # when the register last went and looked at it.
                seen_year = accessed.get(source, "")
                observation = int(seen_year[:4]) if seen_year[:4].isdigit() else None
                key = (t["country"], t["scenario"], t["rate"])
                seen = observation is not None and observation in used[key]
                rows.append(
                    {
                        "cohort_year": cohort_year,
                        "market": market,
                        "country": t["country"],
                        "dataset": "emission_targets",
                        "parameter": f"{t['rate']} ({t['scenario']})",
                        "value": t["value"],
                        "observation_year": observation if observation is not None else "",
                        "lag_years": cohort_year - observation if observation is not None else "",
                        "status": status_of(cohort_year, observation, seen),
                        "tier": t["target_level"],
                        "source_id": t["source_id"],
                        "note": (
                            "the target carries no vintage of its own: this is the date the "
                            "register last read the policy, so every sale year is measured "
                            "against the policy as it stands today rather than as it stood then"
                        ),
                    }
                )
                if observation is not None:
                    used[key].add(observation)
    return rows


def technology_rows() -> list[dict[str, object]]:
    """Readiness rows for the certified product values behind each market's cohorts."""
    built: dict[str, set[int]] = defaultdict(set)
    for r in read_csv(OUT_DIR / "cohorts.csv"):
        built[r["market"]].add(int(r["cohort_year"]))

    rows: list[dict[str, object]] = []
    for market, (name, year_col) in TECHNOLOGY_TABLES.items():
        path = TECHNOLOGY / name
        if not path.exists():
            continue
        table = read_csv(path)
        for cohort_year in sorted(built.get(market, set())):
            if year_col:
                years = [int(r[year_col]) for r in table if r.get(year_col)]
                eligible = [y for y in years if y <= cohort_year] or years
                observation = max(eligible) if eligible else None
                note = ""
            else:
                observation = None
                note = (
                    f"{name} publishes no vintage column, so there is no way to tell which "
                    "edition of the certification list a sale year was assessed on"
                )
            rows.append(
                {
                    "cohort_year": cohort_year,
                    "market": market,
                    "country": market,
                    "dataset": "vehicle_technology",
                    "parameter": "certified values",
                    "value": f"{len(table)} rows",
                    "observation_year": observation if observation is not None else "",
                    "lag_years": cohort_year - observation if observation is not None else "",
                    "status": status_of(cohort_year, observation, seen_before=False),
                    "tier": "",
                    "source_id": name,
                    "note": note,
                }
            )
    return rows


def sales_rows() -> list[dict[str, object]]:
    """Readiness rows for the volumes themselves: which months each cohort actually covers."""
    spans: dict[tuple[int, str, str, str], set[str]] = defaultdict(set)
    for r in read_csv(OUT_DIR / "cohorts.csv"):
        if r["variant"] != "central":
            continue
        key = (int(r["cohort_year"]), r["market"], r["destination"], r["company"])
        spans[key].update(m for m in r["period"].split("..") if m)
    rows: list[dict[str, object]] = []
    for (cohort_year, market, country, company), months in sorted(spans.items()):
        bounds = sorted(months)
        period = f"{bounds[0]}..{bounds[-1]}"
        full = bounds[0].endswith("-01") and bounds[-1].endswith("-12")
        rows.append(
            {
                "cohort_year": cohort_year,
                "market": market,
                "country": country,
                "dataset": "sales",
                "parameter": f"volumes ({company})",
                "value": period,
                "observation_year": cohort_year,
                "lag_years": 0,
                "status": "current" if full else "behind",
                "tier": "",
                "source_id": "",
                "note": "" if full else "a part year: the source does not cover the whole year",
            }
        )
    return rows


def main() -> None:
    """Write the readiness ledger and print what is not current."""
    accessed = {r["source_id"]: r["accessed_date"] for r in read_csv(SOURCES)}
    rows = parameter_rows() + target_rows(accessed) + technology_rows() + sales_rows()
    rows.sort(
        key=lambda r: (
            int(str(r["cohort_year"])),
            str(r["market"]),
            str(r["country"]),
            str(r["dataset"]),
            str(r["parameter"]),
        )
    )
    write_csv(OUT, FIELDS, rows)

    counts: dict[tuple[int, str], int] = defaultdict(int)
    for r in rows:
        counts[(int(str(r["cohort_year"])), str(r["status"]))] += 1
    print(f"{OUT.relative_to(REPO)}: {len(rows)} rows")
    for year in sorted({int(str(r["cohort_year"])) for r in rows}):
        parts = [
            f"{status} {counts[(year, status)]}"
            for status in ("current", "behind", "stale", "carried_forward", "no_observation_year")
            if counts[(year, status)]
        ]
        print(f"  {year}: " + ", ".join(parts))


if __name__ == "__main__":
    main()
