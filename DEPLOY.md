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
`web/requirements.txt` (numpy, pandas). The engine source is vendored into
`web/api/_engine/` by the prebuild script, so the function needs no path outside `web/`.

## Data flow / redeploy

```
edit TI_Data_Workbook_v0.1.xlsx (or a fixture / ESTIMATES value)
  → ti-framework/.venv/bin/python data-pipeline/build_dataset.py   # reruns engine, stamps meta.json
  → commit data/published/ + push                                  # Vercel redeploys
```

`data/published/` is committed (deterministic deploys, provenance pinned to the commit).
`meta.json` records engine SHA, workbook hash, and build date — every report page shows
it. Firm benchmarks (grid, S2 NDC rates, FLAG status) merge from the workbook at
build-dataset time, so a workbook change flows to the published firm results with zero
code edits (verified: doubling KR grid moved Hyundai S2 from −4.38 to −5.30 MtCO₂e).

## Local development

```bash
cd ti-framework && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cd ../web && npm install
../ti-framework/.venv/bin/python scripts/dev_compute.py &   # compute on :8901
npm run dev:local                                           # Next dev with /api/compute rewrite
```

## CI

`.github/workflows/ci.yml`: engine (ruff, mypy, pytest on 3.11/3.12), theory-sync
(`scripts/check_sync.py`), and dataset+web build.
