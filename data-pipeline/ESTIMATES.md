# Estimated inputs — Toyota & Hyundai case fixtures

Every value below is a **rough, documented estimate** (owner request, 2026-07-22): good
enough for a first per-country read, honest about provenance, and to be replaced by
collected data (COLLECTION_STATUS.md is the backlog). Tier meanings per Whitepaper §5.1
(A firm-verified / B estimated from public data / C proxy). Nothing here is engine
default — all of it lives in `data-pipeline/fixtures/{toyota,hyundai}.json` and flows
through the same loader/engine as any collected data.

## What is real (not estimated)

| Input | Source | Tier |
|---|---|---|
| Grid intensity G_c(0), all markets | Ember 2024 via workbook `Layer1_NDC_benchmark` | A |
| S2 economy-wide reduction rates AU / EU / JP / KR | UNFCCC 2035 NDCs via workbook (pro-rata, D1 identity warning applies) | B |
| US = no S2 benchmark | NDC revoked — FLAG per NOTES.md D3, excluded from S2 headline | — |

## Estimated (replace when collected)

| Parameter | Values used | Rationale | Tier |
|---|---|---|---|
| r_fleet S1 (STEPS) | JP 2.4, EU 1.4, AU 1.9, KR 2.5, US 1.0 %/yr | ~0.6× the S2 pro-rata rate; transport under current policies decarbonises slower than NDC ambition | C |
| r_power S1 (STEPS) | JP 2.5, EU 4.0, AU 5.0, KR 3.0, US 2.0 %/yr | IEA STEPS direction: EU/AU grids decarbonising fast on current policy, JP/KR/US slower | C |
| r_fleet S3 (NZE) | 5.5–7 %/yr by market | IEA NZE transport pathway magnitude | C |
| r_power S3 (NZE) | 8–11 %/yr by market | IEA NZE electricity pathway magnitude | C |
| Fleet base intensity I_fleet(0) | JP 0.150, EU 0.140, AU 0.185, KR 0.165, US 0.200, CN 0.160, IN 0.130 kgCO₂e/km | In-use all-vintage fleet average: EU cleanest, AU/US ute/truck-heavy, IN small-car-dominated | C |
| Annual distance D_c | JP 9,500; EU 12,000; AU 13,800; KR 13,000; US 18,000; CN 12,000; IN 10,000 km/yr | National VKT statistics magnitudes (MLIT, EEA, BITRE, KTDB, FHWA; CN/IN regional defaults) | B/C |
| Vehicle lifetime T | 15 yr (± 3 sensitivity) | Mean fleet age magnitude, OECD markets | B |
| ICE real-world intensity | 0.16–0.22 kgCO₂e/km by market mix | Certification values + ICCT Mind-the-Gap uplift; AU/US higher (utes, trucks) | B |
| HEV real-world intensity | 0.11–0.13 kgCO₂e/km | Toyota/Hyundai hybrid fleet averages, real-world corrected | B |
| BEV efficiency η_EV | 0.17–0.19 kWh/km | bZ4X / Ioniq5 certification + real-world uplift | B |
| PHEV UF / η_elec / ICE-mode | UF 0.40–0.50; 0.19–0.21 kWh/km; 0.14–0.16 kgCO₂e/km | Regulatory UF — **structural overstatement caveat applies** (Guideline §3.5); engine reports UF−0.15 lower bound side by side | C |
| 2024 volumes V_c,v | per-fixture placements | Public annual sales totals where available; model/powertrain allocations remain B/C and are tiered independently from the vehicle parameters | A/B/C |

## Scope decisions

- **Markets:** KR, JP, EU, AU (computed S2 benchmarks) + US, CN, IN (FLAG — S1/S3 only,
  excluded from the S2 headline). CN: 2035 target vs undefined peak; IN: GDP-intensity
  target. Hyundai CN has no placement because no auditable 2024 firm volume was found;
  missing data stays missing instead of being represented by a placeholder.
- **Hyundai** = Hyundai brand (excl. Kia/Genesis granularity); **Toyota** = Toyota brand
  (Lexus folded into mixes). Model-level collection supersedes this.
- Engine behaviour on this data: PRORATA_IDENTITY warnings on all computed markets (D1),
  US excluded from the S2 headline with reason (D3), Tier C share drives the
  directional-only check — all visible in each report's data-quality declaration.

