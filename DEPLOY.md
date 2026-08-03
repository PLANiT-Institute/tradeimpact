# Deploying the TI web app to Vercel

The site is static-first: report pages are SSG from `data/published/*.json`; only the
calculator hits compute (`web/api/compute.py`, a Python function wrapping the vendored
engine — option A from the build plan, single source of truth, no TS math port).

## One-time project setup

1. Vercel → New Project → import this GitHub repo.
2. **Root Directory: `web`** (framework auto-detected: Next.js). Keep the default
   "Include source files outside of the Root Directory" **enabled** — the build copies
   `data/published/` and the engine from the repo root (`web/scripts/prepare.mjs`).
3. No env vars needed. `TI_COMPUTE_URL` is local-dev only — do not set it on Vercel.

The Python function is bundled from `web/api/compute.py` with deps from
`web/requirements.txt` (numpy, pandas, openpyxl). The engine source is vendored into
`web/api/_engine/` by the prebuild script, so the function needs no path outside `web/`.

## Data flow / redeploy

```
edit a source snapshot/adapter or TI_Data_Workbook_v0.1.xlsx with sourced values
  → ti-framework/.venv/bin/python data-pipeline/build_dataset.py   # reruns engine, stamps meta.json
  → commit data/published/ + push                                  # Vercel redeploys
```

`data/published/` is committed and deterministically generated. `meta.json` records
content hashes for the engine source, workbook, target workbooks, compute service, and
complete dataset. An accepted adapter change flows to the company evidence pages; a workbook
change flows to the country evidence pages. Unsupported company reports remain absent until the
publication gate is satisfied.

For a Vercel CLI deploy, run `npm run deploy:vercel` from `web/`. It refreshes the copied
dataset and engine and writes a byte-level manifest immediately before upload. A remote
build without repository sources accepts that package only for two hours and only when
all hashes match; a clean or stale copy fails closed.

The public compute function also validates its request boundary before importing data into
the engine: 1 MB maximum JSON body, at most 50 countries and 500 placements, finite bounded
numeric inputs, and a maximum 50-year lifetime. Invalid requests return `400`; oversized
requests return `413`.

## Local development

```bash
cd ti-framework && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cd ../web && npm install
npm run dev:local   # prepares data, starts the :8901 compute sidecar AND next dev; cleans up on exit
```

Override the sidecar's Python with `TI_PYTHON=/path/to/python` if the engine venv
lives elsewhere.

## CI

`.github/workflows/ci.yml`: engine (ruff, mypy, pytest on 3.11/3.12), theory-sync
(`scripts/check_sync.py`), deterministic published-data freshness, source/coverage/comparison
contract validation, MCP tests, web data-contract tests, and the production web build.

The read-only MCP server is deployed separately from the static web app. Local `stdio` and
loopback HTTP usage, plus remote-service security gates, are documented in
[`docs/MCP.md`](docs/MCP.md) and [`mcp-server/README.md`](mcp-server/README.md).
