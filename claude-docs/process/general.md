# General process — invariants every stage obeys

Written once. A stage's own process document states only its specifics and any deviation from here,
with a reason. Silent deviation is a defect.

## 1. The stage loop

```
frame → source → acquire → validate → compute → verify → record → report
```

No step is skipped. Compute before verify is normal; publish before verify is not.

## 2. Data handling

- **Raw is immutable.** A committed snapshot is never edited. A correction is a new snapshot with a
  new hash and a register row explaining the supersession.
- **One-way flow.** source → snapshot → normalised record → published set → outputs. Nothing writes
  backwards.
- **Every source carries a manifest**: publisher, access route, exact query where applicable,
  access date, content hash, licence, evidence class. Recorded in
  [`../toolbox/data/register.md`](../toolbox/data/register.md) and in the pipeline's own
  `sources.json`.
- **No live API in a build.** Builds read pinned snapshots (`C-07`). Refresh is a separate,
  deliberate act.
- **Never hardcode a domain value.** It belongs in config, in the source catalogue, or in
  [`../toolbox/data/assumptions.md`](../toolbox/data/assumptions.md) as a numbered assumption. A
  figure with neither a register row nor an assumption id does not exist.
- **Missing is missing.** A missing input yields an unavailable result with a reason and a unit
  count — never zero, never a generic default (`C-05`). This is the single rule this project has
  most often been tempted to break, and the one that its removed-estimates record exists to enforce.
- **Units travel with values.** Convert once, at reconciliation, and record the conversion.

## 3. Referencing

Preference order for any reference:

1. Primary source — the regulatory dataset, the statute, the NDC submission, the firm's assured
   disclosure, the peer-reviewed paper.
2. Official statistical publication — the national inventory, the statistical office series.
3. Institutional report — IEA, Ember, ICCT, CCC, a ministry projection.
4. Anything else — context only, never evidence.

A citation carries publisher, title, date, and a retrievable locator. Every method file cites at
least one reference. Citing a number you have not seen in its own primary source is not allowed:
`data-pipeline/sectoral-sources.md` marks one such case (an ICCT figure taken from a search
extract) as flagged, which is the correct handling — flagged, not used silently.

## 4. Methodology discipline

The method is written down — statement, scientific basis, inputs and outputs with units, failure
modes, validation test — **before** it is implemented. Understanding precedes the artefact; a
polished dashboard ahead of the analysis is the failure mode this project already corrected once
when it removed the `alignment-v2` presentation.

Methodology precedence: whitepaper → sector guideline → challenges document → project contract
(binding where stricter) → code. When code and methodology disagree, the code is wrong; the
disagreement is recorded in `ti-framework/NOTES.md` with a dated decision, not resolved by silent
edit.

## 5. Verification

- Every headline figure is independently re-derived by a different route before it is called
  verified.
- Tolerances are stated before results are seen (`check_published.py` uses 1e-12 for recomputation;
  engine validation uses ±1% against hand calculation).
- A figure is either **verified** or **compute**. A compute figure never reaches a deliverable.
- Verification does not survive a change to the thing verified. Any re-run reverts its figures to
  compute.
- The three standing gates — theory↔code↔test, full recomputation, evidence/readiness — are
  described in [`st06-verification-gates.md`](st06-verification-gates.md) and run at every stage
  exit and phase gate.

## 6. Integrity

- **Association, not causation.** Findings are areas to explore. A shift-share decomposition
  attributes arithmetic, not behaviour.
- **Ranges, not point estimates.** Every parameter with a band publishes the band; every result
  publishes the S1–S3 spread. Where tier-C exposure crosses the threshold, direction only (`C-09`).
- **Absolute magnitudes alongside shares.** A percentage without its unit count hides the cohort
  size difference; both published cohorts differ by 1.87×, which makes per-unit and total values
  both necessary.
- **Exploratory language.** The metric is a comparative trajectory signal, never an avoided-emissions
  claim, never an offset, never netted against Scope 3 (`W-16`, `M-07`).
- **AI use is stated** in the methodology of any published artefact produced with it.

## 7. Stop and repeat

Every stage document names its own stop condition and repeat triggers. Two rules apply everywhere:

- A stage stops when its stop condition is **evaluated**, not when it feels done. An unevaluated
  check is a failed check.
- A stage repeats when any declared input changes — data, method, assumption, config or pin — and
  its downstream stages repeat with it unless the re-run produces an identical output.

## 8. Backward moves

Named, expected, and logged in [`../log/transitions.md`](../log/transitions.md) with trigger and
consequence:

| Trigger | Goes back to |
|---|---|
| Reconciliation mismatch | ST01 (query or snapshot) |
| Figure with no source and no assumption id | ST02 |
| Implausible base-year benchmark value | ST02 for tier downgrade and flag |
| Decomposition identity failure | ST02 join, then ST05 |
| Recomputation drift | ST05, then ST02 |
| Readiness gate closed | ST01/ST04 for the missing input |
| Rendered page contradicting its dataset | ST08/ST09 for a derived label |
| A rule that changes the framework rather than its implementation | PH5, then the whitepaper owner |

A backward move is the process working. Hiding one is the only failure.
