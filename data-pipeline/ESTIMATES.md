# Removed estimated assessment inputs

Effective 2026-08-03, the project no longer publishes firm assessments built from
analyst-allocated vehicle mixes, proxy fleet intensities, default driving distances, or
reconstructed historical sales cohorts.

## Removed from the active data path

- `data-pipeline/fixtures/toyota.json`
- `data-pipeline/fixtures/hyundai.json`
- Toyota and Hyundai `data/published/{firm}.json` reports
- the public illustrative `ReferenceCo` report and calculator template
- the `placements_by_year` input and `by_year` published result contract

| Removed object | Public state after 2026-08-03 |
|---|---|
| Toyota estimate fixture and report | Deleted; firm remains visible but not runnable |
| Hyundai estimate fixture and report | Deleted; firm remains visible but not runnable |
| ReferenceCo public report/template | Deleted; internal arithmetic fixture only |
| Reconstructed 2022–2023 cohorts | Deleted from input and output contracts |
| Proxy fleet baseline, VKT, lifetime, UF band | Omitted or null until sourced |

The deletions are preserved in Git history. This file remains only as a governance record;
it is not an input source and contains no active estimate table.

## Evidence gate for a future company assessment

A company becomes `runnable: true` only after all of the following are collected with a
source, unit, geography, year, and mapping rule:

1. country/year/model/powertrain registration units;
2. an exact or explicitly disclosed mapping to official certification parameters;
3. operating-country fleet base intensity and annual distance;
4. vehicle lifetime and required uncertainty ranges;
5. scenario-specific transport and power pathways, with pro-rata derivations labelled;
6. a reproducible packaged input that passes `check_published.py`.

Official model certification rows in `Layer2_vehicle_params` are retained as source data.
They do not represent a firm fleet until joined to observed registrations.
