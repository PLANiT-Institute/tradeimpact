# ST11 — Verification

**Main goal.** Mechanical and independent proof that theory, data, computation and reported
numbers agree — before any figure may be called `[verified]`.

## Activity

Four checks, in order, with tolerances stated before results are seen:

1. **Traceability** — every reported figure resolves to a catalogue row or an assumption id
   (`N-03`).
2. **Re-derivation** — every headline recomputed by a different route, by a different agent, from
   the primary source.
3. **Regression** — where a prior published result exists on the same boundary, the new run is
   reconciled against it and any divergence explained rather than absorbed.
4. **Adequacy** — do these checks actually test the claim being made. This is the only
   judgement-based gate, and the reason `auditor` is independent of the producing stages.

The regression baseline that exists today is the archived EU27 Toyota and Hyundai 2024 lifetime
run (`archive/data/published/lifetime_results.json`, `SRC-24`), computed on the boundary the new
pipeline targets. It is **prior work, not a current deliverable**: it is used to catch silent
divergence, and where the new pipeline is deliberately different, the difference is recorded as a
decision in [`../log/README.md`](../log/README.md).

## Phases served

Every phase, and it blocks each one's exit: PH1/6, PH2/2–4, PH3/1 and PH3/4, PH4/2–3, PH5/3 and
PH5/5.

## Consumes (inputs)

The outputs of ST08, ST09, ST10, and for method changes ST12;
[`../toolbox/catalogue.md`](../toolbox/catalogue.md) and
[`../toolbox/assumptions.md`](../toolbox/assumptions.md) (ST07); `SRC-24` — the archived published
set and its recorded input hashes (`archive/data/published/meta.json`).

## Produces (outputs)

A verdict per headline figure (`[verified]` or `[compute]`); a regression note per reconciled
boundary with the tolerance used; rows for [`../tracker.md`](../tracker.md) §3 and §6; log entries
for material findings. Consumed by every phase gate, and by ST13 and ST14, which may not publish a
`[compute]` figure.

## Methodology

[`../process/general.md`](../process/general.md) §5. The archived theory-to-code contract
(`archive/theory/SYNC.md`) is the working model for anchoring an equation to its implementation
and its test; adopting an equivalent contract for `script/auto/` is a PH3 objective.

## Owner agents

`math-reviewer` (re-derivation), `tester` (tests and regression), `provenance-auditor`
(traceability), `auditor` (adequacy), `reviewer` on code changes.

## When to stop

All four checks recorded, every headline marked, tolerances stated in advance, no check skipped. A
skipped check is a failed check.

## When to repeat

Every stage exit, every phase gate, and after any change to an input, method, assumption or pin.
Verification does not survive a change to the thing verified: a re-run reverts its figures to
`[compute]`, while a stage proven unchanged keeps its prior verification.

## Backward moves

A failed re-derivation returns to the producing stage. A failed adequacy review returns to the
method — [`ST12`](st12-15-outputs.md) — because the checks were testing the wrong question, which
no amount of recomputation fixes.
