# Stages ST02–ST06 — the five datasets

One stage per dataset in `data/auto/`. Each section states the same three things: how the data is
**gathered** (source, locator, what is fetched, hand-gathered or downloadable), how it is
**processed** (raw → processed, the script, the file written), and how it is **analysed** (what the
model step consumes from it and how).

Column-level schema for every file below: [`../toolbox/data-schema.md`](../toolbox/data-schema.md).
Sources, per-file hashes and dataset rules stay in each `data/auto/<dataset>/method/method.md` —
their only home. Shared procedure: [`../process/dataset-acquisition.md`](../process/dataset-acquisition.md).

**State at 2026-09-04.** All five datasets have a processed table for the EU27 first pass; each was
built when the step that consumes it became ready, and none covers a market outside that pass.

| Stage | Dataset | Raw on hand | Processed on hand | Scripts |
|---|---|---|---|---|
| ST02 | `sales` | 4 files | 3 tables | `extract_eea_registrations.py`, `extract_kia_ir.py`, `extract_hyundai_ir.py` |
| ST03 | `country_emissions` | via the EU27 snapshot | `country_emissions_eu27.csv` | `extract_eu27_snapshot.py` |
| ST04 | `emission_targets` | `eu_climate_targets.csv` | `emission_targets_eu27.csv` | `derive_eu27_rates.py` |
| ST05 | `vehicle_usage` | `destination_eu27_inputs.json` | `vehicle_usage_eu27.csv` | `extract_eu27_eurostat.py` |
| ST06 | `vehicle_technology` | reads `sales/raw` | `vehicle_technology_eea_2024.csv` plus `method/real_world_correction.csv` | `extract_eea_certified.py` |

Each dataset's processed shape is in [`../toolbox/data-schema.md`](../toolbox/data-schema.md), which
also records three places where a `method.md` now describes a different shape from the data and
needs updating.

---

## ST02 — `sales` · exporter volumes · *live*

**Main goal.** Observed volumes `V_c,v` per company × destination × model × powertrain × cohort
year — the `Volume(t)` term of the TI formula and the anchor of everything downstream.
Rules: [`sales/method/method.md`](../../data/auto/sales/method/method.md).

### Data gathering

| Source | Locator | What is fetched | Route |
|---|---|---|---|
| `SRC-01` EEA CO2 monitoring of new passenger cars (Reg. (EU) 2019/631) | `https://co2cars.apps.eea.europa.eu/` | 2024 **Final** data, EU27, filtered by manufacturer (`Mk=TOYOTA`, `Mk=HYUNDAI`); response is an aggregation of country → commercial name → powertrain with summed registrations | Downloadable via the portal API; two hash-pinned snapshots already held as `raw/eea_toyota_2024_final.json` and `raw/eea_hyundai_2024_final.json` |
| `SRC-04` Kia IR retail sales by model and market | Kia IR disclosure (`(기아차) 2026 현지판매실적.xlsx`), Drive `Trade/Arc_Trade_Data/Auto/` | Monthly sheets plus a `Total` year-to-date sheet: model × market units, in blocks by production plant | **Hand-gathered** from the IR release; no API. Held as `raw/kia_2026_retail_sales_by_model_market.xlsx` |
| `SRC-05` Hyundai IR global plant sales | Hyundai IR disclosure (`hmc-global-plant-sales-dec-y2025.xlsx`), same Drive folder | Monthly plant-side sales by model and plant, with a domestic/export split | **Hand-gathered**. Held as `raw/hyundai_2025_global_plant_sales.xlsx` |
| `SRC-03` EEA, Kia and Honda brands | as `SRC-01` | Same query pattern, `Mk=KIA` and `Mk=HONDA` | Downloadable — **not yet fetched** |
| `SRC-06` United States volumes by model and powertrain | Company IR; EPA certification data | Model-level registrations or sales | **Unresolved.** Experian and WardsAuto are paywalled and therefore out of scope (`X-02`); the fallback route is unproven |
| `SRC-07` Australia volumes by model and powertrain | FCAI public summaries | Model-level sales | **Unresolved.** VFACTS is paywalled (`X-02`); FCAI summaries are aggregate, one data level too coarse |

### Processing

