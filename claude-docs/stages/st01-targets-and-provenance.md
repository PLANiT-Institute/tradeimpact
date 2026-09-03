# Stages ST01 and ST07 — targets and provenance

The two input stages that are not a dataset. The five datasets are in
[`st02-06-datasets.md`](st02-06-datasets.md).

---

## ST01 — Target selection

**Main goal.** Fix and document the unit of analysis: exporters, importer markets, cohort years,
segment, and vehicle lifetime T.

**Activity.** Record the five required parameters of guideline §1.3 (firm, cohort year, operating
country, vehicle type, lifetime T) and evaluate guideline §6.3's market-selection criteria against
each candidate importer: registration-volume rank, at least 70% of the firm's global sales covered
with a minimum of three markets, at least one high- and one low-grid-intensity market, and per
market a submitted NDC, national grid-intensity data and an accessible registration database. A
market that fails a criterion is recorded as failing, not dropped quietly.

The lead's direction of 2026-09-03 — exporters Hyundai, Kia (Korea), Toyota, Honda (Japan);
importers EU27, United States, Australia — is the input to this test, not its conclusion. The
2026-09-04 direction narrows the *first pass* to what the data on hand supports: Toyota and
Hyundai, EU27, cohort year 2024. Kia, Honda, the United States and Australia stay in the target
set as later acquisition, with their absence counted rather than assumed away.

**Phases served.** PH1/1 (the documented target set); PH4/4 (the six-firm bound, `C-11`).

**Consumes.** Lead directions of 2026-09-03 and 2026-09-04
([`../log/README.md`](../log/README.md)); `SRC-01`, `SRC-04`, `SRC-05` for the volume rank;
`SRC-11`, `SRC-13` for NDC and grid-data availability; charter `C-11`, `B-03`, `B-04`.

**Produces.** `data/auto/output/target_set.csv`
([schema](../toolbox/data-schema.md#6-outputs-dataautooutput)) plus a decision entry for every
inclusion that fails a §6.3 criterion. Consumed by ST02–ST06, ST08, ST10.

**Owners.** `consultant` (firm scope against `C-11`), `climate-risk-modeller` (market criteria);
review `research-director` then `auditor`.

**Stop when.** Every target has all five parameters with a source, every §6.3 criterion is marked
met or failed with a reason, and `B-03` is resolved.

**Repeat when.** A firm, market or cohort year changes; `B-03` or `B-04` resolves; a new sector
enters (PH4).

**Backward move.** If no target set satisfies §6.3 — for example because 70% coverage is
unreachable on public data (`X-02`) — the finding goes to PH1's entry criteria and to `consultant`
for change control, never to a relaxed criterion.

---

## ST07 — Source registration and provenance · *live*

**Main goal.** Every value used anywhere is retrievable, licensed, hashed and attributable to a
named `source_id` — or it is a numbered assumption.

**Activity.** For each acquired source, record publisher, title, locator, retrieval date, vintage,
licence and re-use terms, and the **data level** it supports (per-model, per-country, regional or
national aggregate). Where a source is paywalled or unreachable, record the fallback and the
assumption id it creates. Clear licences before anything is redistributed in the open dataset or
the dashboard (`C-02`).

Per-file SHA-256 hashes live in each dataset's `method/method.md`; the catalogue indexes them
rather than copying them, so a hash has exactly one home.

**Phases served.** PH1/2 (makes `N-03` checkable); PH3/4 (licence clearance for release); PH5/3
(traceability clearance before publication); PH4/2–3.

**Consumes.** The raw files and provenance tables from ST02–ST06; `SRC-24` — the archived source
register (`archive/data/published/sources.json`, 26 rows carrying licence, accessed date and
snapshot hashes) as the starting point for reused sources; the reference set in
[`../toolbox/references-and-archive.md`](../toolbox/references-and-archive.md).

**Produces.** [`../toolbox/catalogue.md`](../toolbox/catalogue.md),
[`../toolbox/assumptions.md`](../toolbox/assumptions.md), and a licence verdict per redistributed
source. Consumed by every stage that reports a figure, and by ST11, ST13 and ST14 as a gate.

**Owners.** `provenance-auditor` (owner), `source-reconciliation-analyst` (conflicting sources),
`data-collector` (retrieval metadata); `auditor` on adequacy.

**Stop when.** Every figure in a current output resolves to a catalogue row or an assumption id;
every catalogue row has a licence verdict; every unreachable source has a named fallback and an
assumption.

**Repeat when.** Any acquisition, re-acquisition or vintage change; any assumption added or
retired; before every publication or release gate.

**Backward move.** A figure with no catalogue row and no assumption id is not a documentation
defect to patch at publication time — it returns to the stage that produced it, and that stage's
outputs revert to `[compute]`.

**Open at 2026-09-04.** The three processed sales tables carry `source_file` but no `source_id`
column; `vehicle_technology_eea_2024.csv` carries both. Either the sales tables gain `source_id`
or the schema states that `source_file` is the join into the register — an open item in
[`../tracker.md`](../tracker.md) §6, not a matter of taste.
