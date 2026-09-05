# Trade Impact (TI) — automotive case study

Does a company's exported product help or obstruct the importing country's committed
decarbonisation path over the product's operating lifetime? The methodology is the
[TI whitepaper](methodology/TI_Whitepaper_v1.6.md) and the
[automotive technical guideline](methodology/TI_Automotive_Technical_Guideline_v1.9.md);
the engagement is governed by the Climate Arc grant proposal (see `claude-docs/`).

## Research process

1. **Targets** — companies: Hyundai and Kia (Korea) and Toyota and Nissan (Japan). Lexus,
   Genesis, Honda, Suzuki, Mazda, Mitsubishi and Subaru have pinned EEA snapshots and sit
   out of scope (`in_scope = no` in `data/auto/sales/method/companies.csv`), so any of them
   enters on one flag. Destinations: a company's sales to every
   country worldwide (whitepaper Level 1, operating-country basis) — the reader filters
   destinations in the dashboard (US only, everything except Korea, …). Benchmarks exist
   today for the EU27 member states, the United States and Korea; `ti_coverage.csv` shows
   every other destination in the sales files with the reason it is not yet assessed.
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
methodology/       whitepaper + automotive and power guidelines (methodology truth source)
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
data/power/        the power case study, same raw/processed/method triple per dataset:
                         companies, projects (Global Energy Monitor, hand download), roles (hand
                         register), grid, emission_factors, targets, geography; output/ and
                         registry/ as for auto
script/power/      its pipeline (fetch, extract, derive, model) and run_all.py, which stops with
                         [hand] when a hand-gathered file is missing
