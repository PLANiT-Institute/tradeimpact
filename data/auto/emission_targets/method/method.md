# emission_targets — importer NDC and sector targets, as annual decline rates

## What this dataset is

The policy commitments that turn the observed base-year emissions into a *dynamic*
benchmark trajectory (research process step 2.1; whitepaper §2 dynamic benchmark, §3.1;
guideline §2.3 Method B). For each importer and scenario: the annual decline rate applied to
the fleet benchmark (`r_fleet`) and to grid intensity (`r_power`), with the target it was
derived from.

Scenarios: `S1` the observed trend, a log-linear fit to the country's own published series;
`S2` the furthest target its own government has committed to. Both are always reported together,
because the sign of the result can change between them.

**S3 retired, 2026-09-04.** A third 1.5 °C-aligned scenario on the IEA NZE world trajectory was
removed: it is a modelled construction no government published, and the claim this project makes
is a comparison against what a state has itself committed to. The IEA WEO world anchors were its
only input and were retired with it, raw file and registry rows together. The decision is in
`claude-docs/log/README.md`.

## Required fields (processed output, long format)

| field | type | unit | note |
|---|---|---|---|
| country | text | ISO 3166-1 alpha-2 | |
| scenario | text | — | `S1` / `S2` |
| rate | text | — | `r_fleet` or `r_power` |
| value | real | 1/year | annual decline fraction; positive = falling |
| target_level | text | — | how the rate was derived, which is also what tiers it: `observed_trend` (S1, tier A), `ndc_prorata` and `ndc_prorata_s1_floor` (a government target applied pro-rata to the sector, tier B), `net_zero_2050` (Korea's 2050 Carbon Neutrality Scenarios, tier B), `gx_2040_prorata` (Japan's GX 2040 plan, tier B). A level with no tier rule stops the build rather than defaulting — a proxy is never relabelled as a country target, and a tier is never a silent default |
| base_year | int | year | |
| target_year | int | year | |
| derivation | text | — | how the rate was computed, including any flag (e.g. `PATHWAY_ALREADY_MET`) |
| source_id | text | — | `;`-separated ids resolving in the sources tables of this or the emissions/usage datasets |

## Raw files

| file | source | how obtained | note |
|---|---|---|---|
| `eu_climate_targets.csv` | EU legislation and Commission documents (links below) | **hand-transcribed** table of the target anchors: 2030 −55 % and 2040 −90 % economy-wide vs 1990, EU domestic transport 2023 → 2030 pathway (795.6 → 583.0 MtCO2e) | targets are legal texts, not downloadable series; the row's `source_id` links the text |
| `ndc_anchors.csv` | UNFCCC NDC Registry (`unfccc_ndc_registry`) | **hand-transcribed** target anchors for the non-EU importers: US = 61 % below 2005 net GHG by 2035 (the NDC communicated 2024-12-19, a month before the withdrawal notification; the published range is 61–66 % and the low end is taken, the range not propagated), AU = 43 % below 2005 by 2030 | every row carries a `verified` flag, and the flag is printed into the derived row so a reader sees whether the anchor was checked against the registry text |

## Sources

`eu_climate_law_2021_1119` (Regulation (EU) 2021/1119 Art. 4(1)), `ec_2040_com_2024_63`
(COM(2024) 63) and `ec_2040_impact_assessment_transport` (its impact assessment, transport
pathway) — links in [`../../sources.csv`](../../sources.csv). S1 trends use the observed series in `country_emissions` and `vehicle_usage` (their
`source_id`s are carried into the rows). To collect for the other importers: US NDC status
and Australia NDC (UNFCCC registry). No modelled world trajectory is collected any more.

## Processing method

