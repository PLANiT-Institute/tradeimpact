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
| `destination_parameters_kr.csv` | 3 | `build_reference_kr.py` | the same columns for the Korean market |
| `reference_trajectories_eu27.csv` | 3 | `build_reference.py` | market × country × scenario × t: `e_ref_kgco2_per_vehicle` (benchmark per vehicle-year), `grid_kgco2_per_kwh` |
| `reference_trajectories_us.csv` | 3 | `build_reference_us.py` | the same columns for the US market (S1 and S3 only — see *United States* below) |
| `reference_trajectories_kr.csv` | 3 | `build_reference_kr.py` | the same columns for the Korean market (S1, S2, S3) |
| `ti_by_model.csv` | 4 | `build_ti.py` | market × company × destination × model × powertrain × scenario: units, lifetime, distance + tier, test cycle, real-world factor, year-0 product and benchmark emissions, `ti_per_vehicle_kgco2e`, `ti_tco2e`, and the whitepaper §5.2 tier declaration: `fleet_intensity_tier`, `grid_tier`, `lifetime_tier`, `rate_tier`, `layer1_tier` (benchmark), `technology_tier`, `powertrain_tier`, `layer2_tier` (product), `tier` (worst of both) |
| `ti_annual_by_model.csv` | 4 | `build_ti.py` | market × company × destination × model × powertrain × scenario × year: benchmark and product emissions per vehicle, the annual gap, and the cell's TI flow that year (tCO2e) — the year-by-year view at any aggregation level |
| `ti_annual.csv` | 4 | `build_ti.py` | market × company × cohort_year × scenario × t: annual TI flow (tCO2e) and surviving vehicles |
| `ti_withheld.csv` | 4 | `build_ti.py` | units carrying no result and why — the step-3a rows plus the markets whose benchmark is withheld |
| `ti_exclusions.csv` | 4 | `build_ti.py` | market × company × scenario that the market publishes no benchmark for, with the units affected and the sourced reason |
| `ti_crossover.csv` | 4b | `build_sensitivity.py` | market × company × destination × model × powertrain × scenario: closed-form crossover year (years after sale and calendar year) or the reason there is none |
| `ti_sensitivity.csv` | 4b | `build_sensitivity.py` | company × market × scenario × dimension (lifetime ±3 y, real-world factor low/high, proxied-distance quartiles, powertrain mix) × variant: cohort total |
| `ti_country.csv` | 5 | `aggregate_country.py` | company × market × cohort_year × destination × scenario: units, `ti_tco2e`, per-vehicle, direction |
| `ti_powertrain.csv` | 5 | `aggregate_country.py` | company × market × cohort_year × powertrain × scenario |
| `ti_company.csv` | 5 | `aggregate_country.py` | company × market × cohort_year × scenario: `status` (reported / excluded), covered/withheld units, total, per-vehicle, direction, decomposition identity check, exclusion reason |
| `ti_source_reconciliation.csv` | 5d | `build_reconciliation.py` | company × destination × cohort year × source file: units, basis and which side of the market it counts, whether the cohort was built from it, the brands a group figure covers, and the like-for-like spread against the file used |
| `ti_coverage.csv` | 5c | `build_coverage.py` | company × destination (every destination in the market-side sales files, worldwide) × cohort year × basis: `destination_group` (EU27, US, the company's home country KR or JP, IN, others), `home_country`, units, priced units, withheld units, status (`priced`, `withheld`, `no_benchmark`, `plant_side_only`, `region_unpriced`, `destination_unknown`), market — the coverage picture a reader filters countries from |
| `ti_data_quality.csv` | 5b | `build_data_quality.py` | company × market × cohort year, including `countries` (the destination codes covered), `countries_covered`, `countries_withheld` and `covered_share` (the sales coverage): analysis level, benchmark method, sales basis, test cycles, covered/withheld units, tier-C unit share and the `directional_only` flag (guideline §5.3, threshold 50 %), central lifetime, scenarios reported and excluded, markets by distance tier, withheld reasons, coverage notes, warnings |

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
5. **Companies in scope** — Hyundai, Kia, Toyota and Nissan (`companies.csv`). "The second
   Japanese maker" has three different answers and the lead chose on 2026-09-04: Honda is second
   by worldwide sales (3.52 M in 2025 against Suzuki 3.30 M and Nissan 3.20 M), Suzuki is second
   by worldwide production and by Japanese sales including kei cars, and Nissan is second by
   presence in the markets this project prices (EU27 198,048 registrations against Honda's
   40,270, and a published US table by model that Honda does not offer). Nissan is in scope on
   that last basis. Honda, Suzuki, Mazda, Mitsubishi and Subaru have pinned EEA snapshots and
   enter on one flag. Lexus is held out of Toyota exactly as Genesis is held out of Hyundai: a
   separate make in the registration data, counted and excluded rather than folded in. Genesis is listed as its own
   company with `in_scope = no`, so Genesis nameplates inside Hyundai's IR files (US and Korea)
   are counted and excluded, never folded into the Hyundai brand.
6. **A-US-PT: powertrain split of US nameplates** — the company US releases publish one row per
   nameplate (Tucson, Santa Fe, Sportage, Sorento, Niro, Elantra, Sonata, Kona, Carnival) and
   do not split ICE, HEV and PHEV. The units are divided with the EPA Automotive Trends
   model-year-2024 production-for-US-sale shares of the same nameplate
   (`vehicle_technology/processed/epa_trends_powertrain_share_my2024.csv`, rule
   `epa_share_my2024` in `us_model_map.csv`, largest-remainder rounding so the parts sum to the
   published units). Two caveats travel with it: production volume is not calendar-year sales
   (the brand totals differ by −0.2 % for Kia and +0.6 % for Hyundai against the MY2024 volumes),
   and MY2024 shares are applied to the 2024, 2025 and 2026 cohorts alike, so a hybrid ramp after
   MY2024 (Carnival Hybrid, Palisade Hybrid) is not in the central case. The `powertrain_mix`
   sensitivity keeps the all-hybrid bound for every split nameplate. Where a release separates
   the electric variant (Kia IR: Niro EV) only the remaining shares are applied.
7. **Cohort years are never pooled.** Every aggregate (`ti_annual`, `ti_country`,
   `ti_powertrain`, `ti_company`, `ti_sensitivity`, `ti_data_quality`, `ti_exclusions`) carries
   `cohort_year`; a 2024 full year, a 2025 full year and a 2026 half year are separate rows.

Two markets (BG, PL) show a rising observed per-car CO2 trend, so their S1 benchmark grows;
this is flagged `OBSERVED_INCREASE` in `emission_targets_eu27.csv` and left as observed.

## United States

The US market is built from exporter investor-relations sales, not from a registration
authority, so its coverage caveats are part of the result and travel on every row
(`coverage_note` in `cohorts.csv` and `cohorts_withheld.csv`, pooled into `coverage_notes` in
`ti_data_quality.csv`).

**Cohort caveats.**

1. **Three market-side sources, three cohort years.** Hyundai: the IR "US Retail Sales by
   Model" workbooks for 2024 and 2025 (`sales_hyundai_us.csv`; imports and US-built together;
   the sheet is labelled retail but equals the brand total including fleet, proven against the
   HMA and Genesis releases). Kia: the Kia America December exports for 2024 and 2025
   (`sales_kia_us.csv`, brand total) and the Kia Corporation IR release for Jan–Jun 2026
   (`sales_kia_ir_2026.csv`, retail, a half year that must never be read against a full-year
   cohort at face value). The plant-side file `sales_hyundai_plant_2025.csv` is no longer a US
   cohort source; it remains the only source for Hyundai's other plant countries.
