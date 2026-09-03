# ST01 — Source acquisition

## Main goal

Turn an external source into a hash-pinned snapshot committed to the repository, so that every
later stage reads a fixed artefact and no build depends on a live API (`C-07`).

## Activity

Query the source through its documented access route, record the exact query, write the response as
a canonical JSON snapshot under `data-pipeline/source-snapshots/`, and register the acquisition with
publisher, access date, licence, evidence class and content hash. Where a source is not machine
reachable, the acquisition is a documented retrieval with the same metadata — never a transcription
without one.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH1 | 1, 2, 5 | The EEA cohort and EU27 destination-input snapshots the published result rests on |
| PH3 | 1, 2, 3, 5 | 2022/2023 EEA cohorts, UF and H₂ sources, country pathway documents, firm IR materials |
| PH4 | 2, 4 | Power and shipping company data and the sector benchmark documents |

## Inputs

Consumes: catalogue rows `SRC-01`…`SRC-26` in
[`../toolbox/data/catalogue.md`](../toolbox/data/catalogue.md) — each with its access route, licence
and data level. Units are the source's own; conversion happens in ST02, never here.

## Outputs

Produces:

- `data-pipeline/source-snapshots/<source>.json` — canonical snapshot, content-addressed.
- A row in [`../toolbox/data/register.md`](../toolbox/data/register.md): source id, version or
  vintage, access date, licence, snapshot path.
- The `sources.json` entry (via the adapter) carrying `snapshot_sha256` and, where applicable,
  `query_sha256`.

Consumed by: ST02, ST03, ST04.

## Methodology

[`../toolbox/methods/source-acquisition-and-pinning.md`](../toolbox/methods/source-acquisition-and-pinning.md).
Access routes and per-source notes: `data-pipeline/sectoral-sources.md`; sector source lists:
Guideline Appendices A–C (`G-14`).

## Owner agents

Owner `data-collector`; `kr-power-data-scout` for Korean power-sector sources (PH4).
Review chain: `provenance-auditor` (licence, retrievability, evidence class) → `auditor`.

## When to stop

The snapshot exists, its hash is recorded, the exact query is recorded, and a second run of the
acquisition command reproduces the same hash — or, where the upstream is not deterministic, the
snapshot is pinned and the non-determinism is recorded in the register row.

## When to repeat

- A new source vintage is published (new EEA final year, new Ember release, new NDC submission).
- The catalogue gains a row that a blocked stage needs.
- A licence or access route changes.
- A downstream stage reports that the snapshot does not contain a field the method needs — repeat
  with a corrected query rather than filling the gap downstream.

## Backward moves

- Source unreachable or licence-incompatible → back to the catalogue (ST02 records the fallback and
  the analysis cost as a numbered assumption; the stage does **not** substitute a neighbouring
  source silently).
- Source exists only at an aggregate level the stage needs disaggregated (e.g. a national total
  where per-market values are required) → back to PH-level scoping: this is a scope finding, not an
  acquisition failure.

## Process

[`../process/st01-source-acquisition.md`](../process/st01-source-acquisition.md)
