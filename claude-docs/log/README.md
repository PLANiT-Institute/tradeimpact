# Log — decisions and transitions

The append-only record. Two kinds of entry, both dated, both permanent: **decisions** that changed
the design, and **transitions** — stage entries, exits and backward moves. Current state lives in
[`../tracker.md`](../tracker.md) and is not repeated here; history lives here and is never edited
out of the tracker.

When the first phase gate is crossed and this file exceeds a screen, it splits into `decisions.md`
and `transitions.md` and this README becomes their index. Not before — one file that is read beats
two that are not.

## Decisions

| Date | Decision | Reason | Consequence |
|---|---|---|---|
| 2026-09-03 | Restructure the repository to `data/auto/<dataset>/{raw,processed,method}` plus `data/auto/output/`, with all Python under `script/auto/<dataset>/` and `script/auto/model/` | The previous build had grown an application around the analysis; the research process needed a data-first layout that a researcher can follow | The prior build moved to `archive/` as read-only prior work. Its engine, snapshots and published results remain reusable (`SRC-24`) |
| 2026-09-03 | Focus on automotive first, with the five-step process (targets → data → reference → impact → country aggregation) | A 12-month programme cannot open three sectors at once; automotive is the primary validation vehicle with the best data | PH1 is the live phase; PH4 waits until the process has worked once |
| 2026-09-03 | Target exporters Hyundai, Kia, Toyota, Honda; importers EU27, United States, Australia | Korea and Japan exporters into contrasting grid and policy markets | Creates the six-firm tension with `C-11` — blocker `B-03` |
| 2026-09-04 | Treat the Climate Arc proposal `TI_Proposal_v3.docx` as the governing document | No countersigned grant agreement located | The charter is written from the proposal; if an agreement surfaces, Pass 3 re-runs (`B-05`) |
| 2026-09-04 | First analytical pass is EU27 Toyota and Hyundai, cohort 2024, on data already held; Kia, Honda, the United States and Australia become later acquisition | The EEA snapshots support a complete country × model × powertrain run today; the other markets do not | PH1 objectives 3–5 proceed EU27-only, with the absent markets counted as gaps rather than assumed |
| 2026-09-04 | Build one thing when it is needed — no model scripts, dashboard or database ahead of the step that consumes them | An artefact built before its input exists is a guess dressed as infrastructure | Process documents for ST08–ST15 are written at stage entry; the plan states what does not exist |

| 2026-09-04 | Unit of analysis is a company's sales to every destination country, filtered by the reader; coverage reported by group EU27 / US / home country (HQ country, KR or JP) / IN / others | Lead's clarification: the project is not about exports as such | `ti_coverage.csv` with `destination_group`; plant-side files never a cohort where a market-side file exists |
| 2026-09-04 | US cohorts from the companies' own market-side releases (Hyundai IR US sheet 2024–2025, Kia America 2024–2025, Kia IR 2026 H1); nameplates split by EPA Automotive Trends MY2024 production shares (A-US-PT); Genesis listed as an out-of-scope company | Free publisher files close the import and full-year gaps; the releases do not split powertrains | `mixed_central_ice` rule retired; all-HEV bound kept; cohort years never pooled |

| 2026-09-04 | Korea benchmark from free official statistics; passenger-car CO2 = GIR road CO2 × KOTSA share (tier C); S1 trend on the GIR road series, not the drifting share; lifetime by the EU27 mean-age rule on the MOLIT model-year distribution; S3 mixes the 2050 scenarios (transport A안, power B안) | No Korean publisher issues passenger-car CO2 as a file; the KOTSA share drifts 0.49 → 0.58; the A안 power endpoint is zero | `build_reference_kr.py`, `derive_kr_rates.py`, `kr_labels.csv`, `kr_model_map.csv`; Korea priced for Hyundai (2024, 2025) and Kia (2026 H1) |

