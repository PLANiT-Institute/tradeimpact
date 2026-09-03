# Trade Impact (TI) — automotive case study

Does a company's exported product help or obstruct the importing country's committed
decarbonisation path over the product's operating lifetime? The methodology is the
[TI whitepaper](methodology/TI_Whitepaper_v1.5.md) and the
[automotive technical guideline](methodology/TI_Automotive_Technical_Guideline_v1.8.md);
the engagement is governed by the Climate Arc grant proposal (see `claude-docs/`).

## Research process

1. **Targets** — exporters: Hyundai, Kia (Korea); Toyota, Honda (Japan). Importers: EU27
   member states, United States, Australia.
2. **Gather data** — per importer: sector and electricity emissions, emission targets
   (NDC and sector standards); vehicle usage (distance, lifetime, stock); vehicle
   technology (certified intensity, real-world correction, utility factors); and the
   exporters' sales/registrations per market.
3. **Build the reference** — the dynamic NDC-derived sector benchmark per importer
   (whitepaper §3.1, guideline §2.3).
4. **Build the impact** — actual emission avoidance or addition per model × market ×
   scenario: lifetime product trajectory vs the benchmark (whitepaper §3.2–3.5).
5. **Aggregate to the country** — sum to importer-country and exporter-company totals with
   the decomposition identity intact (whitepaper §3.6–3.7).

## Layout

```text
methodology/       whitepaper + automotive guideline (methodology truth source)
claude-docs/       research governance: charter, phases, stages, process, tracker
data/auto/         one directory per dataset, each with:
  <dataset>/raw/         source files exactly as obtained — never edited
  <dataset>/processed/   tidy CSV produced only by scripts
  <dataset>/method/      method.md: what it is, fields, sources, rules
  output/                model results (steps 3–5), with output/method.md
  sources.csv            source registry: every source_id with link, access date, licence
  raw_files.csv          raw-file provenance: original name, SHA-256, source_id
  tradeimpact_auto.sqlite   THE deliverable: every input, lookup, output and source in one DB
script/auto/       all Python, one directory per dataset plus model/
  <dataset>/             extraction scripts: raw/ -> processed/
  model/                 build_reference, build_ti, aggregate_country, build_database
archive/           the previous application build (engine, web, MCP, pipeline) — read-only
```

Datasets: `sales`, `country_emissions`, `emission_targets`, `vehicle_usage`,
`vehicle_technology`. Current result set: EU27 × 2024 × {Toyota, Hyundai}; it reproduces
the previously published lifetime result to 2 × 10⁻⁷ (see `data/auto/output/method.md`).

Setup and full run:

```bash
uv venv .venv && uv pip install -e ".[dev]" --python .venv/bin/python
for s in sales/extract_eea_registrations sales/extract_kia_ir sales/extract_hyundai_ir \
         vehicle_technology/extract_eea_certified vehicle_usage/extract_eu27_eurostat \
         country_emissions/extract_eu27_snapshot emission_targets/derive_eu27_rates \
         model/build_reference model/build_ti model/aggregate_country model/build_database; do
  .venv/bin/python script/auto/$s.py; done
```

## Naming convention

Everything is lowercase `snake_case` — directories, Python files, data files, CSV columns.
The only capitalised files are `README.md` and `LICENSE`. Raw files are renamed to
`snake_case` on arrival; the original name and SHA-256 are recorded in the dataset's
`method/method.md`.

## Non-negotiables (from the whitepaper and guideline)

- TI is additional to Scope 3 Category 11 and never offsets it.
- A missing input produces an unavailable result — never zero, never a silent default.
- Every processed row carries a `source_id`; every raw file is hash-recorded in its
  `method.md`.
- Proxies and tiers are disclosed; results on proxied inputs are directions, not precise
  magnitudes. Always report S1/S2/S3 together.

## License

GNU GPL v3 — see [LICENSE](LICENSE). © 2026 PLANiT Institute.
