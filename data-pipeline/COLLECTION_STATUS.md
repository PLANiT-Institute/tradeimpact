# Data Collection Status

Mirrors `ti run --workbook ti-framework/data/TI_Data_Workbook_v0.1.xlsx` (engine-reported
`missing_inputs` + warnings). Regenerate any time with:

```bash
cd ti-framework && ti run --workbook data/TI_Data_Workbook_v0.1.xlsx
```

Snapshot date: 2026-07-30 · Workbook: `TI_Data_Workbook_v0.1.xlsx` · Loaded: 11 countries, 17 vehicle rows (collected 2026-07-30), 8 volume rows.

## Collected 2026-07-30 (cleared from the backlog)

- **Sectoral S2 benchmarks JP/KR/EU/UK** — official transport/power pathways now in
  `Layer1_NDC_benchmark` (PRORATA_IDENTITY cleared for these markets). Provenance:
  `SECTORAL_SOURCES.md`.
- **Sectoral S1 CA/AU** — official current-policy projections (ECCC ERP 2025 / DCCEEW 2025).
- **Vehicle parameters** — 17 model-level rows in `Layer2_vehicle_params` from EEA CO2
  monitoring (2022P), EPA fueleconomy.gov (MY2024), MLIT 燃費一覧 (令和8年3月), KEA 표시연비
  (2026-04). Fixture mix intensities cross-checked; 3 corrections applied (ESTIMATES.md).

## Missing / not-yet-collected inputs (collection backlog)

| Item | Sheet / market | What to collect | Source (Guideline Appendix B) |
|---|---|---|---|
| Volume data V_c,v | `Registration_Vcv` — no units collected | Model-level registrations by country, year, powertrain (2024 market totals are collected in fixtures, Tier A; the model/powertrain split is what remains) | VFACTS, KBA, SMMT, KAICA, SIAM, GAIKINDO, etc. |
| Vehicle lifetime T | `Support_params` | Central T + sensitivity per market fleet age (15±3 yr Tier B estimate in use) | National transport statistics |
| S2 sectoral 2035 | JP, EU | No official 2035 sectoral decomposition exists (JP: 2030/2040 目安 only; EU: FF55 2030 only) — structural gap, not collectable today | 차기 정부 발표 대기 |
| S2 sectoral | KR 2035 NDC | 부문별 분해 미발표 (2025-12 제출 NDC 명시: 추후 로드맵) — 2030 기본계획 경로 사용 중 | 관계부처 후속 로드맵 |
| S2 sectoral | CA, AU | NDC에 부문 분해 없음; 공식 부문 수치는 현행정책 투영뿐(S1에 반영). S2는 pro-rata 유지 + 경고 | 차기 정부 발표 대기 |
| S2 benchmark | US — `FLAG_NO_BENCHMARK` | No active NDC; excluded from S2 headline (NOTES.md D3) | S1/S3 via IEA STEPS/NZE if collected |
| S2 benchmark | IN — `FLAG_INTENSITY` | GDP-intensity target, not absolute path | idem |
| S2 benchmark | ID — `FLAG_BAU` | Target vs BAU projection, no base-year level | idem |
| S2 benchmark | SA — `FLAG_NO_BASELINE` | Absolute avoided target, unstated baseline | idem |
| S2 benchmark | CN — `FLAG_PEAK` | Target vs undefined peak | idem |
| S1/S3 rates | JP/KR/EU/UK/US S1; all S3 | r_fleet/r_power from IEA STEPS & NZE ("TO EXTRACT"; CA/AU S1은 공식 투영으로 수집 완료) | IEA WEO |
| Fleet base intensity | all markets | I_fleet,seg,c(0) = IEA transport CO₂ ÷ (OICA fleet × VKT) | IEA / OICA / national VKT |
| VKT refresh | CA | Only official per-vehicle figure is NRCan CVS 2009 (15,366 km) — stale; replace when a current source exists | StatCan / NRCan |
| CA/UK powertrain splits | CA, UK | 2024 volume totals are Tier A/B; model/powertrain allocation is Tier C — collect registration-level splits | DesRosiers, SMMT |
| Export-gap candidates | UAE, MX, TH | Absolute 2035 NDCs exist (NDC 3.0); derivable if ME/LatAm/ASEAN coverage wanted. SA stays FLAG_NO_BASELINE | UNFCCC registry |

## Warnings (data-quality, not blockers)

`PRORATA_IDENTITY` on AU, CA only (2026-07-30: JP/KR/EU/UK cleared via collected sectoral
S2). AU/CA S2 stays economy-wide pro-rata because neither NDC has a sectoral decomposition;
their official sectoral numbers are current-policy projections and live in S1 instead.

## Firm universe reconciliation

Canonical firm list for the TI pipeline lives in `data-pipeline/firms.json` (built by
`build_dataset.py` from the two source workbooks):

- `TI_CaseStudy_Target_Companies.xlsx` — TI case-study candidates. **Automotive (Toyota,
  Hyundai)** are the only firms in the implemented sector; shipping (KHI, Mitsui, HHI, SHI)
  and power (JERA, TEPCO, KEPCO, KOSPO) firms map to engine stub sectors and are carried
  as `runnable: false`.
- `CAP_Target_Companies_Draft.xlsx` — CAP project (steel, petrochemical). Different
  project, no TI sector implementation; carried in the universe as `project: "CAP"`,
  `runnable: false`, for one canonical list rather than two.

No firm currently has complete collected registration + vehicle-parameter data. Toyota and
Hyundai therefore run as explicitly estimated Tier B/C assessments with visible coverage
and directional-only suppression where the Tier C share exceeds the threshold.
`ReferenceCo` remains a separate illustrative validation fixture and is excluded from
country comparisons and firm-assessment headlines.

## Three-tier collection rule (Whitepaper §5.1)

Record `Source` and `Tier` (A measured / B modelled / C proxy) for every row. Empty cell ≠
zero: the loader records gaps in `missing_inputs` and downgrades confidence; it never
defaults.
