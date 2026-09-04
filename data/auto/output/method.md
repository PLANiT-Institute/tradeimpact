# output — model results (research process steps 3–5)

Written only by `script/auto/model/`. Every file is regenerated from the processed datasets;
nothing here is edited by hand. Two markets are in scope — **EU27** (2024 registrations) and the
**United States** (2025/2026 exporter sales) — for Hyundai and Kia. Every result table carries a
`market` column and the markets are never summed together: they rest on different sales bases,
different test cycles and different national benchmarks.

| file | step | script | grain |
|---|---|---|---|
| `cohorts.csv` | 3a | `build_cohorts.py` | market × company × destination × model × powertrain × cohort_year: units, basis, period, certified `tailpipe_gco2_km` / `energy_wh_km`, `test_cycle`, `technology_source`, `sales_source_file`, `powertrain_rule`, `coverage_note`, `variant` |
| `cohorts_withheld.csv` | 3a | `build_cohorts.py` | volumes that cannot be joined to a product parameter and why (unpriceable powertrain, no certified value, no US model-map row, out-of-scope brand, no EPA row) |
| `destination_parameters_eu27.csv` | 3 | `build_reference.py` | importer market: distance (km/yr, tier, band), car stock, car CO2, fleet intensity base (gCO2/km, tier), grid intensity (gCO2/kWh), mean car age, operating lifetime (central/low/high), excluded scenarios, warnings, source ids |
| `destination_parameters_us.csv` | 3 | `build_reference_us.py` | the same columns for the US market |
| `reference_trajectories_eu27.csv` | 3 | `build_reference.py` | market × country × scenario × t: `e_ref_kgco2_per_vehicle` (benchmark per vehicle-year), `grid_kgco2_per_kwh` |
| `reference_trajectories_us.csv` | 3 | `build_reference_us.py` | the same columns for the US market (S1 and S3 only — see *United States* below) |
| `ti_by_model.csv` | 4 | `build_ti.py` | market × company × destination × model × powertrain × scenario: units, lifetime, distance + tier, test cycle, real-world factor, year-0 product and benchmark emissions, `ti_per_vehicle_kgco2e`, `ti_tco2e` |
| `ti_annual_by_model.csv` | 4 | `build_ti.py` | market × company × destination × model × powertrain × scenario × year: benchmark and product emissions per vehicle, the annual gap, and the cell's TI flow that year (tCO2e) — the year-by-year view at any aggregation level |
| `ti_annual.csv` | 4 | `build_ti.py` | market × company × scenario × t: annual TI flow (tCO2e) and surviving vehicles |
| `ti_withheld.csv` | 4 | `build_ti.py` | units carrying no result and why — the step-3a rows plus the markets whose benchmark is withheld |
| `ti_exclusions.csv` | 4 | `build_ti.py` | market × company × scenario that the market publishes no benchmark for, with the units affected and the sourced reason |
| `ti_crossover.csv` | 4b | `build_sensitivity.py` | market × company × destination × model × powertrain × scenario: closed-form crossover year (years after sale and calendar year) or the reason there is none |
| `ti_sensitivity.csv` | 4b | `build_sensitivity.py` | company × market × scenario × dimension (lifetime ±3 y, real-world factor low/high, proxied-distance quartiles, powertrain mix) × variant: cohort total |
| `ti_country.csv` | 5 | `aggregate_country.py` | company × market × destination × scenario: units, `ti_tco2e`, per-vehicle, direction |
| `ti_powertrain.csv` | 5 | `aggregate_country.py` | company × market × powertrain × scenario |
| `ti_company.csv` | 5 | `aggregate_country.py` | company × market × scenario: `status` (reported / excluded), covered/withheld units, total, per-vehicle, direction, decomposition identity check, exclusion reason |
| `ti_coverage.csv` | 5c | `build_coverage.py` | company × destination (every destination in the sales files, worldwide) × cohort year × basis: units, priced units, withheld units, status (`priced`, `withheld`, `no_benchmark`, `region_unpriced`, `destination_unknown`), market — the coverage picture a reader filters countries from |
| `ti_data_quality.csv` | 5b | `build_data_quality.py` | company × market: analysis level, benchmark method, sales basis, test cycles, covered/withheld units, tier-C unit share and the `directional_only` flag (guideline §5.3, threshold 50 %), central lifetime, scenarios reported and excluded, markets by distance tier, withheld reasons, coverage notes, warnings |

`cohorts.csv` carries a `variant` column. `central` is the published cohort; every other value
is a sensitivity variant of the same cell (currently `all_hev`, see *United States*). Only
`variant = central` rows are summed into a result — the variants exist so the sensitivity step
reuses this join instead of repeating it.

Sign convention: positive TI = the product emits less than the destination's committed
benchmark over its lifetime (contribution); negative = lock-in liability. Unit: tCO2e over
the operating lifetime, per-vehicle values in kgCO2e.

## Verification