| Script | Reads | Writes | What it does |
|---|---|---|---|
| `script/auto/sales/extract_eea_registrations.py` | the two EEA snapshots | `processed/sales_eea_eu27_2024.csv` — 1,286 rows (Toyota 660, Hyundai 626) | Flattens the aggregation; powertrain classes as EEA records them (ICE, HEV, PHEV, BEV, FCEV); `basis = registrations`; `destination_level = country` for all rows |
| `script/auto/sales/extract_kia_ir.py` | the Kia workbook, `method/kia_labels.csv` | `processed/sales_kia_ir_2026.csv` — 287 rows | Reads the `Total` sheet, skips plant subtotal rows, resolves market labels through the label map: `destination_level = region` for Kia's IR regions (Europe, Eastern Europe, Latin America, Middle East, Africa, Asia Pacific — 206 rows) and `country` for the rest (81 rows); `basis = retail_sales`; `powertrain` empty, to be joined from ST06 |
| `script/auto/sales/extract_hyundai_ir.py` | the Hyundai workbook, `method/hyundai_plant_codes.csv` | `processed/sales_hyundai_plant_2025.csv` — 113 rows | Maps plant codes to the producing country in `origin`; `basis = plant_sales`; `destination_level = unknown` for the 46 domestic/export split rows, which name no destination at all |

One script per raw source, one processed table per source — never a silently merged file. Bases
are never mixed inside one aggregate (`registrations` ≠ `retail_sales` ≠ `plant_sales`).

### Analysis

ST09 consumes `units` as `V_c,v`, keyed on company + destination + model + powertrain + cohort
year. Three restrictions carry through, and they are what the extra columns exist for:

- Only rows with `destination_level = country` **and** a resolved `powertrain` can enter a
  country-level TI result. The first-pass EU27 2024 run therefore uses
  `sales_eea_eu27_2024.csv` alone.
- `destination_level = region` rows aggregate separately in ST10 and are never folded into a
  country total.
- `basis = plant_sales` rows are production-side. They inform Level 2 attribution context only and
  never a destination TI, because the production country sits outside the Layer 1 and Layer 2
  boundary (`X-04`, `A-10`).

**Phases served.** PH1/2; PH4/2–3 (sector equivalents).
**Owners.** `data-collector`, `developer`, `source-reconciliation-analyst` (basis conflicts);
review `tester` then `auditor`.
**Stop when.** Every company × destination in the target set has processed rows with a stated
basis and destination level, or a withheld row with a reason and a count.
**Repeat when.** A new cohort year, company or market; an EEA vintage moves provisional → final; a
paywall fallback resolves; a powertrain mapping correction lands in ST06.
**Backward move.** If a market's volumes cannot be had at model × powertrain granularity under
`C-08`, the market returns to ST01 for re-scoping rather than proceeding on an aggregate that
hides powertrain.

---

## ST03 — `country_emissions` · importer sector and grid emissions

**Main goal.** Per importer: passenger-car sector emissions (the level the benchmark declines
from) and electricity grid intensity (the enabling reference for BEV and PHEV).
Rules: [`country_emissions/method/method.md`](../../data/auto/country_emissions/method/method.md).

### Data gathering

| Source | Locator | What is fetched | Route |
|---|---|---|---|
| `SRC-08` National GHG inventories, CRF 1.A.3.b.i passenger cars | UNFCCC CRT tables (`https://unfccc.int/ghg-inventories-annex-i-parties`); EEA datahub | ktCO2e per country per year for passenger cars | Downloadable; per-country table extraction |
| `SRC-11` Ember electricity data | `https://ember-energy.org/data/` | gCO2e/kWh per country per year | Downloadable CSV |
| `SRC-12` EEA electricity CO2 intensity series | `https://www.eea.europa.eu/en/datahub` | gCO2e/kWh per EU country | Downloadable; cross-check against Ember |
| `SRC-09` EPA Inventory of US GHG Emissions and Sinks | `https://www.epa.gov/ghgemissions` | US passenger-car CO2 | Downloadable; **hand extraction** from the transport tables |
| `SRC-10` DCCEEW National Greenhouse Accounts | `https://www.dcceew.gov.au/climate-change/publications/national-greenhouse-accounts` | Australian passenger-car CO2 | Downloadable; hand extraction |
| `SRC-20` Archived EU27 destination snapshot | `data/auto/vehicle_usage/raw/destination_eu27_inputs.json` | `car_co2_kt` and `grid_intensity_gco2_per_kwh` per EU27 market, each with tier, reference year and derivation | Already held — reused rather than re-collected (`A-07`) |

