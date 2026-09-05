# emission_factors — CO2 per unit of fuel burned

## What this dataset is

The Layer 2 factor that turns a generating unit's fuel use into CO2: kg CO2 per TJ of fuel, by
fuel. Rule set by the project lead on 2026-09-05: **a unit's factor is the destination
country's own fuel-specific factor where one is on file, and the IPCC 2006 default otherwise.**
Both live in one table with a `basis` column; the model applies the order.

## Raw files and sources

- `raw/ipcc_2006_v2_ch2_stationary_combustion.pdf` — 2006 IPCC Guidelines, Volume 2, Chapter 2,
  fetched by `script/power/emission_factors/fetch_ipcc_defaults.py` (link, access date and hash
  in [`../../registry/raw_files.csv`](../../registry/raw_files.csv)). Table 2.2 gives the defaults
  and their 95 % bounds for energy industries.
- `method/ipcc_2006_table_2_2.csv` — **hand transcription** of Table 2.2 (fuel, default, lower,
  upper, biogenic flag) plus `gem_fuel_pattern`, a regex that maps the tracker's fuel text to a
  fuel row. The extractor verifies every number against the PDF's own text and stops if one is
  not found, so a typo cannot reach the model.
- `raw/national_emission_factors.csv` — **HAND-GATHERED, header-only until filled.** A country's
  own implied CO2 factor per fuel for public electricity, read from its national inventory
  (UNFCCC common reporting table 1.A(a) implied emission factors, or the national inventory
  report). One row per country × fuel with `source_url`, `source_id`, `year`, `accessed_date`.
  Each `source_id` also needs a row in `registry/sources.csv`. Where the register has no row for
  a country × fuel, the IPCC default applies and the result cell says so.

## Processed output

`processed/emission_factors.csv` — `country` (`''` for the default that applies to any
country), `fuel_id`, `ef_kgco2_per_tj`, `ef_low_kgco2_per_tj`, `ef_high_kgco2_per_tj`, `basis`
(`national` | `ipcc_default`), `biogenic`, `source_id`, `source_url`, `tier`.

## Tiers

- `national` — A: the country's own published factor for the quantity used.
- `ipcc_default` — C: a global default standing in for the country's value. The bounds are
  carried so the sensitivity can vary the factor over the IPCC range.

## Rules

- Biogenic CO2 (wood, biomass) is computed and reported in its own column, never inside the fossil
  total, following inventory practice.
- Fuel matching runs on the tracker's fuel text in the order of the table; the first pattern
  that matches wins, so specific fuels (lignite, sub-bituminous) sit above the generic coal row.
