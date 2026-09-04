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

EU27: three Eurostat GHG-inventory cubes (`env_air_gge`) fetched directly from the Eurostat API
as JSON-stat 2.0 by `script/auto/vehicle_usage/fetch_eurostat.py` — `eurostat_env_air_gge_car_co2.json`
(CO2, CRF 1.A.3.b.i passenger cars, per country), `eurostat_env_air_gge_eu_power_co2.json`
(CO2, CRF 1.A.1.a public electricity and heat, EU27 aggregate) and
`eurostat_env_air_gge_eu_transport.json` (all GHG, CRF 1.A.3 transport, EU27 aggregate) — plus
the OWID/Ember grid-intensity CSV (`owid_carbon_intensity_electricity.csv`, all entities) for
every member state. Links, access dates and hashes: [`../../raw_files.csv`](../../raw_files.csv),
[`../../sources.csv`](../../sources.csv).

Second raw file: `owid_carbon_intensity_electricity.csv` — the full OWID grapher export of
Ember grid intensity (all entities), downloaded 2026-09-04; used for the United States and
Australia (`source_id` `owid_ember_grid_intensity`, hash in `raw_files.csv`).

Third and fourth raw files, United States: `epa_ghg_inventory_2025_table_3_13.csv` — the
passenger-car rows of EPA GHG Inventory main-text Table 3-13 (`epa_ghg_inventory_2025`; CO2
from fuel combustion; 1990, 2005, 2019–2023) — and `epa_ghg_inventory_2025_table_a_91.csv` —
the passenger-car rows of Annex 3 Table A-91 (`epa_ghg_inventory_2025_annexes`; total GHG by
fuel, i.e. CO2 plus CH4 and N2O; 1990, 2000, 2010 and every year 2013–2023). Both were
extracted from the PDF text with the table and page recorded per row. The level series is
`car_co2` (comparable with the EU CRF CO2); the annual trend series is `car_ghg_co2e`, which
sits within 0.5 % of `car_co2` where both exist. Australia passenger-car CO2 (DCCEEW National
Inventory) is still to collect; the ABS, BITRE and DCCEEW sites refused automated access on
2026-09-04, so those files will be gathered by hand. Grid intensity for both is done.

## Processed files

| processed file | script | content |
|---|---|---|
| `country_emissions_eu27.csv` | `script/auto/country_emissions/extract_eu27_snapshot.py` | `car_co2` and `grid_intensity` for 27 markets, EU27 `power_co2` and `transport_ghg` from 1990 |
| `country_emissions_owid_grid.csv` | `script/auto/country_emissions/extract_owid_grid.py` | `grid_intensity` for US and AU, all years Ember publishes |
| `country_emissions_au.csv` | `script/auto/country_emissions/extract_anga_inventory.py` | AU `car_co2`, `car_ghg_co2e`, `power_co2`, `transport_ghg` 1990–2024 (kt) |
| `country_emissions_us.csv` | `script/auto/country_emissions/extract_epa_inventory.py` | US `car_co2` (ktCO2; seven years from Table 3-13) and `car_ghg_co2e` (ktCO2e; 14 years incl. 2013–2023 from Table A-91), gasoline + diesel (+ alternative fuel) passenger cars |

## Processing method

Scripts in `script/auto/country_emissions/`; one per source; output one tidy CSV
`processed/country_emissions.csv` in the shape above. Unit conversions are explicit in the
script; no value is typed in by hand without a `source_id`.

## Rules

- Every row carries a `source_id`; a country with no source has no row.
- Grid intensity and sector emissions are separate series — never derived from each other.