| 2026-09-04 | India benchmark not built; recorded as `no_benchmark` with the reasons | Free inputs partial (>50 % proxies, S2 FLAG), no free model-level sales | Coverage group IN counted, not priced; unlock conditions listed in output/method.md |

| 2026-09-04 | Tier flags on every value: A directly sourced / B estimated or derived / C proxy, per whitepaper §5.1, applied by rule at database build and declared per cell (Layer 1, Layer 2, worst) | Lead: every value must be flagged; the guideline names the tiers | `registry/tiers.csv`, `registry/value_tiers.csv`; `ti_by_model` tier columns; tests |
| 2026-09-04 | Dashboard Map view; registry and deliverables moved into `data/auto/registry/`, `data/auto/database/`, `data/auto/dashboard/` | Lead: map-based view by country; no loose files under data/auto | map geometry stored in the database so the page needs one file only |
| 2026-09-04 | No launcher script: `serve_dashboard.py --open` is the one command, and it answers the opaque `null` origin so a double-clicked dashboard.html connects itself while it runs | Lead: the page must get the file by default, without a launcher; browsers forbid a file:// page from reading a sibling file | Picker kept as the no-server fallback |

| 2026-09-04 | Toyota and Honda brought into scope; Lexus treated as a separate company like Genesis; Nissan, Suzuki, Mazda, Mitsubishi, Subaru pinned out of scope | Lead asked for Toyota and the second Japanese maker; Honda is second worldwide, Nissan second in the EU27, so the choice is recorded rather than assumed | EU27 results for four companies; one flag moves Nissan in |

| 2026-09-04 | Nissan in scope as the second Japanese maker, Honda pinned out | Lead's choice after the ranking was shown to depend on the basis: Honda second worldwide, Suzuki second on production and on Japanese sales with kei, Nissan second in the markets this project prices | EU27 result for Toyota, Hyundai, Kia, Nissan |
| 2026-09-04 | Japan sales from JADA: nameplate registrations, maker fuel mix, brand registrations with the imported part | Free, machine-readable, the standard Japanese registration statistic; no Japanese publisher crosses model with fuel | Japan counted and unpriced until the benchmark is built; the fuel mix is the future powertrain-split assumption |

| 2026-09-04 | US cohorts for Toyota and Nissan from their own US releases, transcribed to CSV with the publisher URL recorded; Lexus and Infiniti held out as separate companies | The lead limited the Japanese makers to the US and EU27; both companies publish a US model table, Toyota with powertrain | Toyota's overlay subtraction rule and the unprinted residual kept as a row; Nissan priced explicitly with no assumption |
| 2026-09-04 | `ti_source_reconciliation.csv`: every source a company published for the same cell, compared like for like on brand boundary | Lead asked whether the Korean makers can stand on the same source class and how far a company's own figures differ | All five overlaps agree to 0.0 %; the apparent 17 % and 6 % gaps were Lexus and Infiniti, not data |

| 2026-09-04 | Global coverage as its own output: priced and held units against each company's worldwide sales, with the brands in the denominator named | Lead asked what share of global sales the analysis captures | Toyota's and Nissan's worldwide figures fetched from their own publications; Hyundai's and Kia's derived from theirs and marked derived |