script/registry.py provenance registry helpers shared by both sectors
archive/           the previous application build (engine, web, MCP, pipeline) — read-only
```

Datasets: `sales`, `country_emissions`, `emission_targets`, `vehicle_usage`,
`vehicle_technology`, `trade_flows` (official HS 8703 trade statistics by powertrain class,
country-level, from Eurostat Comext and UN Comtrade — free sources first). Current
result set: four companies across four destination markets — the EU27 (2024
registrations), the United States, Japan and Korea, each assessed on that market's own
official statistics. The engine reproduces the
previously published EU27 result exactly when fed the archived inputs (see
`data/auto/output/method.md`, Verification).

| Market, cohort | Company | Covered | S1 current | S2 committed policy |
|---|---|---|---|---|
| EU27, 2024 registrations | Toyota | 96.8 % | **+1.68 MtCO₂e** | **+14.37** |
| EU27, 2024 registrations | Hyundai | 95.4 % | **+1.66** | **+8.00** |
| EU27, 2024 registrations | Kia | 91.4 % | **+1.52** | **+7.37** |
| EU27, 2024 registrations | Nissan | 99.8 % | **+1.44** | **+4.43** |
| US, 2024 brand sales | Toyota | 97.8 % | −5.53 | **+19.00** |
| US, 2024 brand sales | Hyundai | 99.0 % | −1.56 | **+8.84** |
| US, 2024 brand sales | Kia | 98.0 % | −1.01 | **+8.77** |
| US, 2024 brand sales | Nissan | 99.9 % | −2.26 | **+8.63** |
| US, 2025 brand sales | Toyota | 98.3 % | −8.07 | **+18.60** |
| US, 2025 brand sales | Hyundai | 98.4 % | −1.50 | **+9.63** |
| US, 2025 brand sales | Kia | 98.2 % | −0.001 | **+10.52** |
| US, 2025 brand sales | Nissan | 100.0 % | −1.36 | **+9.65** |
| US, Jan–Jun 2026 retail | Kia | 98.0 % | **+0.49** | **+5.81** |
| Japan, 2024 registrations | Toyota | 99.3 % | −1.07 | **+3.50** |
| Japan, 2024 registrations | Nissan | 93.7 % | −0.35 | **+0.47** |
| Japan, 2025 registrations | Toyota | 100.0 % | −1.13 | **+3.53** |
| Japan, 2025 registrations | Nissan | 94.6 % | −0.24 | **+0.41** |
| Korea, 2024 domestic sales | Hyundai | 94.7 % | −5.02 | **+4.24** |
| Korea, 2025 domestic sales | Hyundai | 94.4 % | −4.84 | **+4.06** |
| Korea, Jan–Jun 2026 retail | Kia | 98.7 % | −1.86 | **+1.65** |

### How much of worldwide sales this captures

| Company | Cohort | Worldwide sales | Assessed | Held | Countries assessed |
|---|---|---|---|---|---|
| Toyota | 2024 | 10.16 M | 38.5 % | 42.6 % | 28 |
| Hyundai | 2024 | 4.17 M | 42.4 % | 48.7 % | 28 |
| Nissan | 2024 | 3.35 M | 38.1 % | 40.3 % | 28 |
| Kia | 2026 H1 | 1.62 M | 44.2 % | 100.0 % | 2 |

`Assessed` is units carrying a result over the company's own worldwide figure; `Held` is every
unit the project holds for those brands, assessed or not, so the gap between the two is sales we
have but cannot yet price. The denominator covers the brands the company reports together, and
the cohorts hold Lexus, Infiniti and Genesis apart, so those units sit in `Held` and are named
in `brands_out_of_scope`. Toyota's and Nissan's worldwide figures are their own published
totals; Hyundai's is derived from its three workbooks because it publishes no single total, and
Kia's is the sum of every destination in its retail release. Full detail, including the 2025
cohorts where only the United States is assessed, is in `ti_global_coverage.csv`.

The `Covered` column in the tables above is the sales coverage within a market: units carrying a
result over units in the source.
Every EU27 row covers 26 of the 27 member states (Luxembourg is withheld, its fleet intensity
being implausible); every US, Japanese and Korean row covers one country. `ti_data_quality.csv` lists the
country codes themselves in `countries`, with `countries_covered` and `countries_withheld`
beside them, and `ti_source_reconciliation.csv` puts every source a company published for the
same cell side by side.

**Sign convention.** TI is the product's emissions minus the benchmark's, so it reads the way
an inventory reads: **positive = tonnes added** over the vehicles' lifetime, emissions the
destination is locked into (bold in the table above); **negative = tonnes avoided** against the
benchmark. The opposite convention is common in avoided-emissions reporting — this project does
not use it. Markets are never summed: different sales bases, test cycles and benchmarks. Withheld units (PHEV, FCEV, no certified value, Luxembourg's
implausible benchmark, the Genesis brand, Ioniq 9 without an EPA row) are listed, not absorbed.

The tables above are lifetime totals. Every one of them has an annual twin that carries both
sides of the comparison in each calendar year rather than only the net figure —
`ti_annual.csv` per company, `ti_annual_country.csv` per destination,
`ti_annual_powertrain.csv` per powertrain, and `ti_annual_by_model.csv` per cohort cell. Each
row gives `e_ref_tco2e` (what the surviving fleet would have emitted on that scenario's
benchmark), `e_prod_tco2e` (what it actually emits), their difference, the running total, and
all three per surviving vehicle. The dashboard's *Results by year* view opens on exactly that,
one column per calendar year.

Read the US rows with their caveats: the cohorts are the companies' own US releases (Hyundai
IR "US Retail Sales" 2024 and 2025, imports included, brand total despite the label; Kia
America full years 2024 and 2025; Kia IR Jan–Jun 2026, a half year); the US S1 benchmark is
the all-light-duty fleet including pickups (217 gCO₂/km, declining 1.1 %/yr) with the segment
ratio set to 1.0, which is why compact crossovers and hybrids sit below it — a segment-matched
benchmark would raise or reverse the S1 avoidances; and nameplates the releases do not split
by powertrain are divided with EPA Automotive Trends MY2024 production shares (assumption
A-US-PT in `data/auto/output/method.md`) with an all-HEV bound (`ti_sensitivity.csv`,
dimension `powertrain_mix`). Cohort years are never pooled: each row above is one sale year.
Korea is assessed on free Korean official statistics (MOLIT stock and age, KOTSA distance, GIR
inventory, KEA label fuel economy, the 2050 carbon-neutral scenarios); its fleet
intensity is tier C because the national inventory has no passenger-car split (see
`data/auto/output/method.md`, Korea). Japan is assessed the same way, on Japanese official statistics
only: the JADA nameplate ranking for volumes (top 50 nameplates, kei and foreign brands
excluded by the source), MLIT's fuel-economy list for the certified gCO₂/km of every grade,
MLIT's Motor Vehicle Fuel Consumption Survey for distance, AIRIA's published mean years of
use for the vehicle life, the
GIO/NIES inventory for road CO₂ by vehicle type, and the GX 2040 target for S2. Japan is the
only market whose distance and stock come from one table at one date and whose lifetime is
published rather than derived — and the only one where battery-electric units cannot be assessed
at all, because the fuel-economy list is a fuel-consumption publication and carries no
electricity
rating. The US S2 benchmark is the NDC the United States
communicated on 2024-12-19 (61 % below 2005 net GHG by 2035) — the last pathway its own
government stated, a month before it notified withdrawal from the Paris Agreement; the
`target_level` column carries that status, and a market whose rate were ever empty would still
appear as a row in `ti_company.csv` and `ti_exclusions.csv`, never as a silent gap. EU27 magnitudes are proxy-heavy (48 % of covered units on an EU-average distance,
guideline §5.3 threshold 50 %).

## The analysis report

`data/auto/report/ti_automotive_report.html` is an interactive, tabbed analysis of the result
set, built by `script/auto/report/build_report.py` (with `template.html` beside it) and rebuilt
by `run_all.py` with everything else. Like the dashboard it carries no data of its own: it opens
`tradeimpact_auto.sqlite` in the browser (sql.js, d3 and topojson pinned on cdnjs with integrity
hashes) and computes every sentence, chart and table with SQL at read time, so a rebuild after a
data change moves the words as well as the figures, and a test asserts that no figure is written
into the file. Serve `data/auto` with `.venv/bin/python script/auto/serve_dashboard.py` and open
<http://127.0.0.1:8765/report/ti_automotive_report.html>; opened from disk the page offers a
file picker for the database instead.

The story runs left to right across seven main tabs, in the order the analysis is built, and each
tab opens sub-tabs (one per company, per market or per view); a filter bar — scenario, company,
market, cohort year — redraws the tab in view while the story text stays on the whole set:

1. **Sales** — what each company sold into which market, by powertrain, segment and nameplate,
   with the sales basis every row rests on.
2. **Coverage** — which units carry a result and why the rest are withheld; assessed share of
   worldwide sales; the two tier-C measures.
3. **Destination benchmarks** — per market: the observed emissions and grid series, the fleet
   parameters (EU27 on a map), the S1 and S2 pathways and the rates behind them.
4. **Other inputs** — annual distance, vehicle lifetime, certified product intensities by
   nameplate, real-world correction factors.
5. **Annual impact** — the company × market grid of year-by-year strips, one cohort's flat
   product line against its falling benchmark with a year scrubber, EU27 by member state, and by
   powertrain.
6. **Total impact** — the lifetime result per cohort under both scenarios, per vehicle, the
   crossover year, the same nameplate across markets, the sensitivity tornado and the full
   result table.
7. **Sources** — the table manifest with content hashes, the source registry and raw-file
   provenance.

The findings the story states, each recomputed at read time: against each destination's own
committed pathway every cohort adds emissions while most avoid against the observed trend; a
cohort stops beating its committed benchmark about five years after sale in every market;
hybrids beat the trend and not the target, battery-electric avoids under both; the same nameplate
avoids in one market and adds several tonnes a vehicle in another; inside the EU27 geography
outweighs technology; and vehicle lifetime moves the result more than any other input without
turning a committed-policy addition into an avoidance.

## The power case study

`data/power/` applies the same framework to the overseas power projects of Korean and Japanese
companies — the generating units they own, built, supplied or financed — measured year by year
against the grid of the country they feed (`methodology/TI_Power_Technical_Guideline_v1.0.md`,
`data/power/output/method.md`). The unit of analysis is a generating unit from the Global Energy
Monitor tracker; attribution is per **role** (developer, equity owner, EPC contractor, equipment
supplier, O&M, lender, ECA cover) with the **phase** and **share** as data columns, never pooled
across roles; the emission factor is the destination's own where on file and the IPCC 2006
default otherwise; the benchmark is the destination grid under S1 (observed trend) and S2
(committed target). Results are published per unit with coordinates and per company × role.
Status and the list of hand-gathered inputs the pipeline waits on are in
`data/power/output/method.md`.

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
  proxied inputs are directions, not precise magnitudes. Always report S1 and S2 together.

## License

GNU GPL v3 — see [LICENSE](LICENSE). © 2026 PLANiT Institute.
