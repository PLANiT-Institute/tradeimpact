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
| 2026-09-04 | ST05 `vehicle_usage` | Raw acquired, not processed | Archived EU27 snapshot copied into `raw/` | Processing waits on ST08's need for it |

Backward moves are recorded here with the same weight as forward ones. A finding that invalidates a
premise and sends work back is the process working; the entry states the trigger and what it cost.
