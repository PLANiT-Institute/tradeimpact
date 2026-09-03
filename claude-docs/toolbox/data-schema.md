# Processed data structure and schema

The single consolidated view of the columns and keys, as the files actually are at 2026-09-04.
Sources, per-file hashes and dataset rules stay in each `data/auto/<dataset>/method/method.md`,
which this document links to and never copies. How each dataset is gathered, processed and
analysed: [`../stages/st02-06-datasets.md`](../stages/st02-06-datasets.md).

Conventions: all names `snake_case`; one processed file **per source or per market scope**, never a
silently merged file; every row carries a `source_id` or the `source_file` whose hash is registered
in its `method.md`; an empty cell means *unavailable* and never zero (`N-02`).

**Status:** *exists* = in the repository at 2026-09-04 · *planned* = specified here, written when
the step that consumes it is ready.

---

## 1. `sales` — exporter volumes

Rules: [`sales/method/method.md`](../../data/auto/sales/method/method.md).

| File | Status | Rows |
|---|---|---|
| `sales/processed/sales_eea_eu27_2024.csv` | exists | 2,126 — Toyota, Honda, Hyundai and Kia EU27 first registrations, 2024 |
| `sales/processed/sales_kia_ir_2026.csv` | exists | 287 — Kia IR retail sales, 2026 year to date |
| `sales/processed/sales_hyundai_plant_2025.csv` | exists | 113 — Hyundai IR plant-side sales, 2025 |

| Column | Type | Unit | Allowed values |
|---|---|---|---|
| `company` | text | — | `hyundai` · `kia` · `toyota` · `honda` |
| `destination` | text | — | ISO 3166-1 alpha-2 when `destination_level = country`; the source's own region label otherwise; empty when unknown |
| `destination_level` | text | — | `country` · `region` · `unknown` |
| `origin` | text | — | ISO 3166-1 alpha-2 producing country, or a non-country plant label as the source states it (`ckd`, `special_vehicle`); empty when the source does not say |
| `cohort_year` | int | year | Year of sale or first registration |
| `period` | text | — | Coverage of the row, `YYYY-MM..YYYY-MM` — a part-year table must never be read as a full year |
| `model` | text | — | Commercial name as reported |
| `powertrain` | text | — | `ICE` · `HEV` · `PHEV` · `BEV` · `FCEV`; empty where the source carries none, to be joined from `vehicle_technology` |
| `units` | int | vehicles | ≥ 0 |
| `basis` | text | — | `registrations` · `retail_sales` · `plant_sales` — never mixed inside one aggregate |
| `source_file` | text | — | The raw file the row came from |

`destination_level` and `basis` exist because the raw IR workbooks force them: Kia IR reports
regions (Europe, Eastern Europe, Latin America, Middle East, Africa, Asia Pacific), and Hyundai IR
reports plant-side sales with a domestic/export split rather than destinations. Both facts are
carried in the data instead of resolved by assumption.

**To reconcile:** `method.md` lists the third basis value as `wholesale`; the data uses
`plant_sales`. The method file is the one to change. Tracked in
[`../tracker.md`](../tracker.md) §6.

---

## 2. `country_emissions` — importer sector and grid emissions

Rules: [`country_emissions/method/method.md`](../../data/auto/country_emissions/method/method.md).
File: `country_emissions/processed/country_emissions_eu27.csv` — **exists**, 1,312 rows, long
format.

| Column | Type | Unit | Allowed values |
|---|---|---|---|
| `country` | text | — | ISO 3166-1 alpha-2 |
| `series` | text | — | `car_co2` · `grid_intensity` · `power_co2` · `transport_ghg` |
| `year` | int | year | Reference year of the observation |
| `value` | real | per `unit` | > 0 |
| `unit` | text | — | `ktCO2` for the emission series; `gCO2e/kWh` for `grid_intensity` |
| `source_id` | text | — | e.g. `eurostat_env_air_gge_crf1a3b1`, `owid_ember_grid_intensity` |
| `source_file` | text | — | The raw or snapshot file behind the row |

One long table; the series are independent evidence and are never derived from one another
(`N-07`).

---

## 3. `emission_targets` — NDC and sector targets

Rules: [`emission_targets/method/method.md`](../../data/auto/emission_targets/method/method.md).
File: `emission_targets/processed/emission_targets_eu27.csv` — **exists**, 162 rows (27 markets ×
3 scenarios × 2 rates), long format.

