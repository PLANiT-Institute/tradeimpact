# ST07 — Research database

## Main goal

Build a SQLite research database in which every published figure is one join away from the source
row or the numbered assumption behind it, and in which the three evidence layers stay
distinguishable.

## Activity

Design the schema against the evidence layers (`C-02`): observed activity, sourced scenario inputs,
derived results — as separate tables with explicit foreign keys to a source register and an
assumption register. Load from the pinned snapshots and the published JSON. Represent every missing
input as a row with a NULL value and a reason. Emit a provenance-coverage report: the count of
numeric facts with no source or assumption reference, which must be zero.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH2 | 1, 2, 3, 5 | The database itself, its schema note, and the retirement or regeneration of the interim spreadsheet audit |
| PH3 | reporting rule | From PH3 onward, a figure that does not resolve in the database is not publishable |
| PH4 | reporting rule | The same rule applies to a new sector, on the same schema |

## Inputs

Consumes: `data/published/*.json` (all of it, including `sources.json` and `meta.json`);
`data-pipeline/source-snapshots/*.json`; [`../toolbox/data/register.md`](../toolbox/data/register.md);
[`../toolbox/data/assumptions.md`](../toolbox/data/assumptions.md); the engine and pipeline hashes in
`meta.json`.

## Outputs

Produces: the SQLite database file (generated, path fixed by the build script), the build script, a
provenance-coverage report, and optionally a generated spreadsheet export replacing
`data/TI_integrated_audit.xlsx`.

Consumed by: ST08, ST09, and any later stage that needs to answer "where does this number come
from".

## Methodology

[`../toolbox/methods/research-database-schema.md`](../toolbox/methods/research-database-schema.md).
Governing text: `C-02` (layers not collapsible), `C-05` (missing ≠ zero), `C-07` (determinism),
`W-15` (the transparency fields that must be queryable).

## Owner agents

Owner `developer`, with `refactor-architect` for the schema shape.
Review chain: `tester` (rebuild determinism, NULL-reason coverage) → `reviewer` →
`provenance-auditor` (every fact reaches a source).

## When to stop

- The database rebuilds from a clean checkout with one documented command, from pinned inputs only.
- The provenance-coverage report shows zero unreferenced numeric facts.
- Every missing input appears as a row with a reason; a query for "what is missing and why" returns
  the same content as `impact_readiness.json`.
- `check_published.py` still passes afterwards.
- Two consecutive builds on the same inputs produce the same content hash.

## When to repeat

- The published set changes for any reason.
- A new source, assumption, sector or cohort year is added.
- The schema changes — in which case the schema note is rewritten first, and the old note is
  deleted rather than kept beside it.

## Backward moves

- A figure exists in the published set with no source and no assumption id → back to ST02. The
  database must not invent a provenance row to make its own coverage report pass; that failure mode
  would turn the record into a laundering step.
- A number found only inside adapter code → back to ST01/ST02 so it becomes either a source value
  or a numbered assumption.
- The schema needing to store a derived value as an observation → back to the schema note; the
  layers are not collapsible.

## Process

[`../process/st07-research-database.md`](../process/st07-research-database.md)
