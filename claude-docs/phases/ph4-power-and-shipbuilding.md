# PH4 — Power generation and shipbuilding case studies

## Purpose

Test whether the framework is sector-agnostic in practice, not only in claim. Power generation
is a **primary** validation vehicle alongside automotive and shares its Month 7 milestone;
shipbuilding is cross-validation at Month 10 (`X-08`). Each sector stresses a structural
challenge the automotive case cannot reach: power tests grid attribution and mixed-portfolio
aggregation masking (challenges Challenge 6), shipping tests the operating-country boundary
itself (Challenge 5).

## Objectives

1. **Sector guidelines drafted.** A power Technical Guideline and a shipping Technical Guideline
   exist to the standard of the automotive guideline: Layer 1 benchmark specification, Layer 2
   parameters, lifetime T, and operating-country data sources.
2. **Power case study delivered.** One Korean and one Japanese power company with deliberately
   mixed portfolios, benchmarked at technology level with mandatory decomposition, isolating the
   aggregation-masking effect.
3. **Shipbuilding case study delivered.** One Korean and one Japanese shipbuilder run under two
   boundary treatments — flag-state and voyage-weighted — with the TI sensitivity to the boundary
   choice as the headline output.
4. **Firm count reconciled.** The six-firm bound (`C-11`) holds across all three sectors, or the
   change is agreed through change control (`B-03`).

## Deliverables

| Charter id | Artefact | Format | Acceptance test | Milestone |
|---|---|---|---|---|
| `D-03` | Power generation case study | Working paper + open dataset + open-source model | Results documented and publicly available; technology-level decomposition present | Month 7 |
| `D-04` | Shipbuilding case study | Open-source GitHub repository | Both boundary treatments run; sensitivity to the boundary choice reported | Month 10 |

## Entry criteria

- The five-step process is proven once in PH1 — at minimum objectives 3 and 4 met — so the
  sector onboarding reuses a working pipeline rather than debugging two at once.
- Sector Layer 1 anchors identified: national power-sector pathway for power; IMO GHG Strategy
  Carbon Intensity Indicator trajectory for international shipping (whitepaper §6).
- Target firms selected within the `C-11` bound.

## Exit criteria

- [ ] Power: technology-level benchmarking rule stated and applied; company-level-only comparison
      not used (guideline Appendix E).
- [ ] Power: cross-border interconnection attribution rule stated with measured sensitivity.
- [ ] Shipping: boundary rule stated, with the TI sensitivity to the alternative measured.
- [ ] Both sectors: S1/S2/S3 reported together, decomposition present, tiers declared, withheld
      units counted.
- [ ] Both sectors run through [`st11`](../stages/st11-verification.md); no headline left
      `[compute]`.
- [ ] Challenges 5 and 6 moved from skeleton to either a stated rule or a bounded limitation.

## Stages serving this phase

| Stage | Evidences objective |
|---|---|
| [`st15`](../stages/st15-sector-onboarding.md) | 1, 4 |
| [`st01`](../stages/st01-target-selection.md) | 4 |
| [`st02`](../stages/st02-sales-data.md) … [`st07`](../stages/st07-source-registration.md) | 2, 3 (sector equivalents of the five datasets) |
| [`st08`](../stages/st08-benchmark-construction.md) | 2, 3 |
| [`st09`](../stages/st09-impact-computation.md) | 2, 3 |
| [`st10`](../stages/st10-country-aggregation.md) | 2, 3 |
| [`st11`](../stages/st11-verification.md) | 2, 3 |
| [`st14`](../stages/st14-publication.md) | 2, 3 |

## Traceability

`D-03`, `D-04`, `C-08`, `C-11`, `X-08`, and `D-08`'s three-sector validation requirement.

## What would invalidate this phase

- **The operating-country boundary does not survive maritime.** If TI is materially sensitive to
  the flag-versus-voyage choice with no defensible rule, the framework's geographic boundary — a
  whitepaper §4.1 premise — is in question, and the work returns to PH2.
- **Aggregation masking cannot be prevented.** If a mixed power portfolio's company-level TI hides
  assets on both sides of the benchmark even with decomposition, the disclosure unit itself has to
  change before `D-03` can claim practical utility.
- **Month 7 is not reachable for power** while automotive absorbs the capacity. That is a
  sequencing conflict with `D-03`, not a detail; it is carried as an open finding in
  [`../tracker.md`](../tracker.md).
