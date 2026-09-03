# emission_targets — importer NDC and sector targets, as annual decline rates

## What this dataset is

The policy commitments that turn the observed base-year emissions into a *dynamic*
benchmark trajectory (research process step 2.1; whitepaper §2 dynamic benchmark, §3.1;
guideline §2.3 Method B). For each importer and scenario: the annual decline rate applied to
the fleet benchmark (`r_fleet`) and to grid intensity (`r_power`), with the target it was
derived from.

Scenarios: `S1` current trajectory (observed trend), `S2` committed policy (NDC or sector
standard), `S3` 1.5 °C-aligned. Always reported together.

## Required fields (processed output, long format)

| field | type | unit | note |
|---|---|---|---|
| country | text | ISO 3166-1 alpha-2 | |
| scenario | text | — | `S1` / `S2` / `S3` |
| rate | text | — | `r_fleet` or `r_power` |
| value | real | 1/year | annual decline fraction; positive = falling |
| target_level | text | — | `observed_trend` (S1), `sector_country`, `sector_regional`, `ndc_prorata`, `regional_prorata`, `1p5c_prorata`, `none` — a proxy is never relabelled as a country target |
| base_year | int | year | |
| target_year | int | year | |
| derivation | text | — | how the rate was computed, including any flag (e.g. `PATHWAY_ALREADY_MET`) |
| source_id | text | — | `;`-separated ids resolving in the sources tables of this or the emissions/usage datasets |

## Raw files

| file | source | how obtained | note |
|---|---|---|---|
| `eu_climate_targets.csv` | EU legislation and Commission documents (links below) | **hand-transcribed** table of the target anchors: 2030 −55 % and 2040 −90 % economy-wide vs 1990, EU domestic transport 2023 → 2030 pathway (795.6 → 583.0 MtCO2e) | targets are legal texts, not downloadable series; the row's `source_id` links the text |

## Sources

`eu_climate_law_2021_1119` (Regulation (EU) 2021/1119 Art. 4(1)), `ec_2040_com_2024_63`
(COM(2024) 63) and `ec_2040_impact_assessment_transport` (its impact assessment, transport
pathway) — links in [`../../sources.csv`](../../sources.csv). S1 trends use the observed series in `country_emissions` and `vehicle_usage` (their
`source_id`s are carried into the rows). To collect for the other importers: US NDC status
(FLAG market if none), Australia NDC (UNFCCC registry), IEA WEO 2024 STEPS/NZE rates for
S1/S3 (`References/IEA_2024_WEO_Full_Report.pdf` in the Drive folder).

## Processing method

`script/auto/emission_targets/derive_eu27_rates.py` → `processed/emission_targets_eu27.csv`.

- S1: log-linear trend of per-car CO2 (car CO2 ÷ stock) and of grid intensity, 2015–2024
  excluding 2020–2021.
- S2 fleet: compound annual decline of the EU transport pathway 2023 → 2030, applied
  pro-rata to every member state (`ndc_prorata`). S2 power: EU public electricity CO2 from
  its latest observation to 45 % of 1990 by 2030; a negative rate (already met) is held at 0
  and flagged.
- S3: same construction against the 2040 −90 % target (`1p5c_prorata`).

## Rules

- A regional or economy-wide pro-rata rate is disclosed via `target_level`; it is never
  presented as a national sector target.
- Markets with no usable NDC anchor are FLAGGED and excluded from the S2 headline, reported
  separately (guideline FLAG-market rule).