2. **Genesis is counted and excluded.** Genesis nameplates in the Hyundai sheets carry
   `company = genesis`, which `companies.csv` puts out of scope (75,003 units in 2024 and
   82,331 in 2025); the IONIQ 5 Robo Taxi rows (49 and 16 units) are `out_of_scope` fleet
   vehicles.
3. **Origin is pooled.** The Kia IR release splits one destination across production origins
   (KR, MX, US); Level 1 does not establish production origin, so the volumes are summed into
   one cohort row per model.
4. **Powertrain is joined, not reported.** The releases state the powertrain only where the
   nameplate carries it (IONIQ 5/6/9, EV6, EV9, Nexo). `sales/method/us_model_map.csv`
   resolves every published name to an EPA `base_model` and either fixes the powertrain
   (`explicit`) or splits the nameplate with the EPA Automotive Trends MY2024 production shares
   (`epa_share_my2024`, decision 6 above); the PHEV part of a split is withheld like every
   PHEV, and the `powertrain_mix` sensitivity reprices every split nameplate as all-hybrid.
   Rio (1,917 units, 2024) and IONIQ 9 (5,189 units, 2025) are withheld because no EPA
   technology row exists at or before their cohort year.
5. **Technology is EPA label data.** `vehicle_technology_us_epa.csv` values are trim-weighted
   means over the EPA model names of the base model, taken from the latest model year at or
   before the cohort year. EPA label values are already 5-cycle adjusted toward real-world use,
   so the real-world correction for `test_cycle = EPA` is 1.0 at the central value and at both
   ends of the band — the real-world sensitivity therefore does not move the US result.