| 2026-09-04 | The benchmark stays on the transport sector's direct-combustion target and is not re-based onto an electricity-allocated inventory; the power-sector target is applied to battery-electric product emissions instead | Lead: the power target already carries the grid's own decarbonisation, and this project already uses it as r_power, so allocating electricity into the benchmark would count the same reduction twice | Korea's and Japan's allocated inventory sheets stay unused; both pathways are documented per scenario |
| 2026-09-04 | Two tier-C measures in `ti_data_quality.csv` renamed so each says its basis: `vkt_tier_c_*` (proxied distance, the only input to `directional_only`) and `cell_tier_c_*` (worst-of cell tier) | The names were near-identical while the measures diverge sharply — 0 % against 100 % outside the EU27 — and a reader took whichever they had in mind | A test pins both names, the old ones being absent, and that the two measures differ; the analysis report's data-quality paragraph is shorter for it |
| 2026-09-04 | `priced` renamed to `assessed` throughout — columns, status values and prose | Emissions accounting has no prices; the word implied a valuation that is not being made | `assessed_units`, `assessed_share_of_global`, `assessed_markets`, `assessed_countries`, and `region_unassessed` in `ti_coverage.csv` |
| 2026-09-04 | **Sign convention reversed**: TI is now `E_prod − E_ref`, so positive is emissions added and negative is emissions avoided (whitepaper v1.6 §3.3, guideline v1.9 §4.1) | TI is reported in tonnes of CO₂e and a positive number of tonnes should mean tonnes emitted; the old ordering made a benefit positive, which read against every emissions inventory and cost a paragraph of explanation in every deliverable | Every published figure keeps its magnitude and reverses its sign (S2 across the 20 cohorts +151.48 MtCO₂e added, S1 −29.01 avoided). `direction` keeps its words on their meanings. Colour follows meaning, not sign, in the report and the dashboard. Earlier log and tracker entries keep the signs in force when they were written; the charter's contract quote is annotated as superseded |

## Transitions

| Date | Stage or phase | Event | Trigger | Consequence |
|---|---|---|---|---|
| 2026-09-03 | PH1 | Entered | Repository restructure complete; methodology and dataset method files in place | ST01–ST07 opened |
| 2026-09-03 | ST02 `sales` | Entered | Four raw files acquired: two EEA snapshots, two IR workbooks | Processing scripts written for all three sources |
| 2026-09-03 | ST06 `vehicle_technology` | Entered | EEA snapshots carry certified WLTP values on the same rows as the volumes | `vehicle_technology_eea_2024.csv` written; correction and utility factor still unsourced |
| 2026-09-04 | ST07 provenance | Entered | First processed tables exist | Catalogue and assumptions established; `source_id` gap on the sales tables raised |
| 2026-09-04 | ST05 `vehicle_usage` | Entered and processed | Archived EU27 snapshot in `raw/`; ST08 needed the parameters | `vehicle_usage_eu27.csv` — long-format observations; distance, tier and lifetime bracket derived downstream in ST08 |
| 2026-09-04 | ST03 `country_emissions` | Entered and processed, EU27 | ST08 needed a base-year level and a grid intensity | `country_emissions_eu27.csv`, four series |
| 2026-09-04 | ST04 `emission_targets` | Entered and processed, EU27 | ST08 needed the benchmark slopes | `emission_targets_eu27.csv` — S1 observed trend, S2 NDC pro-rata, S3 1.5C pro-rata, `r_fleet` and `r_power` separately |
| 2026-09-04 | ST08 benchmark | Run, EU27 only | All three input datasets present | `destination_parameters_eu27.csv`, `reference_trajectories_eu27.csv`. Process document was **not** written first — recorded as finding `F-12` |
| 2026-09-04 | ST09 impact | Run, EU27 only | Benchmark plus volumes and certified values available | `ti_by_model_eu27.csv`, `ti_annual_eu27.csv`, `ti_withheld_eu27.csv` (179 withheld cells). Crossover not emitted — finding `F-06` |

Backward moves are recorded here with the same weight as forward ones. A finding that invalidates a
premise and sends work back is the process working; the entry states the trigger and what it cost.

## 2026-09-04 — independent review of the EU27 result (ST11)

- **Decision:** distance per car is the traffic series divided by the stock of the *same*
  year (`build_reference.py`). The archived pipeline mixed years; LT was 17 % low. Totals move
  1–13 % more negative; the archive is kept as the engine baseline only.
- **Decision:** the real-world sensitivity applies the documented OBFCM range 1.171–1.211 to
  ICE and HEV as a replacement of the central factor (`real_world_correction.csv` gained
  `factor_low`/`factor_high`). BEV stays 1.0 at both ends — a disclosed one-sided bias.
- **Decision:** BEV cells with t* < 0 are labelled "never crosses" when below the benchmark at
  sale, "before sale year" only when above it.