`script/auto/emission_targets/derive_eu27_rates.py` → `processed/emission_targets_eu27.csv`;
`script/auto/emission_targets/derive_us_rates.py` → `processed/emission_targets_us.csv` (S1
observed trends from the EPA annex series and Ember grid; S2 the 2035 NDC applied pro-rata to
light-duty vehicle CO2 and to grid intensity, the intensity leg being looser than the absolute
target wherever generation grows, and said so in the row);
`script/auto/emission_targets/derive_au_rates.py` → `processed/emission_targets_au.csv` (S1
observed trends from the ANGA inventory and Ember grid; S2 the 43 %-below-2005-by-2030 NDC
applied pro-rata per sector, floored at S1 where already met, with the anchor's `verified` flag
printed). Japan and Korea have their own derivations, on the GX 2040 plan and the 2050 Carbon
Neutrality Scenarios respectively.

- S1: log-linear trend of per-car CO2 (car CO2 ÷ stock) and of grid intensity, 2015–2024
  excluding 2020–2021.
- S2 fleet: compound annual decline of EU transport from its 2023 level to 10 % of its 1990
  level by 2040 — the European Climate Law's furthest target, 90 % below 1990, applied pro-rata
  to transport — carried to every member state's car fleet (`ndc_prorata`). S2 power: the same
  construction on public electricity and heat; where that rate is negative (the pathway is
  already met) S2 power is floored at the market's observed S1 grid trend
  (`ndc_prorata_s1_floor`) and flagged `PATHWAY_ALREADY_MET`. The target's furthest year is used
  rather than 2030 so that a cohort's whole 11–25 year operating life sits inside the horizon
  instead of extrapolating a seven-year window over two decades.

## Rules

- A regional or economy-wide pro-rata rate is disclosed via `target_level`; it is never
  presented as a national sector target.
- Markets with no usable NDC anchor are FLAGGED and excluded from the S2 headline, reported
  separately (guideline FLAG-market rule).

## Korea (added 2026-09-04)

| file | content |
|---|---|
| `raw/kr_climate_targets.csv` | hand-transcribed anchors with document, table and URL: 2030 NDC (40 % below 2018, 727.6 → 436.6 MtCO2e), transport (1.A.3) 98.1 → 61.0 with the annual path 2023–2030, power conversion 269.6 → 145.9, 2050 scenarios A and B for transport (2.8 / 9.2) and power (0 / 20.7), and the 2035 NDC (53–61 % below 2018 net 742.3, no transport target; recorded, not used) |
| `processed/emission_targets_kr.csv` | `derive_kr_rates.py`: S1 observed (GIR road CO2 −0.2 %/yr; Ember grid 2.2 %/yr, 2015–2024 excl. 2020–21); S2 `net_zero_2050` fleet 10.5 %/yr (transport 98.1 → 2.8 by 2050, scenario A) and power 7.7 %/yr (269.6 → 20.7, scenario B), floored at the S1 trend where the pathway is already met |

Sources: the National Strategy for Carbon Neutrality and Green Growth and the First National
Basic Plan (`kr_basic_plan_2023`,
https://www.pcccr.go.kr/storage/board/base/2023/07/04/BOARD_ATTACH_1688433504249.pdf); 2050
the 2050 Carbon Neutrality Scenarios (`kr_2050_scenarios_2021`, portal reproduction
https://www.gihoo.or.kr/gallery.es?mid=a30202000000&bid=0010&act=view&list_no=551); Republic of
Korea's 2035 NDC (`kr_ndc_2035`, UNFCCC PDF). All PDF-only; transcribed with table names.

Traps. The Korean transport sector is IPCC 1.A.3 in full (road, domestic aviation, rail,
navigation), so every
transport rate is a pro-rata. The 2018 transport anchor 98.1 MtCO2e is fixed on the 1996-guideline
inventory vintage and is not reproducible from the current inventory (98.88 on the 2006
guidelines). The 2035 NDC restates the 2018 base year to 742.3 net (from 727.6 gross). The 2050
scenario A power endpoint is zero, which a compound decline cannot reach; scenario B anchors the
S2 power rate and A anchors the S2 fleet rate, so the S2 pair mixes the two published scenarios.