**Tests** (`tests/test_model.py`, run with `.venv/bin/python -m pytest`): every ICE/HEV cell
satisfies the closed-form geometric-series sum from its own published year-0 values; the
annual flow summed over years equals the cell totals; company totals equal the country and
powertrain sums; processed sales totals equal the snapshot totals; covered + withheld equals
the source volume in each market (EU27 registrations, US exporter sales); the real-world factor
on every cell matches the (test cycle, powertrain) lookup; every excluded scenario appears in
`ti_exclusions.csv` and as an `excluded` row in `ti_company.csv`; each sensitivity dimension's
central variant reproduces the published cohort total.

**Independent re-derivation (2026-09-04).** A reviewer re-derived the Honda EU27 cohort from
the processed inputs with code written from the whitepaper before reading the scripts. Fed
the pipeline's destination parameters, the independent engine reproduced all 621 Honda cells
to 6 × 10⁻⁷ and the cohort totals to 3 × 10⁻⁹ — the TI equations, `t = 0..T−1` convention,
unit chain and sign are implemented as documented. The review found three input-side defects,
all fixed the same day:

1. Distance per car divided the latest traffic observation by the latest *stock*
   observation, which for LT, BE, IE and EE were different years. Now the stock of the traffic
   year is used. LT moved +20.9 % (10,110 → 12,224 km/yr), BE +5.2 %, IE +5.4 %, EE +0.4 %,
   and the EU-average proxy the 13 tier-C markets use +0.6 %.
2. The real-world sensitivity never used the documented diesel end (1.171); the low variant
   moved only HEV. It now applies the documented range 1.171–1.211 to both ICE and HEV.
3. The BEV crossover label read "before sale year" for cells that in fact never cross
   because the grid decarbonises faster than the fleet benchmark; the two cases are now named.

**Relation to the archived published result** (`archive/data/published/lifetime_results.json`).
Before fix 1 the pipeline reproduced the archived Toyota and Hyundai totals to 2 × 10⁻⁷ (the
archived run carried the same year mismatch). After it, totals are 1–13 % more negative:
Toyota S1 −1.40 → −1.59 MtCO₂e, S2 −5.96 → −6.15, S3 −13.95 → −14.14; Hyundai S1 −1.49 →
−1.57, S2 −3.72 → −3.80, S3 −7.78 → −7.86. The archive remains the regression baseline for
the *engine* (the pipeline reproduces it exactly when fed the archived parameters); it is no
longer the baseline for the *inputs*.

Two further deliberate deviations from the archive: the proxied-distance sensitivity holds
the benchmark per vehicle fixed (distance cancels in CO2 per car) and scales only the product
side, so it is narrower than the archived band; and the real-world range is applied as a
replacement of the central factor, never on top of it.

## Methodological decisions (2026-09-04, project lead: "most plausible")

1. **Luxembourg** — its fleet intensity (391 gCO2/km) fails the 80–320 plausibility band
   because fuel sold in LU is burned by cars registered elsewhere. The market is withheld
   from every company result with its unit count (`ti_withheld.csv`, reason
   "destination benchmark withheld"), the same treatment as PHEV/FCEV. The sensitivity step
   applies the same rule, so each dimension's central variant now equals the published total
   (before the two-market generalisation the sensitivity still priced Luxembourg and its
   central variant sat about 1 % above the headline).
2. **Segment intensity ratio** — set to 1.0 (all-passenger-car fleet average) and disclosed;
   no sourced segment split exists for the EU27 in-use fleet. For crossover-heavy portfolios
   this understates the benchmark and is therefore conservative for the exporter.
3. **S2 grid when the pro-rata target is already met** — committed policy is never read as
   less ambitious than the current trajectory: S2 power is floored at each market's observed
   S1 grid trend (`target_level = ndc_prorata_s1_floor`) instead of being held flat. BEV S2
   is therefore no longer below BEV S1.
4. **Age-band year** — the mean-age partition is taken at or before the cohort year, the
   same cap as stock, CO2 and grid; the "one year ahead" exception is gone.
5. **Exporters in scope** — Hyundai and Kia only for now (`companies.csv`); the Toyota and
   Honda snapshots stay pinned and re-enter with one flag change.

Two markets (BG, PL) show a rising observed per-car CO2 trend, so their S1 benchmark grows;
this is flagged `OBSERVED_INCREASE` in `emission_targets_eu27.csv` and left as observed.

## United States

The US market is built from exporter investor-relations sales, not from a registration
authority, so its coverage caveats are part of the result and travel on every row
(`coverage_note` in `cohorts.csv` and `cohorts_withheld.csv`, pooled into `coverage_notes` in
`ti_data_quality.csv`).

**Cohort caveats.**

1. **Kia US is a partial year.** `sales_kia_ir_2026.csv` is the Jan–Jun 2026 retail-sales
   release; the cohort is six months of sales, not a calendar year, and must never be compared
   with a full-year EU27 cohort at face value.
2. **Hyundai US is US-built cars only.** `sales_hyundai_plant_2025.csv` is production-side
   plant sales; the Domestic segment of the US plants is what lands in the US market. Vehicles
   sold in the US but built in Korea or elsewhere are not in the source and are therefore not
   in the cohort.
