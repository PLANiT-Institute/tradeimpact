# Sectoral decarbonization rates & vehicle-parameter sources — collected 2026-07-30

Research pass answering two backlog items in COLLECTION_STATUS.md: (1) real sectoral
(transport / power) decarbonization rates to replace the PRORATA_IDENTITY pro-rata
construction (NOTES.md D1), and (2) official model-level vehicle parameter databases to
replace the Tier C analyst estimates in ESTIMATES.md. All primary sources were opened and
values read from the government documents themselves unless flagged. **Integrated
2026-07-30**: JP/KR/EU/UK sectoral S2 + CA/AU sectoral S1 are in
`Layer1_NDC_benchmark`; 17 model-level vehicle rows in `Layer2_vehicle_params`; dataset
republished and all gates re-passed. Mapping decision taken: target/NDC-aligned pathways
→ S2, current-policy projections → S1; AU/CA S2 stays pro-rata (no sectoral NDC
decomposition exists) with the D1 warning retained.

## 1. Sectoral emission pathways (official, MtCO2e)

Implied rates are geometric CAGR r = 1 − (end/start)^(1/n), start = most recent
actual/pathway year.

| Market | Sector | Recent actual | 2030 level | 2035 level | Implied %/yr (→2030) | Nature | Confidence |
|---|---|---:|---:|---:|---:|---|---|
| JP | Transport (運輸, 배분후) | 190 (FY2023) | 146 (target) | — (2040: 40–80) | **4.1** | NDC-aligned target | High |
| JP | Energy conversion (배분후) | 81.0 (FY2023) | 56 (target) | — (2040: 10–20) | **5.1** | NDC-aligned target | High |
| KR | 수송 | 88.7 (2024 경로) | 61.0 (target) | — | **6.05** | NDC-aligned target, annual path table exists | High |
| KR | 전환 | 218.4 (2024 경로) | 145.9 (target) | — | **6.50** | NDC-aligned target, annual path table exists | High |
| EU | Domestic transport | 795.6 (2023) | 583 (FF55 path) | ≈289 (interpolated — no official 2035) | **4.3** | Fit-for-55 pathway (PRIMES) | High (2035: Low) |
| EU | Power & district heating | 573.8 (2023, CRF1A1A) | 339 (FF55 path) | ≈119 (interpolated) | **7.2** | Fit-for-55 pathway | High (2035: Low) |
| UK | Surface transport | 102.8 (2023) | 68.6 | 37.0 | **5.6** (→2035: 8.2) | CCC 7CB Balanced Pathway — statutory advice, NOT adopted policy | High |
| UK | Electricity supply | 37.8 (2023) | 9.8 | 5.6 | **17.6** (→2035: 14.8) | CCC 7CB Balanced Pathway | High |
| CA | Transport | 157 (2023) | 137 (WM proj.) | 124 (WM proj.) | **1.9** | Current-policy projection (ERP 2025 Progress Report) | High |
| CA | Electricity | 49 (2023) | 23 (WM proj.) | 14 (WM proj.) | **10.2** | Current-policy projection | High |
| AU | Transport | 100.8 (CY2025) | 92 (baseline proj.) | 83 | **1.5** (→2035: 1.8) | Current-policy projection (DCCEEW 2025) | High |
| AU | Electricity | 145.8 (CY2025) | 55 (baseline proj.) | 46 | **18.0** (→2035: 11.0) | Current-policy projection, assumes 82% RE 2030 | High |

Key structural finding: **pro-rata materially misallocates in every market** — power
decarbonizes 2–10× faster than transport everywhere; CA/AU transport under current policy
decarbonizes far *slower* than the economy-wide NDC rate, while KR/JP/EU/UK transport
targets are *faster* than our current Tier C S1 guesses.

### Primary sources

