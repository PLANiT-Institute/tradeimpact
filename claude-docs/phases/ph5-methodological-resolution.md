# PH5 — Methodological resolution

## Purpose

`methodology/TI_Methodological_Challenges_v1.md` is the intellectual spine of the programme: eight
named problems, each with a stated resolution criterion, and an adversarial principle — every case
study exists to stress a challenge until the framework holds or visibly breaks. PH5 is where those
challenges are answered with rules rather than caveats. A challenge is resolved only when a
defensible rule exists, the residual error is measured, and the whole thing is disclosed; where it
cannot be resolved, the output is a documented limitation with a bounded error, not silence.

PH5 runs alongside PH3 and PH4 rather than after them — the case studies generate the evidence, PH5
converts it into rules — but it gates its own deliverable, the consolidated response.

## Objectives

1. `M-01` — a transport-versus-economy decarbonisation differential (sector-split correction) with
   a stated derivation and a bounded residual, plus a decision rule for unquantifiable-benchmark
   markets, plus a published per-market benchmark-confidence tier. Closes blockers `B-01`, `B-02`,
   `B-05`.
2. `M-02` — a threshold rule for reporting plant-level versus producer-region attribution, tied to
   a measured allocation-error bound.
3. `M-03` — a reproducible uncertainty-propagation procedure yielding a band on the headline TI,
   and a stated tier-C share above which only direction is published. The current 50% threshold is
   a project default, not yet a derived rule.
4. `M-04` — market-calibrated UF defaults replacing the generic ± 0.15 band, and a documented
   decision on non-passenger segment coverage.
5. `M-07` — a literature-anchored positioning section separating TI from avoided-emissions and
   Scope 4, elevating the non-summation caveat (`W-21` §9.2).
6. `M-08` — the exponential-versus-S-curve benchmark error bounded by cross-validation against
   observed sector data in at least one fast-transition market.
7. Promote the engine's four build decisions (`ti-framework/NOTES.md` D1–D4) from code-level
   defaults to methodology-level rules, or replace them.

## Deliverables

| Charter id | Artefact | Format | Acceptance test | Milestone |
|---|---|---|---|---|
| `D-07` | Per-challenge resolution notes | One `claude-docs/toolbox/methods/` file per resolved challenge | Rule stated, derivation cited, residual error bounded, failure modes named, validation test named | rolling |
| `D-07` | Consolidated challenges response | Paper (the M6 synthesis) | Each of `M-01`…`M-08` carries a rule, a bounded limitation, or an explicit non-resolution with its cost | PH5 gate |
| `D-07` | Methodology change requests | Entries in `log/decisions.md` + upstream version bump | Any rule that changes a published figure routes through the refresh discipline and re-arms the verification gates | on each rule |

## Entry criteria

- The challenge document is treated as governing (`M-` ids in the charter), not as background
  reading.
- Evidence exists to test the challenge in question: `M-01`/`M-08` need live-market benchmark runs
  (PH1 gives EU; PH3 extends), `M-03` needs a tier-mixed cohort set, `M-02` needs the PH3 Level 2
  attempt, `M-05`/`M-06` need PH4.
- Every rule proposal states which published figures it would move **before** it is adopted.

## Exit criteria

- [ ] Each of `M-01`…`M-08` has a resolution note, a bounded-limitation note, or a recorded decision
      not to resolve it in this cycle — with its cost to the analysis stated.
- [ ] Two analysts handed the same firm and markets would derive the same benchmark to within the
      declared tolerance (`M-01` resolution criterion), demonstrated on at least one market.
- [ ] Blockers `B-01`, `B-02`, `B-03`, `B-05` closed or explicitly re-scoped.
- [ ] Every adopted rule has a theory anchor, a code token and a test (`C-08`) — a methodology rule
      that lives only in a paper is not implemented.
- [ ] Every figure moved by an adopted rule reverts to unverified until re-derived independently,
      and any figure already in a published draft routes through `consultant`.

## Stages serving this phase

| Stage | Evidences objective |
|---|---|
| [ST10 methodology development](../stages/st10-methodology-development.md) | all |
| [ST03 benchmark construction](../stages/st03-benchmark-construction.md) | 1, 6 |
| [ST04 product parameterisation](../stages/st04-product-parameterisation.md) | 4 |
| [ST05 engine run](../stages/st05-engine-run.md) | 3, 6 |
| [ST06 verification gates](../stages/st06-verification-gates.md) | 7 |

## Traceability

Discharges `M-01`…`M-08`, `W-21` (the limitations the whitepaper requires be disclosed), `G-16`
(Appendix F caveats), and the parts of `G-02`/`G-03` where the guideline instructs disclosure but
does not fix a rule.

## What would invalidate this phase

- A resolution that quietly changes the metric's meaning. The whitepaper wins over the engine and
  over convenience: if a proposed rule needs the benchmark to stop being NDC-derived, the finding is
  that the framework does not hold there, and it goes to the whitepaper owner as a version change —
  not into the code.
- Resolving a challenge on the automotive case and asserting it for all sectors. `M-05` and `M-06`
  are skeletons for a reason; a rule generalised without sector evidence is an assumption wearing a
  rule's clothes.