### Processing

| Script | Reads | Writes | What it does |
|---|---|---|---|
| `script/auto/country_emissions/extract_eu27_snapshot.py` | the EU27 snapshot | `processed/country_emissions_eu27.csv` — 1,312 rows | Emits one long table with four series — `car_co2` (270 rows), `grid_intensity` (972), `power_co2` (35), `transport_ghg` (35) — each row carrying its unit, `source_id` and `source_file` |

Unit conversions are explicit in the script. The series are independent evidence and are never
derived from one another — the discipline that keeps `r_fleet` and `r_power` independent (`N-07`).
Markets beyond EU27 need their own scripts against `SRC-09` and `SRC-10`.

### Analysis

ST08 takes `series = car_co2` as the numerator of the base-year fleet intensity
`I_all_vehicles,c(0) = E_transport,c(Y0) / (Fleet_size,c(Y0) × D_c)`. ST09 takes
`series = grid_intensity` as `G_c(0)`, the starting point of the grid trajectory that drives BEV
and PHEV emissions. Join key: country (plus year for the reference-year check).

**Phases served.** PH1/2; PH4/2–3 (grid intensity is the power sector's own Layer 1 base).
**Owners.** `data-collector`, `developer`, `source-reconciliation-analyst` where inventory and
Ember disagree; review `tester` then `auditor`.
**Stop when.** Every importer has both series with a `source_id` and a stated reference year, or
no row at all (`N-02`).
**Repeat when.** An inventory or Ember vintage update; a market is added; a reconciliation finding
changes a base-year value.
**Backward move.** A base-year quotient far outside the peer range returns here and to ST05 before
ST08 may use it — flagged and tier-downgraded, never adjusted into plausibility.

---

## ST04 — `emission_targets` · NDC and sector targets

**Main goal.** Per importer: target-hierarchy level, base and target year, reduction, and the
derived annual rates `r_fleet` and `r_power` per scenario — what makes the benchmark dynamic.
Rules: [`emission_targets/method/method.md`](../../data/auto/emission_targets/method/method.md).

### Data gathering

| Source | Locator | What is fetched | Route |
|---|---|---|---|
| `SRC-13` UNFCCC NDC Registry | `https://unfccc.int/NDCREG` | Per market: base year, base-year level, target year, reduction, conditional or unconditional status, and whether any transport or power sub-target exists | Documents — **hand-read**. The June 2026 scan found no explicit transport or power sub-target in any priority market (challenges Ch1) |
| `SRC-14` Regulation (EU) 2019/631 as amended, plus Fit-for-55 trajectory | EUR-Lex | EU car CO2 fleet-standard trajectory, which outranks the NDC in the target hierarchy | Legal text — hand-read |
| `SRC-15` IEA World Energy Outlook 2024 | `https://www.iea.org/reports/world-energy-outlook-2024`; full report PDF held in Drive `Trade/References/` | STEPS and NZE transport and electricity sector pathways, for S1 and S3 | Hand extraction from the report |
| `SRC-16` IEA Global EV Outlook 2024 | `https://www.iea.org/reports/global-ev-outlook-2024`; PDF in Drive `Trade/References/` | Scenario-consistent EV penetration, for new-entrant intensity under Method A or C | Hand extraction |
| `SRC-20` Archived EU27 snapshot | as ST03 | Derived S1/S2/S3 `r_fleet` and `r_power` per EU27 market with the pro-rata derivation disclosed | Already held — reused (`A-07`) |

### Processing

| Script | Reads | Writes | What it does |
|---|---|---|---|
| `script/auto/emission_targets/derive_eu27_rates.py` | `raw/eu_climate_targets.csv`, `country_emissions_eu27.csv` | `processed/emission_targets_eu27.csv` — 162 rows (27 markets × 3 scenarios × 2 rates) | Derives `r_fleet` and `r_power` per market and scenario, each row recording `target_level` (`observed_trend` for S1, `ndc_prorata` for S2, `1p5c_prorata` for S3), base and target year, the derivation in words, and the `source_id` set |

The derivation `r = 1 − (E_target/E_base)^(1/Δy)` is implemented once, here, not re-derived per
country. Guideline §6.2's five checks belong on the row: vintage confirmed, sub-target or pro-rata,
conditional status, base year and level, target year and the post-target extrapolation rule — the
`derivation` column is where that record lives, and `math-reviewer` re-derives against it.

### Analysis

ST08 consumes `r_fleet` per country + scenario as the benchmark decline rate; ST09 consumes
`r_power` per country + scenario for the grid trajectory. `target_level` travels with every result
as the hierarchy disclosure, and flagged markets — no usable base-to-target arithmetic, or no
active NDC, which is the United States as of the June 2026 scan — are excluded from the S2 headline
and reported separately (`B-04`). Join key: country + scenario.

**Phases served.** PH1/2–3; PH2/2 (the empirical record of pro-rata dependence); PH4/2–3.
**Owners.** `climate-risk-modeller` (target reading and rate derivation), `data-collector`,
`developer`; `math-reviewer` re-derives every rate by hand from the primary document; then
`auditor`.
**Stop when.** Three scenarios per importer for both rates, each from a separately named source,
with target level, conditional status, pro-rata use and any extrapolation recorded — and every
rate independently re-derived.
**Repeat when.** A new NDC submission or revision; a sector-standard update; a new WEO vintage;
`B-04` resolves; PH2 adopts a sector-split correction.
**Backward move.** A market whose NDC yields no evaluable arithmetic returns to ST01 for a scope
decision and to ST12 for a rule — not to an analyst's improvised proxy.

---

## ST05 — `vehicle_usage` · how vehicles are used

**Main goal.** Annual distance `D_c`, operating lifetime T, and the passenger-car stock the fleet
benchmark is normalised against.
Rules: [`vehicle_usage/method/method.md`](../../data/auto/vehicle_usage/method/method.md).

### Data gathering

| Source | Locator | What is fetched | Route |
|---|---|---|---|
| `SRC-20` Archived EU27 destination inputs | `raw/destination_eu27_inputs.json` (from the archived pipeline) | Per EU27 market: VKT, operating life, car stock, fleet intensity base, grid intensity and S1/S2/S3 rates — each with tier, reference year and a derivation string | **Already held.** Reused with its tiers and derivations intact, not re-collected (`A-07`) |
| `SRC-21` FHWA highway statistics; BTS vehicle survival tables | `https://www.fhwa.dot.gov/policyinformation/statistics.cfm`; `https://www.bts.gov` | US VMT per vehicle and survival curves | Downloadable tables |
| `SRC-22` ABS Survey of Motor Vehicle Use (last edition 2020) plus BITRE | `https://www.abs.gov.au`; `https://www.bitre.gov.au` | Australian VKT per vehicle, fleet stock | Downloadable; the survey is discontinued, so the last edition is used with its vintage disclosed |
| `SRC-18` ICCT EU vehicle market statistics pocketbook 2024 | PDF in Drive `Trade/References/` | Cross-check on stock and market structure | Hand extraction |

### Processing

| Script | Reads | Writes | What it does |
|---|---|---|---|
| `script/auto/vehicle_usage/extract_eu27_eurostat.py` | the EU27 snapshot | `processed/vehicle_usage_eu27.csv` — 2,092 rows | Emits observations as a long table: `car_stock`, `car_traffic`, `car_traffic_fallback`, and the five `car_stock_age_*` bands, each with unit, `source_id` and `source_file` |

Nothing is averaged across markets here. Distance per car, its tier and the lifetime bracket are
**derived** downstream in ST08 and land in `destination_parameters_eu27.csv` with their derivation
string and warning attached — so the proxy is visible on the value that uses it. US and Australian
rows need their own scripts against `SRC-21` and `SRC-22`.

### Analysis

ST08 uses `car_stock × vkt` as the denominator of the base-year fleet intensity. ST09 uses `vkt`
to convert per-kilometre intensities into annual emissions, and `operating_life` as the lifetime
T that sets the summation horizon `t = 0 … T−1`, with the mandatory T ± 3 sensitivity (`A-04`).
`vkt_tier` is what makes `N-04` operable: more than half of the EU27 units currently rest on a
proxied distance (`A-08`), so first-pass results are directions with a stated coverage ratio
rather than magnitudes. Join key: country.

**Phases served.** PH1/2–3; PH2/3 (the Tier-C share the propagation rule must handle).
**Owners.** `data-collector`, `developer`, `data-scientist`; `math-reviewer` on tier assignment
and the T choice; then `auditor`.
**Stop when.** Every importer has distance, operating life and stock with a tier and a
`source_id`, or no row (`N-02`), and the Tier-C share per market is recorded.
**Repeat when.** A national statistics release; a tier upgrade; a change in T; a market is added.
**Backward move.** If a market's Tier-C share exceeds the suppression threshold PH2 sets, that
market moves to directional-only reporting — a logged decision, and it changes what ST14 may claim.

---

## ST06 — `vehicle_technology` · product parameters · *live*

**Main goal.** Layer 2 product parameters: certified tailpipe intensity, electric consumption,
real-world correction, PHEV utility factor, and the test cycle each came from.
Rules: [`vehicle_technology/method/method.md`](../../data/auto/vehicle_technology/method/method.md).

### Data gathering

| Source | Locator | What is fetched | Route |
|---|---|---|---|
| `SRC-01` EEA CO2 monitoring snapshots | same two files as ST02, in `sales/raw/` | Certified WLTP tailpipe CO2 and electric energy consumption per commercial name × powertrain — the primary EU technology source, already on the same rows as the volumes | Already held |
| `SRC-17` ICCT lab-to-road (2018) and real-world CO2 in Europe (January 2024) | `https://theicct.org`; both PDFs in Drive `Trade/References/` | Real-world correction factors by powertrain | **Hand extraction** from the primary documents — never from a summary or a search extract |
| `SRC-19` Transport and Environment PHEV report (2023) | `https://www.transportenvironment.org`; PDF in Drive `Trade/References/` | Real-world PHEV utility factors | Hand extraction |
| `SRC-23` EPA certification data | `https://www.fueleconomy.gov/feg/download.shtml` | US model-level certified values and test cycle | Downloadable |

### Processing

| Script | Reads | Writes | What it does |
|---|---|---|---|
| `script/auto/vehicle_technology/extract_eea_certified.py` | the two EEA snapshots | `processed/vehicle_technology_eea_2024.csv` — 1,286 rows | Aggregates certified values per company × destination × model × powertrain: `tailpipe_gco2_km` with the count of registrations behind it (`tailpipe_units`), `energy_wh_km` with its own count, `test_cycle = WLTP`, `source_id = eea_co2_monitoring_2024` |

The real-world correction lives in `method/real_world_correction.csv` — one factor per powertrain
with its derivation and `source_id` — and is applied **once**, arriving on each result row as
`real_world_factor` (`A-05`). No PHEV utility factor is sourced yet, so PHEV cells are withheld
rather than defaulted (`A-06`); the same holds for cells the registration dataset gives no
certified intensity for.

### Analysis

ST09 consumes, per company + model + powertrain: `tailpipe_gco2_km × rw_correction` for ICE and
non-plug-in HEV (fixed for all t); `energy_wh_km` against the grid trajectory for BEV;
and the utility-factor composite for PHEV. `test_cycle` blocks the silent mixing of cycles across
markets. A model with no sourced technology row contributes no result and its units are reported
as withheld (`N-02`). Join key into `sales`: company + model + powertrain — which is also how the
Kia and Hyundai IR tables acquire the powertrain they lack.

**Phases served.** PH1/2 and PH1/4; PH2/4 (the utility-factor evidence base).
**Owners.** `data-collector`, `developer`, `data-scientist` (correction application);
`math-reviewer` on double-correction and cycle-mixing checks; then `auditor`.
**Stop when.** Every model in the sales table has a technology row with its test cycle and
correction source, or is in the withheld list with its unit count. No row carries two corrections.
No PHEV row carries an unsourced utility factor.
**Repeat when.** An ICCT correction vintage update; a utility-factor study release; a new model or
market; a discovered double correction or mixed cycle.
**Backward move.** A model whose certified values exist only on an incompatible cycle with no
sourced conversion is withheld and returns to ST02's coverage count — never absorbed into a market
average.
