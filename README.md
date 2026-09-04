# Trade Impact (TI) — automotive case study

Does a company's exported product help or obstruct the importing country's committed
decarbonisation path over the product's operating lifetime? The methodology is the
[TI whitepaper](methodology/TI_Whitepaper_v1.5.md) and the
[automotive technical guideline](methodology/TI_Automotive_Technical_Guideline_v1.8.md);
the engagement is governed by the Climate Arc grant proposal (see `claude-docs/`).

## Research process

1. **Targets** — companies: Hyundai and Kia (Korea) and Toyota and Nissan (Japan). Lexus,
   Genesis, Honda, Suzuki, Mazda, Mitsubishi and Subaru have pinned EEA snapshots and sit
   out of scope (`in_scope = no` in `data/auto/sales/method/companies.csv`), so any of them
   enters on one flag. Destinations: a company's sales to every
   country worldwide (whitepaper Level 1, operating-country basis) — the reader filters
   destinations in the dashboard (US only, everything except Korea, …). Benchmarks exist
   today for the EU27 member states, the United States and Korea; `ti_coverage.csv` shows
   every other destination in the sales files with the reason it is not yet priced.
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
  registry/              sources.csv (every source_id with link, access date, licence),
                         raw_files.csv (raw-file provenance: original name, SHA-256, source_id),
                         tiers.csv (the A/B/C data-quality hierarchy) and value_tiers.csv (the
                         per-value tier rules applied when the database is built)
  dashboard/             raw/ world geometry and ISO code list, method/ country_codes.csv
                         (the geometry is loaded into the database, so the page needs no
                         second file)
  database/              tradeimpact_auto.sqlite: raw, lookup, processed and output tables with
                         per-value tier flags, sources, raw-file provenance, the map geometry,
                         a tables manifest and a column dictionary; dashboard.html: reader for
                         that database, no data of its own: lineage, results, results by year,
                         map by country, pivot, browse and read-only SQL
script/auto/       all Python, one directory per dataset plus model/
  <dataset>/             extraction scripts: raw/ -> processed/
  model/                 build_cohorts, build_reference (EU27), build_reference_us, build_ti,
                         build_sensitivity, aggregate_country, build_data_quality,
                         build_database, build_dashboard
  serve_dashboard.py     serves data/auto on http://127.0.0.1:8765 so database/dashboard.html
                         can read the database beside it and the map geometry
