# country_emissions — importer sector and electricity emissions

## What this dataset is

Observed emissions of each importer country (research process step 2.1), two series:

1. **Road-transport / passenger-car sector emissions** — the base year level the sector
   benchmark declines from (whitepaper Layer 1, `E_ref` base).
2. **Electricity grid intensity** — gCO2e/kWh, the enabling reference for BEV/PHEV use-phase
   emissions (whitepaper Layer 2, `G_c(0)`).

Importers: EU27 member states, United States, Australia.

## Required fields (processed output)

| field | type | unit | note |
|---|---|---|---|
| country | text | ISO 3166-1 alpha-2 | |
| series | text | — | `car_co2` or `grid_intensity` |
| year | int | year | reference year of the observation |
| value | real | ktCO2e (car_co2) / gCO2e_per_kWh (grid_intensity) | |
| source_id | text | — | row in `method/sources.md` |

## Sources (to register per country in `sources.md` as collected)

- EU27 car CO2: EEA national GHG inventories (CRF 1.A.3.b.i passenger cars) or UNFCCC CRT.
- EU27 grid intensity: EEA electricity CO2 intensity series, or Ember yearly data.
- US: EPA GHG Inventory (transport, passenger cars); eGRID / Ember for grid.
- Australia: DCCEEW National Inventory; AEMO / Ember for grid.
- The archived pipeline's `destination_eu27_inputs.json` (now in `vehicle_usage/raw/`)
  already carries sourced `car_co2_kt` and `grid_intensity_gco2_per_kwh` per EU27 market
  with tiers and derivations — reuse those values and their citations rather than
  re-collecting.

## Processing method

Scripts in `script/auto/country_emissions/`; one per source; output one tidy CSV
`processed/country_emissions.csv` in the shape above. Unit conversions are explicit in the
script; no value is typed in by hand without a `source_id`.

## Rules

- Every row carries a `source_id`; a country with no source has no row.
- Grid intensity and sector emissions are separate series — never derived from each other.
