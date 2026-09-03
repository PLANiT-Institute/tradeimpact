# ST02 — Source reconciliation

## Main goal

Convert pinned snapshots into normalised, tiered, reconciled input records in which every value
carries its unit, key, source, tier and derivation — and every gap is an explicit missing marker
rather than an absence.

## Activity

Aggregate snapshot rows onto the analysis keys (destination × product × powertrain × cohort year);
reconcile the aggregate back to the source total and fail on mismatch; assign the data tier per
`W-14`; assign the destination target-hierarchy level per `C-03`; write the derivation sentence for
every derived value; and record every unresolved input in the readiness record with its reason.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH1 | 1, 4 | 1,286 destination × commercial-name × powertrain rows reconciled to the registration totals; readiness record derived from the input records |
| PH2 | 1, 2 | The normalised records are the rows the research database is built from |
| PH3 | 1, 4, 5 | Multi-year cohort comparability; per-destination target level; origin mapping status |
| PH4 | 2, 3 | Sector cohort reconciliation without hidden allocation |

## Inputs

Consumes: ST01 snapshots; catalogue and register rows; the tier definitions in `W-14`; the target
hierarchy in `C-03`; the powertrain classification rule (`A-13`).

## Outputs

Produces: `data/published/product_cohorts.json`, `destination_inputs.json`, `pathways.json`,
`impact_readiness.json`, `sources.json` — plus new or amended rows in
[`../toolbox/data/assumptions.md`](../toolbox/data/assumptions.md) for every fallback used.

Consumed by: ST03, ST04, ST05, ST07.

## Methodology

[`../toolbox/methods/tiering-and-target-hierarchy.md`](../toolbox/methods/tiering-and-target-hierarchy.md).
Evidence-class and publication-boundary rules: `docs/evidence-audit.md`,
`data-pipeline/sectoral-sources.md` §4.

## Owner agents

Owner `source-reconciliation-analyst`.
Review chain: `provenance-auditor` (every value traces to a source row) → `reviewer` → `auditor`.

## When to stop

- Every aggregate reconciles to its source total within the declared tolerance.
- Every value has a unit, a key, a source id, a tier and a derivation sentence.
- Every required input is either present or listed in `missing_required_inputs` with a reason.
- Every fallback has a numbered assumption id.

## When to repeat

- ST01 delivers a new or corrected snapshot.
- A tier or target-level assignment is challenged.
- A new destination, product type or cohort year enters scope.
- An assumption is retired or re-sourced (the derivation sentence changes even when the number does
  not).

## Backward moves

- Reconciliation mismatch → ST01: the snapshot or the query is wrong, not the aggregation.
- A required input with no source at any tier → the phase's exit criteria: the honest output is a
  withheld result with a unit count (`C-04`, `C-05`), which is a phase-level decision, not a stage
  workaround.
- A value that can only be produced by relabelling a proxy as a country target → stop and escalate;
  `C-03` makes this a hard failure.

## Process

[`../process/st02-source-reconciliation.md`](../process/st02-source-reconciliation.md)
