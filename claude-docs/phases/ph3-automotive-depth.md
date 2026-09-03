# PH3 — Automotive depth: close the withheld outputs

## Purpose

The published automotive result is honest but incomplete, and each incompleteness is a whitepaper
requirement rather than a nicety. The rolling portfolio is named the *primary disclosure metric*
(`W-09`) and is withheld. PHEV and FCEV registrations are withheld with their unit counts. The
benchmark is a regional all-transport proxy where the contract asks for a country passenger-car
pathway (`C-03` level 2 where level 1 is wanted). Production origin is uncollected, so a project
named Trade Impact currently reports destination-cohort impact. PH3 closes what can be closed and
converts what cannot into a documented, bounded limitation.

## Objectives

1. Publish `TI_portfolio` from genuinely multi-year observed cohorts — not from a repeated single
   cohort (`W-09`, `W-18` output 3).
2. Publish PHEV results with a sourced, market-calibrated utility factor and the mandatory
   UF ± 0.15 lower bound reported alongside the central value (`G-07`, `G-09`, `M-04`).
3. Publish FCEV results with a sourced hydrogen supply intensity, or restate the withholding with
   its unit count and the specific missing source.
4. Replace the EU regional transport proxy with destination-country passenger-car or road-transport
   pathways where such a pathway exists, and record the target-hierarchy level per destination
   (`C-03`).
5. Resolve the Level 2 question: either a `V_p,c,v` matrix with an exact/estimated split per model,
   or a written finding that no public source supports it for these cohorts (`W-11`, `M-02`,
   blocker `B-06`).
6. Reduce the tier-C exposure that currently forces magnitude suppression, or state the floor below
   which it cannot fall with public data (`C-09`, `M-03`).

## Deliverables

| Charter id | Artefact | Format | Acceptance test | Milestone |
|---|---|---|---|---|
| `D-04` | Multi-year cohorts | Pinned snapshots + `product_cohorts.json` | 2022 and 2023 EEA cohorts pinned on the same boundary as 2024; reconciliation per year | PH3 gate |
| `D-04` | Rolling portfolio | `lifetime_results.json` + web | Series built from distinct observed cohorts; the single-cohort repetition path stays disabled | PH3 gate |
| `D-04` | PHEV and FCEV closure | Published JSON + declaration | UF sourced with tier and market; UF−0.15 reported beside central; H₂ intensity sourced or withholding restated | PH3 gate |
| `D-05` | Level 2 decision | Published field + method note | Either exact/estimated split per model, or a documented impossibility with the sources checked | PH3 gate |
| `D-04` | Country pathway upgrade | `destination_inputs.json` | Target level recorded per destination; no proxy relabelled (`C-03`) | PH3 gate |

## Entry criteria

- PH2 exit met: every new figure must be resolvable in the research database.
- Blockers `B-03` (EU `r_power` S2 pinned to zero) and `B-06` (Level 2 feasibility) have named
  owners.
- The tier-C suppression threshold and its rationale are settled with PH5 (`M-03`), or PH3 proceeds
  reporting direction only and says so.

## Exit criteria

- [ ] `TI_portfolio` published, or a written statement of why multi-year cohorts remain
      unobtainable — the current placeholder reason ("repeating one cohort is a counterfactual") is
      no longer sufficient once the data question has been tested.
- [ ] Every powertrain present in the observed cohorts is either computed or withheld **with a
      named missing input and a unit count**. No powertrain silently absent.
- [ ] Target-hierarchy level recorded per destination; no destination carries a proxy labelled as a
      country target.
- [ ] `check_sync.py`, the engine suite, and `check_published.py` all pass after every change.
- [ ] Every new figure resolves in the research database (PH2 rule).
- [ ] Sensitivity band published for each new parameter: T ± 3, UF ± 0.15, real-world correction
      range, S1/S2/S3 (`G-09`).

## Stages serving this phase

| Stage | Evidences objective |
|---|---|
| [ST01 source acquisition](../stages/st01-source-acquisition.md) | 1, 2, 3, 5 |
| [ST02 source reconciliation](../stages/st02-source-reconciliation.md) | 1, 4, 5 |
| [ST03 benchmark construction](../stages/st03-benchmark-construction.md) | 4, 6 |
| [ST04 product parameterisation](../stages/st04-product-parameterisation.md) | 2, 3, 6 |
| [ST05 engine run](../stages/st05-engine-run.md) | 1, 2, 3 |
| [ST06 verification gates](../stages/st06-verification-gates.md) | all |
| [ST09 publication](../stages/st09-publication.md) | all |
| [ST10 methodology development](../stages/st10-methodology-development.md) | 2, 4, 6 |

## Traceability

Discharges `W-09`, `W-11`, `W-18` (outputs 2 and 3), `G-07`, `G-09`, `C-03`, and the automotive
half of `M-02`, `M-03`, `M-04`.

## What would invalidate this phase

- EEA 2022/2023 data proving non-comparable with 2024 on the classification boundary. A portfolio
  series assembled across shifting boundaries would be worse than the current withholding, and this
  finding sends objective 1 back to ST01 with a documented stop.
- A real-world-calibrated UF that flips the PHEV sign relative to the regulatory value. That is the
  expected direction (`M-04`) and is a finding, not a failure — but it invalidates any interim PHEV
  figure published on regulatory UF.
- Country pathways proving to sit below the EU proxy in most destinations, which would move the
  headline magnitude materially and require PH1's published comparison to be reissued through
  `consultant`.
