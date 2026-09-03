# Tracker

The single live tracking document. Current state only — history is in
[`log/README.md`](log/README.md), specifications are in `phases/`, `stages/` and `process/`.

**Last pass:** 2026-09-04 (design, conformance and state; state refreshed after ST10 and the
database build the same day; refreshed after the Kia and Honda EU27 acquisition, the independent
review, and the first US/AU inputs). **Next pass due:** when US or AU passenger-car CO2, stock
or distance series land, or at any charter change.

## 1. Where we are

PH1 (automotive case study) entered 2026-09-03 and is the only live phase. The five-step chain now
runs end to end for the first pass — **EU27, Toyota and Hyundai, cohort 2024** — on data already
held: all five datasets have a processed table, `build_reference.py`, `build_ti.py` and
`aggregate_country.py` have written their outputs, and `build_database.py` has loaded every input,
lookup, output and source table into `data/auto/tradeimpact_auto.sqlite` (21 tables).

Kia and Honda EU27 2024 registrations were acquired on 2026-09-04 from the same EEA query, so all
four exporters now sit on one destination boundary (Kia 414,677 and Honda 40,270 registrations;
both net liabilities in every scenario). For the United States and Australia the first inputs exist
(Ember grid intensity 2000–2025 for both; NDC anchors hand-transcribed with `verified = no` — the
US is a FLAG market with no NDC in force; US light-duty stock and distance from FHWA VM-1 2023,
197 million short-wheelbase vehicles at ~17,700 km/yr, tier B for the wheelbase-not-body-type
definition; US passenger-car CO2 from EPA Inventory Table 3-13 for 1990, 2005 and 2019–2023 —
295 MtCO2 in 2023 — transcribed from the PDF text with page reference). Still to collect: the EPA
annex annual series (the main text has too few trend-window years for a US S1 rate), US operating
life (survival tables), Australian passenger-car CO2, stock and distance, and model-level sales for
both markets — so neither can enter a result yet. `script/auto/run_all.py` now runs the whole
chain fail-fast before any commit. Their absence is counted, not
assumed away: the Kia and Hyundai IR tables are processed but cannot enter
a country-level result as they stand (regions and plant-side sales respectively).

Crossover years per cell and the lifetime, real-world and proxied-distance sensitivities now
exist (`ti_crossover_eu27.csv`, `ti_sensitivity_eu27.csv`, both in the database). Built only
when needed, and therefore still absent: an independent re-derivation of any figure, a P10/P50/P90
treatment of the crossover (`B-07`), and any dashboard. The regression check against the archived
published baseline has run and passed (all 189 destination parameters exact; company × scenario
totals within 2 × 10⁻⁷; crossover and lifetime sensitivities agree). Phase exit is blocked by the
independent re-derivation and `B-03`, `B-04`, `B-07`.

## 2. Phases

| Phase | Objectives met | Deliverables accepted | Status | Gate verdict |
|---|---|---|---|---|
| [PH1 automotive](phases/ph1-automotive-case-study.md) | 0 of 7 (4 partial) | 0 of 3 | Live since 2026-09-03; first pass EU27-only | Not at gate |
| [PH2 white paper](phases/ph2-methodology-white-paper.md) | 0 of 7 | 0 of 1 | Not started; methodology documents exist as inputs | — |
| [PH3 model and dashboard](phases/ph3-model-and-dashboard.md) | 0 of 4 | 0 of 3 | Not started; `B-08` open | — |
| [PH4 power and shipbuilding](phases/ph4-power-and-shipbuilding.md) | 0 of 4 | 0 of 2 | Not started — and `D-03` shares PH1's Month 7 milestone (`F-03`) | — |
| [PH5 synthesis and release](phases/ph5-synthesis-and-release.md) | 0 of 5 | 0 of 3 | Not started | — |

**Judgement.** The week's work moved PH1 objectives 2, 3 and 4 from unserved to partial — a real
advance, and faster than expected. The regression against the archived baseline has now run and
passed, which shows the new scripts reproduce the old engine — not that either is right: no figure
had been independently re-derived — until 2026-09-04, when the Honda cohort was: the engine is
exact, and the review surfaced a distance-year mismatch inherited from the archived pipeline that
moved every total 1–13 % more negative once fixed. Crossover and the three guideline
sensitivities exist, and the EU27 result covers all four exporters — the Korea-versus-Japan
comparison the proposal promises, on one market boundary. The next units of work are the lead's
decisions on the four open review items and the United States and Australia inputs. A result set that grows faster than its verification is the failure mode this
phase has to avoid.