6. **Parameters lag the cohort.** The sale years are 2024, 2025 and 2026; the destination
   parameters are the latest observations at or before 2024 (stock, traffic and inventory
   2023; grid 2024). Trajectories are indexed on `t` = years after sale, not on
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

## Korea

Korea is the home market of both companies in scope and the first destination priced on free,
keyless, machine-readable Korean official statistics (all data.go.kr and portal files carry
licence 제한 없음).

**Cohorts.** Hyundai: the IR "Unit Sales by Model" Korea domestic block for 2024 and 2025
(`sales_hyundai_kr.csv`, `domestic_sales`), with the powertrain read from the trim code
(CN7 HEV, SX2 EV, ...), so every Hyundai unit is priced on its stated powertrain; Genesis
nameplates carry `company = genesis` and are out of scope. Kia: the IR Jan–Jun 2026 release
(`sales_kia_ir_2026.csv`, `retail_sales`, a half year); its labels do not split ICE from HEV, so
Carnival, K5, K8, Seltos, Sorento and Sportage are priced as ICE centrally with an all-HEV bound
(`powertrain_rule = kr_unsplit_central_ice`, sensitivity `powertrain_mix`). Bongo, Bus, Tasman
and military vehicles are outside the 승용 registration class and are withheld as out of scope
(19,790 units); Nexo is withheld like every FCEV.

**Technology.** KEA label fuel economy per trim (5-cycle corrected, `test_cycle = KR_5CYCLE`,
real-world factor 1.0), converted to gCO2/km with EPA fuel carbon factors and to Wh/km for BEVs;
trim means per model × powertrain (`vehicle_technology_kr_kea.csv`).

**Benchmark.** Distance 11,963 km/yr (tier A: KOTSA inspection odometers over the MOLIT 승용
stock, 2024). Fleet intensity 203 gCO2/km (2023, tier C: GIR road CO2 × the KOTSA passenger-car
share, see country_emissions/method). Grid 415.5 gCO2/kWh (Ember 2024). Mean age 7.3 years from
the MOLIT model-year distribution (tier C, biased low) gives an operating life of 11 years
[10, 15] under the EU27 rule (1.5 × mean age, clamped). S1: GIR road CO2 nearly flat
(−0.2 %/yr) and grid −2.2 %/yr; S2: Basic Plan transport path 2023–2030 (−5.9 %/yr) and power
2018–2030 (−5.0 %/yr); S3: 2050 scenarios (transport A안 −10.5 %/yr, power B안 −7.7 %/yr).

**Reading the result.** Because the observed Korean fleet trend is flat, S1 is a contribution
for both companies (their label-basis product intensities sit below the 203 gCO2/km fleet
average), while S2 and S3 turn every cohort into a liability: the committed and 1.5 °C paths
decline faster than the products' fixed intensities. The lifetime sensitivity moves the Korean
S1 by about ±30 % because the operating life is short and uncertain.

## India (assessed 2026-09-04, not built)

The lead's scope puts India in its own coverage group where data allow. The free-source scout
found that only the grid (CEA CO2 baseline database, Ember) and the car stock to 2020 (MoRTH Road
Transport Year Book, data.gov.in) are sourced; passenger-car CO2 exists only as whole-road-transport
totals at 2016, 2020 and 2022 with no car split (the BTR1 common reporting tables would add 2005
and 2020–2022 but sit behind a hand download), there is no distance survey, no vehicle-age table,
no certified technology by model (BEE CAFE reports manufacturer averages on the MIDC cycle), and
the NDC is an intensity target, so S2 would be a FLAG. More than half of the inputs would be
proxies, which under guideline §5.3 makes any India figure a direction only. Model-level sales
are not free either: Hyundai Motor India and Kia India publish company totals, SIAM sells the
model data, and Vahan's public report hides the model. India therefore stays `no_benchmark` in
`ti_coverage.csv` with this reasoning in `sales/method/destination_notes.csv`; Hyundai's Indian
plant-side domestic sales (571,878 in 2025) and Kia's Indian retail (156,523 in Jan–Jun 2026)
are counted, not priced. What would change the verdict: the BTR1 CRT workbook (hand fetch), the
2020-21/2021-22 Year Book (hand fetch) and a Vahan maker-level active-stock export.

