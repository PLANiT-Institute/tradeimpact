# Process — dataset acquisition (ST02–ST06)

The live procedure. It governs all five datasets; what differs per dataset — the sources, the
scripts, the columns — is in [`../stages/st02-06-datasets.md`](../stages/st02-06-datasets.md) and
in each `data/auto/<dataset>/method/method.md`. Invariants:
[`general.md`](general.md).

## Goal

Turn a named source into a processed table whose every row can be traced back to it, without
touching the raw file and without inventing a value. Serves PH1 objective 2, and everything
downstream depends on it.

## Preconditions

- The source is identified in [`../toolbox/catalogue.md`](../toolbox/catalogue.md) with its access
  route and data level, and the data level is adequate for the stage that will consume it.
- The dataset's `method/method.md` states the required fields, and
  [`../toolbox/data-schema.md`](../toolbox/data-schema.md) agrees with it. If they disagree, that
  is fixed before any script runs.
- Licence and re-use terms are known, because a source that cannot be redistributed changes what
  the open dataset can contain (`C-02`).

## Steps

| # | Step | Who or what | Artefact |
|---|---|---|---|
| 1 | Fetch the source exactly as published; for an API, record the literal query | `data-collector` | file in `data/auto/<dataset>/raw/` |
| 2 | Rename to `snake_case`; record the original name, origin and SHA-256 | `data-collector` | provenance row in `method/method.md` |
| 3 | Register the source: publisher, title, locator, retrieval date, vintage, licence, data level | `provenance-auditor` (ST07) | row in `toolbox/catalogue.md` |
| 4 | Write one script per raw source under `script/auto/<dataset>/`; no cleaning by hand, ever | `developer` | script |
| 5 | Emit the processed table in the schema, one file per source, with `source_file` on every row | script | file in `processed/` |
| 6 | Count what did not survive: rows dropped, models unmatched, markets missing — reported, not discarded | script | summary in the run output |
| 7 | Re-run and compare: same inputs, byte-identical output | `tester` | determinism verdict |
| 8 | Record any value that stands in for a source | `research-director` via ST07 | numbered row in `toolbox/assumptions.md` |

Mapping tables that a workbook needs to be readable — `sales/method/kia_labels.csv`,
`sales/method/hyundai_plant_codes.csv` — live beside the method file, not inside the script. A
label map is data about a source, and it belongs where the source's rules are.

## Data handling for these stages

- Raw is never edited. A wrong value in a raw file is corrected in the script, with the correction
  and its reason in the script's docstring — never by hand in the file.
- Every row carries `source_file`; the register row carries the hash. Nothing carries a value with
  neither.
- Units are converted in the script, explicitly, and the target unit is in the schema.
- A missing input produces no row (`N-02`). It never produces a zero, an empty string treated as
  zero, or a market-average fill.
- Nothing about a domain — a rate, a factor, a market label, a lifetime — is hardcoded in a
  script. It comes from a processed table, a mapping file beside the method, or a numbered
  assumption.

## References and methodology

The dataset's `method/method.md` and, for parameter choices, the automotive guideline sections it
cites. Where a correction factor or a utility factor is needed, it is taken from the primary
document (`SRC-17`, `SRC-19`) — a figure lifted from a summary, a secondary citation or a search
extract is not evidence and is rejected at review.

## When to stop

Every source in the dataset's scope is either processed with its provenance recorded, or listed as
a gap with the reason and the consequence. The processed table validates against the schema, and a
re-run reproduces it byte for byte.

## When to repeat

A new vintage of a source; a new market, company, model or cohort year; a correction to a script;
a schema change; a mapping-table correction. In each case the downstream closure in
[`general.md`](general.md) §8 re-runs, and the affected figures revert to `[compute]`.

## Failure modes

| What goes wrong | What it looks like | The check that catches it |
|---|---|---|
| Mixed bases summed together | Registrations and plant-side sales in one total, inflating volume | `basis` is mandatory per row; ST10 aggregates by basis and refuses to mix |
| Region rows treated as country rows | A "Europe" row lands in a country total and double-counts | `destination_level`; ST10 aggregates regions separately |
| Plant-side rows treated as destination sales | Production allocated to a market it never reached | `basis = plant_sales` plus `origin`; ST09 excludes them from destination TI (`X-04`) |
| Powertrain lost in an IR workbook | Models silently pooled across powertrains, which the framework forbids before per-vehicle TI | Empty `powertrain` blocks the row from ST09 until the ST06 join resolves it |
| A model name that does not join | Units quietly disappear between sales and technology | Step 6's unmatched count, reconciled against the sales total |
| Test cycles mixed across markets | WLTP and EPA values averaged into one intensity | `test_cycle` per row; no conversion without a sourced factor |
| Correction applied twice | Real-world intensity inflated | Correction applied once, at ST06 processing time, with its factor on the row |
| A hand-edited raw file | A hash that no longer matches its register row | Step 2's hash, re-checked at every stage entry |

## Deviations from general.md

None. Two structural notes rather than deviations: processed tables are **one file per source**
(not one per dataset), because the bases and destination levels differ per source and merging them
would hide exactly what the schema exists to keep visible; and the sales tables currently carry
`source_file` but no `source_id`, which is an open item in [`../tracker.md`](../tracker.md) §6.
