# sales — exporter sales / registrations by destination market

## What this dataset is

Observed sales or first registrations of the target exporters' vehicles in each importer
market, by model and powertrain, per cohort year. This is the `Volume(t)` term of the TI
formula and the anchor of the whole analysis (research process step 1–2).

- **Exporters**: Hyundai, Kia (Korea); Toyota, Honda (Japan; Honda is the second-largest
  Japanese automaker by global sales — swap if the team decides otherwise).
- **Importers**: EU27 member states, United States, Australia.

## Required fields (processed output)

| field | type | unit | note |
|---|---|---|---|
| company | text | — | hyundai / kia / toyota / honda |
| destination | text | ISO 3166-1 alpha-2, or region label | importer market (country when the source gives it) |
| destination_level | text | — | `country`, `region` (Kia IR reports Europe, Eastern Europe, Middle East, …), or `unknown` (Hyundai IR export rows: plant-side, destination not stated) |
| origin | text | ISO 3166-1 alpha-2, or `ckd` / `special_vehicle` | production country when the source states the plant; empty for EEA registrations (origin unproven) |
| cohort_year | int | year | year of sale / first registration |
| period | text | — | months covered, e.g. `2024-01..2024-12`; IR year-to-date files are partial years |
| model | text | — | commercial name as reported |
| powertrain | text | — | ICE / HEV / PHEV / BEV / FCEV, or empty when the source does not state it (joined later from vehicle_technology) |
| units | int | vehicles | sales or registrations |
| basis | text | — | `registrations` (EEA), `retail_sales` (Kia IR), `plant_sales` (Hyundai IR: production-side by plant) — never mixed silently |
| source_file | text | — | raw file the row came from |

## Raw files and sources

Registered in [`../../raw_files.csv`](../../raw_files.csv) (file, original name, SHA-256,
`source_id`) and [`../../sources.csv`](../../sources.csv) (publisher, title, link, how
obtained, access date, licence). In short:

- `eea_toyota_2024_final.json`, `eea_hyundai_2024_final.json` — EEA CO2 monitoring
  database, 2024 final, downloaded via the API (<https://co2cars.apps.eea.europa.eu/>);
  each JSON holds the exact query and response hash.
- `kia_2026_retail_sales_by_model_market.xlsx`, `hyundai_2025_global_plant_sales.xlsx` —
  **local files only, gathered by hand** from the Kia and Hyundai IR sales-results pages
  into Google Drive `Trade/Arc_Trade_Data/Auto/`; exact download links not recorded.

## Processed files

All share the schema above; one file per raw source, written by the script named.

| processed file | script | rows | note |
|---|---|---|---|
| `sales_eea_eu27_2024.csv` | `script/auto/sales/extract_eea_registrations.py` | 1,286 | Toyota 803,094 + Hyundai 429,936 registrations; powertrain from EEA; `ICE_OTHER` → `ICE` |
| `sales_kia_ir_2026.csv` | `script/auto/sales/extract_kia_ir.py` | 287 | Jan–Jun 2026 year-to-date; markets are IR regions except KR/US/CA/MX/IN/CN; `origin` = plant block; zero cells dropped |
| `sales_hyundai_plant_2025.csv` | `script/auto/sales/extract_hyundai_ir.py` | 113 | overseas plants only, 2025; destination known for Domestic (plant country) and Korea segments, `export` otherwise |

Label lookups used by the scripts: `kia_labels.csv` (IR market and plant labels → codes),
`hyundai_plant_codes.csv` (plant code → country).

## Processing method

Scripts in `script/auto/sales/`. One script per raw source; each writes a CSV to
`processed/` in the required-fields shape above.

1. EEA snapshots: flatten the `response` evidence rows; powertrain classes as recorded by
   EEA; basis = `registrations`. (EU27 coverage for Toyota and Hyundai is complete for 2024.)
2. Kia workbook: `Total` sheet, Retail Sales block — model × market annual totals; map
   market labels to ISO codes; basis = `retail_sales`. Powertrain must be joined from the
   vehicle_technology dataset (the workbook carries model names only).
3. Hyundai workbook: plant sales are production-side, not destination sales — use only
   where destination sales are absent, and record the basis honestly.

## Gaps (to collect)

- Kia and Honda EU27 registrations (EEA API, same query pattern as the two snapshots).
- US sales by model/powertrain for all four companies (candidates: company IR, EPA
  certification/ sales data, Experian/Wards are paywalled).
- Australia sales by model/powertrain (VFACTS is paywalled; FCAI summaries public).

## Rules

- Raw files are never edited; every processed row keeps `source_file`.
- A missing market or powertrain yields **no row**, never zero.
