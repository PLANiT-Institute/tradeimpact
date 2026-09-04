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
| `sales/processed/sales_eea_eu27_2024.csv` | exists | 1,226 — Hyundai and Kia EU27 first registrations, 2024 (Toyota and Honda snapshots pinned, out of scope) |
| `sales/processed/sales_kia_ir_2026.csv` | exists | 287 — Kia IR retail sales, 2026 year to date |
| `sales/processed/sales_hyundai_plant_2025.csv` | exists | 113 — Hyundai IR plant-side sales, 2025 |
| `sales/method/us_model_map.csv` | exists | 20 — IR model name → EPA `base_model` + powertrain for the US market, with `powertrain_rule` (`explicit` · `mixed_central_ice` · `out_of_scope`) and a note |

| Column | Type | Unit | Allowed values |
|---|---|---|---|
| `company` | text | — | exporter brand in lower case as listed in `sales/method/companies.csv` (`hyundai`, `kia` in scope; `toyota`, `honda` deferred) |
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

Resolved 2026-09-04: `method.md` now lists `plant_sales` and the coverage caveats of both IR workbooks.

---

## 2. `country_emissions` — importer sector and grid emissions

Rules: [`country_emissions/method/method.md`](../../data/auto/country_emissions/method/method.md).
File: `country_emissions/processed/country_emissions_eu27.csv` — **exists**, 1,312 rows, long
format.

| Column | Type | Unit | Allowed values |
|---|---|---|---|
| `country` | text | — | ISO 3166-1 alpha-2 |
| `series` | text | — | `car_co2` · `grid_intensity` · `power_co2` · `transport_ghg`; US adds `ldt_co2`, `ldv_co2`, `car_ghg_co2e`, `ldt_ghg_co2e`, `ldv_ghg_co2e` (see §7) |
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
File: `vehicle_usage/processed/vehicle_usage_eu27.csv` — **exists**, 2,081 rows, long format,
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

Resolved 2026-09-04: `method.md` describes the long format and the derivation in the model step.

---

## 5. `vehicle_technology` — product parameters

Rules: [`vehicle_technology/method/method.md`](../../data/auto/vehicle_technology/method/method.md).

| File | Status | Rows |
|---|---|---|
| `vehicle_technology/processed/vehicle_technology_eea_2024.csv` | exists | 1,226 — certified values per company × destination × model × powertrain, in-scope brands, 2024 |
| `vehicle_technology/method/real_world_correction.csv` | exists | 6 — real-world factor with low/high range per test cycle (WLTP, EPA) × powertrain, with derivation and `source_id` |

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

Two markets are built: **EU27** (2024 registrations) and **US** (2025/2026 exporter sales).
Every result table carries a `market` column; EU27 and US figures are never summed together.
Output file names carry no market suffix — the reference step is the only per-market script and
its two files are named for the market they describe.