3. **Origin is pooled.** The Kia release splits one destination across production origins
   (KR, MX, US); Level 1 does not establish production origin, so the volumes are summed into
   one cohort row per model.
4. **Powertrain is joined, not reported.** Neither release states the powertrain.
   `sales/method/us_model_map.csv` resolves each commercial name to an EPA `base_model` and a
   powertrain. Where the name fixes the powertrain the rule is `explicit`; where the same name
   covers several powertrains and the release does not split them the rule is
   `mixed_central_ice` — the central case prices those units on the rule's powertrain and the
   `powertrain_mix` sensitivity reprices every one of them as a hybrid, which is the honest
   upper bound of the cohort. Genesis-brand rows are `out_of_scope` and withheld with their
   units.
5. **Technology is EPA label data.** `vehicle_technology_us_epa.csv` values are trim-weighted
   means over the EPA model names of the base model, taken from the latest model year at or
   before the cohort year. EPA label values are already 5-cycle adjusted toward real-world use,
   so the real-world correction for `test_cycle = EPA` is 1.0 at the central value and at both
   ends of the band — the real-world sensitivity therefore does not move the US result.
6. **Parameters lag the cohort.** The sale years are 2025 (Hyundai) and 2026 (Kia); the
   destination parameters are the latest observations at or before 2024 (stock, traffic and
   inventory 2023; grid 2024). Trajectories are indexed on `t` = years after sale, not on
   calendar year, so the lag affects the level of the benchmark, not its alignment.

**Benchmark.** Distance and stock are all light-duty vehicles — FHWA VM-1 short- plus
long-wheelbase — because the inventory numerator (`ldv_co2`: EPA passenger cars plus
light-duty trucks) covers the same population. FHWA partitions by wheelbase, not by body type,
so distance is tier B, not tier A. The operating life is the NHTSA expected lifetime (12.76 →
13 years), bracketed ±3 years to match the lifetime sensitivity, and is tier C: the survival
schedule behind it was fitted to 1977–2002 registrations, not to the current fleet.

**S2 is excluded for the US.** `emission_targets_us.csv` carries S2 with an empty rate and
`target_level = flag_no_ndc`: the United States notified withdrawal from the Paris Agreement on
2025-01-27, so no NDC is in force over the cohort's lifetime and there is no committed-policy
benchmark to compare against. No S2 trajectory is built. The exclusion is never a silent gap —
it is published as `scenarios_excluded` on `destination_parameters_us.csv`, as a row per
company in `ti_exclusions.csv` with the units affected, as a `status = excluded` row in
`ti_company.csv`, and in the `scenarios_excluded` column of `ti_data_quality.csv`. A test
asserts all four.

**Australia** has processed inputs on disk but is deliberately not built yet.

## Run order

`script/auto/run_all.py` runs everything and exits non-zero at the first failure: extraction,
the rate derivations (`derive_eu27_rates.py`, `derive_us_rates.py`, `derive_au_rates.py`), then
the model in this order —

1. `build_cohorts.py` — sales × technology per market → `cohorts.csv`, `cohorts_withheld.csv`
2. `build_reference.py` — EU27 destination parameters and trajectories
3. `build_reference_us.py` — US destination parameters and trajectories
4. `build_ti.py` — per-cell lifetime TI, annual flow, withheld and excluded tables
5. `build_sensitivity.py` — crossover years and the four sensitivity dimensions
6. `aggregate_country.py` — country, powertrain and company × market roll-ups
7. `build_data_quality.py` — the §5.3 declaration per company × market
8. `build_database.py`, `build_dashboard.py`

then ruff and pytest. The model scripts can also be run individually in that order. Steps 2 and
3 are independent of each other and of step 1; steps 4 onward read every
`destination_parameters_*.csv` and `reference_trajectories_*.csv` present, so a new market is
one new `build_reference_<market>.py` plus its branch in `build_cohorts.py` — no change to the
downstream scripts. Shared field lists and loaders live in `script/auto/model/model_io.py`, so
the per-market reference builders cannot drift apart on schema.

`build_database.py` writes `data/auto/tradeimpact_auto.sqlite` — every raw table, lookup,
processed dataset and output table, the source registry, raw-file provenance, a `tables`
manifest (dataset, stage, source path, rows, hash) and a `columns` dictionary (type, non-null,
distinct, example). `build_dashboard.py` writes `data/auto/dashboard.html`, a reader for that
database carrying no data of its own (about 55 KB): it fetches `tradeimpact_auto.sqlite` from
its own directory and reads the manifest, the dictionary, the source registry and the raw-file
provenance out of it with SQL. Views: lineage per data type (raw → method → processed → output
with source links), results and results by year, a pivot over any table, a browse view and a
read-only SQL console. Serve the directory with `.venv/bin/python
script/auto/serve_dashboard.py` and open <http://127.0.0.1:8765/dashboard.html>; opened
straight from disk the browser blocks the sibling read, so the page then offers a file picker
and a drag-and-drop zone for the database instead. The network is needed only for the sql.js
engine (pinned on cdnjs).
