# ST11 — Sector onboarding

## Main goal

Decide whether a sector may become an active cohort pilot, by evidencing every acceptance gate
before any number is computed — and to say no when the evidence is not there.

## Activity

For the candidate sector: write the destination and service boundary; identify the cohort/activity
object and the primary policy pathway; check each of the eight acceptance gates in
`docs/sector-expansion.md` against actual artefacts; record which gates fail and what would close
them; and produce the sector method note that ST03 and ST04 will implement.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH4 | 1, 3, 5 | The power sector boundary and gate evidence; the shipping boundary options; the cross-sector comparison rule |

## Inputs

Consumes: `docs/sector-expansion.md` (the gates and the order); `docs/product-contract.md` §Sector
expansion; Whitepaper §6 (`W-17`) and §4.1 (`W-10`); challenges `M-05`, `M-06`; the existing
current-period snapshots `SRC-16` (JERA), `SRC-17` (KOEN), `SRC-18` (MOL) and their recorded
defects.

## Outputs

Produces: a sector method note in `../toolbox/methods/`; new catalogue rows for the sector's
sources; a gate-by-gate verdict recorded in [`../tracker.md`](../tracker.md); an entry in
[`../log/decisions.md`](../log/decisions.md) for the go / no-go.

Consumed by: ST01 (what to acquire), ST03 and ST04 (what to implement), PH4's entry criteria.

## Methodology

The eight acceptance gates are the method. A sector is a *pilot* when all eight are evidenced, and
*supported* only when at least two companies and two destination geographies can be assessed
without hidden allocation. No universal physical denominator is imposed across sectors, and
cross-sector views compare coverage, availability, quality and direction — never a summed score
(`C-06`).

## Owner agents

Owner `planner-and-qc-lead` (gate evidence), with `climate-risk-modeller` for the sector benchmark
and `kr-power-data-scout` for Korean power sources.
Review chain: `reviewer` → `auditor`.
**Named gap:** no agent owns maritime domain knowledge (IMO CII, voyage attribution, well-to-wake
versus tank-to-wake fuels). Recorded in [`../team/roster.md`](../team/roster.md); to be resolved
before shipping enters PH4, not by stretching an existing agent's remit silently.

## When to stop

Either all eight gates are evidenced and the sector method note is written — or the failing gates
are named with what would close each, and the sector stays out of scope with that decision logged.
A partially evidenced sector is not a pilot.

## When to repeat

- A previously failing gate becomes satisfiable (a firm discloses, a registry opens).
- The sector guideline for that sector is drafted, changing the Layer 1 specification.
- A cohort object proves unassemblable at the granularity the method needs.

## Backward moves

- A gate that can only be passed with an undisclosed allocation → sector deferred. `C-06` calls this
  out by name, and the JERA/KOEN/MOL snapshots are the live example: useful source research, not
  cohorts.
- Reported intensity that does not reconcile with the firm's own totals (the KOEN case) → back to
  ST01 with a clarification request to the source; not estimated into place.
- A sector whose operating-country analogue is genuinely ambiguous (shipping) → the deliverable
  becomes the bounded sensitivity to the boundary choice, not a result under one arbitrary boundary.

## Process

[`../process/st11-sector-onboarding.md`](../process/st11-sector-onboarding.md)
