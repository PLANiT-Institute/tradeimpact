"""Derive US passenger-car operating life from the NHTSA survival schedule.

Input   data/auto/vehicle_usage/raw/nhtsa_809952_passenger_car_survival.csv — Table 7 of
        NHTSA DOT HS 809 952 (Vehicle Survivability and Travel Mileage Schedules, 2006):
        survival probability by vehicle age from 1977-2002 registrations, and annual miles.
Output  data/auto/vehicle_usage/processed/vehicle_usage_us_lifetime.csv (long format)

Algorithm:
    $$ E[T] = \\sum_{a=1}^{25} S(a) $$
    $$ T_{50}: S(T_{50}) = 0.5 \\text{ (linear interpolation)} $$
    ASCII: expected life = sum of survival probabilities over ages 1..25 (years);
           median life = age at which survival crosses 0.5; lifetime miles = sum S(a)*VMT(a).
    S(a) survival probability at age a (-), VMT(a) annual miles at age a.

The schedule predates the current fleet (registrations to 2002), so the series is tier C.
Run from the repository root:  .venv/bin/python script/auto/vehicle_usage/extract_nhtsa_survival.py
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data" / "auto" / "vehicle_usage"
RAW = DATASET / "raw" / "nhtsa_809952_passenger_car_survival.csv"
OUT = DATASET / "processed" / "vehicle_usage_us_lifetime.csv"

KM_PER_MILE = 1.609344
SCHEDULE_YEAR = 2002  # last registration year in the schedule
FIELDS = ["country", "series", "year", "value", "unit", "source_id", "source_file"]


def main() -> None:
    """Compute expected and median lifetime and lifetime distance from the schedule."""
    rows = list(csv.DictReader(RAW.open(newline="")))
    ages = [
        (
            int(r["vehicle_age_years"]),
            float(r["survival_probability"]),
            float(r["annual_vmt_miles"]),
        )
        for r in rows
    ]
    source_id = rows[0]["source_id"]
    expected = sum(s for _, s, _ in ages)
    median = None
    for (a0, s0, _), (a1, s1, _) in zip(ages, ages[1:], strict=False):
        if s0 >= 0.5 > s1:
            median = a0 + (s0 - 0.5) / (s0 - s1) * (a1 - a0)
            break
    lifetime_km = sum(s * v for _, s, v in ages) * KM_PER_MILE
    out = [
        {
            "country": "US",
            "series": "car_expected_lifetime_years",
            "year": SCHEDULE_YEAR,
            "value": round(expected, 3),
            "unit": "years",
            "source_id": source_id,
            "source_file": RAW.name,
        },
        {
            "country": "US",
            "series": "car_median_lifetime_years",
            "year": SCHEDULE_YEAR,
            "value": round(median, 3) if median else None,
            "unit": "years",
            "source_id": source_id,
            "source_file": RAW.name,
        },
        {
            "country": "US",
            "series": "car_lifetime_distance_km",
            "year": SCHEDULE_YEAR,
            "value": round(lifetime_km, 0),
            "unit": "km",
            "source_id": source_id,
            "source_file": RAW.name,
        },
    ]
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print(
        f"{OUT.relative_to(REPO)}: expected life {expected:.2f} y, median {median:.2f} y, "
        f"lifetime distance {lifetime_km:,.0f} km"
    )


if __name__ == "__main__":
    main()