| Column | Type | Unit | Allowed values |
|---|---|---|---|
| `country` | text | — | ISO 3166-1 alpha-2 |
| `scenario` | text | — | `S1` current trajectory · `S2` committed policy · `S3` 1.5C-aligned |
| `rate` | text | — | `r_fleet` · `r_power` — the two are derived independently (`N-07`) |
| `value` | real | 1/year | ≥ 0, annual fractional decline |
| `target_level` | text | — | As used: `observed_trend` (S1) · `ndc_prorata` (S2) · `1p5c_prorata` (S3). The whitepaper's five-level hierarchy (`sector_country`, `sector_regional`, `ndc_prorata`, `regional_prorata`, `none`) is what a market *qualifies* for; the value here records what was actually applied |
| `base_year` | int | year | |
| `target_year` | int | year | > `base_year` |
| `derivation` | text | — | The derivation in words, verbatim — how the rate was obtained from the source |
| `source_id` | text | — | Semicolon-separated ids naming the documents the rate actually came from |

A market with no usable base-to-target arithmetic, or no active NDC, gets no S2 row and is reported
separately (`A-09`, `B-04`) — not a substituted rate.

---

## 4. `vehicle_usage` — how vehicles are used

Rules: [`vehicle_usage/method/method.md`](../../data/auto/vehicle_usage/method/method.md).
File: `vehicle_usage/processed/vehicle_usage_eu27.csv` — **exists**, 2,092 rows, long format,
same column set as `country_emissions`.

| Column | Type | Unit | Allowed values |
|---|---|---|---|
| `country` | text | — | ISO 3166-1 alpha-2 |
| `series` | text | — | `car_stock` · `car_traffic` · `car_traffic_fallback` · `car_stock_age_total` · `car_stock_age_y_lt2` · `car_stock_age_y2-5` · `car_stock_age_y5-10` · `car_stock_age_y10-20` · `car_stock_age_y_gt20` |
| `year` | int | year | |
| `value` | real | per `unit` | > 0 |
| `unit` | text | — | `vehicles` for stock and age bands; `Mkm` or `km/year` for traffic as the source publishes it |
| `source_id` | text | — | e.g. `eurostat_road_eqs_carpda`, `eurostat_road_eqs_carage` |
| `source_file` | text | — | |

Distance per car, the tier and the lifetime bracket are **derived** from these series in ST08 and
land in `destination_parameters_eu27.csv` (§6), where the derivation string and warning travel with
the value.

**To reconcile:** `method.md` specifies a wide table (`vkt`, `vkt_tier`, `operating_life`,
`car_stock`, `stock_year`); the data is long-format observations and the derived parameters sit in
the output. The method file should describe what is built. Tracked in
[`../tracker.md`](../tracker.md) §6.

---

## 5. `vehicle_technology` — product parameters

Rules: [`vehicle_technology/method/method.md`](../../data/auto/vehicle_technology/method/method.md).

| File | Status | Rows |
|---|---|---|
| `vehicle_technology/processed/vehicle_technology_eea_2024.csv` | exists | 2,126 — certified values per company × destination × model × powertrain, four brands, 2024 |
| `vehicle_technology/method/real_world_correction.csv` | exists | 3 — the real-world correction factor per powertrain, with derivation and `source_id` |

| Column | Type | Unit | Allowed values |
|---|---|---|---|
| `company` | text | — | as `sales.company` |
| `destination` | text | — | ISO 3166-1 alpha-2 |
| `model` | text | — | Commercial name; must match `sales.model` to join |
| `powertrain` | text | — | `ICE` · `HEV` · `PHEV` · `BEV` · `FCEV` |
| `cohort_year` | int | year | |
| `tailpipe_gco2_km` | real | gCO2/km | ≥ 0, certified |
| `tailpipe_units` | int | vehicles | Registrations behind the tailpipe value |
| `energy_wh_km` | real | Wh/km | Certified electric consumption; empty for pure combustion |
| `energy_units` | int | vehicles | Registrations behind the energy value |
| `units` | int | vehicles | Total registrations for the cell |
| `test_cycle` | text | — | `WLTP` · `EPA` · `NEDC` — never mixed without a sourced conversion |
| `source_id` | text | — | e.g. `eea_co2_monitoring_2024` |
| `source_file` | text | — | |

The real-world correction lives in `method/real_world_correction.csv` and is applied **once**, in
the model step, as `real_world_factor` on each result row (`A-05`). No PHEV utility factor is
sourced yet, so PHEV cells are withheld (`A-06`).