| File | Status | Key | Payload |
|---|---|---|---|
| `cohorts.csv` | exists, 1,042 rows | market + company + destination + model + powertrain + cohort_year + variant | `period`, `units`, `basis`, `tailpipe_gco2_km`, `energy_wh_km`, `test_cycle`, `technology_source`, `sales_source_file`, `powertrain_rule`, `coverage_note` — sales joined to product technology per market (`build_cohorts.py`). `variant = central` is the published cohort; other variants are sensitivity repricings of the same cell |
| `cohorts_withheld.csv` | exists, 210 rows | market + company + destination + model | `units`, `reason`, `coverage_note` — volumes that cannot be joined to a product parameter |
| `destination_parameters_eu27.csv` | exists, 27 rows | market + country + cohort_year | `vkt_km` with low/high bracket, `vkt_tier`, `vkt_derivation`, `car_stock`, `car_co2_kt`, `fleet_intensity_gco2_km` + tier, `grid_gco2_kwh` + tier, `mean_car_age_years` + tier, `lifetime_years` with low/high, `scenarios_excluded`, `scenario_exclusion_reason`, `warnings`, `source_ids` — each value with its reference year |
| `destination_parameters_us.csv` | exists, 1 row | as above | identical columns (`build_reference_us.py`); distance tier B (FHWA wheelbase classes), lifetime tier C (NHTSA schedule), `scenarios_excluded = S2` |
| `reference_trajectories_eu27.csv` | exists, 1,890 rows | market + country + scenario + t | `calendar_year`, `r_fleet`, `r_power`, `fleet_intensity_gco2_km`, `e_ref_kgco2_per_vehicle`, `grid_kgco2_per_kwh` |
| `reference_trajectories_us.csv` | exists, 32 rows | as above | S1 and S3 only; no S2 trajectory exists for the US |
| `ti_by_model.csv` | exists, 2,971 rows | market + company + destination + model + powertrain + scenario + cohort_year | `units`, `lifetime_years`, `vkt_km`, `vkt_tier`, `test_cycle`, `real_world_factor`, `e_prod_year0_kgco2e`, `e_ref_year0_kgco2e`, `ti_per_vehicle_kgco2e`, `ti_tco2e` |
| `ti_annual_by_model.csv` | exists (`build_ti.py`) | market + company + destination + cohort_year + model + powertrain + scenario + t | `calendar_year`, `units`, `e_ref_kgco2e_per_vehicle`, `e_prod_kgco2e_per_vehicle`, `gap_kgco2e_per_vehicle`, `ti_tco2e` |
| `ti_annual.csv` | exists, 182 rows | market + company + scenario + t | `calendar_year`, `surviving_vehicles`, `ti_tco2e` — the annual TI flow of the cohort |
| `ti_withheld.csv` | exists, 250 rows | market + company + destination + model + powertrain | `units`, `reason`, `coverage_note` — every cell that produced no result, with its unit count (`N-02`) |
| `ti_exclusions.csv` | exists, 2 rows | market + company + scenario | `cohort_year`, `units_affected`, `reason` — a scenario the market publishes no benchmark for, never a silent gap (`N-05`) |
| `ti_country.csv` | exists (`aggregate_country.py`) | company + market + destination + scenario | `units`, `ti_tco2e`, `ti_per_vehicle_kgco2e`, `direction` |
| `ti_powertrain.csv` | exists | company + market + powertrain + scenario | as above |
| `ti_company.csv` | exists | company + market + scenario | `status` (reported/excluded), covered/withheld units, `ti_tco2e`, per-vehicle, `direction`, `decomposition_identity_holds`, `exclusion_reason` |
| `ti_crossover.csv` | exists (`build_sensitivity.py`) | as `ti_by_model` | `crossover_year` (years after sale), `crossover_calendar_year`, `reason`; the `C-05` range treatment waits on `B-07` |
| `ti_sensitivity.csv` | exists (`build_sensitivity.py`) | company + market + scenario + dimension + variant | `parameter`, `ti_tco2e` — lifetime ±3 y, real-world factor range (per test cycle), proxied-distance quartiles, powertrain mix (`all_hev`) |
| `ti_data_quality.csv` | exists (`build_data_quality.py`) | company + market | analysis level, benchmark method, `sales_basis`, `test_cycles`, covered/withheld units, `tier_c_share`, `directional_only`, central lifetime, `scenarios_reported`, `scenarios_excluded`, markets by tier, withheld reasons, `coverage_notes`, warnings |
| `target_set.csv` | planned (ST01) | company + destination + cohort_year | segment, lifetime and its bracket, criteria met, exclusion reason |

Sign convention throughout: positive TI is displacement relative to the importing country's
benchmark, negative TI is lock-in. Every output carries every scenario the market has a
benchmark for (`N-05`); a scenario a market cannot support is published in `ti_exclusions.csv`
with its reason and the units affected, never dropped. No single-scenario headline is ever
published.

---

## 7. Join keys

| From | To | Key | Note |
|---|---|---|---|
| `sales` | `vehicle_technology` | EU27: company + destination + model + powertrain. US: company + `us_model_map.ir_model` → `epa_base_model` + powertrain, then EPA `model_year` ≤ cohort year | Where `sales.powertrain` is empty (Kia and Hyundai IR), `sales/method/us_model_map.csv` supplies it; unmatched models are counted into `cohorts_withheld` and carried into `ti_withheld`, never dropped silently |
| `sales` | `vehicle_usage`, `country_emissions`, `emission_targets` | destination → country | Only for `destination_level = country` |
| `country_emissions` + `vehicle_usage` | `destination_parameters` | market + country | `fleet_intensity = co2 ÷ (stock × vkt)` on one consistent fleet definition per market (EU27: passenger cars; US: all light-duty). EU27 takes the lifetime bracket from the age bands, the US from the NHTSA expected lifetime ±3 y |
| `emission_targets` | `reference_trajectories` | market + country + scenario (+ `rate`) | `r_fleet` drives the benchmark, `r_power` the grid; a scenario with no rate builds no trajectory and lands in `ti_exclusions.csv` |
| `cohorts` + `reference_trajectories` | `ti_by_model` | market + country + scenario + t | Benchmark minus product emissions, per year |
| `ti_by_model` | `ti_country` / `ti_powertrain` / `ti_company` | company + market + destination / powertrain + scenario | The decomposition identity must hold within a market (`N-06`); markets are never summed |

