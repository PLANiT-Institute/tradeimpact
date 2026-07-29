# Trade Impact (TI) — analysis product

Data-driven implementation of the [TI Framework](Whitepaper%20&%20Guidelines/TI_Whitepaper_v1.5.md):
does a firm's product portfolio contribute to, or lock in emissions against, each
operating country's NDC-committed decarbonisation path?

| Piece | Where | What |
|---|---|---|
| Engine (source of truth for numbers) | [`ti-framework/`](ti-framework/) | Python package `ti_framework`, CLI `ti`, pytest suite; xlsx **and** CSV inputs against one schema |
| Data pipeline | [`data-pipeline/`](data-pipeline/) | `build_dataset.py` runs the engine over the firm universe → `data/published/*.json` with provenance; [collection backlog](data-pipeline/COLLECTION_STATUS.md); [estimate log](data-pipeline/ESTIMATES.md) |
| Web app (Vercel) | [`web/`](web/) | Next.js: `/report/[firm]`, `/country/[code]` (SSG), `/calculator` (Python compute function). Renders engine JSON only — never computes TI itself |
| Theory ↔ code contract | [`theory/SYNC.md`](theory/SYNC.md) | Anchors ↔ docstring tokens ↔ tests, enforced by [`scripts/check_sync.py`](scripts/check_sync.py) in CI |
| Assumption / conflict log | [`ti-framework/NOTES.md`](ti-framework/NOTES.md) | Every default, fallback, and doc conflict (D1–D4) |

Deploy: see [DEPLOY.md](DEPLOY.md). Method rules that never bend: S1/S2/S3 always
reported together; TI never netted against Scope 3; missing inputs stay missing and
flagged — never fabricated.

Published results are content-addressed: the metadata records hashes for the engine source,
effective post-workbook inputs, workbook, target-company sources, the public compute
service (`api/compute.py`), and the complete dataset. `countries.json` is the canonical
cross-firm benchmark contract; generation fails if two real-firm inputs disagree on a
shared country **or** on the sector-wide support parameters (VKT, lifetime, UF band —
published in `meta.json` as `support_contract`). `contract.json` records the emitted
report key sets; the web test suite pins its TypeScript types against it.

The public calculator accepts only bounded fixture-shaped requests: JSON bodies are limited
to 1 MB, 50 countries, 500 placements, and a 50-year product lifetime. Its handler fails
closed on malformed, incomplete, or computationally unbounded inputs.
