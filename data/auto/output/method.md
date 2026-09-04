# output — model results (research process steps 3–5)

Written only by `script/auto/model/`. Every file is regenerated from the processed datasets;
nothing here is edited by hand. Four markets are in scope — **EU27** (2024 registrations), the
**United States**, **Japan** and **Korea** — for Hyundai, Kia, Toyota and Nissan. Every result
table carries a `market` column and the markets are never summed together: they rest on
different sales bases, different test cycles and different national benchmarks.

| file | step | script | grain |
|---|---|---|---|
| `cohorts.csv` | 3a | `build_cohorts.py` | market × company × destination × model × powertrain × cohort_year: units, basis, period, certified `tailpipe_gco2_km` / `energy_wh_km`, `test_cycle`, `technology_source`, `sales_source_file`, `powertrain_rule`, `coverage_note`, `variant` |
| `cohorts_withheld.csv` | 3a | `build_cohorts.py` | volumes that cannot be joined to a product parameter and why (unpriceable powertrain, no certified value, no US model-map row, out-of-scope brand, no EPA row) |
| `destination_parameters_eu27.csv` | 3 | `build_reference.py` | importer market: distance (km/yr, tier, band), car stock, car CO2, fleet intensity base (gCO2/km, tier), grid intensity (gCO2/kWh), mean car age, operating lifetime (central/low/high), excluded scenarios, warnings, source ids |
| `destination_parameters_us.csv` | 3 | `build_reference_us.py` | the same columns for the US market |
| `destination_parameters_kr.csv` | 3 | `build_reference_kr.py` | the same columns for the Korean market |
| `destination_parameters_jp.csv` | 3 | `build_reference_jp.py` | the same columns for the Japanese market |
| `reference_trajectories_eu27.csv` | 3 | `build_reference.py` | market × country × scenario × t: `e_ref_kgco2_per_vehicle` (benchmark per vehicle-year), `grid_kgco2_per_kwh` |
| `reference_trajectories_us.csv` | 3 | `build_reference_us.py` | the same columns for the US market (S1, S2) |
| `reference_trajectories_kr.csv` | 3 | `build_reference_kr.py` | the same columns for the Korean market (S1, S2) |
| `reference_trajectories_jp.csv` | 3 | `build_reference_jp.py` | the same columns for the Japanese market (S1, S2) |
| `ti_by_model.csv` | 4 | `build_ti.py` | market × company × destination × model × powertrain × scenario: units, lifetime, distance + tier, test cycle, real-world factor, year-0 product and benchmark emissions, `ti_per_vehicle_kgco2e`, `ti_tco2e`, and the whitepaper §5.2 tier declaration: `fleet_intensity_tier`, `grid_tier`, `lifetime_tier`, `rate_tier`, `layer1_tier` (benchmark), `technology_tier`, `powertrain_tier`, `layer2_tier` (product), `tier` (worst of both) |
| `ti_annual_by_model.csv` | 4 | `build_ti.py` | the same grain × calendar year: benchmark and product emissions per vehicle and in total (`e_ref_tco2e`, `e_prod_tco2e`), the annual gap, and the cell's TI that year |
| `ti_annual.csv` | 4 | `build_ti.py` | market × company × cohort_year × scenario × calendar year: surviving vehicles, what the scenario benchmark would have emitted (`e_ref_tco2e`), what the products emit (`e_prod_tco2e`), their difference (`ti_tco2e`), the running total (`cumulative_ti_tco2e`), and all three per surviving vehicle |
| `ti_withheld.csv` | 4 | `build_ti.py` | units carrying no result and why — the step-3a rows plus the markets whose benchmark is withheld |
| `ti_exclusions.csv` | 4 | `build_ti.py` | market × company × scenario that the market publishes no benchmark for, with the units affected and the sourced reason |
| `ti_crossover.csv` | 4b | `build_sensitivity.py` | market × company × destination × model × powertrain × scenario: closed-form crossover year (years after sale and calendar year) or the reason there is none |
| `ti_sensitivity.csv` | 4b | `build_sensitivity.py` | company × market × scenario × dimension (lifetime ±3 y, real-world factor low/high, proxied-distance quartiles, powertrain mix) × variant: cohort total |
| `ti_country.csv` | 5 | `aggregate_country.py` | company × market × cohort_year × destination × scenario: units, `ti_tco2e`, per-vehicle, direction |
| `ti_powertrain.csv` | 5 | `aggregate_country.py` | company × market × cohort_year × powertrain × scenario |
| `ti_annual_country.csv` | 5 | `aggregate_country.py` | the destination roll-up by calendar year: units, `e_ref_tco2e`, `e_prod_tco2e`, `ti_tco2e`, `cumulative_ti_tco2e` and the three per-vehicle values |
| `ti_annual_powertrain.csv` | 5 | `aggregate_country.py` | the same by powertrain |
| `ti_company.csv` | 5 | `aggregate_country.py` | company × market × cohort_year × scenario: `status` (reported / excluded), covered/withheld units, total, per-vehicle, direction, decomposition identity check, exclusion reason |
| `ti_global_coverage.csv` | 5e | `build_global_coverage.py` | company × cohort year: the company's own worldwide sales and what covers it, units assessed and their share of worldwide, the markets and country count assessed, units held and their share, and the brands inside the denominator that the cohorts hold apart |
| `ti_source_reconciliation.csv` | 5d | `build_reconciliation.py` | company × destination × cohort year × source file: units, basis and which side of the market it counts, whether the cohort was built from it, the brands a group figure covers, and the like-for-like spread against the file used |
| `ti_coverage.csv` | 5c | `build_coverage.py` | company × destination (every destination in the market-side sales files, worldwide) × cohort year × basis: `destination_group` (EU27, US, the company's home country KR or JP, IN, others), `home_country`, units, assessed units, withheld units, status (`assessed`, `withheld`, `no_benchmark`, `plant_side_only`, `region_unassessed`, `destination_unknown`), market — the coverage picture a reader filters countries from |
| `ti_data_quality.csv` | 5b | `build_data_quality.py` | company × market × cohort year, including `countries` (the destination codes covered), `countries_covered`, `countries_withheld` and `covered_share` (the sales coverage): analysis level, benchmark method, sales basis, test cycles, covered/withheld units, tier-C unit share and the `directional_only` flag (guideline §5.3, threshold 50 %), central lifetime, scenarios reported and excluded, markets by distance tier, withheld reasons, coverage notes, warnings |

`cohorts.csv` carries a `variant` column. `central` is the published cohort; every other value
is a sensitivity variant of the same cell (currently `all_hev`, see *United States*). Only
`variant = central` rows are summed into a result — the variants exist so the sensitivity step
reuses this join instead of repeating it.

Sign convention: positive TI = the product emits less than the destination's committed
benchmark over its lifetime (contribution); negative = lock-in liability. Unit: tCO2e over
the operating lifetime, per-vehicle values in kgCO2e.

**Reading a result year by year.** Every lifetime total in `ti_company.csv`, `ti_country.csv`
and `ti_powertrain.csv` has an annual twin — `ti_annual.csv`, `ti_annual_country.csv`,
`ti_annual_powertrain.csv` — and each annual row carries both sides of the comparison rather
than only its result: `e_ref_tco2e` is what the surviving fleet would have emitted on the
scenario's benchmark that calendar year, `e_prod_tco2e` is what it actually emits, `ti_tco2e` is
the difference, and `cumulative_ti_tco2e` is the running total that ends at the published
lifetime figure. Because the benchmark declines each year (S1 at the observed trend, S2 at the
government's committed rate) while a sold vehicle's intensity is fixed, the annual gap shrinks
and usually changes sign; `ti_crossover.csv` gives the year it does. Four tests hold the
arithmetic together: the identity `ti = e_ref - e_prod` at every annual grain, both roll-ups
reproducing the company flow year by year, the cell table summing to the company flow, and the
last cumulative value equalling the published lifetime total.

## Language, and the one exception

Everything the project writes is in English: every docstring, comment, note, derivation, column
name, method document and output value. A source's own title is given in English — the
publisher's own English name where it has one, otherwise a translation — and the URL, not the
title, is what locates it.

The exception is a string that has to match a source byte for byte: a spreadsheet column header,
a sheet name, a vehicle-class label, a file name the portal serves, an API parameter the portal
expects. Translating one of those would break the join, so they stay verbatim, and each is
handled the same way in three places:

- in code, they sit in a named constant or a dict key with a comment giving the English reading
  (`COLUMNS`, `CLASSES`, `KEYWORDS`, `POWERTRAIN_WORDS`, `NAMEPLATE_HEADER`, and so on), never
  inline in a sentence;
- in a lookup table, the verbatim key sits beside an English column that reads it
  (`jada_brands.csv` has `brand_en`, `jp_maker_map.csv` has `make_en`, `jp_segment_map.csv` has
  `row_en`, `kr_model_map.csv` and `jp_model_names.csv` have `model_en`);
- in an output table, the English name is the value and the source string travels beside it in
  `source_label`, so `sales_jada_jp.csv` and `vehicle_technology_jp_mlit.csv` join in English
  and still say what they were read from.

`registry/raw_files.csv` keeps each file's original name as the source served it, which is
provenance rather than prose, and `registry/sources.csv` gives every publisher and title in
English.

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
Toyota S1 −1.40 → −1.59 MtCO₂e and the archive's 1.5 °C column −13.95 → −14.14; Hyundai
S1 −1.49 → −1.57 and −7.78 → −7.86. The archive's S2 column is not comparable to the
current S2, which was re-anchored on 2026-09-04 (see *Scenarios* below). The archive remains the regression baseline for
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
   (before the two-market generalisation the sensitivity still assessed Luxembourg and its
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

**S2 for the US is the last NDC the country itself communicated.** The United States
notified withdrawal from the Paris Agreement on 2025-01-27, a month after communicating
its 2035 NDC on 2024-12-19: economy-wide net GHG 61–66 % below 2005 by 2035, a range the
NDC's own text places "on a straight line or steeper trajectory to net zero emissions by
2050". The build takes the low end, 61 %, and applies it pro-rata exactly as Australia's
and the EU's anchors are applied: light-duty CO2 from its latest observation to 61 % below
its 2005 level by 2035 (6.61 %/yr), and grid intensity likewise (4.33 %/yr). Two things
are disclosed rather than hidden. The status is *communicated, then withdrawal notified*,
carried in `ndc_anchors.csv` and in every `target_level` cell — this is the government's
own stated pathway, not a pathway in force. And the power leg is applied to intensity
because the US inventory tables on hand carry no power-sector series, which is looser
than the absolute target wherever generation grows — the same caveat as Korea's. A market
whose rate were ever empty would still be published as `scenarios_excluded` on
`destination_parameters_us.csv`, as a row per company in `ti_exclusions.csv`, as a
`status = excluded` row in `ti_company.csv`, and in `ti_data_quality.csv`; a test asserts
all four, and that no market currently drops a scenario.

**Australia** has processed inputs on disk but is deliberately not built yet.

## Korea

Korea is the home market of both companies in scope and the first destination assessed on free,
keyless, machine-readable Korean official statistics (all data.go.kr and portal files carry
and every file carries no restriction on use).

**Cohorts.** Hyundai: the IR "Unit Sales by Model" Korea domestic block for 2024 and 2025
(`sales_hyundai_kr.csv`, `domestic_sales`), with the powertrain read from the trim code
(CN7 HEV, SX2 EV, ...), so every Hyundai unit is assessed on its stated powertrain; Genesis
nameplates carry `company = genesis` and are out of scope. Kia: the IR Jan–Jun 2026 release
(`sales_kia_ir_2026.csv`, `retail_sales`, a half year); its labels do not split ICE from HEV, so
Carnival, K5, K8, Seltos, Sorento and Sportage are assessed as ICE centrally with an all-HEV bound
(`powertrain_rule = kr_unsplit_central_ice`, sensitivity `powertrain_mix`). Bongo, Bus, Tasman
and military vehicles are outside the passenger-car registration class and are measured
against their own segment or withheld as out of scope
(19,790 units); Nexo is withheld like every FCEV.

**Technology.** KEA label fuel economy per trim (5-cycle corrected, `test_cycle = KR_5CYCLE`,
real-world factor 1.0), converted to gCO2/km with EPA fuel carbon factors and to Wh/km for BEVs;
trim means per model × powertrain (`vehicle_technology_kr_kea.csv`).

**Benchmark.** Distance 11,963 km/yr (tier A: KOTSA inspection odometers over the MOLIT
passenger-car
stock, 2024). Fleet intensity 203 gCO2/km (2023, tier C: GIR road CO2 × the KOTSA passenger-car
share, see country_emissions/method). Grid 415.5 gCO2/kWh (Ember 2024). Mean age 7.3 years from
the MOLIT model-year distribution (tier C, biased low) gives an operating life of 11 years
[10, 15] under the EU27 rule (1.5 × mean age, clamped). S1: GIR road CO2 nearly flat
(−0.2 %/yr) and grid −2.2 %/yr; S2: the 2050 Carbon Neutrality Scenarios (2021), transport
scenario A 98.1 → 2.8 MtCO2e (−10.5 %/yr) and power scenario B 269.6 → 20.7 (−7.7 %/yr).

**Reading the result.** Because the observed Korean fleet trend is flat, S1 is a contribution
for both companies (their label-basis product intensities sit below the 203 gCO2/km fleet
average), while S2 turns every cohort into a liability: the government's own net-zero
pathway declines faster than the products' fixed intensities. The lifetime sensitivity moves the Korean
S1 by about ±30 % because the operating life is short and uncertain.

## Japan (added 2026-09-04)

Japan is assessed entirely on Japanese official statistics, with no licensed dataset and no
cross-market transfer except one disclosed factor. It is also the market where the sources fit
the method best: distance and stock come from one table at one date, the vehicle life is
published rather than derived, and the emissions numerator is already split by vehicle type.

**Cohorts.** JADA's passenger-car nameplate ranking (`sales_jada_jp.csv`), the annual
January-to-December edition.
Two properties of that source shape the coverage. It is a top-50 ranking, so a nameplate outside
the top 50 is not in the cohort at all — which is why Toyota's coverage of its own registered
volume is 99.0 % (2024) and 97.7 % (2025) while Nissan's is 57.4 % and 54.0 %: Nissan has only
four nameplates in the top 50. And it excludes kei vehicles and foreign brands by
construction (its
own note), so no kei unit can enter a cohort, which matters for the benchmark below. JADA's
ranking sums every variant of one nameplate, including units built abroad, so Corolla is the
whole Corolla family and the certified value pooled against it must be too (`jp_labels.csv`).
Every nameplate enters the tables under its English name, with the string the source prints
kept beside it in `source_label` (`jp_model_names.csv` is the one home for that mapping).

**Technology.** The MLIT fuel-economy list, which publishes CO2 emissions per kilometre in
gCO2/km per
certified grade — the only market in the project where the product value needs no conversion from
fuel economy at all. Two editions are read (March 2025 and March 2026) because the
publication lists
only what is type-approved on its own date: a nameplate withdrawn during the cohort year is in the
older edition and gone from the newer one, so the newest edition that carries a nameplate wins and
the older one supplies only what the newer one dropped. A nameplate's value is the grade-weighted
mean over its family, weighting by certified grades exactly as the US build weights over EPA trim
names. Test cycle `WLTC_JP`.

**Powertrain (assumption A-JP-PT).** The ranking publishes no powertrain, so what a nameplate is
sold as comes from the certificates: where every grade is a hybrid (Prius, Aqua, Note, X-Trail)
all its units are hybrid (`powertrain_rule = jp_certified_single`), and where a nameplate is
certified both ways its units are divided by the maker's own JADA fuel mix for that year,
restricted to the powertrains that nameplate offers and renormalised
(`jp_jada_fuel_share`; Toyota 2024 is 65.6 % hybrid, 30.6 % petrol, 2.0 % diesel, 1.6 % plug-in,
0.14 % battery-electric). A maker-wide share applied nameplate by nameplate is the weak link — the
real hybrid share of a Corolla is higher than that of an Alphard — so every divided nameplate
carries an `all_hev` variant that the sensitivity step prices (`ti_sensitivity.csv`, dimension
`powertrain_mix`). A hybrid grade is identified by the H code in the
fuel-economy-improvement column, cross-checked against the engine column listing an
internal-combustion engine plus a motor code; an engine cell that lists two power sources
without an H code stops the extractor.

**Benchmark.** The Motor Vehicle Fuel Consumption Survey, Table 1, prints total
vehicle-kilometres and kilometres per vehicle-day on the same row, and the survey defines the
second as vehicle-kilometres over surveyed vehicles times
*calendar* days. Annual distance per vehicle is therefore that figure times 365, and the vehicles
behind a row are its vehicle-kilometres divided by the same product. The implied fleet is what
confirms the
reading: 61.7 M cars and 15.0 M goods vehicles against the 62 M and 14.6 M AIRIA publishes, where
a working-day reading would have overstated the car fleet by 47 %. Fiscal 2024 throughout, matched
to the emissions year rather than taken as the latest observation (the survey has fiscal 2025, the
inventory does not).

| Segment | Distance | Fleet intensity | Life | Numerator |
|---|---|---|---|---|
| passenger_car | 8,107 km/yr | 170.0 gCO2/km | 13 y [10, 16] | GIO/NIES Passenger Vehicle 84,972 kt |
| freight | 11,918 km/yr | 394.2 gCO2/km | 16 y [13, 19] | GIO/NIES Truck and Lorry 70,672 kt |

The life is AIRIA's mean years of use — 13.35 years for cars, 16.29 for goods vehicles — a
published
expected life, which neither the EU27 nor the Korean build can source and both have to derive from
mean age. It is tier B rather than A only because AIRIA counts a temporary deregistration as
an ending, making
it a floor; it is bracketed ±3 years. Grid 483.4 gCO2/kWh (Ember 2024).

**Buses are not built.** The distance survey separates diesel buses but bundles petrol buses into
the car and special-vehicle rows, so a bus denominator would be diesel-only against an all-bus
numerator and the intensity would be biased high. The bus rows are published in
`vehicle_usage_jp.csv`; no company in scope sells buses in Japan.

**Four things are disclosed rather than smoothed over.**

1. *No battery-electric unit is assessed.* The fuel-economy list is a fuel-consumption
   publication and carries no electricity-consumption rating, so a Japanese battery-electric
   nameplate has no certified value here.
   None of the cohort nameplates is battery-electric, so nothing is withheld on this ground — but
   the moment a BEV nameplate enters the top 50 it will be, and the bias runs against the company,
   since its cleanest product is the one that cannot be counted.
2. *The real-world correction is borrowed.* Japan publishes no official real-world gap, so the EEA
   OBFCM gap for the same WLTP/WLTC procedure is carried across (1.191 ICE, 1.211 HEV). Japan's
   WLTC omits the Extra-High phase, so the true Japanese gap is likely larger and this factor
   understates real-world product emissions — which flatters the company.
3. *The benchmark includes kei cars, the cohort cannot.* The fleet intensity is the whole national
   fleet, kei vehicles included, while the ranking excludes them. Kei cars are lower-emitting,
   so the
   fleet average is harder for a registered car to beat than a registered-car-only average would
   be. The segment ratio stays 1.0, as in every other market.
4. *Two nameplates are counted and left unassessed.* The JPN Taxi (8,103 units in 2024) is an
   LPG hybrid certified in the LPG passenger-car workbook, which this build does not read; the
   Kicks (14,346
   in 2024, 9,595 in 2025) was withdrawn before either edition on hand. Both sit in
   `cohorts_withheld.csv` with those reasons.

**Reading the result.** S1 is a contribution for both companies — a Toyota cohort at roughly
85 gCO2/km hybrid and 120 petrol, corrected to real-world, sits well below a 170 gCO2/km fleet
average that is falling only 1.9 %/yr — while S2 turns both into a liability, the GX 2040 pathway
(−6.8 %/yr transport) outrunning a fixed product intensity. Japan's S1 contribution is far smaller
than Korea's or the United States' for the same reason the fleet intensity is low: the Japanese
fleet average already contains the hybrids and kei cars that make a Japanese cohort look clean
elsewhere.

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
are counted, not assessed. What would change the verdict: the BTR1 CRT workbook (hand fetch), the
2020-21/2021-22 Year Book (hand fetch) and a Vahan maker-level active-stock export.

## Toyota and Nissan (EU27, added 2026-09-04)

Both were assessed from the EEA snapshots already on disk, so nothing new was acquired: the
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

Both companies publish a US sales table by model, so both are assessed on their own release rather
than on an investor summary.

**Toyota** prints models by division and, in a second table, model by powertrain. The two are an
overlay, not two sets of rows: the Camry appears in both because every Camry sold is a hybrid, so
combustion volume is the model total minus its electrified rows and never a sum of the tables.
The extractor enforces that, checks each division's models against the published division total,
and keeps the small difference the release itself leaves unprinted (6 units in 2025, 15 in 2024)
as its own row rather than dropping it. Lexus is held out as its own company, exactly as Genesis
is held out of Hyundai. Result: 2,111,810 covered units in 2025 (98.3 %), S1 +8.07 MtCO₂e,
S2 −18.60; 2024 +5.53 and −19.00. The large current-path contribution is the same segment-ratio
artefact described above, amplified: Toyota's cohort is hybrid-heavy and the US benchmark is the
all-light-duty fleet including pickups.

**Nissan** prints models but no powertrain. It needs no assumption anyway: its US line-up in
these years is combustion except the LEAF and the Ariya, which the EPA certification data
confirms, so every nameplate is assessed explicitly. Infiniti is held out as its own company.
Result: 873,293 covered units in 2025 (100.0 %), S1 +1.36 MtCO₂e, S2 −9.65. Nissan also
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

## Global coverage

`ti_global_coverage.csv` answers how much of a company's worldwide sales the assessed markets
speak for. Two shares sit side by side: `assessed_share_of_global`, the units carrying a result
over the company's own worldwide figure, and `held_share_of_global`, every unit the project
holds for those brands whether assessed or not. The gap between them is sales acquired but not yet
priceable, which `ti_coverage.csv` lists destination by destination.

| Company | Cohort | Worldwide | Assessed | Held | Countries |
|---|---|---|---|---|---|
| Toyota | 2024 | 10,159,336 | 26.8 % | 42.6 % | 27 |
| Toyota | 2025 | 10,536,807 | 20.0 % | 35.4 % | 1 |
| Hyundai | 2024 | 3,978,567 | 41.6 % | 47.5 % | 28 |
| Hyundai | 2025 | 3,940,709 | 33.9 % | 39.6 % | 2 |
| Nissan | 2024 | 3,348,692 | 31.7 % | 40.3 % | 27 |
| Nissan | 2025 | 3,202,137 | 27.3 % | 34.5 % | 1 |
| Kia | 2026 H1 | 1,619,037 | 43.2 % | 100 % | 2 |

The 2025 rows are lower than the 2024 rows for one reason only: the EU27 cohort is a 2024
registration year, so a 2025 row is the United States alone. Kia's held share is 100 % because
its retail release covers every market it sells in, and 43.2 % of that is assessed.

**Where each denominator comes from, and what it counts** (`global_sales_totals.csv`).

1. **Toyota**: the group workbook's worldwide-sales row for Toyota including Lexus. Daihatsu and
   Hino are separate blocks and are outside it.
2. **Nissan**: the global release's "Global sales" row, covering Nissan and Infiniti.
3. **Hyundai**: derived, and marked so, because Hyundai publishes no worldwide total. Korea
   domestic sales plus shipments exported from Korea plus sales by the overseas plants, each
   from its own Hyundai workbook. The export leg is shipments rather than sales, so the figure
   is approximate; it lands about 4 % below the figure Hyundai quotes in its earnings material,
   which is the direction that under-statement predicts.
4. **Kia**: the sum of every destination in its retail workbook, which is its own worldwide
   retail for that half year.

**The brand boundary is stated, never assumed.** A group denominator covers brands the cohorts
hold apart, so Lexus, Infiniti and Genesis units are counted in `held_units` and named in
`brands_out_of_scope`. A assessed share is therefore always the brand in scope measured against
the group total, which understates it: Toyota's 26.8 % would be higher against the Toyota brand
alone, and the Lexus worldwide figure needed for that is on the workbook's own Lexus sheet.

## Two scenarios, two pathways each, and no re-allocation of electricity

**Scenarios (decision, 2026-09-04).** There are two, and both run the full length of a vehicle's
life. **S1** is the observed trajectory: a log-linear trend of the market's own transport and grid
series, 2015 onward, 2020–2021 excluded. **S2** is the government's own committed pathway, and
nothing else — no modelled 1.5 °C scenario appears in the results, because no government stated
one and the project's claim is a comparison against what a state has itself committed to.

The earlier build had a third scenario, and its S2 was derived from a 2030 waypoint. Both were
removed. A rate fitted to a seven-year window (2023–2030) and then compounded over an 11- to
25-year operating life describes a pathway nobody published; each S2 anchor is now the furthest
year the policy itself sets, so the whole cohort lifetime sits inside the target horizon:

| Market | S2 anchor | Transport pathway | Power pathway |
|---|---|---|---|
| EU27 | European Climate Law, 90 % below 1990 by 2040 | 13.51 %/yr | 8.56 %/yr |
| Korea | 2050 Carbon Neutrality Scenarios (2021), transport scenario A / power scenario B | 10.52 | 7.71 |
| US | NDC communicated 2024-12-19, 61 % below 2005 by 2035 | 6.61 | 4.33 |

Australia's table is built the same way (43 % below 2005 by 2030, pro-rata) but no Australian
cohort is assessed, so it produces no result.

The transport rate moves the benchmark; the power rate moves the grid a battery-electric car
charges from, so its product emissions fall year by year (Korea S2: 0.4155 kgCO₂/kWh in 2024,
0.1863 in 2034). Combustion and hybrid products have no power term.

**The benchmark is not re-based onto electricity, and that is deliberate.** A national account
puts a vehicle's direct fuel combustion in transport and the electricity it charges with in the
power sector, and the NDC sets a separate target for each. This model uses both of them exactly
where the account puts them: the transport target on the benchmark, the power target on the
battery-electric product. Allocating electricity into the transport benchmark as well would
count the same committed decarbonisation twice, once in the benchmark and once in the product.
Korea and Japan both publish an electricity-allocated inventory sheet that would make such a
re-basing possible; it is deliberately not used. The project lead settled this on 2026-09-04.

## Vehicle segments, and why a benchmark is chosen per segment (2026-09-04)

These companies do not only sell cars, so a result that assessed everything against a car
benchmark would be wrong twice: it would leave trucks out, and it would measure the trucks it
did keep against the wrong fleet. Every cohort row therefore carries a `segment`, and the
benchmark it is assessed against is the one built for that same population.

| Segment | What it is | Where it is used |
|---|---|---|
| `passenger_car` | cars: EU27 M1 and the Korean and Japanese passenger-car classes | EU27, Korea, Japan |
| `light_duty` | cars and light trucks together | the United States |
| `freight` | goods vehicles: the Korean goods class, the Japanese goods class | Korea, Japan |
| `bus` | buses and minibuses: the Korean bus class | Korea |

**Why the United States is one segment and not two.** The EPA inventory does publish passenger
cars (295,400 ktCO₂ in 2023) and light-duty trucks (709,900) separately, so segment emissions
are not missing. The distance and stock statistics are the problem: FHWA VM-1 splits the fleet
by **wheelbase**, not by body type. Cars are 29 % of light-duty CO₂ while the short-wheelbase
class holds 76 % of the vehicles, so dividing the car numerator by the short-wheelbase
denominator gives 84 gCO₂/km, below the plausibility floor and plainly wrong. Pairing like with
like gives 217 gCO₂/km. The consequence is stated because it flatters the companies: a benchmark
that includes pickups and large SUVs is higher than a car-only benchmark would be, and a higher
benchmark makes any product look better. This is the same disclosure as the segment ratio of
1.0 and is why US pickups (Tacoma, Tundra, Frontier, Santa Cruz) sit inside the cohort rather
than beside it.

**Europe needs no such compromise.** Its numerator is Eurostat CRF 1.A.3.b.i, passenger cars
alone rather than transport as a whole, and its denominator is passenger-car stock and
passenger-car vehicle-kilometres. Both sides describe the same population.

**Korea carries all three segments** because emissions, stock, distance and vehicle age are all
published under the same four registration classes:

| Segment | Distance | Intensity | Lifetime |
|---|---|---|---|
| passenger car | 11,963 km/yr | 203.3 gCO₂/km | 11 y |
| goods vehicle | 17,363 km/yr | 428.1 gCO₂/km | 13 y |
| bus | 20,630 km/yr | 690.6 gCO₂/km | 14 y |

That is what lets Hyundai's Porter class (111,373 units in 2024) be measured against Korean
goods vehicles instead of against cars: S1 +3.13 MtCO₂e, S2 −0.12. Heavy trucks and coaches
above 3.5 t are counted and withheld (26,864 units in 2024) because Korea's fuel-economy
labelling scheme does not certify them, so no product intensity exists.

**Japan carries two of the three.** Its inventory publishes passenger vehicles, buses and
goods vehicles
separately, so the numerator is there for all three, but the distance survey bundles petrol buses
into the car and special-vehicle rows. A bus benchmark would then divide an all-bus numerator by a
diesel-only denominator, so buses are not built and the reason is on the row (see *Japan* above).
The two that are built are matched on both sides, cars against cars and goods vehicles
against goods vehicles.

**Where a country publishes no split**, the rule is to fall back to the road-transport sector as
a whole and to tier the value down to C, saying so on the row. No market needs that fallback
today; it is recorded here so the choice is not reinvented later.

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
the rate derivations (`derive_eu27_rates.py`, `derive_us_rates.py`, `derive_au_rates.py`,
`derive_kr_rates.py`, `derive_jp_rates.py`), then the model in this order —

1. `build_cohorts.py` — sales × technology per market → `cohorts.csv`, `cohorts_withheld.csv`
2. `build_reference.py` — EU27 destination parameters and trajectories
3. `build_reference_us.py`, `build_reference_kr.py`, `build_reference_jp.py` — the same for the
   single-country markets
4. `build_ti.py` — per-cell lifetime TI, annual flow, withheld and excluded tables
5. `build_sensitivity.py` — crossover years and the four sensitivity dimensions
6. `aggregate_country.py` — country, powertrain and company × market roll-ups
7. `build_data_quality.py` — the §5.3 declaration per company × market
8. `build_coverage.py`, `build_reconciliation.py`, `build_global_coverage.py` — coverage and
   source agreement
9. `build_database.py`, `build_dashboard.py`

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