archive/           the previous application build (engine, web, MCP, pipeline) — read-only
```

Datasets: `sales`, `country_emissions`, `emission_targets`, `vehicle_usage`,
`vehicle_technology`, `trade_flows` (official HS 8703 trade statistics by powertrain class,
country-level, from Eurostat Comext and UN Comtrade — free sources first). Current result set: Hyundai and Kia in the EU27 (2024 registrations)
and the United States (the cohorts in the gathered IR workbooks). The engine reproduces the
previously published EU27 result exactly when fed the archived inputs (see
`data/auto/output/method.md`, Verification).

| Market, cohort | Company | Covered | S1 current | S2 committed | S3 1.5 °C |
|---|---|---|---|---|---|
| EU27, 2024 registrations | Toyota | 96.8 % | −1.68 MtCO₂e | −6.29 | −14.37 |
| EU27, 2024 registrations | Hyundai | 95.4 % | −1.66 | −3.82 | −8.00 |
| EU27, 2024 registrations | Kia | 91.4 % | −1.52 | −3.49 | −7.37 |
| EU27, 2024 registrations | Nissan | 99.8 % | −1.44 | −2.38 | −4.43 |
| US, 2024 brand sales | Toyota | 97.8 % | **+5.53** | excluded (no NDC in force) | −29.92 |
| US, 2025 brand sales | Toyota | 98.3 % | **+8.07** | excluded (no NDC in force) | −30.50 |
| US, 2024 brand sales | Nissan | 99.9 % | **+2.26** | excluded (no NDC in force) | −13.32 |
| US, 2025 brand sales | Nissan | 100.0 % | **+1.36** | excluded (no NDC in force) | −14.46 |
| US, 2024 brand sales | Hyundai | 99.0 % | **+1.56** | excluded (no NDC in force) | −13.13 |
| US, 2025 brand sales | Hyundai | 98.4 % | **+1.50** | excluded (no NDC in force) | −14.20 |
| US, 2024 brand sales | Kia | 98.0 % | **+1.01** | excluded (no NDC in force) | −12.77 |
| US, 2025 brand sales | Kia | 98.2 % | **+0.00** | excluded (no NDC in force) | −14.96 |
| US, Jan–Jun 2026 retail | Kia | 98.0 % | −0.49 | excluded (no NDC in force) | −8.11 |
| Korea, 2024 domestic sales | Hyundai | 99.3 % | **+1.89** | −0.96 | −2.49 |
| Korea, 2025 domestic sales | Hyundai | 98.8 % | **+2.17** | −0.92 | −2.56 |
| Korea, Jan–Jun 2026 retail | Kia | 93.3 % | **+1.30** | −0.53 | −1.50 |

### How much of worldwide sales this captures

| Company | Cohort | Worldwide sales | Priced | Held | Countries priced |
|---|---|---|---|---|---|
| Toyota | 2024 | 10.16 M | 26.8 % | 42.6 % | 27 |
| Hyundai | 2024 | 3.98 M | 41.6 % | 47.5 % | 28 |
| Nissan | 2024 | 3.35 M | 31.7 % | 40.3 % | 27 |
| Kia | 2026 H1 | 1.62 M | 43.2 % | 100 % | 2 |

`Priced` is units carrying a result over the company's own worldwide figure; `Held` is every
unit the project holds for those brands, priced or not, so the gap between the two is sales we
have but cannot yet price. The denominator covers the brands the company reports together, and
the cohorts hold Lexus, Infiniti and Genesis apart, so those units sit in `Held` and are named
in `brands_out_of_scope`. Toyota's and Nissan's worldwide figures are their own published
totals; Hyundai's is derived from its three workbooks because it publishes no single total, and
Kia's is the sum of every destination in its retail release. Full detail, including the 2025
cohorts where only the United States is priced, is in `ti_global_coverage.csv`.

The `Covered` column in the tables above is the sales coverage within a market: units carrying a
result over units in the source.
Every EU27 row covers 26 of the 27 member states (Luxembourg is withheld, its fleet intensity
being implausible); every US and Korean row covers one country. `ti_data_quality.csv` lists the
country codes themselves in `countries`, with `countries_covered` and `countries_withheld`
beside them, and `ti_source_reconciliation.csv` puts every source a company published for the
same cell side by side.

Negative = lifetime emissions above the destination's committed benchmark (lock-in
liability); positive = below it (contribution). Markets are never summed: different sales
bases, test cycles and benchmarks. Withheld units (PHEV, FCEV, no certified value, Luxembourg's
implausible benchmark, the Genesis brand, Ioniq 9 without an EPA row) are listed, not absorbed.

Read the US rows with their caveats: the cohorts are the companies' own US releases (Hyundai
IR "US Retail Sales" 2024 and 2025, imports included, brand total despite the label; Kia
America full years 2024 and 2025; Kia IR Jan–Jun 2026, a half year); the US S1 benchmark is
the all-light-duty fleet including pickups (217 gCO₂/km, declining 1.1 %/yr) with the segment
ratio set to 1.0, which is why compact crossovers and hybrids sit below it — a segment-matched
benchmark would lower or reverse the S1 contributions; and nameplates the releases do not split
by powertrain are divided with EPA Automotive Trends MY2024 production shares (assumption
A-US-PT in `data/auto/output/method.md`) with an all-HEV bound (`ti_sensitivity.csv`,
dimension `powertrain_mix`). Cohort years are never pooled: each row above is one sale year.
Korea is priced on free Korean official statistics (MOLIT stock and age, KOTSA distance, GIR
inventory, KEA label fuel economy, the 2023 Basic Plan and the 2050 scenarios); its fleet
intensity is tier C because the national inventory has no passenger-car split (see
`data/auto/output/method.md`, Korea). The US S2 scenario is excluded because no
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
- Proxies and tiers are disclosed: every input value carries a tier (A directly sourced,
  B estimated or derived, C proxy) in the database, and every result cell carries its Layer 1,
  Layer 2 and worst tier (`data/auto/registry/tiers.csv`, `value_tiers.csv`). Results on
  proxied inputs are directions, not precise magnitudes. Always report S1/S2/S3 together.

## License

GNU GPL v3 — see [LICENSE](LICENSE). © 2026 PLANiT Institute.
