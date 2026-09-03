# General process — the invariants every stage obeys

Written once. A stage document names only what is specific to it; anything not named there is
governed here. A deviation from this document is allowed, but never silently: it is stated in the
stage's own process document with its reason.

## 1. The stage loop

frame → source → acquire → validate → compute → verify → record → report.

No step is skipped, and the order is not negotiable. In particular, *source* precedes *compute*:
a value is registered before it is used, not after a result needs justifying.

## 2. Data handling

- **Raw is immutable.** Files under `data/auto/<dataset>/raw/` are never edited, reformatted or
  cleaned in place. A raw file is renamed to `snake_case` on arrival and its original name and
  SHA-256 are recorded in that dataset's `method/method.md`.
- **One-way flow.** `raw` → `processed` → `data/auto/output/`. Nothing writes backwards, and
  `processed/` is written only by scripts under `script/auto/`.
- **Deterministic.** The same raw inputs produce byte-identical processed outputs. No timestamps
  in outputs, no unpinned ordering, no unseeded randomness.
- **Every processed row carries a `source_id`.** A row that cannot carry one is not written.
- **No hardcoded domain values.** Parameters arrive from `processed/` tables, each row with its
  `source_id`; anything genuinely configurable goes to config and is mirrored into `.env.example`.
- **A missing input yields an unavailable result** — never zero, never a silent default. Withheld
  units are counted and reported beside the result they are missing from (`N-02`).
- **Column schema** for every processed file and every output file:
  [`../toolbox/data-schema.md`](../toolbox/data-schema.md). Sources and per-dataset rules stay in
  `data/auto/<dataset>/method/method.md`, which is their only home.

## 3. Referencing

Preference order for any value: primary source (dataset, filing, statute, peer-reviewed paper) →
official statistical publication → institutional report → anything else, which is context and
never evidence. A citation carries author, title, publisher, date and a retrievable locator.
Secondary citation of a number not seen in its primary source is not allowed — an extract from a
search result is not the document.

Every source used sits in [`../toolbox/catalogue.md`](../toolbox/catalogue.md) with its access
route and its **data level**. Data level is a hard constraint, not metadata: a national aggregate
cannot serve a stage that needs per-model values, and discovering that during design is cheap.

## 4. Methodology discipline

The method is written down — with its scientific basis and its failure modes — before it is
implemented. The methodology truth source is `methodology/` (whitepaper, sector guideline,
challenges document); this governance set links to it and never restates its equations.

**Build one thing when it is needed.** A script, a table, a dashboard or a database is created at
the moment the preceding step produces something it must consume, and not before. As of
2026-09-04 that means: the five raw files are in, so the ST02 processing scripts are next; no
model, dashboard or database exists, and the plan does not pretend otherwise.

## 5. Verification

- Every headline figure is independently re-derived by a **different route** and a different
  agent, from the primary source.
- Tolerances are stated **before** results are seen.
- Figures are marked `[verified]` or `[compute]`. A `[compute]` figure never reaches a
  deliverable, a client draft or a dashboard.
- Where a prior published result exists on the same boundary, the new run is reconciled against it
  (`SRC-24`) and any divergence is explained, not absorbed.
- A change to an input, method or assumption reverts the dependent figures to `[compute]`.
  Verification does not survive a change to the thing verified.

## 6. Integrity of interpretation

- Findings are associations and directions — "areas to explore" — never causes or predictions.
- Absolute magnitudes always accompany percentages; uncertainty is a range, not a point estimate.
- Tier C inputs produce directions with a stated coverage ratio, not magnitudes (`N-04`).
- S1, S2 and S3 are reported together, always (`N-05`), and every headline carries its
  decomposition by country and powertrain (`N-06`).
- TI is never netted against Scope 3 Category 11 (`N-01`), and it is not an avoided-emissions or
  Scope 4 number (`X-05`).
- Pro-rata allocation, proxies, extrapolations and flags are disclosed rather than smoothed
  (`N-09`).
- AI assistance in producing an analysis is stated in that analysis's methodology section.

## 7. Stop and repeat

Each stage carries its own stop condition and repeat triggers. Universally: a stage stops when its
outputs exist, are traced and are verified; it repeats when any declared input changes. Backward
moves are healthy and are logged in [`../log/README.md`](../log/README.md) with their trigger and
consequence — a finding that invalidates a premise is the process working, not a failure to hide.

## 8. Dependency order

The graph the repeat rules propagate along. Acyclic; re-runs follow this order, never alphabetical
order.

```text
ST01 targets
  ├─ ST02 sales ──────────────┐
  ├─ ST03 country emissions ──┤
  ├─ ST04 emission targets ───┼─→ ST08 benchmark ─→ ST09 impact ─→ ST10 aggregation ─→ ST14 publication
  ├─ ST05 vehicle usage ──────┤                        ↑                   │
  └─ ST06 vehicle technology ─┘                        │                   ├─→ ST13 tool and dashboard
                                                        └── ST12 methodology
ST07 provenance   — serves every stage, gates ST13 and ST14
ST11 verification — gates every stage exit and every phase gate
ST15 sector onboarding — re-enters at ST01 for a new sector
```

ST02 and ST06 have a two-way join (powertrain mapping); ST06 runs first for models where the
workbook carries names only, and ST02's coverage count is recomputed after it.

**Refresh rule.** When an input changes, re-run the changed stage and its downstream closure in
the order above. A stage may be skipped only when its inputs' hashes are unchanged, and the skip
is recorded with the hash that justified it. If a re-run stage's output is byte-identical, its
downstream stays fresh and propagation stops there.

## 9. Which process documents exist

| Stage | Process document | Status |
|---|---|---|
| ST02–ST06 | [`dataset-acquisition.md`](dataset-acquisition.md) | Written — this is the live procedure |
| ST01, ST07 | This document plus the stage sections in [`../stages/st01-07-inputs.md`](../stages/st01-07-inputs.md) | Sufficient at current scope |
| ST08, ST09, ST10 | Written at stage entry, triggered by the first processed table that makes the stage computable | Deferred |
| ST11 | Written at the first stage exit that needs a gate | Deferred |
| ST12, ST13, ST14, ST15 | Written at their phase entry (PH2, PH3, PH4, PH5) | Deferred |

This is a deliberate deviation from one-process-document-per-stage: at current scope the deferred
documents would describe work that has not begun, and a procedure written months before its first
use is one nobody follows. The deferral is tracked in [`../tracker.md`](../tracker.md) §6, so a
missing document is visible rather than assumed.
