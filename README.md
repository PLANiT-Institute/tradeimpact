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
| Automotive comparison | [`data-pipeline/adapters/automotive_eea.py`](data-pipeline/adapters/automotive_eea.py) | 2024 Toyota- and Hyundai-brand EU27 registrations on one destination, product, and powertrain boundary |
| Destination inputs | [`data-pipeline/adapters/destination_eu.py`](data-pipeline/adapters/destination_eu.py) | Distance, operating life, fleet baseline, grid intensity, and S1/S2/S3 pathways per EU27 market, each with a tier and a stated derivation |
| Lifetime run | [`data-pipeline/lifetime_run.py`](data-pipeline/lifetime_run.py) | Joins observed cohorts to destination inputs, runs the engine, and writes the report bundle |
| Web application | [`web/`](web/) | Lifetime result, decomposition, destination exposure, sensitivity, target hierarchy, and data gaps |
| MCP server | [`mcp-server/`](mcp-server/) | Read-only lifetime-result, destination-input, cohort, pathway, readiness, and source queries |
| Whitepaper and automotive method | [`Whitepaper & Guidelines/`](Whitepaper%20%26%20Guidelines/) | Theory, equations, scenario architecture, and sector-specific rules |

The first comparison contains 803,094 Toyota-brand and 429,936 Hyundai-brand 2024 EU27 first
registrations, resolved into 1,286 destination × commercial-name × powertrain evidence rows. It
establishes destination and product mix but does not prove Japanese or Korean export origin.
Toyota reports that about seven in ten European sales are produced in Europe; Hyundai reports
around 80% for its broader European scope in the first three quarters of 2024. These company-level
claims are context only, not registration-to-factory mappings.

## First lifetime result

Every destination-side input is now sourced, so the lifetime calculation runs. Both cohorts are a
net liability against all three pathways, and the result is published as a direction rather than a
precise magnitude because more than half the affected units run on a proxied distance.

| Cohort | Units | Covered | S1 current trajectory | S2 committed policy | S3 1.5°C aligned |
|---|---|---|---|---|---|
| Toyota EU27 2024 | 803,094 | 96.9% | −1.40 MtCO₂e | −5.97 | −13.95 |
| Hyundai EU27 2024 | 429,936 | 95.6% | −1.49 MtCO₂e | −3.72 | −7.78 |

Toyota's 610,881 non-plug-in hybrids are the single largest liability under a 1.5°C-aligned
benchmark (−10.41 Mt); Hyundai's 41,582 battery-electric registrations are the only positive
contribution in any scenario, and that advantage shrinks as the benchmark tightens.

What is *not* in those numbers stays visible rather than being absorbed: PHEV and FCEV
registrations are withheld with their unit counts because no utility factor or hydrogen intensity
is sourced; the rolling-portfolio indicator is withheld because repeating a single observed cohort
would publish a counterfactual; and registrations are still not mapped to production origin, so
this is a destination-cohort impact and not an export claim.

## Published data

`data/published/` contains:

- `product_cohorts.json` — observed sold/deployed product cohorts and mapping coverage;
- `destination_inputs.json` — sourced distance, operating life, fleet baseline, grid intensity, and S1/S2/S3 rates per market, with tier, reference year, derivation, and warnings;
- `lifetime_results.json` — lifetime TI per scenario with destination and product-type decomposition, coverage, and sensitivity;
- `pathways.json` — destination target hierarchy, proxy role, and source IDs;
- `impact_readiness.json` — observed and missing inputs plus publication decision;
- `sources.json` — structured provenance;
- `sectors.json` — sector-specific boundaries and data requirements;
- `company_metrics.json` and `benchmarks.json` — supporting current-period evidence;
- `meta.json` — method versions, content hashes, and inventory counts.

Build and verify the dataset:

```bash
ti-framework/.venv/bin/python data-pipeline/adapters/destination_eu.py --refresh
ti-framework/.venv/bin/python data-pipeline/build_dataset.py
ti-framework/.venv/bin/python data-pipeline/check_published.py
ti-framework/.venv/bin/python data-pipeline/lifetime_run.py --out outputs
```

The last command writes, per cohort, the run input, five result CSVs, the data-quality
declaration, and the charts. `check_published.py` recomputes the whole published set from the
committed snapshots and fails if a single number drifts.

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
