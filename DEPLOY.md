# Deploying the Trade Impact web app

The web application is static-first. Next.js renders the published cohort, pathway, readiness,
and source JSON at build time. The former public research calculator and Python compute function
have been removed; audited calculations run in `ti-framework`, while external read-only access is
provided through the MCP server.

## Vercel setup

1. Import this GitHub repository.
2. Set the root directory to `web`.
3. Keep “Include source files outside of the Root Directory” enabled so the build can copy
   `data/published`.
4. No environment variable is required for the static site.

## Data flow

```text
source snapshot / adapter / workbook
  → ti-framework/.venv/bin/python data-pipeline/build_dataset.py
  → ti-framework/.venv/bin/python data-pipeline/check_published.py
  → commit data/published and push
  → Next.js prebuild copies the content-addressed dataset
```

`meta.json` records engine, workbook, source-adapter, and complete-dataset hashes. Unsupported
lifetime results remain absent until the evidence gate is complete.

For a Vercel CLI deploy, run `npm run deploy:vercel` from `web`. A packaged copy is accepted for
two hours and only when its data and dataset hashes match.

## Local development

```bash
cd web
npm install
npm run dev:local
```

## CI

CI validates the Python engine, theory-to-code anchors, deterministic dataset freshness, cohort
reconciliation, source and target roles, MCP queries, web data contracts, and the production
Next.js build.

The MCP server is deployed separately. Local `stdio`, loopback HTTP, and remote security gates are
documented in [`docs/MCP.md`](docs/MCP.md) and [`mcp-server/README.md`](mcp-server/README.md).
