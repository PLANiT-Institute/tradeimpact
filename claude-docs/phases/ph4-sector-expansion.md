# PH4 — Sector expansion: power, then shipping

## Purpose

The framework claims to apply to any sector where firms sell energy-using products operating over
multi-year lifetimes in defined markets (`W-17`). That claim is currently untested: automotive is
the only cohort pilot, and the JERA, KOEN and MOL snapshots are current-period evidence, not
cohorts. PH4 tests the claim on one more sector under the acceptance gates already written in
`docs/sector-expansion.md`, and in doing so tests whether the shared object — company × product ×
destination × cohort — survives a change of physical units.

Order is fixed by `docs/sector-expansion.md`: power generation, then shipping.

## Objectives

1. Written destination and service boundary for power generation, with the Layer 1 benchmark source
   named per market and the aggregation level decided at technology rather than company level
   (`M-06`, Guideline App. E).
2. An observed power cohort: commissioned capacity or delivered MWh by technology and connected
   grid, with mapping coverage — not a company-level average.
3. Power pilot passing all eight acceptance gates in `docs/sector-expansion.md`, including the test
   that missing required inputs block results.
4. Shipping boundary study: flag-state versus voyage-weighted attribution, with the TI sensitivity
   to that choice as the headline output (`M-05`).
5. A cross-sector view that compares coverage, availability, evidence quality and direction —
   without adding incompatible units into one score (`C-06`).

## Deliverables

| Charter id | Artefact | Format | Acceptance test | Milestone |
|---|---|---|---|---|
| `D-06` | Power sector method note | `claude-docs/toolbox/methods/` file | Boundary, service unit, benchmark source, aggregation level, and failure modes stated with citations | PH4 entry |
| `D-06` | Power cohort | Pinned snapshot + published JSON | Company × technology × connected grid × cohort year resolved; coverage stated; no hidden allocation | PH4 gate |
| `D-06` | Power lifetime result | Published JSON + web | S1/S2/S3 + decomposition by market and technology; declaration present; asset-level rather than company-average comparison | PH4 gate |
| `D-06` | Shipping boundary sensitivity | Method note + result | TI computed under both boundary treatments; the difference reported as the finding | PH4 gate |

## Entry criteria

- PH2 exit met — a new sector's figures must be resolvable in the research database on the same
  terms as automotive.
- A written sector method note exists **before** any number is computed (methodology discipline:
  the method precedes the deliverable).
- For power: the KOEN generation-intensity problem recorded in `data-pipeline/sectoral-sources.md`
  §2 (gross/net basis unstated, plant rows not reconciling with reported totals) is either resolved
  with the source or the firm is deferred. It is not estimated.

## Exit criteria

- [ ] All eight `docs/sector-expansion.md` acceptance gates evidenced for power, each with the
      artefact that evidences it.
- [ ] At least two companies and two destination geographies assessable without hidden allocation
      before the sector is called *supported* — one company is a pilot, not a sector.
- [ ] A missing-input test proves the readiness gate closes for the new sector, not only for
      automotive.
- [ ] Technology-level decomposition mandatory in every power output; no company-level-only
      comparison published (`M-06`).
- [ ] Shipping boundary sensitivity published, with the boundary rule either chosen and justified
      or explicitly left open with the measured cost of the ambiguity.
- [ ] No cross-sector arithmetic that adds gCO₂/km, kgCO₂e/MWh, gCO₂e/t-nm or tCO₂e/t.

## Stages serving this phase

| Stage | Evidences objective |
|---|---|
| [ST11 sector onboarding](../stages/st11-sector-onboarding.md) | 1, 3, 5 |
| [ST01 source acquisition](../stages/st01-source-acquisition.md) | 2, 4 |
| [ST02 source reconciliation](../stages/st02-source-reconciliation.md) | 2, 3 |
| [ST03 benchmark construction](../stages/st03-benchmark-construction.md) | 1, 4 |
| [ST04 product parameterisation](../stages/st04-product-parameterisation.md) | 2 |
| [ST05 engine run](../stages/st05-engine-run.md) | 3, 4 |
| [ST06 verification gates](../stages/st06-verification-gates.md) | 3 |
| [ST09 publication](../stages/st09-publication.md) | 3, 4, 5 |
| [ST10 methodology development](../stages/st10-methodology-development.md) | 1, 4 |

## Traceability

Discharges `W-17` (sector coverage claim), `W-10` (operations outside national jurisdiction),
`C-06`, and the sector halves of `M-05` and `M-06`.

## What would invalidate this phase

- The engine's automotive physics proving not separable from the core aggregation. `W-17` asserts
  the core formulas apply unmodified; if power requires changes inside `core/`, that is a framework
  finding that returns to PH5 before any power number is published.
- A power cohort that can only be assembled at company-average level. Aggregation masking is
  exactly the failure `M-06` predicts, and publishing it would demonstrate the framework's weakness
  as if it were a result.
- Shipping proving to have no defensible operating-country analogue, in which case the honest output
  is `M-05` restated as a bounded limitation and the sector deferred — not a flag-state number
  presented as a destination result.
