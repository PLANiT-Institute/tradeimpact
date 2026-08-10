# Deploying the Trade Impact web app

The web application is static-first. Next.js renders the published cohort, pathway, readiness,
and source JSON at build time. The former public research calculator and Python compute function
have been removed; audited calculations run in `ti-framework`, while external read-only access is
provided through the MCP server.

## Vercel setup

The project (`plan-i-t/tradeimpact`) is **not connected to the GitHub repository**: its `link`
is null, so pushing to `main` deploys nothing. Every production release so far has been a CLI
deploy from `web/`, and that is the supported path until someone connects the repository.

Deploy a release from `web/`:

```bash
npm run package:deploy   # copies data/published into public/data and stamps a manifest
npx vercel --prod
```

`prepare.mjs` runs again on Vercel, finds no `../data/published` in the uploaded root, and falls
back to the packaged copy — which it accepts only if the manifest is under two hours old and its
data and dataset hashes match. Package immediately before deploying, or the build fails closed.

To switch to Git-triggered deploys instead, connect the repository, set the root directory to
`web`, and keep “Include source files outside of the Root Directory” enabled so the build can
read `data/published` directly. No environment variable is required either way.

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

`npm run deploy:vercel` is the same flow without `--prod`, which produces a preview URL and
leaves production alone.

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
