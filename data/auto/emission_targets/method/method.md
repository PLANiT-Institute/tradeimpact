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
| target_level | text | — | `observed_trend` (S1), `sector_country`, `sector_regional`, `ndc_prorata`, `regional_prorata`, `1p5c_prorata`, `world_prorata` (IEA world scenario applied pro-rata), `flag_no_ndc` (no rate; S2 excluded from the headline), `none` — a proxy is never relabelled as a country target |
| base_year | int | year | |
| target_year | int | year | |
| derivation | text | — | how the rate was computed, including any flag (e.g. `PATHWAY_ALREADY_MET`) |
| source_id | text | — | `;`-separated ids resolving in the sources tables of this or the emissions/usage datasets |

## Raw files

| file | source | how obtained | note |
|---|---|---|---|
| `eu_climate_targets.csv` | EU legislation and Commission documents (links below) | **hand-transcribed** table of the target anchors: 2030 −55 % and 2040 −90 % economy-wide vs 1990, EU domestic transport 2023 → 2030 pathway (795.6 → 583.0 MtCO2e) | targets are legal texts, not downloadable series; the row's `source_id` links the text |
| `ndc_anchors.csv` | UNFCCC NDC Registry (`unfccc_ndc_registry`) | **hand-transcribed** NDC status for the non-EU importers: US = FLAG market (no NDC in force after the 2025 Paris withdrawal took effect), AU = 43 % below 2005 by 2030 | every row carries `verified = no` until checked against the registry text; the US derivation uses only the FLAG status and prints the verified flag into the row |
| `iea_weo_2024_world_co2.csv` | IEA World Energy Outlook 2024, Annex A Tables A.4a–c (`iea_weo_2024`; local PDF in the Drive References folder) | world CO2 for electricity and heat, transport and passenger cars under STEPS, APS and NZE at 2010, 2022, 2023, 2030, 2035, 2040, 2050 — extracted from the PDF text with table and page per row | anchor values only; the world NZE path is the S3 proxy (`world_prorata`) for importers without a published regional NZE path |

## Sources

`eu_climate_law_2021_1119` (Regulation (EU) 2021/1119 Art. 4(1)), `ec_2040_com_2024_63`
(COM(2024) 63) and `ec_2040_impact_assessment_transport` (its impact assessment, transport
pathway) — links in [`../../sources.csv`](../../sources.csv). S1 trends use the observed series in `country_emissions` and `vehicle_usage` (their
`source_id`s are carried into the rows). To collect for the other importers: US NDC status
(FLAG market if none), Australia NDC (UNFCCC registry), IEA WEO 2024 STEPS/NZE rates for
S1/S3 (`References/IEA_2024_WEO_Full_Report.pdf` in the Drive folder).

## Processing method

`script/auto/emission_targets/derive_eu27_rates.py` → `processed/emission_targets_eu27.csv`;
`script/auto/emission_targets/derive_us_rates.py` → `processed/emission_targets_us.csv` (S1
observed trends from the EPA annex series and Ember grid; S2 `flag_no_ndc` with no rate; S3
world NZE pro-rata 2023 → 2040 for passenger cars and for electricity and heat);
`script/auto/emission_targets/derive_au_rates.py` → `processed/emission_targets_au.csv` (S1
observed trends from the ANGA inventory and Ember grid; S2 the 43 %-below-2005-by-2030 NDC
applied pro-rata per sector, floored at S1 where already met, with the anchor's `verified` flag
printed; S3 world NZE pro-rata).

- S1: log-linear trend of per-car CO2 (car CO2 ÷ stock) and of grid intensity, 2015–2024
  excluding 2020–2021.
- S2 fleet: compound annual decline of the EU transport pathway 2023 → 2030, applied
  pro-rata to every member state (`ndc_prorata`). S2 power: EU public electricity CO2 from
  its latest observation to 45 % of 1990 by 2030; where that rate is negative (already met)
  S2 power is floored at the market's observed S1 grid trend (`ndc_prorata_s1_floor`) and
  flagged `PATHWAY_ALREADY_MET`.
- S3: same construction against the 2040 −90 % target (`1p5c_prorata`).

## Rules

- A regional or economy-wide pro-rata rate is disclosed via `target_level`; it is never
  presented as a national sector target.
- Markets with no usable NDC anchor are FLAGGED and excluded from the S2 headline, reported
  separately (guideline FLAG-market rule).

## Korea (added 2026-09-04)

| file | content |
|---|---|
| `raw/kr_climate_targets.csv` | hand-transcribed anchors with document, table and URL: 2030 NDC (40 % below 2018, 727.6 → 436.6 MtCO2e), transport (1.A.3) 98.1 → 61.0 with the annual path 2023–2030, power (전환) 269.6 → 145.9, 2050 scenarios A/B for transport (2.8 / 9.2) and power (0 / 20.7), and the 2035 NDC (53–61 % below 2018 net 742.3, no transport target; recorded, not used) |
| `processed/emission_targets_kr.csv` | `derive_kr_rates.py`: S1 observed (GIR road CO2 −0.2 %/yr; Ember grid 2.2 %/yr, 2015–2024 excl. 2020–21); S2 `ndc_prorata` fleet 5.9 %/yr (transport path 93.7 → 61.0, 2023–2030) and power 5.0 %/yr (2018–2030), floored at S1 where already met; S3 `1p5c_prorata` fleet 10.5 %/yr (98.1 → 2.8 by 2050, A안) and power 7.7 %/yr (269.6 → 20.7, B안) |

Sources: 탄소중립·녹색성장 국가전략 및 제1차 국가 기본계획 (`kr_basic_plan_2023`,
https://www.pcccr.go.kr/storage/board/base/2023/07/04/BOARD_ATTACH_1688433504249.pdf); 2050
탄소중립 시나리오 (`kr_2050_scenarios_2021`, portal reproduction
https://www.gihoo.or.kr/gallery.es?mid=a30202000000&bid=0010&act=view&list_no=551); Republic of
Korea's 2035 NDC (`kr_ndc_2035`, UNFCCC PDF). All PDF-only; transcribed with table names.

Traps. 수송 is IPCC 1.A.3 in full (road, domestic aviation, rail, navigation), so every
transport rate is a pro-rata. The 2018 transport anchor 98.1 MtCO2e is fixed on the 1996-guideline
inventory vintage and is not reproducible from the current inventory (98.88 on the 2006
guidelines). The 2035 NDC restates the 2018 base year to 742.3 net (from 727.6 gross). The 2050
scenario A power endpoint is zero, which a compound decline cannot reach; scenario B anchors the
S3 power rate and A anchors the S3 fleet rate, so the S3 pair mixes the two published scenarios.
