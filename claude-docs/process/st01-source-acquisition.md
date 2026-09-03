# Process — ST01 source acquisition

Stage: [`../stages/st01-source-acquisition.md`](../stages/st01-source-acquisition.md).
Invariants: [`general.md`](general.md).

## Goal

A pinned, hashed, licence-recorded snapshot of an external source. Serves PH1/2, PH3/1–3,5, PH4/2,4.

## Preconditions

- The source has a catalogue row with an access route and a data level.
- The licence permits the intended use, checked before retrieval, not after.
- The stage that needs the source has named the fields and the granularity it requires.

## Steps

| # | Step | Command or agent | Artefact |
|---|---|---|---|
| 1 | Confirm the source is the most recent applicable vintage (for an NDC, confirm against the UNFCCC registry per `G-14` step 5) | `data-collector` | note in the register row |
| 2 | Retrieve through the documented route | the sector adapter's `--refresh` mode (canonical invocations in `docs/project-status.md`) | `data-pipeline/source-snapshots/<source>.json` |
| 3 | Record the exact query alongside the response | adapter | `query_sha256` in `sources.json` |
| 4 | Hash the snapshot | adapter | `snapshot_sha256` |
| 5 | Write the register row: source id, publisher, vintage, access date, licence, evidence class, snapshot path | `data-collector` | [`../toolbox/data/register.md`](../toolbox/data/register.md) |
| 6 | Re-run the retrieval and compare hashes | `tester` | determinism verdict |
| 7 | Licence and retrievability clearance | `provenance-auditor` | clearance note |

## Data handling for this stage

Sources and their access routes: [`../toolbox/data/catalogue.md`](../toolbox/data/catalogue.md).
Nothing is transformed here — no unit conversion, no aggregation, no gap filling. The snapshot is
the source's own content in canonical JSON form.

Must not be hardcoded: query filters (year, brand, geography), endpoints, and vintages. They live in
the adapter's configuration and are echoed into the snapshot so the query is auditable.

## References and methodology

[`../toolbox/methods/source-acquisition-and-pinning.md`](../toolbox/methods/source-acquisition-and-pinning.md).
Per-source notes and primary URLs: `data-pipeline/sectoral-sources.md`. Sector source lists:
Guideline Appendix B (`G-14`).

## When to stop

Snapshot committed, hash recorded, query recorded, licence cleared, determinism checked or the
non-determinism recorded.

## When to repeat

New vintage published; a blocked stage needs a new catalogue row; access route or licence changed;
a downstream stage reports a missing field.

## Failure modes

| What goes wrong | What it looks like | The check that catches it |
|---|---|---|
| Provisional data pinned as final | Counts shift when the source finalises | Step 1 vintage confirmation; the snapshot records `Final` in its query |
| A live query silently replacing a snapshot | Build results change with no commit | `check_published.py` recomputation drift |
| Series that looks right but measures something else | Values implausible by orders of magnitude — the Eurostat territory-versus-registration distance case, up to 85× | Cross-series comparison at step 2; such a series is excluded, not tier-downgraded |
| Licence prohibiting redistribution discovered after publication | Takedown risk | `provenance-auditor` clearance at step 7, before use |

## Deviations from general.md

None.
