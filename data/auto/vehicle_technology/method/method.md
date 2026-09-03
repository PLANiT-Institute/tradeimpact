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

## Raw files and sources

Raw files: `../sales/raw/eea_toyota_2024_final.json` and `eea_hyundai_2024_final.json`
(shared, not copied) — certified WLTP CO2 (`Ewltp__g_km_`) and electric energy
consumption (`z__Wh_km_`) per registration, aggregated by the EEA API per country × model ×
powertrain (`source_id` `eea_co2_monitoring_2024`). Real-world correction factors:
`method/real_world_correction.csv` (`eea_obfcm_real_world_2022`). Both resolve in
[`../../sources.csv`](../../sources.csv).

## Processed files

| processed file | script | content |
|---|---|---|
| `vehicle_technology_eea_2024.csv` | `script/auto/vehicle_technology/extract_eea_certified.py` | one row per company × destination × model × powertrain (Toyota, Honda, Hyundai, Kia; EU27 2024); rows without a certified value are kept with an empty value and withheld downstream |

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
Certified values stay certified in this dataset. The real-world correction is applied
**once**, in the model step (`script/auto/model/build_ti.py`), reading the factor and its
range per powertrain from `method/real_world_correction.csv`; the factor used is recorded on
every result row (`real_world_factor` in `ti_by_model_eu27.csv`), so it can never be applied
twice.

## Rules

- Test cycles are never mixed across markets without an explicit, sourced conversion.
- A model with no sourced technology row contributes no result — its units are reported as
  withheld with their count, never absorbed.