- **Decision:** negative observed S1 trends (BG, PL) are flagged `OBSERVED_INCREASE` in the
  rates table and left in the result, not clamped.
- **Open for the lead:** LU implausible fleet intensity carried into the headline; segment
  intensity ratio not applied; S2 grid held flat (absolute target already met) makes BEV S2
  below BEV S1; age bands use the 2025 partition while stock uses 2024; PHEV utility factor
  route (Appendix C.2) not yet taken.

## 2026-09-04 — five methodological decisions taken by the lead ("most plausible")

- Luxembourg withheld from all results (implausible national benchmark), reported with units.
- Segment intensity ratio = 1.0, disclosed as assumption; conservative for crossover portfolios.
- S2 grid floored at the observed S1 trend where the EU pro-rata power target is already met.
- Age bands capped at the cohort year, consistent with stock, CO2 and grid.
- Exporters in scope: Hyundai and Kia; Toyota and Honda deferred (snapshots pinned,
  `companies.csv` `in_scope = no`). US and Australian inputs are being downloaded by the
  automated pipeline where sites allow it (ABS census and use survey obtained 2026-09-04).

## 2026-09-04 — source-of-truth policy and direct fetches

- **Policy (lead):** every raw file under `data/auto` must trace to its source of truth by link;
  archived compilations are not sources; JSON is fine when the source publishes JSON; an HTML
  page is never a raw file; company sales come only from the IR workbooks the lead gathered.
- **Applied:** the archived `destination_eu27_inputs.json` was replaced by seven Eurostat cubes
  fetched directly from the Eurostat API (`fetch_eurostat.py`; values reproduce the archive
  exactly); the Hyundai EEA snapshot was re-fetched directly; a Kia America press-release scrape
  was removed; ABS census and use survey, NHTSA survival schedule, EPA inventory tables, FHWA
  VM-1 and OWID/Ember grid were obtained directly and registered with links and hashes.
- **Deliverable (lead):** one SQLite holding raw, lookup, processed and output tables with
  stage, source and column types, and an HTML pivot dashboard over it.

## 2026-09-04 — dashboard prototype

- `script/auto/model/build_dashboard.py` embeds `tradeimpact_auto.sqlite` (gzip + base64) in
  `data/auto/database/dashboard.html`: lineage raw → method → processed → output per data type with source
  links, pivot table with generated SQL, browse, read-only SQL console. Opens from disk; sql.js
  1.10.3 from cdnjs is the only network dependency. Added as the last `run_all.py` step.

## 2026-09-04 — gap review before the US build

- Toyota EEA snapshot re-fetched directly from the EEA API: no raw file now originates from the
  archived pipeline. CSV is preferred but JSON from a source of truth is acceptable (lead).
- US benchmark population fixed: EPA passenger cars alone are narrower than FHWA's short-wheelbase
  class, so the light-duty totals (cars + light-duty trucks; EPA Tables 3-13, A-91, A-93) are used
  against FHWA's all-light-duty stock and distance; the US S1 fleet trend is re-derived on that
  series (1.1 %/yr).
- US cohorts come from the lead's IR workbooks only: Kia U.S.A column (Jan–Jun 2026, model level,
  no powertrain split) and Hyundai US plants' Domestic segment (US-built cars only). Model names
  map to EPA base models through `us_model_map.csv`; mixed ICE/HEV models take ICE centrally with
  an all-HEV sensitivity bound; Genesis is out of scope; Ioniq 9 waits for an EPA row.
- EPA label values are 5-cycle adjusted, so the real-world factor for the EPA cycle is 1.0
  (`real_world_correction.csv` keyed on test cycle).
- Australia deferred by the lead; its inputs stay in the database.

## 2026-09-04 — United States built for Hyundai and Kia

- Model generalised: `build_cohorts.py` (sales × technology per market), `build_reference_us.py`,
  generic outputs with a `market` column, US S2 carried as an explicit exclusion row. EU27
  headline unchanged to the last digit; the sensitivity now withholds Luxembourg like the headline.
