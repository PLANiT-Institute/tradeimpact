# vehicle_technology — product technology parameters

## What this dataset is

Technology-side inputs per model / powertrain (research process step 2.3; whitepaper
Layer 2): certified tailpipe intensity, electric energy consumption, real-world correction
factors, and PHEV utility factors. Together with grid intensity these produce the product
emissions trajectory `E_prod(t)`.

## Required fields (processed output)

| field | type | unit | note |
|---|---|---|---|
| company | text | — | |
| model | text | — | as in the sales dataset (join key with company + powertrain) |
| powertrain | text | — | ICE / HEV / PHEV / BEV / FCEV |
| tailpipe_gco2_km | real | gCO2/km | certified, registrations-weighted across markets; empty when no bucket reported it |
| tailpipe_units | int | vehicles | registrations behind the tailpipe value |
| energy_wh_km | real | Wh/km | certified electric energy consumption (BEV/PHEV), same weighting |
| energy_units | int | vehicles | registrations behind the energy value |
| units | int | vehicles | total registrations of the model × powertrain |
| test_cycle | text | — | WLTP / EPA / NEDC — never mixed silently |
| source_id | text | — | row in the sources table below |
| source_file | text | — | raw file the row came from |

Real-world correction factors and PHEV utility factors are separate small inputs (one row
per powertrain, with their own `source_id`), added to this dataset when sourced; they are
applied in the model step, never folded into the certified columns.

## Raw files

| file | source | how obtained | sha256 |
|---|---|---|---|
| `../sales/raw/eea_toyota_2024_final.json`, `../sales/raw/eea_hyundai_2024_final.json` (shared, not copied) | EEA CO2 monitoring database, certified WLTP CO2 (`Ewltp__g_km_`) and electric energy consumption per registration, aggregated per country × model × powertrain — <https://co2cars.apps.eea.europa.eu/> | downloaded 2026-08-05 by the archived adapter | see `../sales/method/method.md` |

## Sources

| source_id | dataset | link |
|---|---|---|
| `eea_co2_monitoring_2024` | EEA monitoring of CO2 emissions from new passenger cars, 2024 final | <https://co2cars.apps.eea.europa.eu/> |

## Processed files

| processed file | script | content |
|---|---|---|
| `vehicle_technology_eea_2024.csv` | `script/auto/vehicle_technology/extract_eea_certified.py` | 177 company × model × powertrain rows (Toyota, Hyundai, EU27 2024); 15 rows carry no certified CO2 value |

## Sources

- EU: the EEA registration snapshots in `../sales/raw/` carry certified WLTP values per
  row — the primary EU technology source, already joined to volumes.
- Real-world correction: ICCT lab-to-road series (`References/ICCT_2018_LabToRoad.pdf`,
  `ICCT_2024_realworld_CO2_Europe_Jan2024.pdf` in the Drive folder).
- PHEV utility factors: T&E 2023 PHEV report (Drive `References/TE_2023_PHEVs_2_report.pdf`);
  publish PHEV results only when a sourced UF exists (they were withheld in the EU27 run
  for exactly this reason).
- US: EPA certification data by model.

## Processing method

Scripts in `script/auto/vehicle_technology/`; output `processed/vehicle_technology.csv`.
Certified values are corrected to real-world **once**, at processing time, with the factor
and its source recorded per row — never inside the model scripts.

## Rules

- Test cycles are never mixed across markets without an explicit, sourced conversion.
- A model with no sourced technology row contributes no result — its units are reported as
  withheld with their count, never absorbed.
