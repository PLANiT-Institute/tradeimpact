# ST10 — Methodology development

## Main goal

Convert a named methodological challenge into a defensible rule with a bounded residual error — or
into a documented limitation with a bounded error. Never into a caveat that stands in for a
decision.

## Activity

Take one challenge from `methodology/TI_Methodological_Challenges_v1.md`; state precisely what the
framework currently does and where that fails; derive a candidate rule from primary evidence rather
than from convenience; quantify the residual error; state which published figures the rule would
move; write the rule as a method file with its failure modes and its validation test; and route the
adoption through the verification gates so the rule acquires a theory anchor, a code token and a
test (`C-08`).

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH5 | all | The per-challenge resolution notes and the consolidated response |
| PH3 | 2, 4, 6 | The UF calibration, the target-level upgrade rule, and the tier-C propagation the automotive results need |
| PH4 | 1, 4 | The power aggregation rule and the shipping boundary rule |

## Inputs

Consumes: the three methodology documents; `ti-framework/NOTES.md` decisions D1–D4; the case-study
evidence from ST03/ST04/ST05 runs; the reference sets in
[`../toolbox/references/`](../toolbox/references/framework-and-accounting.md); blockers `B-01`,
`B-02`, `B-03`, `B-05` from the charter.

## Outputs

Produces: a method file per resolved challenge in `../toolbox/methods/`; a decision entry in
[`../log/decisions.md`](../log/decisions.md); a change request against the whitepaper or guideline
where the rule changes the framework rather than its implementation; the `D-07` consolidated
response.

Consumed by: ST03, ST04, ST05 (the rules they apply), ST06 (the anchor and test), ST09 (the
disclosure text).

## Methodology

Each challenge's resolution criterion **is** the method's acceptance test, quoted from the
challenges document. Cross-cutting positioning: `M-07` against the avoided-emissions literature in
[`../toolbox/references/framework-and-accounting.md`](../toolbox/references/framework-and-accounting.md).

## Owner agents

Owner `climate-risk-modeller` (benchmark and policy-pathway rules) or `computational-economist`
(uncertainty propagation, allocation rules), per challenge.
Review chain: `math-reviewer` (derivation and error bound) → `auditor` (is the disclosure adequate
to the residual) → `reviewer`. Writing support from `writing-support-team` for `D-07`; framing for
an external audience via `consultant`.

## When to stop

- The rule is stated so that two analysts applying it to the same firm and markets get the same
  answer within the declared tolerance.
- The residual error is measured, not asserted.
- Every figure the rule moves is listed before adoption.
- The rule has an anchor, a code token and a test — or it is explicitly recorded as a
  documentation-only limitation.

## When to repeat

- New case-study evidence contradicts an adopted rule.
- A sector guideline is drafted (shipping `M-05`, power `M-06` are skeletons by design).
- Peer-reviewer feedback on the whitepaper or guideline arrives — the challenges document states it
  will be revised on exactly that trigger.

## Backward moves

- A rule that requires the benchmark to stop being NDC-derived → this is a framework finding, not an
  implementation choice. It goes to the whitepaper owner as a version change; PH5's exit criteria
  make this explicit.
- A rule adopted in code before it exists in a method file → back out the code. Method precedes
  implementation, and a code-level default masquerading as a rule is what `A-01`…`A-04` currently
  are.
- A resolution generalised from automotive to all sectors without sector evidence → back to the
  challenge's own sector depth.

## Process

[`../process/st10-methodology-development.md`](../process/st10-methodology-development.md)
