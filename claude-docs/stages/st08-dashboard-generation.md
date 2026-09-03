# ST08 — Dashboard generation

## Main goal

Render the research record as a generated HTML dashboard that contains no hand-typed number and no
status sentence the data can contradict.

## Activity

Generate the dashboard from the research database: cohort and destination panels, the S1/S2/S3 band,
the two mandatory decompositions, the sensitivity ranges, the tier and target-level distribution,
the missing-input list, and the data-quality declaration. Every label, count and state string is
derived from a query. Every panel names the source of what it shows.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH2 | 4 | The dashboard, and the retirement of hand-written status prose |
| PH3 | reporting | New outputs appear without hand-editing anything |
| PH4 | 5 | The cross-sector view that compares coverage and direction without adding units |

## Inputs

Consumes: the ST07 database; the generator templates; the figure conventions in
[`../toolbox/methods/presentation-rules.md`](../toolbox/methods/presentation-rules.md).

## Outputs

Produces: the generated HTML dashboard and its figures.

Consumed by: readers; ST09 where any part of it travels externally.

## Methodology

[`../toolbox/methods/presentation-rules.md`](../toolbox/methods/presentation-rules.md).
Governing text: Whitepaper §7.2 (`W-19`) for the required chart set, `G-10` for the declaration,
`C-09` for magnitude suppression, `W-07` for decomposition alongside every headline.

## Owner agents

Owner `visualizer`, with `web-app-engineer` where the dashboard shares components with `web/`.
Review chain: `reviewer` (no hand-typed numbers, no stale prose) → `auditor` before external use.

Note: this stage produces the **research** dashboard over the data. The engagement progress
dashboard under [`../dashboard/`](../dashboard/README.md) is a different artefact owned by
`report-manager`; the two link to each other and neither restates the other.

## When to stop

- Every number on every panel traces to a query, verifiable by removing a database row and seeing
  the panel change.
- No numeric literal in the templates (checked by grep, not by inspection).
- Direction-only rendering active wherever `C-09` suppression applies — a suppressed magnitude must
  not appear in a tooltip or an axis label.
- Every headline panel carries its decomposition and its S1/S2/S3 band.
- The dashboard regenerates from a clean build.

## When to repeat

Whenever the database changes, whenever a figure convention changes, and after every refresh. A
dashboard built on a superseded database is worse than no dashboard, because it is credible.

## Backward moves

- A panel that cannot be sourced from a query → back to ST07 (the fact is missing from the database)
  or to ST02 (the fact was never sourced). Not to a hardcoded value: that is the exact failure this
  project has already had three times in the web application.
- A chart that implies causation or a point estimate → back to the presentation rules; findings are
  directions and ranges.

## Process

[`../process/st08-dashboard-generation.md`](../process/st08-dashboard-generation.md)
