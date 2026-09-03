# emission_targets — importer NDC and sector targets

## What this dataset is

The policy commitments that turn the observed base-year emissions into a *dynamic*
benchmark trajectory (research process step 2.1; whitepaper §2 dynamic benchmark, §3.1).
For each importer: the NDC economy-wide target, any sector-specific target that outranks
it (e.g. EU CO2 fleet standards), and the derived annual decline rates.

## Required fields (processed output)

| field | type | unit | note |
|---|---|---|---|
| country | text | ISO 3166-1 alpha-2 | |
| target_level | text | — | whitepaper five-level hierarchy: sector_country / sector_regional / ndc_prorata / regional_prorata / none |
| scenario | text | — | S1 current-trajectory / S2 committed-policy / S3 1.5C-aligned |
| base_year | int | year | |
| target_year | int | year | |
| reduction | real | fraction of base-year level | |
| r_fleet | real | 1/year | derived annual decline applied to fleet benchmark |
| r_power | real | 1/year | derived annual decline applied to grid intensity |
| source_id | text | — | row in `method/sources.md` |

## Sources

- NDCs: UNFCCC NDC registry (EU joint NDC; US NDC status noted honestly — if withdrawn or
  absent it is a FLAG market per the guideline, never silently defaulted; Australia NDC).
- EU sector: CO2 emission performance standards for cars (Regulation (EU) 2019/631 as
  amended); Fit-for-55 trajectory.
- S1/S3 rates: IEA WEO STEPS / NZE (see `References/IEA_2024_WEO_Full_Report.pdf` in the
  Drive folder).
- The archived `destination_eu27_inputs.json` carries derived S1/S2/S3 `r_fleet`/`r_power`
  per EU27 market with the pro-rata derivation disclosed — reuse.

## Processing method

Scripts in `script/auto/emission_targets/`; output `processed/emission_targets.csv`.
The derivation from target to annual rate follows whitepaper §3.1 / guideline §2.3 Method B
(NDC pro-rata exponential decline) and is implemented once in `script/auto/model/`, not
re-derived ad hoc per country.

## Rules

- A proxy (regional or economy-wide pro-rata) is disclosed as such via `target_level` —
  never relabelled as a country sector target.
- Markets with no usable NDC anchor are FLAGGED and excluded from the S2 headline, reported
  separately (guideline FLAG-market rule).