- US results: Hyundai S1 +1.53 MtCO2e (BEV +1.57, HEV +0.73, ICE −0.78), S3 −4.80; Kia S1 −0.76,
  S3 −8.53. Caveats recorded in README and output/method.md: cohorts from the lead's IR workbooks
  (Hyundai US-built only, Kia half year), all-light-duty benchmark with segment ratio 1.0, unsplit
  models priced as ICE with an all-HEV bound, EPA label values uncorrected.

## 2026-09-04 — dashboard reads the database instead of carrying it

- `data/auto/database/dashboard.html` (55 KB) embeds no data: it fetches the sibling
  `tradeimpact_auto.sqlite` when served by `script/auto/serve_dashboard.py`
  (http://127.0.0.1:8765/dashboard.html) and offers a file picker when opened from disk.
  Navigation, lineage, column panel and presets are built from the database's own `tables`,
  `columns`, `sources` and `raw_files` tables. sql.js (cdnjs 1.10.3) remains the only network
  dependency; vendoring it would make the page fully offline.
- New result table `ti_annual_by_model` gives the year-by-year TI flow at cell grain; the
  dashboard's "Results by year" view lands on it.

## 2026-09-04 — team roster refreshed against the pack update

- Four user-level agents added to the pack (`claude-md` 798e47d) and rostered here:
  `ir-disclosure-analyst` (ST02 basis map and build-vs-buy; the 2026-09-03 rejection of the role is
  withdrawn — every PH1 stall since was an IR workbook on the wrong basis), `transport-emissions-reviewer`
  (ST11/ST12 review chain and the ST14 publication gate; owns the design of the `B-07` propagation),
  `esg-disclosure-analyst` (ST12 `C-06` overview, ST14 `D-09` standard-setter text — white-paper stage,
  not now), `policy-analyst` (ST01/ST04 target anatomy and the `B-04` no-target rule; `D-09` storyline).
- Financial IR (valuation, guidance) explicitly out of scope: the framework never touches company financials.
- Tracker F-01 owner updated accordingly. No project-scoped agent created.

## 2026-09-04 — free sources first: trade statistics as a new data type

- Lead's order: exhaust free sources before any licensed sales dataset. New dataset
  `trade_flows`: EU member-state imports of HS 8703 passenger cars from Korea and Japan (Eurostat
  Comext, units and euros) and both sides of the KR/JP → US/AU flows (UN Comtrade public API),
  2022–2025, by HS six-digit sub-heading mapped to ICE/HEV/PHEV/BEV. Country-level; it bounds
  the Korean-built share of registrations and gives each exporter's powertrain mix per market,
  and it is the only free coverage of Japan and Australia so far. A dossier of free model-level
  sales releases for the four brands is in progress.

## 2026-09-04 — trade flows: what the free statistics say

- Korea → EU27 imports 2024 (27 member states as Comtrade reporters, aggregate rows): BEV 68,965,
  HEV 91,625, ICE 159,720, PHEV 28,184 vehicles, against Hyundai + Kia EU27 registrations of
  91,086 / 311,175 / 389,556 / 52,774 — an upper bound on the Korean-built share of about 0.76 /
  0.29 / 0.41 / 0.53 (Korean exports to the EU include other brands, so the true Hyundai–Kia share
  is at or below these ratios). Level 2 (production origin) is therefore boundable without any
  paid dataset.
- Korea → US 2024 (US-reported): ICE 1,179,630, HEV 238,126, BEV 108,718, PHEV 27,581; exporter-
  reported figures differ (BEV 135,202; ICE 860,722) — both sides are published.
- Korea → Australia 2024 (AU-reported): ICE 125,892, HEV 25,310, BEV 5,404, PHEV 159.
- Fix: the Comtrade preview mixes mode-of-transport breakdowns with aggregates; only aggregate
  rows are kept (the Australian side had been double counted).