## Audited 2024 totals and allocation decisions

These sources anchor totals only. A model/powertrain split described as an analyst proxy
is not presented as a reported number and remains Tier C.

| Firm / market | Published total used | Allocation in fixture | Primary source |
|---|---:|---|---|
| Hyundai / India | 605,433 domestic units | One fixed-emission mix; intensity 0.150 kgCO₂e/km is Tier C | [HMIL CY2024 sales release, 2025-01-01](https://www.hyundai.com/content/dam/hyundai/in/en/data/hyundai-story/announcements/Press-release-Intimation-of-press-release-by-Hyundai-Motor-India-Limited-Sales-Units-in-December-2024.pdf) |
| Toyota / India | 300,159 domestic units | One fixed-emission mix; intensity 0.155 kgCO₂e/km is Tier C | [TKM CY2024 sales release, 2025-01-01](https://www.toyotabharat.com/news/2025/tkm-records-its-highest-ever-calendar-year-sales-in-2024-by-selling-326329-units.html) |
| Toyota / China | 1,780,000 units represented | ICE/HEV/BEV allocation is Tier C and constrained to the official country total | [Toyota 2024 detailed sales data, 2025-01-30](https://global.toyota/en/company/profile/production-sales-figures/202412.html) |
| Hyundai / China | — | No placement published; the former 250,000-unit placeholder was removed | [BAIC Motor 2024 annual report](https://www.baicmotor.com/Uploads/file/20250528/20250528121254_79204.pdf) confirms the JV scope but does not provide a usable audited split for this fixture |

Global coverage denominators shown in the web assessment are 10.16 million Toyota + Lexus
sales ([Toyota 2024 fact data](https://global.toyota/pages/fact-data/fact-data_001_06_en.pdf))
and 4,141,959 Hyundai Motor sales ([Hyundai 2024 annual results](https://www.hyundai.com/worldwide/en/newsroom/detail/0000000897)).
They are disclosure denominators only and never enter the TI calculation.

## Canada & United Kingdom (added 2026-07-29)

Added because they are the largest KR/JP auto-export destinations missing from the
contract (KITA/Comtrade: CA is Korea's #2 auto export market; JAMA: CA is Japan's #3,
UK #6). Saudi Arabia (JP #5) stays FLAG_NO_BASELINE. UAE/Mexico/Thailand have
absolute 2035 NDCs and are derivable if coverage expands further.

| Parameter | CA | UK | Source / tier |
|---|---|---|---|
| NDC (workbook) | 45–50% below 2005 by 2035 → 1.97–2.28 %/yr pro-rata | ≥81% below 1990 by 2035 → 3.62 %/yr | [canada.ca / CAT](https://climateactiontracker.org/countries/canada/2035-ndc/), [gov.uk ICTU](https://www.gov.uk/government/publications/uks-2035-nationally-determined-contribution-ndc-emissions-reduction-target-under-the-paris-agreement) · A |
| Grid intensity 2024 | 185.35 gCO₂/kWh | 216.5 gCO₂/kWh | Ember via [OWID](https://ourworldindata.org/grapher/carbon-intensity-electricity) · A. UK note: NESO/Carbon Brief ~124 g differs on bioenergy accounting; Ember kept for cross-country consistency |
| VKT | 15,366 km/yr — **2009 vintage (NRCan CVS, discontinued); stale, flag** | 11,426 km/yr (DfT NTS 2024, England) | [NRCan](https://oee.nrcan.gc.ca/publications/statistics/cvs/2009/chapter2.cfm), [DfT](https://assets.publishing.service.gov.uk/media/68e8f5af57038b5739b98656/NTS_Factsheet_2024.pdf) · A(dated)/A |
| Fleet base intensity | 0.190 kgCO₂e/km (truck-heavy, US-like) | 0.145 kgCO₂e/km (EU-like) | Tier C analyst judgment; official figures are new-car compliance values (CA MY2024 ECCC; UK VEH0156 102.5 g WLTP), not in-use fleet averages |
| S1/S3 rates | S1 fleet 1.2, power 3.5; S3 fleet 6.0, power 9.0 %/yr | S1 fleet 2.2, power 5.0; S3 fleet 6.5, power 10.0 %/yr | Tier C, same construction as other markets (S1 fleet ≈ 0.6×S2) |
| 2024 volumes | Toyota+Lexus 238,933 ([Toyota Canada](https://media.toyota.ca/en/releases/2025/record-electrified-vehicle-sales-power-toyota-canada-inc--to-rec.html)); Hyundai 131,715 ([Hyundai Canada](https://www.hyundainews.ca/releases/4388)) | Toyota+Lexus 118,095; Hyundai 91,808 (SMMT via [best-selling-cars](https://www.best-selling-cars.com/britain-uk/2024-full-year-britain-best-selling-car-brands-in-the-uk/)) | A / B; powertrain splits are Tier C allocations constrained to these totals |

## Historical cohort years (`placements_by_year`, 2022–2023)

Each fixture carries 2022/2023 placement sets so the pipeline can publish a
`by_year` series (verified 2026-07-29). **Benchmarks and support parameters stay at
the current workbook vintage** — year-over-year differences isolate export volume
and powertrain-mix changes; they are not restated historical assessments.

Construction (per market, per year): `units_pt,y = units_pt,2024 × r_market,y × r_pt,y`,
ICE rows take the residual so the market total equals the 2024 fixture total × the
market ratio. Ratios:

- **Market volume ratios** `r_market,y` = reported market units (y) ÷ (2024):
  - Toyota+Lexus, Tier A, all markets (JP/US/EU/CN/IN/AU/KR): Toyota
    [production-sales Excel 2024-12](https://global.toyota/en/company/profile/production-sales-figures/202412.html)
    (2022: 9,567,184 · 2023: 10,307,395 · 2024: 10,159,336 worldwide).
  - Hyundai, Tier A/B/C by market: KR from HMC global-sales releases
    ([2022](https://www.hyundai.com/worldwide/en/newsroom/detail/hyundai-motor-reports-2022-global-sales-and-2023-goals-0000000174),
    [2023](https://www.hyundai.com/worldwide/en/newsroom/detail/hyundai-motor-reports-2023-global-sales-and-2024-targets-0000000392),
    [2024](https://www.hyundai.com/worldwide/en/newsroom/detail/hyundai-motor-announces-2024-annual-and-q4-business-results-0000000897));
    US from HMA releases; EU from ACEA data via best-selling-cars; IN from HMIL releases;
    AU from VFACTS press.
- **Powertrain mix ratios** `r_pt,y` = global powertrain units (y) ÷ (2024):
  - Toyota, Tier A ("Sales of Electrified vehicle" sheet): BEV 24,466 / 104,018 / 139,892 ·
    HEV 2,603,019 / 3,420,078 / 4,142,412 · PHEV 90,346 / 124,653 / 153,829.
  - Hyundai, Tier A for 2023/24 (Q4 business results): BEV 268,785 / 218,500 ·
    HEV 373,941 / 496,780; 2022 Tier C derived (BEV ≈195,000 via third party;
    HEV ≈267,000 residual of electrified ≈506,800).

Per-row tiers are inherited from the 2024 fixture rows (same construction quality:
reported totals × documented split). Generator scripts recorded in the session log;
the resulting rows live in the fixtures and republish deterministically.

## Net-zero commitments (fixture `netzero` block)

| Firm | Target | Interim | Source |
|---|---|---|---|
| Toyota | Life-cycle carbon neutrality 2050 (Environmental Challenge 2050, 2015-10); Scope 1+2 −68% by 2035 vs 2019 (SBTi) | gCO₂e/km −33.3% by 2030, >50% by 2035 vs 2019 · BEV 1.5M/yr 2026, 3.5M/yr 2030 · plants CN 2035 | [New Management Policy 2023-04](https://global.toyota/en/newsroom/corporate/39013233.html), [Sustainability Data Book 2025](https://global.toyota/pages/global_toyota/sustainability/report/sdb/sdb25_en.pdf) |
| Hyundai | Carbon neutral 2045 (IAA 2021-09); −75% vs 2019 by 2040 | 30% ZEV by 2030 · 2M BEV/yr by 2030 · EU ICE stop 2035 · RE100 | [IAA announcement](https://www.hyundainews.com/en-us/releases/3390) |
