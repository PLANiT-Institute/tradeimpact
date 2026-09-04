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
  dashboard.html            the database embedded in one page: lineage raw -> processed -> output
                            per data type, pivot table, browse and read-only SQL (open from disk)
script/auto/       all Python, one directory per dataset plus model/
  <dataset>/             extraction scripts: raw/ -> processed/
  model/                 build_reference, build_ti, build_sensitivity, aggregate_country,
                         build_data_quality, build_database, build_dashboard
archive/           the previous application build (engine, web, MCP, pipeline) — read-only
```

Datasets: `sales`, `country_emissions`, `emission_targets`, `vehicle_usage`,
`vehicle_technology`. Current result set: EU27 × 2024 × {Toyota, Honda, Hyundai, Kia}, all
from one EEA registration query. The engine reproduces the previously published lifetime
result exactly when fed the archived inputs; a review-driven fix to the distance derivation
moved the totals 1–13 % (see `data/auto/output/method.md`, Verification).

| Exporter (EU27, 2024) | Registrations | Covered | S1 current | S2 committed | S3 1.5 °C |
|---|---|---|---|---|---|
| Hyundai | 429,936 | 95.4 % | −1.66 MtCO₂e | −3.82 | −8.00 |
| Kia | 414,677 | 91.4 % | −1.52 | −3.49 | −7.37 |

Negative = lifetime emissions above the destination's committed benchmark (lock-in
liability). Withheld units (PHEV, FCEV, no certified value, and Luxembourg's 2,711 units
whose national benchmark is implausible) are listed, not absorbed. Both brands have just
under half their covered units in markets whose distance is an EU-average proxy (tier C:
48.5 % and 48.2 %), so magnitudes are published but proxy-heavy (guideline §5.3 threshold
50 %). Five methodological calls made on 2026-09-04 are recorded in
`data/auto/output/method.md` and `claude-docs/log/README.md`.

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
