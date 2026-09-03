# Tracker

The single live tracking document. Current state only — history is in
[`log/README.md`](log/README.md), specifications are in `phases/`, `stages/` and `process/`.

**Last pass:** 2026-09-04 (design and conformance). **Next pass due:** at the first ST08 output,
or at any charter change.

## 1. Where we are

PH1 (automotive case study) entered 2026-09-03 and is the only live phase. The repository
restructure is complete, the five dataset method files are written, four raw sales sources and one
usage snapshot are held, and three sales tables plus one technology table are processed.

The analytical pass now running is deliberately narrow: **EU27, Toyota and Hyundai, cohort 2024**,
on data already held. Kia, Honda, the United States and Australia remain in the target set as
later acquisition and are counted as gaps, not assumed away.

Nothing else exists yet, and the plan does not pretend otherwise: **no model script, no dashboard,
no database.** Each is built when the step before it produces something it must consume. Phase
exit is blocked by: no benchmark table (ST08 has no `country_emissions` or `emission_targets`
input yet), and `B-03`, `B-04`, `B-07` open.

## 2. Phases

| Phase | Objectives met | Deliverables accepted | Status | Gate verdict |
|---|---|---|---|---|
| [PH1 automotive](phases/ph1-automotive-case-study.md) | 0 of 7 (2 partial) | 0 of 3 | Live since 2026-09-03 | Not at gate |
| [PH2 white paper](phases/ph2-methodology-white-paper.md) | 0 of 7 | 0 of 1 | Not started; methodology documents exist as inputs | — |
| [PH3 model and dashboard](phases/ph3-model-and-dashboard.md) | 0 of 4 | 0 of 3 | Not started; `B-08` open | — |
| [PH4 power and shipbuilding](phases/ph4-power-and-shipbuilding.md) | 0 of 4 | 0 of 2 | Not started — and `D-03` shares PH1's Month 7 milestone (finding `F-03`) | — |
| [PH5 synthesis and release](phases/ph5-synthesis-and-release.md) | 0 of 5 | 0 of 3 | Not started | — |

**Judgement.** Activity since 2026-09-03 has moved PH1 objective 2 materially and objective 1
partially; nothing has yet moved objectives 3–7, because those need `country_emissions` and
`emission_targets`, which have no data at all. The next unit of work that actually advances a phase
objective is ST03 and ST04 for the EU27 markets — not more sales sources.

## 3. Stages

| Stage | Phases served | Status | Last activity | Latest output | Figures |
|---|---|---|---|---|---|
| [ST01 targets](stages/st01-targets-and-provenance.md) | PH1, PH4 | Partial — set named by direction, §6.3 criteria not yet evaluated, `B-03` open | 2026-09-04 | none (`target_set.csv` not written) | — |
| [ST02 `sales`](stages/st02-06-datasets.md) | PH1, PH4 | In progress — 3 of 6 sources processed | 2026-09-03 | `sales_eea_eu27_2024.csv` (1,286 rows), `sales_kia_ir_2026.csv` (287), `sales_hyundai_plant_2025.csv` (113) | `[compute]` |
| [ST03 `country_emissions`](stages/st02-06-datasets.md) | PH1, PH4 | **Not started — no raw data** | — | none | — |
| [ST04 `emission_targets`](stages/st02-06-datasets.md) | PH1, PH2, PH4 | **Not started — no raw data** | — | none | — |
| [ST05 `vehicle_usage`](stages/st02-06-datasets.md) | PH1, PH2 | Raw held, not processed | 2026-09-03 | `raw/destination_eu27_inputs.json` | — |
| [ST06 `vehicle_technology`](stages/st02-06-datasets.md) | PH1, PH2 | In progress — EEA certified values done; correction and utility factor unsourced | 2026-09-03 | `vehicle_technology_eea_2024.csv` (177 rows) | `[compute]` |
| [ST07 provenance](stages/st01-targets-and-provenance.md) | all | In progress — catalogue and assumptions established | 2026-09-04 | `toolbox/catalogue.md`, `toolbox/assumptions.md` | — |
| [ST08 benchmark](stages/st08-10-analysis.md) | PH1, PH2, PH4 | In progress, EU27 only — specification written, inputs incomplete, no script | 2026-09-04 | none | — |
| [ST09 impact](stages/st08-10-analysis.md) | PH1, PH2, PH3, PH4 | In progress, EU27 only — specification written, no script | 2026-09-04 | none | — |
| [ST10 aggregation](stages/st08-10-analysis.md) | PH1, PH3, PH4 | In progress, EU27 only — specification written, no script | 2026-09-04 | none | — |
| [ST11 verification](stages/st11-verification.md) | all | Not started; regression baseline identified (`SRC-24`) | 2026-09-04 | none | — |
| [ST12 methodology](stages/st12-15-outputs.md) | PH1, PH2, PH4, PH5 | Not started; three methodology documents in place as inputs | — | none | — |
| [ST13 tool and dashboard](stages/st12-15-outputs.md) | PH3, PH5 | Not started; `B-08` open | — | none | — |
| [ST14 publication](stages/st12-15-outputs.md) | PH1, PH2, PH4, PH5 | Not started | — | none | — |
| [ST15 sector onboarding](stages/st12-15-outputs.md) | PH3, PH4, PH5 | Not started | — | none | — |

