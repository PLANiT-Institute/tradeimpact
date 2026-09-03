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
| country | text | ISO 3166-1 alpha-2, or `EU27` for the aggregate series | |
| series | text | — | `car_co2`, `grid_intensity` (per country); `power_co2`, `transport_ghg` (EU27 aggregate, for pro-rata pathways) |
| year | int | year | reference year of the observation |
| value | real | see `unit` | |
| unit | text | — | `ktCO2`, `gCO2_per_kWh`, `MtCO2e` |
| source_id | text | — | row in the sources table below |
| source_file | text | — | raw file the row came from |

## Raw files

| file | source | how obtained | sha256 |
|---|---|---|---|
| `../vehicle_usage/raw/destination_eu27_inputs.json` (shared, not copied) | Eurostat GHG inventory series and Ember grid intensity via Our World in Data (links below) | downloaded by the archived adapter on 2026-08-09 into one hash-pinned JSON | `c0fdf593…c1c5ff` |

## Sources

| source_id | dataset | link |
|---|---|---|
| `eurostat_env_air_gge_crf1a3b1` | GHG inventory, CO2, source sector CRF 1.A.3.b.i passenger cars, thousand tonnes | <https://ec.europa.eu/eurostat/databrowser/view/env_air_gge/default/table?lang=en> |
| `eurostat_env_air_gge_crf1a1a` | GHG inventory, CO2, CRF 1.A.1.a public electricity and heat, EU27, thousand tonnes | same dataset |
| `eurostat_env_air_gge_crf1a3` | GHG inventory, all GHG, CRF 1.A.3 transport, EU27, million tonnes | same dataset |
| `owid_ember_grid_intensity` | Carbon intensity of electricity (gCO2e/kWh), Ember Yearly Electricity Data as published by Our World in Data | <https://ourworldindata.org/grapher/carbon-intensity-electricity> (Ember: <https://ember-energy.org/data/yearly-electricity-data/>) |

To collect for the other importers: US — EPA GHG Inventory (passenger cars) and eGRID or
Ember for grid; Australia — DCCEEW National Inventory and AEMO or Ember for grid.

## Processed files

| processed file | script | content |
|---|---|---|
| `country_emissions_eu27.csv` | `script/auto/country_emissions/extract_eu27_snapshot.py` | `car_co2` and `grid_intensity` for 27 markets, EU27 `power_co2` and `transport_ghg` from 1990 |

## Processing method

Scripts in `script/auto/country_emissions/`; one per source; output one tidy CSV
`processed/country_emissions.csv` in the shape above. Unit conversions are explicit in the
script; no value is typed in by hand without a `source_id`.

## Rules

- Every row carries a `source_id`; a country with no source has no row.
- Grid intensity and sector emissions are separate series — never derived from each other.