## 3. Stages

| Stage | Phases served | Status | Latest output | Figures |
|---|---|---|---|---|
| [ST01 targets](stages/st01-targets-and-provenance.md) | PH1, PH4 | Partial — set named by direction; §6.3 criteria not evaluated; `target_set.csv` not written; `B-03` open | none | — |
| [ST02 `sales`](stages/st02-06-datasets.md) | PH1, PH4 | In progress — EU27 complete for all four exporters (four EEA snapshots); US and Australia not started | `sales_eea_eu27_2024.csv` (2,126), `sales_kia_ir_2026.csv` (287), `sales_hyundai_plant_2025.csv` (113) | `[compute]` |
| [ST03 `country_emissions`](stages/st02-06-datasets.md) | PH1, PH4 | EU27 done; US and Australia not started | `country_emissions_eu27.csv` (1,312) | `[compute]` |
| [ST04 `emission_targets`](stages/st02-06-datasets.md) | PH1, PH2, PH4 | EU27 done; US and Australia not started | `emission_targets_eu27.csv` (162) | `[compute]` |
| [ST05 `vehicle_usage`](stages/st02-06-datasets.md) | PH1, PH2 | EU27 done; US and Australia not started | `vehicle_usage_eu27.csv` (2,092) | `[compute]` |
| [ST06 `vehicle_technology`](stages/st02-06-datasets.md) | PH1, PH2 | EU27 certified values and the real-world factors done; no PHEV utility factor | `vehicle_technology_eea_2024.csv` (1,286), `method/real_world_correction.csv` (3) | `[compute]` |
| [ST07 provenance](stages/st01-targets-and-provenance.md) | all | In progress — catalogue and assumptions established; licence verdicts outstanding | `toolbox/catalogue.md`, `toolbox/assumptions.md` | — |
| [ST08 benchmark](stages/st08-10-analysis.md) | PH1, PH2, PH4 | Run, EU27 only | `destination_parameters_eu27.csv` (27), `reference_trajectories_eu27.csv` (1,899) | `[compute]` |
| [ST09 impact](stages/st08-10-analysis.md) | PH1, PH2, PH3, PH4 | Run, EU27 only; crossover and sensitivities output | `ti_by_model_eu27.csv` (3,321), `ti_annual_eu27.csv` (150), `ti_withheld_eu27.csv` (179), `ti_crossover_eu27.csv` (3,321), `ti_sensitivity_eu27.csv` (54) | `[compute]` |
| [ST10 aggregation](stages/st08-10-analysis.md) | PH1, PH3, PH4 | Run, EU27, four exporters; identity holds for all twelve company × scenario rows; guideline §5.3 data-quality declaration written (Toyota and Honda `directional_only`: tier-C unit share 53.6 % and 53.8 %); `tradeimpact_auto.sqlite` built | `ti_country_eu27.csv` (324), `ti_powertrain_eu27.csv` (36), `ti_company_eu27.csv` (12), `ti_data_quality_eu27.csv` (4), `tradeimpact_auto.sqlite` (24 tables) | `[compute]` |
| [ST11 verification](stages/st11-verification.md) | all | Independent re-derivation of the Honda cohort done 2026-09-04 (engine reproduced to 6 × 10⁻⁷; three input defects found and fixed: distance year mismatch, real-world range, BEV crossover label); `tests/test_model.py` (5 checks) passes; archive remains the engine baseline, no longer the input baseline | `data/auto/output/method.md` §Verification, `tests/test_model.py` | `[verified-engine]` |
| [ST12 methodology](stages/st12-15-outputs.md) | PH1, PH2, PH4, PH5 | Not started; three methodology documents in place as inputs | none | — |
| [ST13 tool and dashboard](stages/st12-15-outputs.md) | PH3, PH5 | Not started; `B-08` open | none | — |
| [ST14 publication](stages/st12-15-outputs.md) | PH1, PH2, PH4, PH5 | Not started | none | — |
| [ST15 sector onboarding](stages/st12-15-outputs.md) | PH3, PH4, PH5 | Not started | none | — |