**To reconcile:** `method.md` specifies `energy_kwh_100km`, `rw_correction` and `utility_factor`
columns on this table; the data uses `energy_wh_km` (the unit the EEA publishes) and carries the
correction separately. Tracked in [`../tracker.md`](../tracker.md) §6.

---

## 6. Outputs — `data/auto/output/`

| File | Status | Key | Payload |
|---|---|---|---|
| `destination_parameters_eu27.csv` | exists, 27 rows | country + cohort_year | `vkt_km` with low/high bracket, `vkt_tier`, `vkt_derivation`, `car_stock`, `car_co2_kt`, `fleet_intensity_gco2_km` + tier, `grid_gco2_kwh` + tier, `mean_car_age_years` + tier, `lifetime_years` with low/high, `warnings`, `source_ids` — each value with its reference year |
| `reference_trajectories_eu27.csv` | exists, 1,899 rows | country + scenario + t | `calendar_year`, `r_fleet`, `r_power`, `fleet_intensity_gco2_km`, `e_ref_kgco2_per_vehicle`, `grid_kgco2_per_kwh` |
| `ti_by_model_eu27.csv` | exists, 3,321 rows | company + destination + model + powertrain + scenario + cohort_year | `units`, `lifetime_years`, `vkt_km`, `vkt_tier`, `real_world_factor`, `e_prod_year0_kgco2e`, `e_ref_year0_kgco2e`, `ti_per_vehicle_kgco2e`, `ti_tco2e` |
| `ti_annual_eu27.csv` | exists, 150 rows | company + scenario + t | `calendar_year`, `surviving_vehicles`, `ti_tco2e` — the annual TI flow of the cohort |
| `ti_withheld_eu27.csv` | exists, 179 rows | company + destination + model + powertrain | `units`, `reason` — every cell that produced no result, with its unit count (`N-02`) |
| `ti_country_eu27.csv` | exists (`aggregate_country.py`) | company + destination + scenario | `units`, `ti_tco2e`, `ti_per_vehicle_kgco2e`, `direction` |
| `ti_powertrain_eu27.csv` | exists | company + powertrain + scenario | as above |
| `ti_company_eu27.csv` | exists | company + scenario | covered/withheld units, `ti_tco2e`, per-vehicle, `direction`, `decomposition_identity_holds` |
| `ti_crossover_eu27.csv` | exists (`build_sensitivity.py`) | as `ti_by_model` | `crossover_year` (years after sale), `crossover_calendar_year`, `reason`; the `C-05` range treatment waits on `B-07` |
| `ti_sensitivity_eu27.csv` | exists (`build_sensitivity.py`) | company + scenario + dimension + variant | `parameter`, `ti_tco2e` — lifetime ±3 y, real-world factor range, proxied-distance quartiles |
| `ti_data_quality_eu27.csv` | exists (`build_data_quality.py`) | company | analysis level, benchmark method, covered/withheld units, `tier_c_share`, `directional_only`, central lifetime, markets by tier, withheld reasons, warnings |
| `target_set.csv` | planned (ST01) | company + destination + cohort_year | segment, lifetime and its bracket, criteria met, exclusion reason |

Sign convention throughout: positive TI is displacement relative to the importing country's
benchmark, negative TI is lock-in. Every output carries all three scenarios (`N-05`); no
single-scenario headline is ever published.

---

## 7. Join keys

| From | To | Key | Note |
|---|---|---|---|
| `sales` | `vehicle_technology` | company + model + powertrain (+ destination + cohort_year for the EEA tables) | Where `sales.powertrain` is empty (Kia and Hyundai IR), the join supplies it; unmatched models are counted into `ti_withheld`, never dropped silently |
| `sales` | `vehicle_usage`, `country_emissions`, `emission_targets` | destination → country | Only for `destination_level = country` |
| `country_emissions` + `vehicle_usage` | `destination_parameters` | country | `fleet_intensity = car_co2 ÷ (car_stock × vkt)`; the age bands give the lifetime bracket |
| `emission_targets` | `reference_trajectories` | country + scenario (+ `rate`) | `r_fleet` drives the benchmark, `r_power` the grid |
| `reference_trajectories` | `ti_by_model` | country + scenario + t | Benchmark minus product emissions, per year |
| `ti_by_model` | `ti_country` / `ti_powertrain` / `ti_company` | company + destination / powertrain + scenario | The decomposition identity must hold (`N-06`) |

Rows that cannot join — a region-level destination, an unknown destination, a missing powertrain, a
model with no certified intensity — are counted into `ti_withheld_eu27.csv` with their units. That
count is part of every published result, not an internal detail.
