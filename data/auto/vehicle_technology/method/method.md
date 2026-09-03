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
| model | text | — | as in the sales dataset (join key) |
| powertrain | text | — | ICE / HEV / PHEV / BEV / FCEV |
| tailpipe_gco2_km | real | gCO2/km | certified (WLTP or CAFE-cycle; cycle recorded) |
| energy_kwh_100km | real | kWh/100km | BEV/PHEV electric consumption |
| utility_factor | real | fraction | PHEV electric share — only if sourced |
| rw_correction | real | multiplier | real-world correction by powertrain (ICCT lab-to-road) |
| test_cycle | text | — | WLTP / EPA / NEDC — never mix cycles silently |
| source_id | text | — | row in `method/sources.md` |

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
