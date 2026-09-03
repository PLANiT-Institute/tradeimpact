# PH3 — Open-source model, dashboard and Arc integration

## Purpose

Make the methodology operable by someone who is not its author. The proposal promises an
open-source TI model on GitHub (`D-06`), a prototype dashboard released publicly and
"validated against the three case study sectors" (`D-08`), and a specification for TI as an
additional analytical layer on Climate Arc's Transition Arc (`D-05`). Nothing in this phase has started: at 2026-09-04 there is no model beyond the extraction scripts,
no dashboard and no database, and each is built only when the step before it has an output to
package. The test of this phase is replication without the research team: "researchers, national statistics agencies, and data
providers can replicate and extend the framework without any involvement from the original
research team."

## Objectives

1. **Model runs end to end.** `script/auto/` reproduces the case-study result set from raw
   inputs, deterministically, with tests covering each equation it implements.
2. **Dashboard functional.** The prototype presents result, decomposition, scenario spread,
   crossover, sensitivity and data-quality declaration for each case-study sector, and reads
   only published outputs — never a hand-typed number (`N-03`).
3. **Integration specification written.** `D-05` states the data contract, the layer boundary
   and what Transition Arc would consume (`C-09`).
4. **Release hygiene clean.** GPL v3, open dataset, reproducible build, and a licence check on
   every redistributed source (`C-01`, `C-02`).

## Deliverables

| Charter id | Artefact | Format | Acceptance test | Milestone |
|---|---|---|---|---|
| `D-06` | Open-source TI model | GitHub repository, GPL v3 | Runs the case studies from registered sources; tests pass | Month 10 |
| `D-05` | Climate Arc integration specification | Specification document | Data contract and layer boundary specified against Transition Arc | Month 10 |
| `D-08` | Prototype dashboard public release | Open-source tool | "fully functional and validated against the three case study sectors, with results documented and made publicly available" | Month 12 |

## Entry criteria

- PH1 objective 5 met for at least one exporter-importer pair, so there is a result set to
  present.
- `B-08` resolved: rebuild from `data/auto/output/` or resurrect the archived web application.
- Licence terms of every redistributed source recorded in
  [`../toolbox/catalogue.md`](../toolbox/catalogue.md).

## Exit criteria

- [ ] A clean clone reproduces the published outputs byte-identically (`N-08`).
- [ ] Every dashboard figure resolves to a `source_id` or an assumption id.
- [ ] Dashboard shows S1/S2/S3 together and refuses to render a single-scenario headline
      (`N-05`), and shows the decomposition alongside every headline (`N-06`).
- [ ] No source is redistributed whose licence does not permit it — cleared by
      `provenance-auditor`.
- [ ] `D-05` reviewed by `consultant` before it reaches Climate Arc.
- [ ] Three sectors present, or the shortfall stated plainly against `D-08`'s wording.

## Stages serving this phase

| Stage | Evidences objective |
|---|---|
| [`st13`](../stages/st12-15-outputs.md) | 1, 2, 3, 4 |
| [`st09`](../stages/st08-10-analysis.md) | 1 (the computation being packaged) |
| [`st10`](../stages/st08-10-analysis.md) | 2 (what the dashboard presents) |
| [`st11`](../stages/st11-verification.md) | 1, 4 |
| [`st07`](../stages/st01-targets-and-provenance.md) | 4 (licence clearance) |

## Traceability

`D-05`, `D-06`, `D-08`, `C-01`, `C-02`, `C-09`, `C-14`(b).

## What would invalidate this phase

- **`D-08` requires three sectors.** A dashboard validated on automotive alone does not meet the
  acceptance wording, so PH4 is a hard dependency of this phase's exit, not a parallel option.
- **A source that cannot be redistributed.** If a licence forbids republishing an input, the open
  dataset (`C-02`) and the dashboard both lose that market, and the fallback must be sourced
  before release rather than after.