No figure anywhere in this project is `[verified]`. The archived EU27 2024 published results are
**prior work** (`SRC-24`) and count as a regression baseline, never as a current result.

## 4. Objective coverage

| Phase objective | Evidenced by | Verdict |
|---|---|---|
| PH1/1 targets fixed | ST01 | partial — named, criteria unevaluated |
| PH1/2 inputs acquired and registered | ST02, ST06, ST07 (done in part); ST03, ST04, ST05 | partial |
| PH1/3 reference benchmark built | ST08 | **unserved** — blocked on ST03 and ST04 |
| PH1/4 impact built | ST09 | **unserved** — blocked on ST08 |
| PH1/5 aggregated to country and company | ST10 | **unserved** — blocked on ST09 |
| PH1/6 verified | ST11 | **unserved** |
| PH1/7 published | ST14 | **unserved** |
| PH2/1–7 | ST12, ST14 | **unserved** |
| PH3/1–4 | ST13 | **unserved** |
| PH4/1–4 | ST15 and the sector runs | **unserved** |
| PH5/1–5 | ST14 | **unserved** |
| Rolling portfolio TI (whitepaper §3.8, the "primary disclosure metric") | ST10 | **unserved and unservable** on one cohort — see `F-07` |

## 5. Deliverable coverage

| id | Deliverable | Stage | Status | Acceptance test |
|---|---|---|---|---|
| `D-01` | Methodology white paper | ST12, ST14 | Not started | Not run |
| `D-02` | Automotive case study | ST14 | Not started; inputs in progress | Not run |
| `D-03` | Power generation case study | ST15, ST14 | Not started — same Month 7 milestone as `D-02` (`F-03`) | Not run |
| `D-04` | Shipbuilding case study | ST15, ST14 | Not started | Not run |
| `D-05` | Climate Arc integration specification | ST13 | Not started | Not run |
| `D-06` | Open-source TI model | ST13 | Not started; three extraction scripts exist | Not run |
| `D-07` | Final synthesis report | ST14 | Not started | Not run |
| `D-08` | Prototype dashboard public release | ST13 | Not started; `B-08` open | Not run |
| `D-09` | Policy brief | ST14 | Not started | Not run |
| `D-10` | Open dataset | ST02–ST07 | In progress; IR workbook redistribution not cleared | Not run |

## 6. Process conformance

| Stage | Process document | Deviations and open items |
|---|---|---|
| ST02–ST06 | [`process/dataset-acquisition.md`](process/dataset-acquisition.md) | Processed tables are one file per source, by design. **Open:** the three sales tables carry `source_file` but no `source_id` — `N-03` is satisfied only through the raw-file hash in `method.md`; decide whether the column is added or the schema states the join |
| ST02, ST06 | as above | **Open:** `sales/method/method.md` lists `wholesale` where the data uses `plant_sales`; `vehicle_technology/method/method.md` specifies `energy_kwh_100km` where the data uses `energy_wh_km`. The method files are the ones to change |
| ST01, ST07 | [`process/general.md`](process/general.md) plus the stage sections | Sufficient at current scope |
| ST08–ST15 | Deferred, written at stage entry | Declared deviation from one-document-per-stage, with reasons, in `process/general.md` §9 |
| all | `process/general.md` §8 | Fingerprint-based refresh is specified but not yet instrumented; no state file exists because nothing downstream has run |