**No figure in this project is `[verified]`.** Every output above is `[compute]` and none may reach
a deliverable, a client draft or a dashboard until ST11 has run (`process/general.md` §5). The
archived EU27 2024 published results are **prior work** (`SRC-24`) and count only as a regression
baseline.

## 4. Objective coverage

| Phase objective | Evidenced by | Verdict |
|---|---|---|
| PH1/1 targets fixed | ST01 | partial — named, criteria unevaluated, no `target_set.csv` |
| PH1/2 inputs acquired and registered | ST02–ST07 | partial — complete for EU27, absent for US and Australia |
| PH1/3 reference benchmark built | ST08 | partial — 27 markets × 3 scenarios exist, unverified |
| PH1/4 impact built | ST09 | partial — per-cell TI, crossover year and the three guideline sensitivities exist for EU27; no P10/P50/P90 range (`B-07`) |
| PH1/5 aggregated to country and company | ST10 | partial — EU27 country, powertrain and company tables exist, identity holds |
| PH1/6 verified | ST11 | partial — engine independently re-derived (Honda, exact); inputs corrected once; open review items (LU implausible benchmark, rising-trend markets, segment ratio, flat S2 grid) await a lead decision |
| PH1/7 published | ST14 | **unserved** |
| PH2/1–7 | ST12, ST14 | **unserved** |
| PH3/1–4 | ST13 | **unserved** |
| PH4/1–4 | ST15 and the sector runs | **unserved** |
| PH5/1–5 | ST14 | **unserved** |
| Rolling portfolio TI (whitepaper §3.8, the "primary disclosure metric") | ST10 | **unserved and unservable** on one cohort — `F-07` |

## 5. Deliverable coverage

| id | Deliverable | Stage | Status | Acceptance test |
|---|---|---|---|---|
| `D-01` | Methodology white paper | ST12, ST14 | Not started | Not run |
| `D-02` | Automotive case study | ST14 | Not started; EU27 result set in place but unverified | Not run |
| `D-03` | Power generation case study | ST15, ST14 | Not started — same Month 7 milestone as `D-02` (`F-03`) | Not run |
| `D-04` | Shipbuilding case study | ST15, ST14 | Not started | Not run |
| `D-05` | Climate Arc integration specification | ST13 | Not started | Not run |
| `D-06` | Open-source TI model | ST13 | In progress — nine scripts across five datasets and the model step; no tests, no release packaging | Not run |
| `D-07` | Final synthesis report | ST14 | Not started | Not run |
| `D-08` | Prototype dashboard public release | ST13 | Not started; `B-08` open | Not run |
| `D-09` | Policy brief | ST14 | Not started | Not run |
| `D-10` | Open dataset | ST02–ST07 | In progress — EU27 tables exist; IR workbook redistribution not cleared | Not run |

## 6. Process conformance

| Stage | Process document | Deviations and open items |
|---|---|---|
| ST02–ST06 | [`process/dataset-acquisition.md`](process/dataset-acquisition.md) | One processed file per source or market scope, by design. **Open:** the three sales tables carry `source_file` but no `source_id` — provenance holds only through the raw-file hash in `method.md` |
| ST02, ST05, ST06 | as above | Resolved 2026-09-04: the three method files were rewritten to the shape the data has (`plant_sales`, long-format usage, `energy_wh_km` plus the separate correction file); sources and raw-file provenance moved to `data/auto/sources.csv` and `raw_files.csv` as their single home |
| ST08, ST09 | **Missing** — the scripts ran before their process document was written | Write both at the next re-run, or accept that the method-before-implementation rule (`process/general.md` §4) was inverted here. Recorded rather than excused |
| ST10, ST11 | Deferred, written at stage entry | ST10 has run and ST11's regression has run without a process document for either — same inversion as ST08/ST09, recorded here |
| ST01, ST07 | [`process/general.md`](process/general.md) plus the stage sections | Sufficient at current scope |
| ST12–ST15 | Deferred to their phase entry | Declared deviation in `process/general.md` §9 |
| all | `process/general.md` §8 | Fingerprint-based refresh specified but not instrumented; no state file exists, so a re-run cannot yet prove which stages were unaffected |

