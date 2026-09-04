# Trade Impact (TI) — automotive case study

Does a company's exported product help or obstruct the importing country's committed
decarbonisation path over the product's operating lifetime? The methodology is the
[TI whitepaper](methodology/TI_Whitepaper_v1.5.md) and the
[automotive technical guideline](methodology/TI_Automotive_Technical_Guideline_v1.8.md);
the engagement is governed by the Climate Arc grant proposal (see `claude-docs/`).

## Research process

1. **Targets** — exporters: Hyundai and Kia (Korea) now; the Japanese exporters are
   deferred (their EEA snapshots stay pinned, `in_scope = no` in
   `data/auto/sales/method/companies.csv`). Importers: EU27 member states, United States,
   Australia.
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
  tradeimpact_auto.sqlite   the database: raw, lookup, processed and output tables, sources,
                            raw-file provenance, a tables manifest and a column dictionary
  dashboard.html            reader for that database, no data of its own: lineage
                            raw -> processed -> output per data type, pivot table, browse and
                            read-only SQL (serve data/auto, or open it and pick the file)
script/auto/       all Python, one directory per dataset plus model/
  <dataset>/             extraction scripts: raw/ -> processed/
  model/                 build_cohorts, build_reference (EU27), build_reference_us, build_ti,
                         build_sensitivity, aggregate_country, build_data_quality,
                         build_database, build_dashboard
  serve_dashboard.py     serves data/auto on http://127.0.0.1:8765 so dashboard.html can read
                         the database beside it
archive/           the previous application build (engine, web, MCP, pipeline) — read-only
```

Datasets: `sales`, `country_emissions`, `emission_targets`, `vehicle_usage`,
`vehicle_technology`. Current result set: Hyundai and Kia in the EU27 (2024 registrations)
and the United States (the cohorts in the gathered IR workbooks). The engine reproduces the
previously published EU27 result exactly when fed the archived inputs (see
`data/auto/output/method.md`, Verification).

| Market, cohort | Exporter | Covered | S1 current | S2 committed | S3 1.5 °C |
|---|---|---|---|---|---|
| EU27, 2024 registrations | Hyundai | 95.4 % | −1.66 MtCO₂e | −3.82 | −8.00 |
| EU27, 2024 registrations | Kia | 91.4 % | −1.52 | −3.49 | −7.37 |
| US, 2025 US-built sold in US | Hyundai | 91.5 % | **+1.53** | excluded (no NDC in force) | −4.80 |
| US, Jan–Jun 2026 retail | Kia | 100 % | −0.76 | excluded (no NDC in force) | −8.53 |

Negative = lifetime emissions above the destination's committed benchmark (lock-in
liability); positive = below it (contribution). EU27 and US are never summed: different sales
bases, test cycles and benchmarks. Withheld units (PHEV, FCEV, no certified value, Luxembourg's
implausible benchmark, the Genesis brand, Ioniq 9 without an EPA row) are listed, not absorbed.

Read the US rows with their caveats: the Hyundai cohort is US-built cars only (Korean-built
imports are not in the gathered file) and the Kia cohort is a half year; the US S1 benchmark
is the all-light-duty fleet including pickups (217 gCO₂/km, declining 1.1 %/yr) with the
segment ratio set to 1.0, which is why compact crossovers and hybrids sit below it — a
segment-matched benchmark would lower or reverse Hyundai's S1 contribution; and models the IR
files do not split by powertrain are priced as ICE centrally with an all-HEV bound
(`ti_sensitivity.csv`, dimension `powertrain_mix`). The US S2 scenario is excluded because no
NDC is in force; the exclusion is a row in `ti_company.csv` and `ti_exclusions.csv`, never a
silent gap. EU27 magnitudes are proxy-heavy (48 % of covered units on an EU-average distance,
guideline §5.3 threshold 50 %).

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
