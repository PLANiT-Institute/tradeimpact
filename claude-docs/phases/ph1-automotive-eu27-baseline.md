# PH1 — Automotive EU27 2024 baseline

## Purpose

Prove that the framework runs end to end on evidence: one sector, one cohort year, two firms, one
shared destination and product boundary, with every destination-side input sourced and every
un-sourced quantity withheld rather than filled. PH1 is the existence proof for the whole
engagement — until a lifetime TI existed that survived full recomputation, every later phase was
speculative.

## Objectives

1. Establish observed cohorts for two firms on **one** destination × commercial-name × powertrain
   boundary, with mapping coverage reported per firm.
2. Source every destination-side input — annual distance, operating life, fleet benchmark base,
   grid intensity, and S1/S2/S3 transport and power pathways — for all 27 destinations, each with a
   tier and a stated derivation.
3. Compute lifetime TI under all three scenarios with the mandatory country and powertrain
   decompositions, and the per-cohort annual time-series.
4. Publish with a data-quality declaration, a disclosed target-hierarchy level, and an explicit
   withheld list carrying unit counts.
5. Make the published set reproducible from pinned snapshots by full recomputation.

## Deliverables

| Charter id | Artefact | Format | Acceptance test | Milestone |
|---|---|---|---|---|
| `D-01` | Observed cohorts | `data/published/product_cohorts.json` | Rows reconcile to registration totals per firm; coverage stated | 2026-08-05 |
| `D-01` | Destination inputs | `data/published/destination_inputs.json` | 27/27 destinations, zero missing required fields, tier + derivation per value | 2026-08-09 |
| `D-01` | Lifetime results | `data/published/lifetime_results.json` | S1/S2/S3 present; `TI_cohort = Σ_country = Σ_powertrain`; annual series length T | 2026-08-09 |
| `D-01` | Readiness decision | `data/published/impact_readiness.json` | Decision and reason derived from the input records, not hardcoded | 2026-08-09 |
| `D-01` | Public report | `web/` `/impact`, `/analysis/<firm>`, `/compare/automotive` | Every status string derived from the dataset; declaration rendered from the engine payload | 2026-08-11 |

## Entry criteria

- Whitepaper v1.5 and Automotive Guideline v1.8 accepted as the truth source.
- Engine implementing `W-02`…`W-09` with the theory↔code↔test link in place (`C-08`).
- At least one registration source reachable and pinnable.

## Exit criteria

- [x] `scripts/check_sync.py` passes — every anchored rule has code and a test.
- [x] `data-pipeline/check_published.py` passes — the whole published set recomputes from the
      committed snapshots (tolerance 1e-12).
- [x] Engine test suite green.
- [x] `impact_readiness.json` shows `missing_required_inputs: []` for both cohorts and a publication
      decision derived from the records.
- [x] Headline appears nowhere without both decompositions and the S1/S2/S3 band.
- [x] Withheld outputs (PHEV, FCEV, rolling portfolio) listed with unit counts and reasons.
- [x] Tier-C exposure declared and magnitude suppression active where the threshold is crossed
      (`C-09`).

Gate verdict and the evidence behind each check: [`../tracker.md`](../tracker.md).

## Stages serving this phase

| Stage | Evidences objective |
|---|---|
| [ST01 source acquisition](../stages/st01-source-acquisition.md) | 1, 2, 5 |
| [ST02 source reconciliation](../stages/st02-source-reconciliation.md) | 1, 4 |
| [ST03 benchmark construction](../stages/st03-benchmark-construction.md) | 2 |
| [ST04 product parameterisation](../stages/st04-product-parameterisation.md) | 2 |
| [ST05 engine run](../stages/st05-engine-run.md) | 3 |
| [ST06 verification gates](../stages/st06-verification-gates.md) | 5 |
| [ST09 publication](../stages/st09-publication.md) | 4 |

## Traceability

Discharges `W-01`…`W-08`, `W-12`, `W-14`, `W-15`, `W-16`, `W-22`, `G-01`…`G-03`, `G-05`…`G-14`,
`C-01`…`C-05`, `C-07`, `C-08`, `C-09`. Deliberately **does not** discharge `W-09` (rolling
portfolio) or `W-11`/`M-02` (Level 2) — those are PH3, and the withholding is itself an exit
criterion here.

## What would invalidate this phase

- The EU domestic-transport pathway proving unusable as a passenger-car sector proxy (`C-03` level
  2 collapsing to level 5 context-only) — the S2 benchmark, and therefore the sign of the headline,
  rests on it.
- The 13 proxy-VKT destinations proving to change the direction, not just the magnitude. The
  recorded sensitivity says the sign holds across the measured-country quartile band; a wider band
  would return this phase to ST03.
- Any published figure failing to trace to a snapshot row or a numbered assumption — this returns
  the work to ST02 and blocks all downstream phases.