Rows that cannot join — a region-level destination, an unknown destination, a missing powertrain, a
model with no certified intensity, an IR model name with no `us_model_map.csv` row — are counted
into `ti_withheld.csv` with their units. That count is part of every published result, not an
internal detail.

## 7. Processed files added for the United States and Australia (2026-09-04)

Same long-format conventions as sections 2–5 (`country`, `series`, `year`, `value`, `unit`, `source_id`, `source_file`) unless a different header is shown.

| file | rows | columns |
|---|---|---|
| `country_emissions/processed/country_emissions_au.csv` | 140 | country, series, year, value, unit, source_id, source_file |
| `country_emissions/processed/country_emissions_owid_grid.csv` | 52 | country, series, year, value, unit, source_id, source_file |
| `country_emissions/processed/country_emissions_us.csv` | 62 | country, series, year, value, unit, source_id, source_file |
| `emission_targets/processed/emission_targets_au.csv` | 6 | country, scenario, rate, value, target_level, base_year, target_year, derivation, source_id |
| `emission_targets/processed/emission_targets_us.csv` | 6 | country, scenario, rate, value, target_level, base_year, target_year, derivation, source_id |
| `vehicle_technology/processed/vehicle_technology_us_epa.csv` | 147 | company, model_year, model, base_model, powertrain, tailpipe_gco2_km, energy_wh_km, n_trims, test_cycle, source_id, source_file |
| `vehicle_usage/processed/vehicle_usage_au.csv` | 15 | country, series, year, value, unit, source_id, source_file |
| `vehicle_usage/processed/vehicle_usage_au_smvu.csv` | 15 | country, series, year, value, unit, source_id, source_file |
| `vehicle_usage/processed/vehicle_usage_us.csv` | 8 | country, series, year, value, unit, source_id, source_file |
| `vehicle_usage/processed/vehicle_usage_us_lifetime.csv` | 3 | country, series, year, value, unit, source_id, source_file |

Lookups added: `sales/method/companies.csv` (exporter scope), `sales/method/us_model_map.csv` (IR model → EPA base model, powertrain, powertrain_rule), `vehicle_technology/method/real_world_correction.csv` now keyed on `test_cycle` × `powertrain` with `factor_low`/`factor_high`.

## 8. `trade_flows` — passenger-car trade by exporter, importer and powertrain class (added 2026-09-04)

Rules: [`trade_flows/method/method.md`](../../data/auto/trade_flows/method/method.md). Country-level
only — never a company or model figure. File: `trade_flows/processed/trade_flows.csv`, long format.

| Column | Type | Unit | Allowed values |
|---|---|---|---|
| `reporter` | text | — | ISO 3166-1 alpha-2 of the reporting customs authority, or `EU27` |
| `flow` | text | — | `imports` (importer-reported) · `exports` (exporter-reported) |
| `exporter` | text | — | `KR` · `JP` |
| `importer` | text | — | EU member state, `EU27`, `US`, `AU` |
| `year` | int | year | 2022–2025 |
| `hs6` | text | — | HS 2022 six-digit sub-heading of 8703 (`method/hs_passenger_cars.csv`) |
| `powertrain_class` | text | — | `ICE` · `HEV` · `PHEV` · `BEV` · `OTHER` |
| `units` | int | vehicles | empty when the reporter gave no quantity |
| `quantity_flag` | text | — | `reported` · `estimated` · `member_state_sum` (EU27 row) · `not_reported` |
| `value` | real | per `currency` | trade value as reported |
| `currency` | text | — | `EUR` (Comext) · `USD` (Comtrade) |
| `source_id` | text | — | `eurostat_comext_ds045409` · `un_comtrade_public` |
| `source_file` | text | — | raw file behind the row |