## Toyota and Nissan (EU27, added 2026-09-04)

Both were priced from the EEA snapshots already on disk, so nothing new was acquired: the
registration dataset carries the volumes and the certified values on the same rows. Toyota
covers 777,277 units (96.8 %) and Nissan 197,588 (99.8 %, the highest coverage of the four).

**Both are `directional_only`.** Their tier-C unit share is 53.6 % and 54.6 %, above the
guideline §5.3 threshold of 50 %, because their EU27 volumes sit disproportionately in member
states whose distance is the EU-average proxy. Hyundai (48.5 %) and Kia (48.2 %) fall just under
the same threshold. Toyota and Nissan figures are therefore directions, not magnitudes, until
those member states publish vehicle-kilometres.

**A hybrid share does not tell you the outcome; the certified intensity behind it does.** Toyota
is 78.5 % hybrid and Nissan 74.0 %, yet Toyota's hybrid sits at −7,124 kgCO₂e per vehicle and
Nissan's at −13,509. The reason is the cars underneath: Toyota's hybrid fleet averages
105.7 gCO₂/km (Yaris 90.9, Corolla 106.2, Yaris Cross 104.4) while Nissan's averages
132.0 (Qashqai 134.5, X-Trail 143.8). Nissan's European hybrid is a larger crossover, so the
same powertrain label carries a quarter more carbon per kilometre.

## United States, Toyota and Nissan (added 2026-09-04)

Both companies publish a US sales table by model, so both are priced on their own release rather
than on an investor summary.

**Toyota** prints models by division and, in a second table, model by powertrain. The two are an
overlay, not two sets of rows: the Camry appears in both because every Camry sold is a hybrid, so
combustion volume is the model total minus its electrified rows and never a sum of the tables.
The extractor enforces that, checks each division's models against the published division total,
and keeps the small difference the release itself leaves unprinted (6 units in 2025, 15 in 2024)
as its own row rather than dropping it. Lexus is held out as its own company, exactly as Genesis
is held out of Hyundai. Result: 2,111,810 covered units in 2025 (98.3 %), S1 +8.07 MtCO₂e,
S3 −30.50; 2024 +5.53 and −29.92. The large current-path contribution is the same segment-ratio
artefact described above, amplified: Toyota's cohort is hybrid-heavy and the US benchmark is the
all-light-duty fleet including pickups.

**Nissan** prints models but no powertrain. It needs no assumption anyway: its US line-up in
these years is combustion except the LEAF and the Ariya, which the EPA certification data
confirms, so every nameplate is priced explicitly. Infiniti is held out as its own company.
Result: 873,293 covered units in 2025 (100.0 %), S1 +1.36 MtCO₂e, S3 −14.46. Nissan also
publishes the split of its US volumes into North American production and imports
(`us_release_origin_split.csv`, 760,213 against 113,094 in 2025), which no other company in
scope discloses.

## A company against its own second publication

`ti_source_reconciliation.csv` puts every source held for the same company, destination and year
side by side, and compares a group figure against the same set of brands rather than against a
narrower cohort. All five overlaps agree exactly:

| Company | Year | Cohort source | Second publication | Covers | Spread |
|---|---|---|---|---|---|
| Toyota | 2025 | 2,147,811 (Toyota) + 370,260 (Lexus) | 2,518,071 group workbook | Toyota, Lexus | 0.0 % |
| Nissan | 2025 | 873,307 (Nissan) + 52,846 (Infiniti) | 926,153 group release | Nissan, Infiniti | 0.0 % |
| Hyundai | 2024 | 836,802 investor sheet | 836,802 US subsidiary release | Hyundai | 0.0 % |
| Genesis | 2024 | 75,003 investor sheet | 75,003 US subsidiary release | Genesis | 0.0 % |
| Kia | 2024 | 796,488 sales workbook | 796,488 press release | Kia | 0.0 % |

