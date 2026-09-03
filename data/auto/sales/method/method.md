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

## Raw files

| file | source | how obtained | sha256 |
|---|---|---|---|
| `eea_toyota_2024_final.json` | EEA "CO2 emissions from new passenger cars" monitoring database, 2024 final dataset, brand filter `Mk=TOYOTA`, EU27 — <https://co2cars.apps.eea.europa.eu/> (API: <https://co2cars.apps.eea.europa.eu/tools/api>) | downloaded by the archived adapter on 2026-08-05; the JSON holds the exact query and the response hash | `e379e2ab…56ba1625` |
| `eea_hyundai_2024_final.json` | same database, brand filter `Mk=HYUNDAI` | same, 2026-08-05 | `364de073…4a00683b` |
| `kia_2026_retail_sales_by_model_market.xlsx` | Kia Corporation IR, "Retail Sales by Country" monthly sales results (original file name `(기아차) 2026 현지판매실적.xlsx`) — IR page: <https://worldwide.kia.com/int/company/ir> | **local file only, gathered by hand** into Google Drive `Trade/Arc_Trade_Data/Auto/`; the exact download link was not recorded | `6b54b241…1f1cf8a` |
| `hyundai_2025_global_plant_sales.xlsx` | Hyundai Motor Company IR, "Global Plant Sales" monthly sales results, Dec 2025 edition (original file name `(현대차) hmc-global-plant-sales-dec-y2025.xlsx`) — IR page: <https://www.hyundai.com/worldwide/en/company/ir> | **local file only, gathered by hand** into the same Drive folder; exact download link not recorded | `527e658b…578a3a2` |

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