## 7. Alignment findings

From the 2026-09-04 conformance pass against the proposal.

| # | Finding | Charter id | Verdict | Action | Owner |
|---|---|---|---|---|---|
| F-01 | Crossover Points are promised as P10/P50/P90 ranges; the methodology gives three deterministic scenarios and no propagation method exists | `C-05`, `B-07` | gap | Build a propagation procedure in PH2/3, or renegotiate the wording | `climate-risk-modeller`, then `consultant` |
| F-02 | Four automotive exporters against a six-firm bound across three sectors | `C-11`, `B-03` | drift | Decide: six per programme or two per sector, through change control | `consultant` |
| F-03 | The power generation case study shares the Month 7 milestone with automotive, while automotive absorbs all capacity | `D-03` | unpriced | Sequence explicitly with Climate Arc, or accept a milestone slip in writing | `consultant` |
| F-04 | The United States has no active NDC, so it has no S2 benchmark; the substitution rule is unmade | `B-04` | gap | Decide before ST08 runs on any non-EU market | `climate-risk-modeller` |
| F-05 | United States and Australian volumes at model × powertrain level may be unobtainable on public data | `C-08`, `X-02` | gap | Prove a public route, or drop the markets from the headline | `data-collector` |
| F-06 | "Crossover Point modelling framework" is a Month 7 activity; the computation runs but emits no crossover year | `D-01`, `D-02` | gap | Add crossover to `build_ti.py`'s output | `data-scientist` |
| F-07 | Rolling portfolio TI is the whitepaper's primary disclosure metric and needs T cohorts; one cohort is held | `D-02` | gap | Acquire 2022 and 2023 snapshots, or state single-cohort scope in every output | `data-collector`, `result-reporter` |
| F-08 | Three method files disagree with the data they describe; sales tables carry no `source_id` | `N-03` | gap | Reconcile in the method files (see §6) | `developer`, `provenance-auditor` |
| F-09 | `D-08` requires validation across three case-study sectors, so PH3 cannot exit on automotive alone | `D-08` | aligned, dependency | Recorded in both phase documents | `research-director` |
| F-10 | No project start date, so no milestone can be dated | `B-01` | gap | Obtain from the grant agreement | `consultant` |
| F-11 | The Technical Advisory Group is not convened while the methodology-design and pilot stages are live | `C-07`, `B-06` | gap | Convene, or record the obligation as at risk | Project lead |
| F-12 | ST08 and ST09 were implemented before their process documents existed | `process/general.md` §4 | drift | Write both at the next re-run | `research-director` |
| F-13 | The mandatory sensitivities — T ± 3, utility factor ± 0.15, correction-factor range, all three scenarios — are not yet run as a set | guideline §5.2, `C-05` | gap | Add a sensitivity step before any figure is verified | `data-scientist` |

## 8. Drift and risk

- **Activity with no objective behind it:** further work on the Kia and Hyundai IR tables. Both are
  processed and neither can produce a country-level TI as it stands — Kia reports regions, Hyundai
  reports plant-side sales. They matter for later acquisition and Level 2 context, not for closing a
  PH1 objective now.
- **Objective with no activity:** PH1/6, verification. Five datasets, two model steps and a
  3,321-row result set now exist with **zero** independently re-derived figures. This is the largest
  open risk in the project and it grows with every new output.
- **Risk — sequencing:** `D-02` and `D-03` share Month 7; one sector is live, the other has not
  started (`F-03`).
- **Risk — accumulating unavailability:** 179 cells are withheld, PHEV units carry no sourced
  utility factor, and the EU27 distance is a Tier C proxy for markets with no national traffic
  series. Each is disclosed and individually defensible; together they make the first result a
  **direction with a coverage ratio**, not a magnitude (`N-04`, `A-08`, `A-13`), and the case study
  must be written that way from the first draft rather than corrected later.
- **Risk — method-after-code:** ST08 and ST09 ran ahead of their process documents (`F-12`). The
  code cites the whitepaper equations, so the substance is anchored, but the failure modes and the
  validation tests were never written down before implementation — which is exactly where a
  convenient neighbouring method hides.