## 7. Alignment findings

From the 2026-09-04 conformance pass against the proposal.

| # | Finding | Charter id | Verdict | Action | Owner |
|---|---|---|---|---|---|
| F-01 | Crossover Points are promised as P10/P50/P90 ranges; the methodology gives three deterministic scenarios plus parameter-by-parameter sensitivity, and no propagation method exists | `C-05`, `B-07` | gap | Build a propagation procedure in PH2/3, or renegotiate the wording | `climate-risk-modeller`, then `consultant` |
| F-02 | Four automotive exporters against a six-firm bound across three sectors | `C-11`, `B-03` | drift | Decide: six per programme or two per sector, through change control | `consultant` |
| F-03 | The power generation case study shares the Month 7 milestone with automotive, while automotive absorbs all capacity | `D-03` | unpriced | Sequence explicitly with Climate Arc or accept a milestone slip in writing | `consultant` |
| F-04 | The United States has no active NDC, so it has no S2 benchmark; the substitution rule is unmade | `B-04` | gap | Decide the rule before ST08 runs on any non-EU market | `climate-risk-modeller` |
| F-05 | United States and Australian volumes at model × powertrain level may be unobtainable on public data | `C-08`, `X-02` | gap | Prove a public route or drop the markets from the headline | `data-collector` |
| F-06 | "Crossover Point modelling framework" is a Month 7 activity but had no stage in the five-step direction | `D-01`, `D-02` | resolved in design | Now an explicit ST09 output | `research-director` |
| F-07 | Rolling portfolio TI is the whitepaper's primary disclosure metric and needs T cohorts; one cohort is held | `D-02` | gap | Acquire 2022 and 2023 snapshots, or state single-cohort scope in every output | `data-collector`, `result-reporter` |
| F-08 | Schema and method files disagree on two column definitions; sales tables carry no `source_id` | `N-03` | gap | Reconcile in the method files (see §6) | `developer`, `provenance-auditor` |
| F-09 | `D-08` requires validation across three case-study sectors, so PH3 cannot exit on automotive alone | `D-08` | aligned, dependency | PH4 is a hard dependency of PH3's exit, recorded in both phase documents | `research-director` |
| F-10 | No project start date, so no milestone can be dated | `B-01` | gap | Obtain from the grant agreement | `consultant` |
| F-11 | The Technical Advisory Group is not convened while the methodology-design and pilot stages are live | `C-07`, `B-06` | gap | Convene, or record the obligation as at risk | Project lead |

## 8. Drift and risk

- **Activity with no objective behind it:** the Kia and Hyundai IR tables. Both are processed, and
  neither can produce a country-level TI as it stands — Kia reports regions, Hyundai reports
  plant-side sales. They are useful for later acquisition and for Level 2 context, but further work
  on them does not advance a PH1 objective while `country_emissions` and `emission_targets` are
  empty.
- **Objective with no activity:** PH1/3 and PH1/4, the benchmark and the impact — the two
  objectives the case study actually exists to satisfy. They need ST03 and ST04, which have no data.
- **Risk — sequencing:** `D-02` and `D-03` share Month 7. One sector is live, one has not started
  (`F-03`).
- **Risk — accumulating unavailability:** at present the EU27 run would withhold PHEV units (no
  utility factor), leave combustion values uncorrected (no ICCT factors registered), and rest on a
  proxied distance for most units. Each is disclosed and each is individually defensible; together
  they make the first result a **direction with a coverage ratio**, not a magnitude, and the case
  study's claims must be written that way from the start.
- **Risk — verification debt:** no figure is verified and no verification procedure has run once.
  ST11 should be exercised on the first EU27 benchmark, not saved for the phase gate.
