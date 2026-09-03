# PH2 — Methodology white paper and challenge resolution

## Purpose

Turn the TI Framework from a documented proposition into a peer-reviewable methodology. The
proposal's theory of change rests on this phase: "the primary barrier to trade-aware climate
accounting is not political will or regulatory capacity — it is the absence of a methodology
rigorous enough to be trusted." The phase maintains the whitepaper, the sector guidelines and
the challenges document, resolves the open challenges with evidence produced by the case-study
phases, and submits the paper for open-access peer review.

## Objectives

1. **Positioning written.** The comparative overview of TI against Scope 3 Category 11,
   Scope 4 and PCAF is in the paper, with the contribution-based attribution choice defended
   against the additionality objection (`C-06`; challenges cross-cutting issue A).
2. **Challenge 1 closed or bounded.** A stated sector-split correction for pro-rata markets
   with a bounded residual error, plus a decision rule for unquantifiable-benchmark markets,
   such that two analysts produce the same benchmark within a declared tolerance.
3. **Challenge 3 closed or bounded.** A reproducible uncertainty-propagation procedure giving a
   band on the headline TI, and a stated Tier-C share above which only a direction is
   published. This is also the route to the `C-05` P10/P50/P90 commitment (`B-07`).
4. **Challenge 4 closed or bounded.** Market-calibrated PHEV utility factors and a documented
   segment-coverage decision (`X-07`).
5. **Non-linearity bounded.** The exponential benchmark cross-validated against observed recent
   sector data in at least one fast-transition market (challenges cross-cutting issue B).
6. **Advisory feedback incorporated.** Technical Advisory Group input at the methodology-design
   and pilot stages is recorded and answered (`C-07`, `B-06`).
7. **Submitted.** White paper submitted for open-access peer review (`C-03`).

## Deliverables

| Charter id | Artefact | Format | Acceptance test | Milestone |
|---|---|---|---|---|
| `D-01` | Methodology white paper | Working paper, open access | Submitted to "the Journal of Cleaner Production or equivalent journal"; comparative overview present (`C-06`) | Month 7 |

## Entry criteria

- Charter accepted.
- Whitepaper v1.5, guideline v1.8 and challenges v1.0 in `methodology/`.
- At least one case-study result set exists to test a challenge against — PH1 objectives 3–5.

## Exit criteria

- [ ] Each of challenges 1, 3, 4, A and B is marked resolved with a stated rule, or carried as
      a documented limitation with a bounded error. Silence is not an option.
- [ ] `C-05`'s range commitment either delivered as a propagated band or formally renegotiated
      through `consultant`; `B-07` closed either way.
- [ ] Every equation changed in the paper has its `theory` anchor, implementation and test moved
      together (see [`st12`](../stages/st12-methodology-maintenance.md)).
- [ ] TAG feedback log exists with a response per item.
- [ ] Submission confirmed, with the journal and date recorded in `log/transitions.md`.

## Stages serving this phase

| Stage | Evidences objective |
|---|---|
| [`st12`](../stages/st12-methodology-maintenance.md) | 1, 2, 3, 4, 5 |
| [`st08`](../stages/st08-benchmark-construction.md) | 2, 5 (supplies the empirical test) |
| [`st09`](../stages/st09-impact-computation.md) | 3, 4 (supplies the sensitivity behaviour) |
| [`st11`](../stages/st11-verification.md) | 2, 3, 4 (adequacy of the resolution) |
| [`st14`](../stages/st14-publication.md) | 7 |

## Traceability

`D-01`, `C-03`, `C-04`, `C-05`, `C-06`, `C-07`, `C-14`(a). Exclusions in force: `X-05`, `X-06`,
`X-07`.

## What would invalidate this phase

- **The counterfactual objection lands.** If the policy-trajectory baseline cannot be defended
  as a legitimate reference, the metric's interpretation changes and the case-study phases must
  re-report against a revised reading — this is the objection most likely to sink the journal
  submission (challenges cross-cutting A).
- **Pro-rata bias proves dominant.** If the S1–S3 spread shows the TI sign is an artefact of the
  pro-rata assumption rather than a signal, PH1 and PH4 results become directional only, and
  `D-02`/`D-03` claims must be rewritten.
