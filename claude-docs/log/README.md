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
  `data/auto/dashboard.html`: lineage raw → method → processed → output per data type with source
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
