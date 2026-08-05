# Trade Impact (TI) — exported-product climate exposure

Trade Impact asks a specific question: **when a company sells a product into a destination
market, will that product's use-phase emissions over its operating life help or obstruct the
destination's sector pathway and NDC?**

The framework begins with observed company sales or deployment cohorts, keeps product technology
and destination geography attached, builds an annual use-phase trajectory, and compares that
trajectory with the destination's policy-committed sector benchmark. It is additional to Scope 3
Category 11 and must never be used to reduce or offset a company's GHG inventory.

## Analytical chain

```text
company × cohort year × destination × product
    → product emissions channel and efficiency
    → destination use, survival, fuel/grid pathway
    → destination sector benchmark (NDC fallback disclosed)
    → annual and cumulative contribution / carbon lock-in
    → decomposition by destination and product type
```

Observed inputs, sourced scenario inputs, and derived outputs are separate objects. Missing
lifetime, use, energy, or policy inputs produce an unavailable result—not zero and not an invented
estimate.

## Current implementation

| Piece | Where | Role |
|---|---|---|
| Calculation engine | [`ti-framework/`](ti-framework/) | S1/S2/S3 lifetime cohort engine with country and product decomposition |
| Exported-product contract | [`docs/PRODUCT_CONTRACT.md`](docs/PRODUCT_CONTRACT.md) | Required dimensions, target hierarchy, readiness gate, and publication rules |
| Data pipeline | [`data-pipeline/`](data-pipeline/) | Reproducible source snapshots and published cohort/pathway/readiness JSON |
| Toyota pilot | [`data-pipeline/adapters/automotive_eea.py`](data-pipeline/adapters/automotive_eea.py) | 2024 Toyota-brand EU27 registrations by destination, commercial name, and powertrain |
| Web application | [`web/`](web/) | Visual cohort, portfolio, destination exposure, target hierarchy, and data gaps |
| MCP server | [`mcp-server/`](mcp-server/) | Read-only cohort, destination-pathway, readiness, and source queries |
| Whitepaper and automotive method | [`Whitepaper & Guidelines/`](Whitepaper%20%26%20Guidelines/) | Theory, equations, scenario architecture, and sector-specific rules |

The first live cohort contains 803,094 Toyota-brand 2024 EU27 first registrations, resolved into
660 destination × commercial-name × powertrain evidence rows. It establishes destination and
product mix but does not prove production/export origin. A lifetime TI result is currently
withheld because destination VKT, survival, real-world correction, country-level transport/grid
pathways, PHEV utility factors, and hydrogen intensity are not yet source-complete.

## Published data

`data/published/` contains:

- `product_cohorts.json` — observed sold/deployed product cohorts and mapping coverage;
- `pathways.json` — destination target hierarchy, proxy role, and source IDs;
- `impact_readiness.json` — observed and missing inputs plus publication decision;
- `sources.json` — structured provenance;
- `sectors.json` — sector-specific boundaries and data requirements;
- `company_metrics.json` and `benchmarks.json` — supporting current-period evidence;
- `meta.json` — method versions, content hashes, and inventory counts.

Build and verify the dataset:

```bash
ti-framework/.venv/bin/python data-pipeline/build_dataset.py
ti-framework/.venv/bin/python data-pipeline/check_published.py
```

Run the web app:

```bash
cd web
npm run dev:local
```

Run the MCP server:

```bash
tradeimpact-mcp --transport stdio
# or local HTTP
tradeimpact-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Deployment notes are in [`DEPLOY.md`](DEPLOY.md). Code is published under GNU GPL v3.
