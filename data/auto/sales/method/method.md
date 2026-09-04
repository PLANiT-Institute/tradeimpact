# sales — exporter sales / registrations by destination market

## What this dataset is

Observed sales or first registrations of the target exporters' vehicles in each importer
market, by model and powertrain, per cohort year. This is the `Volume(t)` term of the TI
formula and the anchor of the whole analysis (research process step 1–2).

- **Exporters in scope now**: Hyundai and Kia (Korea) — `method/companies.csv`. The Japanese
  exporters (Toyota, Honda) are deferred; their EEA snapshots stay pinned and re-enter with one
  flag change.
- **Importers**: EU27 member states and the United States now; Australia deferred.

## Required fields (processed output)

| field | type | unit | note |
|---|---|---|---|
| company | text | — | exporter brand in lower case (`companies.csv`) |
| destination | text | ISO 3166-1 alpha-2, or region label | importer market (country when the source gives it) |
| destination_level | text | — | `country`, `region` (Kia IR reports Europe, Eastern Europe, Middle East, …), or `unknown` (Hyundai IR export rows: plant-side, destination not stated) |
| origin | text | ISO 3166-1 alpha-2, or `ckd` / `special_vehicle` | production country when the source states the plant; empty for EEA registrations (origin unproven) |
| cohort_year | int | year | year of sale / first registration |
| period | text | — | months covered, e.g. `2024-01..2024-12`; IR year-to-date files are partial years |
| model | text | — | commercial name as reported |
| powertrain | text | — | ICE / HEV / PHEV / BEV / FCEV, or empty when the source does not state it (joined later from vehicle_technology) |
| units | int | vehicles | sales or registrations |
| basis | text | — | `registrations` (EEA), `retail_sales` (Kia IR), `brand_total_sales` (Hyundai IR US sheet and Kia America: brand total including fleet), `domestic_sales` (Hyundai IR Korea domestic), `plant_sales` (Hyundai IR: production-side by plant), `export_shipments` (Hyundai IR Korea export block: plant-side, destination not stated) — never mixed silently. Market-side bases form cohorts; plant-side bases are reconciliation only |
| source_file | text | — | raw file the row came from |

## Raw files and sources

Registered in [`../../raw_files.csv`](../../raw_files.csv) (file, original name, SHA-256,
`source_id`) and [`../../sources.csv`](../../sources.csv) (publisher, title, link, how
obtained, access date, licence). In short:

