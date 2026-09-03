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

## Raw files and sources

Raw file: `../vehicle_usage/raw/destination_eu27_inputs.json` (shared, not copied) —
Eurostat GHG inventory `env_air_gge` (CRF 1.A.3.b.i passenger cars per country; EU27
CRF 1.A.1.a public electricity and CRF 1.A.3 transport) and Ember grid intensity via Our
World in Data, downloaded 2026-08-09. Source ids `eurostat_env_air_gge_crf1a3b1`,
`eurostat_env_air_gge_crf1a1a`, `eurostat_env_air_gge_crf1a3`, `owid_ember_grid_intensity`
resolve in [`../../sources.csv`](../../sources.csv); the file hash is in
[`../../raw_files.csv`](../../raw_files.csv).

Second raw file: `owid_carbon_intensity_electricity.csv` — the full OWID grapher export of
Ember grid intensity (all entities), downloaded 2026-09-04; used for the United States and
Australia (`source_id` `owid_ember_grid_intensity`, hash in `raw_files.csv`).

Third raw file: `epa_ghg_inventory_2025_table_3_13.csv` — the passenger-car rows of EPA GHG
Inventory Table 3-13 (`epa_ghg_inventory_2025`), extracted from the inventory PDF text for
1990, 2005 and 2019–2023 (gasoline and diesel). The main text reports only those years; the
full annual series lives in the inventory annex and is still to collect, so the US S1 trend
cannot yet be derived. Australia passenger-car CO2 (DCCEEW National Inventory) is still to
collect. Grid intensity for both is done.

## Processed files

| processed file | script | content |
|---|---|---|
| `country_emissions_eu27.csv` | `script/auto/country_emissions/extract_eu27_snapshot.py` | `car_co2` and `grid_intensity` for 27 markets, EU27 `power_co2` and `transport_ghg` from 1990 |
| `country_emissions_owid_grid.csv` | `script/auto/country_emissions/extract_owid_grid.py` | `grid_intensity` for US and AU, all years Ember publishes |
| `country_emissions_us.csv` | `script/auto/country_emissions/extract_epa_inventory.py` | US `car_co2` (gasoline + diesel passenger cars, ktCO2) for the seven years the main text reports |

## Processing method

Scripts in `script/auto/country_emissions/`; one per source; output one tidy CSV
`processed/country_emissions.csv` in the shape above. Unit conversions are explicit in the
script; no value is typed in by hand without a `source_id`.

## Rules

- Every row carries a `source_id`; a country with no source has no row.
- Grid intensity and sector emissions are separate series — never derived from each other.