- **JP**: 地球温暖化対策計画 (각의결정 2025-02-18) — https://www.env.go.jp/content/000291669.pdf ; 부문표: https://www.cas.go.jp/jp/seisakukaigi/ondanka/kaisai/dai53/siryou1-1.pdf ; FY2023 확정치: https://www.env.go.jp/content/000310279.pdf . 주의: エネルギー転換 = 전기·열 배분후 (발전 총배출 아님; 배분전 시계열은 526→397, FY2013→FY2023, 2030 목표 없음). 2035 부문치 없음 (경제 전체 −60%만).
- **KR**: 제1차 탄소중립·녹색성장 기본계획 (2023.4) — https://www.pcccr.go.kr/storage/board/base/2023/07/04/BOARD_ATTACH_1688433504249.pdf . 연도별 경로 (전환: 2023 223.2 … 2030 145.9 / 수송: 93.7 … 61.0) 수록 — 보간 불필요. 2035 NDC (2025.12 제출, −53~61% vs 2018 net 742.3)는 부문 분해 없음: https://unfccc.int/sites/default/files/2025-12/The%20Republic%20of%20Koreas%202035%20NDC.pdf
- **EU**: SWD(2024) 63 Part 3 (2040 target IA), Table 3 — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A52024SC0063 ; 실적: Eurostat env_air_gge (CRF 1.A.3 / 1.A.1a). ETS cap: LRF 4.3%/yr 2024–27, 4.4%/yr 2028~ — https://climate.ec.europa.eu/eu-action/carbon-markets/eu-emissions-trading-system-eu-ets/eu-ets-emissions-cap_en . 주의: PRIMES Power&DH ≠ CRF1A1A (약 5% 차이); 2040 부문치는 제안 시나리오.
- **UK**: CCC Seventh Carbon Budget full dataset (2025-02) — https://www.theccc.org.uk/wp-content/uploads/2025/02/The-Seventh-Carbon-Budget-full-dataset.xlsx (Balanced Pathway, direct emissions). 정부 Carbon Budget & Growth Delivery Plan (2025-10)은 부문별 Mt 경로 미공표.
- **CA**: 2025 Progress Report on the 2030 ERP (ECCC, 2025-12), Tables 2-2/2-3 — https://www.canada.ca/en/services/environment/weather/climatechange/climate-plan/climate-plan-overview/emissions-reduction-2030/2025-progress-report.html . 주의: 최종 Clean Electricity Regulations (2024-12)는 2035 넷제로 그리드 아님 (65 tCO2/GWh from 2035, 넷제로는 2050). 2035 NDC 부문 분해 없음.
- **AU**: Australia's emissions projections 2025 (DCCEEW, 2025-11) — https://www.dcceew.gov.au/climate-change/publications/australias-emissions-projections-2025 ; 실적: Quarterly Update Dec 2025. 주의: baseline은 2035 NDC (−62~70%)에 60–100 Mt 미달 — NDC 추가 감축분은 부문 미배분. Transport Net Zero Roadmap에 정량 Mt 목표 없음 (확인됨).

## 2. Vehicle-parameter databases (model-level, official)

| Market | Source | Granularity | Latest | Access |
|---|---|---|---|---|
| EU | EEA CO2 monitoring (Reg. 2019/631) — https://co2cars.apps.eea.europa.eu/ | 등록 단위: 제조사·모델·연료·WLTP gCO2/km·전비 Wh/km·전기 주행거리 | 2024 final / 2025 provisional | CSV + REST |
| EU 실주행 | COM(2024) 122 OBFCM 보고 — https://climate.ec.europa.eu/document/download/b644dafe-1385-4b56-98d9-21e7e9f3601b_en?filename=report.pdf | 파워트레인별 실주행 갭 | 2021–22 등록분 | PDF + 포털 |
| US | fueleconomy.gov downloads — https://www.fueleconomy.gov/feg/download.shtml | 모델별 MPG·CO2 g/mi·EV kWh/100mi | MY2026 (+MY2027 prelim) | CSV/XML/API |
| JP | MLIT 自動車燃費一覧 (令和8年3月판) — https://www.mlit.go.jp/jidosha/jidosha_tk10_000050.html | 모델별 WLTC km/L | 2025년말 시판차 | Excel/PDF |
| KR | 에너지공단 자동차 표시연비 (data.go.kr 15083023) — https://www.data.go.kr/data/15083023/fileData.do | 모델별 복합/도심/고속 연비, EV 주행거리 (~2,800 모델) | 2026-04 갱신 | CSV/API |
| 실주행 갭 | ICCT real-world CO2 (2026-06) — https://theicct.org/publication/real-world-co2-emission-values-vehicles-europe-jun26/ | ICE/HEV 갭 ~19%, PHEV 실주행 ≈ 공인치 4–5배 (실주행 UF ~0.25–0.30) | OBFCM 2021–23 | PDF (직접 열람 실패 — 검색 발췌 기반, flag) |

EU OBFCM 공식 결과: 휘발유 +19.8~21.1%, 디젤 +17.1~18.2%, **PHEV 실주행 = 공인치 3.5배** (+99 g/km, 실주행 전기주행 비율 ~27% vs 규제 가정 ~84%). 현행 fixture의
ICE ×1.19 보정과 PHEV UF−0.15 하한 병기는 방향은 맞으나, PHEV는 공식 데이터 기준 하한을
UF≈0.27로 당길 근거 확보.

## 3. Integration mapping (반영 전 결정 필요)

- **시나리오 매핑이 관건**: JP/KR/EU/UK 수치는 목표·NDC 정합 경로 → **S2 벤치마크** 대체
  (pro-rata → 실제 부문 경로; PRORATA_IDENTITY 경고 해소, Tier 상향). CA/AU 수치는
  현행정책 투영 → 성격상 **S1**에 가까움; CA/AU의 S2는 (a) pro-rata 유지 + 주석, (b)
  투영을 S2로 쓰고 Tier 강등 표기, 중 선택 필요.
- 시작점 불일치 주의: 각 시장 실적 연도가 다름 (FY2023/CY2023/CY2025). 엔진은 2024 기점
  — 경로표(KR) 또는 CAGR 재계산으로 2024 정렬 필요.
- 부문 정의 차이: JP 배분후 vs 발전 총배출; EU PRIMES vs CRF — 워크북에 정의 주석 필수.
- 차량 파라미터는 EEA/EPA/MLIT/KEA CSV에서 Toyota·Hyundai 모델별 추출 →
  `Layer2_vehicle_params` 시트 채우는 별도 수집 작업 (fixture Tier C → Tier A/B 승격).
- 반영 시 전체 재발행 필요: workbook 수정 → build_dataset.py → check_published →
  50_build_integrated_audit.py 재실행.
