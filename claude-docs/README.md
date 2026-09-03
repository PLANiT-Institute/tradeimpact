# Research governance — Trade as a Climate Amplifier

The governance set for the Climate Arc grant *Trade as a Climate Amplifier — A Framework to
Quantify the Climate Impact of Global Trade* (PLANiT, 12 months). Every document is reachable from
this page. Twenty-three documents, about 2,200 lines; a full read is roughly twenty minutes.

**The truth source is the grant proposal**, not this set. Where they disagree, the proposal wins
and [`charter.md`](charter.md) is wrong. The methodology truth source is `methodology/` in the
repository; nothing here restates its equations.

## Start here

| Document | What it answers |
|---|---|
| [`charter.md`](charter.md) | What was promised: purpose, the TI formula as the proposal states it, deliverables `D-01`–`D-10`, obligations `C-01`–`C-14`, exclusions `X-01`–`X-08`, non-negotiables `N-01`–`N-09`, and the eight open blockers |
| [`tracker.md`](tracker.md) | Where the work is, and whether it is moving a phase objective. Current state only |
| [`log/README.md`](log/README.md) | What was decided and when — append-only |

## Phases — why the work exists

| Phase | Purpose | Deliverables |
|---|---|---|
| [PH1 automotive case study](phases/ph1-automotive-case-study.md) | The five-step process on the automotive sector — the live phase | `D-02`, `D-10` |
| [PH2 methodology white paper](phases/ph2-methodology-white-paper.md) | Peer-reviewable methodology; close or bound the open challenges | `D-01` |
| [PH3 model and dashboard](phases/ph3-model-and-dashboard.md) | Make it operable by someone who is not its author | `D-05`, `D-06`, `D-08` |
| [PH4 power and shipbuilding](phases/ph4-power-and-shipbuilding.md) | Test whether the framework is sector-agnostic in practice | `D-03`, `D-04` |
| [PH5 synthesis and release](phases/ph5-synthesis-and-release.md) | Publish everything openly; policy brief; knowledge transfer | `D-07`, `D-08`, `D-09` |

## Stages — what is actually done

Stages serve phases many-to-many: one data stage serves several phases, and one phase needs
several stages. Fifteen stages in four documents.

| Document | Stages |
|---|---|
| [`stages/st01-targets-and-provenance.md`](stages/st01-targets-and-provenance.md) | ST01 target selection · ST07 source registration |
| [`stages/st02-06-datasets.md`](stages/st02-06-datasets.md) | ST02 `sales` · ST03 `country_emissions` · ST04 `emission_targets` · ST05 `vehicle_usage` · ST06 `vehicle_technology` — each with how it is gathered, processed and analysed |
| [`stages/st08-10-analysis.md`](stages/st08-10-analysis.md) | ST08 reference benchmark · ST09 impact computation · ST10 country and company aggregation |
| [`stages/st11-verification.md`](stages/st11-verification.md) | ST11 verification — the gate on every stage exit |
| [`stages/st12-15-outputs.md`](stages/st12-15-outputs.md) | ST12 methodology · ST13 tool and dashboard · ST14 publication · ST15 sector onboarding |

## Process — how it is done

| Document | Contents |
|---|---|
| [`process/general.md`](process/general.md) | The invariants: the stage loop, data handling, referencing, verification, integrity, the dependency graph and the refresh rule |
| [`process/dataset-acquisition.md`](process/dataset-acquisition.md) | The live procedure for ST02–ST06: raw → script → processed, with its failure modes |

## Toolbox — what makes the process runnable

| Document | Contents |
|---|---|
| [`toolbox/data-schema.md`](toolbox/data-schema.md) | The consolidated processed-data structure: every file, every column with type, unit and allowed values, and the join keys |
| [`toolbox/catalogue.md`](toolbox/catalogue.md) | Every source: what is held, what is missing, access route, data level, licence, and what each gap costs |
| [`toolbox/assumptions.md`](toolbox/assumptions.md) | Every assumption, numbered, cited, with the direction of the bias it introduces |
| [`toolbox/references-and-archive.md`](toolbox/references-and-archive.md) | The methodology documents, the dataset method files, the key reference documents, and the reusable prior work in `archive/` |

## Team and records

| Document | Contents |
|---|---|
| [`team/roster.md`](team/roster.md) | Agent per stage, review chains, what can run in parallel, and the two capabilities still without an owner |
| [`engagement/README.md`](engagement/README.md) | The client-facing record — `consultant` only, drafts only |
| [`dashboard/README.md`](dashboard/README.md) | Generated progress views — `report-manager` only |

## How this set is kept honest

- **Three files at the root**, always: this index, the charter, the tracker.
- **One concern per document, one home per fact.** Phase and stage documents are specifications;
  the tracker holds status; the log holds history. Sources and dataset rules live in
  `data/auto/<dataset>/method/method.md`; equations live in `methodology/`. A fact copied into a
  second document will be wrong within a week.
- **Every figure traces** to a source in the catalogue or a numbered assumption. A figure with
  neither does not exist.
- **Build one thing when it is needed.** At 2026-09-04 that means: raw data and extraction scripts
  for `sales` and `vehicle_technology` exist; no model, dashboard or database does, and this set
  does not pretend otherwise.