So the Korean makers stand on the same class of source as the Japanese ones: a market-side count
the company itself published. Kia's is its US newsroom workbook, and Hyundai's is its
investor-relations sheet because the US subsidiary's release index is script-rendered and offers
no file. The reconciliation shows the choice costs nothing: the investor sheet and the subsidiary
release carry the same number. What differs between publications is the brand boundary, not the
data, and that is why the table records which brands each figure covers.

## Data-quality tiers (whitepaper §5.1, every value flagged)

Three tiers, defined in `data/auto/registry/tiers.csv` with the whitepaper wording and the
operational rule used here: **A** directly sourced (the authoritative publisher of that quantity
for that country, on the population the model uses); **B** estimated or derived (authoritative
sources for the country plus a documented step: unit or fuel-factor conversion, pro-rata of a
sector target, split by production shares, a close but not identical population, a rounding
rule); **C** proxy (another population, market, year or average; a share whose level disagrees
with the national one; an old survival schedule; an ICE-central assumption; a world pathway).

Where the flags live. (1) Every row of every processed input table (country_emissions_*,
vehicle_usage_*, emission_targets_*, vehicle_technology_*, sales_*, trade_flows) carries `tier`
and `tier_reason` in the database, assigned when the database is built from the rules in
`data/auto/registry/value_tiers.csv` (one rule per table pattern, column and value pattern; the
worst matching tier wins and every matching reason is kept). (2) The destination parameters carry
`vkt_tier`, `fleet_intensity_tier`, `grid_tier`, `mean_car_age_tier` and `lifetime_tier`.
(3) Every result cell in `ti_by_model.csv` carries the Layer 1 tier (worst of distance, fleet
intensity, grid, lifetime and scenario-rate tiers), the Layer 2 tier (worst of the certified-value
tier by test cycle and the powertrain-attribution tier by rule) and `tier`, the worst of both;
the year-by-year cells carry `tier`. (4) `ti_data_quality.csv` counts covered units by tier per
company, market and cohort year. A test asserts that every cell and every input row is flagged.

Today's picture: every EU27 cell is B or C (B from the mean-age lifetime rule, C where the
distance is the EU-average proxy), every US cell is C (the NHTSA lifetime schedule) and every
Korean cell is C (the fleet-intensity share and the biased mean age). The per-input columns say
which input is responsible; the single `tier` says how far the cell is from fully sourced.

## Reading the dashboard

`data/auto/database/dashboard.html` is a plain HTML file with no data of its own; it reads
`tradeimpact_auto.sqlite`. One command connects it and keeps it connected:

```bash
.venv/bin/python script/auto/serve_dashboard.py --open
```

That serves `data/auto` on 127.0.0.1:8765 (the next free port if one is busy) and opens the
page already loaded. It also makes the file itself work: a `dashboard.html` opened by
double-click has the opaque origin `null`, so the browser forbids it from reading the database
beside it, but the server answers that one origin (`Access-Control-Allow-Origin: null`, no
other site), and the page tries the server for two seconds before offering its file reader. So
with the server running, double-clicking the HTML file also opens with data.

Without any server the page offers its reader and one click on `tradeimpact_auto.sqlite` gives
the whole dashboard, map included: the world geometry is a row in the database
(`map_geometry`), not a second file, so nothing else has to be fetched.

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

`build_database.py` writes `data/auto/database/tradeimpact_auto.sqlite` — every raw table, lookup,
processed dataset and output table, the source registry, raw-file provenance, a `tables`
manifest (dataset, stage, source path, rows, hash) and a `columns` dictionary (type, non-null,
distinct, example). `build_dashboard.py` writes `data/auto/database/dashboard.html`, a reader for that
database carrying no data of its own (about 55 KB): it fetches `tradeimpact_auto.sqlite` from
its own directory and reads the manifest, the dictionary, the source registry and the raw-file
provenance out of it with SQL. Views: lineage per data type (raw → method → processed → output
with source links), results and results by year, a pivot over any table, a browse view and a
read-only SQL console. Serve the directory with `.venv/bin/python
script/auto/serve_dashboard.py` and open <http://127.0.0.1:8765/dashboard.html>; opened
straight from disk the browser blocks the sibling read, so the page then offers a file picker
and a drag-and-drop zone for the database instead. The network is needed only for the sql.js
engine (pinned on cdnjs).
