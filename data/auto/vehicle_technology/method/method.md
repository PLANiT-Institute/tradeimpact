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

Real-world correction factors are a separate small input keyed on test cycle × powertrain
(`method/real_world_correction.csv`, each row with its own `source_id`): WLTP values get the
EEA OBFCM factors and range; EPA label values are already 5-cycle adjusted, so their factor is
1.0 at both ends. They are applied in the model step, never folded into the certified columns.
PHEV utility factors are still unsourced, so PHEV stays withheld.

## Raw files and sources

United States: `epa_fueleconomy_vehicles.csv` — the complete EPA/DOE fueleconomy.gov vehicle
dataset (`epa_fueleconomy_vehicles`; 50,242 model-year trims, 1984 onward, 84 columns)
downloaded verbatim from <https://www.fueleconomy.gov/feg/epadata/vehicles.csv>; EPA
combined-cycle values, so never mixed with WLTP rows without an explicit conversion.

EU27: `../sales/raw/eea_*_2024_final.json`
(shared, not copied) — certified WLTP CO2 (`Ewltp__g_km_`) and electric energy
consumption (`z__Wh_km_`) per registration, aggregated by the EEA API per country × model ×
powertrain (`source_id` `eea_co2_monitoring_2024`). Real-world correction factors:
`method/real_world_correction.csv` (`eea_obfcm_real_world_2022`). Both resolve in
[`../../sources.csv`](../../sources.csv).

## Processed files

| processed file | script | content |
|---|---|---|
| `vehicle_technology_eea_2024.csv` | `script/auto/vehicle_technology/extract_eea_certified.py` | one row per company × destination × model × powertrain for the companies in scope (EU27 2024; WLTP); rows without a certified value are kept with an empty value and withheld downstream |
| `vehicle_technology_us_epa.csv` | `script/auto/vehicle_technology/extract_epa_fueleconomy.py` | one row per company × model year (2024–2025) × EPA model name × powertrain for the companies in scope; EPA combined-cycle CO2 (g/mile → g/km) and electricity (kWh/100 mi → Wh/km), unweighted mean over trims with the trim count; `base_model` is the join key to model-level sales |

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
