# ST05 — Engine run

## Main goal

Join the reconciled cohort to the destination inputs, run the lifetime TI computation under S1, S2
and S3, and produce the four required outputs with their mandatory decompositions and sensitivity
bands.

## Activity

Build the run input from the published records; execute the engine; produce `TI_gap` series,
per-product cumulative TI, cohort TI, the annual time-series, the decomposition by destination and
product type, the crossover years, and the sensitivity sweeps (T ± 3, UF ± 0.15, real-world
correction range, scenario band). Assert the decomposition identity before anything leaves the
stage. Where the tier-C share crosses the threshold, suppress magnitudes and publish direction.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH1 | 3 | The published lifetime results for both cohorts with per-cell decomposition |
| PH3 | 1, 2, 3 | Rolling portfolio from multi-year cohorts; PHEV and FCEV inclusion |
| PH4 | 3, 4 | The new sector's cohort result; shipping boundary sensitivity as two runs |
| PH5 | 3, 6 | The runs that quantify tier-C uncertainty propagation and the benchmark non-linearity error |

## Inputs

Consumes: ST02 cohort records, ST03 Layer 1 fields, ST04 Layer 2 parameters; the engine code under
`ti-framework/ti_framework/`; the scenario configuration; assumptions `A-01`…`A-04`, `A-15`.

## Outputs

Produces: `data/published/lifetime_results.json`, `cohort_comparison.json`, and the per-cohort run
bundle written by `lifetime_run.py` (run input, result CSVs, the data-quality declaration, charts).

Consumed by: ST06, ST07, ST09.

## Methodology

[`../toolbox/methods/aggregation-and-comparison.md`](../toolbox/methods/aggregation-and-comparison.md)
and [`../toolbox/methods/uncertainty-and-sensitivity.md`](../toolbox/methods/uncertainty-and-sensitivity.md).
Governing text: Whitepaper §3.3–3.8 (`W-04`…`W-09`), Guideline §4, §5.2 (`G-08`, `G-09`).

## Owner agents

Owner `data-scientist`, with `developer` for the run harness.
Review chain: `math-reviewer` (identity, summation convention, sign convention) → `tester` →
`reviewer`.

## When to stop

- All three scenarios present; S2 never alone (`G-08`).
- `TI_cohort = Σ_country = Σ_powertrain` holds to the declared tolerance (`W-07`).
- Annual series has exactly T terms, `t = 0…T−1` (`W-05`).
- Every mandatory sensitivity in `G-09` is computed.
- Every cell with a missing input is recorded as missing, never zero (`C-05`).
- The data-quality declaration is generated from the engine payload, not written by hand (`G-10`).

## When to repeat

- Any upstream input changes — a benchmark rate, a product parameter, a cohort row, an assumption.
- The engine, its scenario configuration, or a method file changes.
- A new scenario definition or a new sensitivity requirement is adopted.

Every re-run reverts the affected figures to unverified until independently re-derived, and every
phase objective those figures evidence is re-judged rather than carried forward.

## Backward moves

- Decomposition identity fails → ST05 is not at fault by default: check the join first (ST02), then
  the aggregation code. Never reconcile by adjusting a total.
- Rolling portfolio produced from a single repeated cohort → stop and withhold; this is a
  counterfactual, not a result (charter exclusion).
- Tier-C share above the threshold → the run completes but publishes direction only (`C-09`); if
  that is unacceptable for the deliverable, the move is back to ST01/ST04 for better inputs, not to
  a looser threshold.

## Process

[`../process/st05-engine-run.md`](../process/st05-engine-run.md)