- `eea_toyota_2024_final.json`, `eea_hyundai_2024_final.json`, `eea_kia_2024_final.json`,
  `eea_honda_2024_final.json` — EEA CO2 monitoring database, 2024 final, downloaded via the
  API (<https://co2cars.apps.eea.europa.eu/>) with one shared query (brand term swapped) by
  `script/auto/sales/fetch_eea_registrations.py`; each JSON holds the exact query and
  response hash. All four exporters are therefore on one EU27 boundary for 2024.
- `kia_2026_retail_sales_by_model_market.xlsx`, `hyundai_2025_global_plant_sales.xlsx` —
  **local files only, gathered by hand** from the Kia and Hyundai IR sales-results pages
  into Google Drive `Trade/Arc_Trade_Data/Auto/`; exact download links not recorded.

## Sales-results workbook families (Hyundai IR)

Hyundai's IR page publishes five workbooks per year, listed by the endpoint
`POST https://www.hyundai.com/wsvc/ww/salesPerformance.list.do` (lang=en&year=YYYY) and
downloaded by `script/auto/sales/fetch_hyundai_ir.py` into `raw/hyundai_<year>_<family>.xlsx`:
`sales_by_model` (Korea domestic and export, trim codes), `global_plant_sales` (plant-side),
`export_by_region` (plant-side by region: U.S.A., Canada, Mexico, Europe subsidiaries /
distributors / Türkiye, Latin America, Russia/CIS, Middle East/Africa, Asia/Pacific),
`us_retail_sales` (market-side US, Hyundai + Genesis) and `eu_retail_sales` (Europe
subsidiaries retail by model). One node per year is overwritten monthly; the December edition
is the full year and superseded editions are not retained. The `eu_retail_sales` file is a
reconciliation series only: its 2024 total (423,959 incl. 3,274 light commercial vehicles) sits
1.4 % below the EEA EU27 Hyundai registrations (429,936), the difference being the distributor
markets and the registration-versus-retail timing.

Kia America's newsroom serves an xlsx per month
(`salesbymonthexport?month=12&year=YYYY&yeartocompare=YYYY-1`, Referer required), fetched by
`script/auto/sales/fetch_kia_america.py`. Kia Corporation's IR workbook (`kia_2026_retail_sales_by_model_market.xlsx`)
remains hand-gathered: the IR page is a client-rendered application with no file list endpoint.

## Processed files

All share the schema above; one file per raw source, written by the script named.

| processed file | script | rows | note |
|---|---|---|---|
| `sales_eea_eu27_2024.csv` | `script/auto/sales/extract_eea_registrations.py` | see script output | in-scope brands only: Hyundai 429,936 and Kia 414,677 registrations (Toyota 803,094 and Honda 40,270 are pinned but excluded); powertrain from EEA; `ICE_OTHER` → `ICE` |
| `sales_kia_ir_2026.csv` | `script/auto/sales/extract_kia_ir.py` | 287 | Jan–Jun 2026 year-to-date; markets are IR regions except KR/US/CA/MX/IN/CN; `origin` = plant block; zero cells dropped |
| `sales_hyundai_plant_2025.csv` | `script/auto/sales/extract_hyundai_ir.py` | 113 | overseas plants only, 2025; destination known for Domestic (plant country) and Korea segments, `export` otherwise; plant-side, so it is the only source for India, Brazil, China, Türkiye, Vietnam, Indonesia and Singapore and is never a US cohort |
| `sales_hyundai_us.csv` | `script/auto/sales/extract_hyundai_us_retail.py` | 41 | Hyundai IR "US Retail Sales by Model" 2024 and 2025: Hyundai and Genesis nameplates, imports and US-built together. The sheet is labelled retail but its 2024 total (911,805) equals HMA total sales incl. fleet (836,802) plus Genesis (75,003), hence `brand_total_sales`; Genesis rows carry `company = genesis` (out of scope in `companies.csv`); powertrain only where the nameplate states it, the rest split by `us_model_map.csv` rule `epa_share_my2024` |
| `sales_kia_us.csv` | `script/auto/sales/extract_kia_america.py` | 23 | Kia America December exports, full-year 2024 and 2025 by model (`brand_total_sales`); K4 and Forte on one row as published; EV6 and EV9 BEV, the rest split downstream |
| `sales_hyundai_kr.csv` | `script/auto/sales/extract_hyundai_sales_by_model.py` | 146 | Hyundai IR "Unit Sales by Model" 2024 and 2025: Korea domestic block (`domestic_sales`, destination KR) and Korea export block (`export_shipments`, plant-side, destination unknown); powertrain from the trim code (CN7 HEV, SX2 EV, …); Genesis rows `company = genesis`; commercial vehicles skipped |

Label lookups used by the scripts: `kia_labels.csv` (IR market and plant labels → codes),
`hyundai_plant_codes.csv` (plant code → country), `companies.csv` (exporters in scope) and
`us_model_map.csv` (IR model name → EPA base model and powertrain rule for the US cohort:
`explicit` where the name fixes the powertrain, `mixed_central_ice` where the IR file does not
split ICE from hybrid variants — central case ICE, all-HEV bound in the sensitivity — and
`out_of_scope` for the Genesis brand).

## Processing method

Scripts in `script/auto/sales/`. One script per raw source; each writes a CSV to
`processed/` in the required-fields shape above.

1. EEA snapshots: flatten the `response` evidence rows for the brands in scope; powertrain
   classes as recorded by EEA; basis = `registrations`.
2. Kia workbook: `Total` sheet, Retail Sales block — model × market annual totals; map
   market labels to ISO codes; basis = `retail_sales`. Powertrain must be joined from the
   vehicle_technology dataset (the workbook carries model names only).
3. Hyundai workbook: plant sales are production-side, not destination sales — use only
   where destination sales are absent, and record the basis honestly.

## Coverage and gaps

- EU27 2024: complete for both exporters (EEA registrations by country, model, powertrain).
- United States: the Kia IR workbook's U.S.A column gives Kia retail sales by model for
  January–June 2026 (a partial year, no powertrain split); the Hyundai IR workbook gives only
  US-built cars sold in the US (HMMA and HMGMA Domestic segments), so imports from Korea are
  missing from the Hyundai US cohort. A Hyundai monthly sales-by-region file would complete it.
- Australia: deferred; the gathered files report Kia's Asia-Pacific region only.

## Rules

- Raw files are never edited; every processed row keeps `source_file`.
- A missing market or powertrain yields **no row**, never zero.

## Korea label map

`method/kr_labels.csv` resolves every Korea sales label to a KEA model and a powertrain rule:
`stated` (Hyundai IR trim codes carry the powertrain), `explicit` (single-powertrain labels such
as EV3, Ray EV, Niro), `unsplit` (Kia IR labels that fold ICE and HEV: Carnival, K5, K8, Seltos,
Sorento, Sportage — assessed as ICE centrally with an all-HEV bound) and `out_of_scope` (Bongo,
Bus, Tasman and military vehicles: outside the passenger-car class).

## Japan (JADA, added 2026-09-04)

| processed file | script | content |
|---|---|---|
| `sales_jada_jp.csv` | `script/auto/sales/extract_jada.py` | Japan registrations by nameplate and cohort year for the companies in scope (Toyota 1,197,210 in 2024 and 1,212,140 in 2025; Nissan 228,787 and 179,123), basis `registrations` |
| `jada_fuel_mix_jp.csv` | same | company × cohort year × fuel: registrations and share, summed over the twelve monthly sheets, every maker (Toyota 2024: 65.6 % hybrid, 30.6 % petrol, 2.0 % diesel, 1.6 % plug-in hybrid, 0.14 % battery electric; Nissan: 83.4 % hybrid, 13.3 % petrol, 3.3 % battery electric) |
| `jada_brand_registrations_jp.csv` | same | company × cohort year: passenger-car registrations including kei cars, and the part built outside Japan (JADA's imported-of-which row): Nissan imported 3.6 % of its 2024 Japanese sales, Honda 7.1 %, Toyota 0.13 % |

Source: Japan Automobile Dealers Association (JADA) statistics data, pages 340, 342 and 337
(`jada_registration_statistics`), fetched by `fetch_jada.py`, which reads each page for its annual
workbook link because the file ids change when a workbook is reissued. JADA sells the back series
as paid books (page 517), so republishing these rows at row level is a question for the provenance
audit; downloading them is free.

Boundaries, none of which reconcile with each other, all recorded on the tables. The nameplate
ranking excludes kei cars and foreign brands and is cut at the top 50, so it is a subset of a
company's Japanese sales rather than the whole: Toyota's 1.20 M nameplate units sit against
1.21 M in the brand table, but Nissan's 229 k sits against 398 k because Nissan's kei cars are
outside the ranking. The fuel table excludes kei cars, folds Lexus into Toyota, and counts
Japanese-brand cars built abroad as imports. **No JADA table crosses model with fuel**, so a
Japanese cohort must apply the maker-level fuel mix to each nameplate as a disclosed assumption.
