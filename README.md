# Trade Impact (TI) — evidence-first multi-sector analysis product

Trade Impact connects observed company activity in an operating geography with directly
comparable official sector targets, while showing broader sector and NDC pathways as context.
Automotive and power are the first data pilots; shipping, steel, and petrochemicals share the
evidence, coverage, query, web, and MCP contract but retain sector-specific units and boundaries.

| Piece | Where | What |
|---|---|---|
| Engine (source of truth for numbers) | [`ti-framework/`](ti-framework/) | Python package `ti_framework`, CLI `ti`, pytest suite; xlsx **and** CSV inputs against one schema |
| Alignment contract | [`ti-framework/ti_framework/alignment/`](ti-framework/ti_framework/alignment/) | Sector registry, like-for-like comparison rules, coverage, and shared read-only query service |
| Data pipeline | [`data-pipeline/`](data-pipeline/) | `build_dataset.py` publishes source-backed benchmark data and provenance; [collection backlog](data-pipeline/COLLECTION_STATUS.md); [removed-estimate record](data-pipeline/ESTIMATES.md) |
| Web app (Vercel) | [`web/`](web/) | Next.js Toyota/EU27, JERA/Japan, and KOEN/Korea evidence pages plus an explicit publication gate. No estimated firm result is rendered |
| MCP server | [`mcp-server/`](mcp-server/) | Read-only tools/resources/prompts over the same published data used by the web app |
| Product contract | [`docs/PRODUCT_CONTRACT.md`](docs/PRODUCT_CONTRACT.md) | Multi-sector comparison boundary and publication rules; [sector expansion](docs/SECTOR_EXPANSION.md); [evidence audit](docs/EVIDENCE_AUDIT.md) |
| Theory ↔ code contract | [`theory/SYNC.md`](theory/SYNC.md) | Anchors ↔ docstring tokens ↔ tests, enforced by [`scripts/check_sync.py`](scripts/check_sync.py) in CI |
| Assumption / conflict log | [`ti-framework/NOTES.md`](ti-framework/NOTES.md) | Every default, fallback, and doc conflict (D1–D4) |

Deploy: see [DEPLOY.md](DEPLOY.md). Method rules that never bend: S1/S2/S3 always
reported together; TI never netted against Scope 3; missing inputs stay missing and
flagged — never fabricated.

Published data is content-addressed: metadata records hashes for the engine source,
workbook, target-company sources, compute service, and complete dataset. `countries.json`
contains only workbook-backed country fields. Unsourced support parameters remain null in
`meta.json`; `contract.json` pins the future report schema without publishing the internal
illustrative validation fixture.

The legacy compute API still accepts bounded, user-supplied inputs for methodology validation,
but it is not the public alignment contract. Public direct comparisons fail closed unless sector,
metric definition, applicable geography, and unit match. Missing activity remains missing.
