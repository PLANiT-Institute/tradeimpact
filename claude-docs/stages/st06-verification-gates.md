# ST06 — Verification gates

## Main goal

Prove, mechanically and independently of anyone's belief about the result, that the theory, the code
and the published numbers are the same thing.

## Activity

Run the three standing gates and record their verdicts:

1. **Theory ↔ code ↔ test** — `scripts/check_sync.py`: every anchored rule in `theory/SYNC.md` has
   its anchor in the methodology document, its `[anchor]` token in the cited code docstring, and its
   test. A rule with no code and test, or a token with no table row, fails the build (`C-08`).
2. **Full recomputation** — `data-pipeline/check_published.py`: the entire published set is
   recomputed from the committed snapshots and compared to what is published, to a tolerance of
   1e-12; a single drifting number fails (`C-07`).
3. **Evidence and readiness** — the `docs/product-contract.md` publication gate: all eight required
   input families source-complete for the affected activity, or the status is `inputs_incomplete`
   and no lifetime value, avoided-emissions claim or firm score is published (`C-04`).

Plus the engine test suite, and — for math changes — an independent re-derivation by a different
route (`W-15` transparency fields must survive the re-derivation too).

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH1 | 5 | The three gates green on the published set |
| PH2 | 1, 3 | The database and dashboard must not perturb the published set; the gates prove they did not |
| PH3 | all | Every re-opened output re-passes the gates before publication |
| PH4 | 3 | A missing-input test proves the readiness gate closes for the new sector too |
| PH5 | 7 | Every adopted methodology rule acquires an anchor, a token and a test |

## Inputs

Consumes: `theory/SYNC.md`; the methodology anchors; the engine and pipeline code; the committed
snapshots; the published set; `ti-framework/NOTES.md` decision log.

## Outputs

Produces: gate verdicts recorded in [`../tracker.md`](../tracker.md) §6 and in
[`../log/transitions.md`](../log/transitions.md); a `[verified]` or unverified marking per headline
figure.

Consumed by: ST09 (nothing publishes on an unverified figure), and every phase gate.

## Methodology

[`../toolbox/methods/verification-gates.md`](../toolbox/methods/verification-gates.md).
Governing text: `C-07`, `C-08`, `C-04`, `W-15`.

## Owner agents

Owner `tester`, with `developer` for gate maintenance and `debugger` when a gate fails
inexplicably.
Independent review: `auditor` (are the gates adequate to the claim) and `math-reviewer` (for any
math change). `provenance-auditor` before anything travels externally.

## When to stop

All three gates green, the engine suite green, and every headline figure either independently
re-derived or explicitly marked unverified. A gate that was skipped is a failed gate.

## When to repeat

At every stage exit, at every phase gate, and after every refresh of any input, method or pin. Gate
results do not survive a change to the thing they gated.

## Backward moves

- `check_sync.py` fails → the change is incomplete, not the gate: either the theory anchor, the code
  token or the test is missing. Back to the stage that made the change.
- `check_published.py` fails → the published set and the snapshots disagree. Back to ST05, then ST02.
  Never republish over the discrepancy.
- Readiness gate closes → back to ST01/ST04 for the missing input, and the deliverable publishes the
  observed cohort and the missing-input list only (`C-04`).

## Process

[`../process/st06-verification-gates.md`](../process/st06-verification-gates.md)
