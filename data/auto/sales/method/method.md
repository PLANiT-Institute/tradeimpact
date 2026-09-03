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
| destination | text | ISO 3166-1 alpha-2 | importer market |
| cohort_year | int | year | year of sale / first registration |
| model | text | — | commercial name as reported |
| powertrain | text | — | ICE / HEV / PHEV / BEV / FCEV |
| units | int | vehicles | sales or registrations |
| basis | text | — | `registrations` or `retail_sales` or `wholesale` — never mix silently |
| source_file | text | — | raw file the row came from |

## Raw files

| file | original name / origin | sha256 |
|---|---|---|
| `kia_2026_retail_sales_by_model_market.xlsx` | `(기아차) 2026 현지판매실적.xlsx`, Google Drive `Trade/Arc_Trade_Data/Auto/` (Kia IR retail sales by model × market, monthly sheets) | `6b54b241…1f1cf8a` |
| `hyundai_2025_global_plant_sales.xlsx` | `(현대차) hmc-global-plant-sales-dec-y2025.xlsx`, same Drive folder (Hyundai IR global plant sales by model, monthly) | `527e658b…578a3a2` |
| `eea_toyota_2024_final.json` | Hash-pinned EEA CO2 monitoring API snapshot, Toyota-brand 2024 EU27 first registrations by country × model × powertrain (from the archived pipeline) | `e379e2ab…56ba1625` |
| `eea_hyundai_2024_final.json` | Same, Hyundai-brand | `364de073…4a00683b` |

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
