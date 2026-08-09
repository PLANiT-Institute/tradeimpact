# TI 재설계 스펙 v0 — 데이터셋 · 프로세스 · 아웃풋 정의

> 2026-08-06 작성. 재설계 1단계 산출물: 결과(lifetime TI)를 뽑기 위해 필요한 데이터셋,
> 프로세스별 코드, 아웃풋의 완전한 정의. 근거: 코드 전체(main `09abf2c`), 백서 v1.5,
> 자동차 기술 가이드라인 v1.8, Methodological Challenges v1.0.
>
> **2026-08-09 실행 완료.** 본 스펙의 데이터·프로세스·아웃풋 정의는 그대로 유효하며,
> 수집 경로만 바뀌었다: 수동 엑셀 워크북 대신 **공개 API 어댑터**
> (`adapters/destination_eu.py`)가 Eurostat·Ember에서 직접 수집해 해시 고정 스냅샷으로
> 커밋하고, `lifetime_run.py`가 이를 엔진 fixture로 조인한다. 워크북/CSV 경로는
> 수동 수집용으로 남아 있으나 1차 결과의 임계경로가 아니다. 결과와 남은 한계는
> [PROJECT_STATUS.md](PROJECT_STATUS.md).

---

## 0. 현재 상태 진단 — 왜 결과가 안 나오는가

리포에는 **서로 코드를 공유하지 않는 엔진이 2개** 있다.

| | Engine A — lifetime TI 계산 엔진 | Engine B — 증거 정렬(alignment) 서비스 |
|---|---|---|
| 위치 | `ti-framework/ti_framework/` (core, layer1, layer2, io, report) | `ti-framework/ti_framework/alignment/` |
| 입력 | 엑셀 워크북 / CSV / JSON fixture | `data/published/*.json` |
| 상태 | **수식·테스트 완성(96개 통과), 실데이터 없어 가동 불가** | 가동 중 — web/MCP가 사용 |
| 결과 | TI_cohort, TI_annual, TI_portfolio, 분해, 교차연도 | 관측 코호트·경로·준비도 조회만 |

**Lifetime TI가 안 나오는 이유 = 필수 입력 9개 미수집** (`impact_readiness.json`):

1. 생산공장→판매국 매핑 (Level 2)
2. 판매국별 연간 주행거리 VKT
3. 생존곡선/운행수명 분포
4. 실주행 보정계수 (시장×파워트레인)
5. 승용차 플릿 서비스 강도 기준값 `I_fleet(0)`
6. 판매국별 도로수송 S1/S2/S3 경로
7. 판매국별 전력망 S1/S2/S3 경로
8. PHEV 실주행 유틸리티 팩터
9. FCEV 수소 공급 강도

**코드 함정 3개** (데이터를 채워도 안 돌아가는 지점):

- ~~**워크북 로더에 필수 컬럼 4개가 없다.**~~ → **우회 완료.** `io/fixtures.py`는
  `fleet_intensity_base`·`vkt`·`eta_elec`·`ice_mode_intensity`를 이미 전부 받는다.
  1차 결과는 fixture 경로로 산출했고, 워크북 로더 확장은 수동 수집을 재개할 때만 필요.
- ~~**준비도(readiness)가 하드코딩.**~~ → **해소.** `_build_readiness`가 목적지 입력
  레코드에서 결측 여부를 실제로 도출한다. 한 국가의 VKT를 지워도 게이트가 닫히는지
  테스트로 고정(`test_alignment_eea.py`).
- **헤더 검증이 죽어있다.** 미해소. 워크북/CSV 경로 한정 문제이며 1차 결과의 임계경로
  밖. 수동 수집 재개 전에 처리할 것.

**추가 발견 (2026-08-09):**

- **`_portfolio_rampup`이 단일 코호트로도 시리즈를 만든다.** 동일 코호트 T회 반복
  가정이라 공표하면 반사실. `lifetime_run.py`가 공표 페이로드·CSV·차트 전부에서
  보류 처리하고 사유를 기록한다.
- **VKT 폴백 개념 불일치.** Eurostat `road_tf_vehmov TERNAT_REG`은 "국내 영토를 달린
  모든 차량(외국차 포함)"이라 자국 등록대수로 나눌 수 없다. 두 계열이 겹치는 국가에서
  최대 85배 차이(HR 12,446 vs 146 km/yr). Tier 강등이 아니라 **사다리에서 제외**.
  이 수정으로 S1 부호가 뒤집혔다(+1.98 → −1.40 Mt).
- **`Scenario.label`이 IEA STEPS/NZE로 하드코딩.** 실제 소싱과 무관한 라벨이라
  야심도 표현으로 교체하고, 실제 출처는 `DataQuality.scenario_sources`에 기록.

### 백서 v1.5 정합성 점검 (2026-08-06 재검증)

수식(§3.1–3.8), 부호 규약, S1/S2/S3 정의, Tier A/B/C, 분해 항등식, Scope 3 비상계 —
**전부 코드와 일치.** 백서는 여전히 유효한 방법론 기준. 어긋나는 지점 3곳:

1. **롤링 포트폴리오(백서 §3.8 "주력 공시 지표")는 현재 데이터로 산출 불가.**
   다년 코호트가 필요한데 확보된 것은 2024 단일 코호트뿐이고, 2022–23 재구성 코호트는
   의도적으로 삭제됨(`ESTIMATES.md`). 엔진의 `_portfolio_rampup`은 동일 코호트 T회
   반복 가정이라 단일 코호트로 돌리면 가상의 숫자가 나옴. → **다년 등록 데이터 확보
   전까지 포트폴리오 지표는 보고 대상에서 제외**, 백서 산출물 1·2·4(코호트, 연간
   시계열, 분해)만 공표.
2. **"Layer" 용어 충돌.** 백서 Layer 1/2 = 벤치마크/제품 배출. 계약 문서
   (`PRODUCT_CONTRACT.md`)의 3-layer = 관측/시나리오입력/도출결과. 재설계 문서·시트명
   에서는 벤치마크/제품 쪽을 Layer로 유지하고 계약 쪽은 "증거 계층"으로 부를 것.
3. **백서에는 없는 후속 규칙 2개가 계약에 추가됨** (백서보다 엄격, 계약이 우선):
   5단계 목적지 타깃 위계(§1 Sheet 3의 `prorata_used`를 `target_level 1–5`로 확장
   필요), 그리고 8종 입력 완비 시에만 결과 공표하는 publication gate. 본 스펙 §1은
   이 gate 기준으로 이미 설계됨.

부수: 백서 §8의 공개 주소(transitionarc.climatearc.org)는 현 리포 상황과 불일치 —
재설계 4단계(GitHub 공개) 때 갱신 필요.

핵심 설계 불변식 (유지할 것):
- 누락 입력 → `unavailable`, 절대 0이나 임의 추정 아님.
- S2 단독 보고 금지 — S1/S2/S3 항상 함께.
- 헤드라인은 반드시 국가별·파워트레인별 분해 동반. `TI_cohort = Σ_국가 = Σ_파워트레인`.
- Scope 3 Cat.11과 절대 상계 금지.
- `r_fleet ≠ r_power` — 독립적으로 소싱 (프레임워크 1번 오류).
- 셀 품질 = 3개 입력(벤치마크/차량/물량) tier 중 최악.

---

## 1. 필요한 데이터셋 — 엑셀 워크북 설계

원칙: **모든 입력 행에 5개 메타 컬럼** — 값, 단위, 키(국가/연도/모델/파워트레인),
출처(문서·버전·접근일), Tier(A/B/C). 모든 비율 파라미터는 S1/S2/S3 **3컬럼**.
T·UF·보정계수·세그먼트 비율은 점값이 아닌 **범위**로 저장.

### Sheet 1 — `Market_Selection` (시장 선정 게이트)

| 컬럼 | 내용 |
|---|---|
| country, code | 판매국 |
| annual_registrations | 연간 신규 등록대수 (순위용) |
| share_of_firm_sales | 기업 글로벌 판매 비중 |
| grid_intensity_class | high / low (각 1개 이상 포함) |
| has_ndc, has_grid_data, has_reg_db | 게이트 3조건 |

게이트: 기업 글로벌 판매의 ≥70% 커버, 최소 3개 시장, 고·저 그리드 각 1개 이상.

### Sheet 2 — `Registrations` (물량 V_c,v)

키: 국가 × 연도 × 브랜드 × 모델 × 파워트레인

| 컬럼 | 단위 | 소스 |
|---|---|---|
| country, code, year, brand, model | | |
| powertrain_raw (BEV/PHEV/HEV/ICE) | | 등록 DB 원본 4분류 |
| powertrain_calc (BEV/PHEV/ICE-HEV) | | 계산용 3분류 (HEV→ICE 케이스) |
| units | 대 | EEA(EU27, 이미 확보), KBA(DE), SMMT(UK), VFACTS(AU), KAICA(KR), SIAM(IN)… |
| segment | | |
| source_db, tier, status | | Comtrade HS8703은 Tier B 폴백 |

**EU27 2024 Toyota/Hyundai 1,286행은 이미 확보됨** (`data/published/product_cohorts.json`).

### Sheet 3 — `Layer1_Benchmark` (판매국 벤치마크 파라미터)

키: 국가

| 컬럼 | 단위 | 소스 |
|---|---|---|
| grid_intensity G_c(0) | gCO2/kWh | Ember (국가별 필수, 지역평균 금지) |
| fleet_intensity_base I_fleet(0) | gCO2/km | IEA 수송 CO2 ÷ (OICA 보유대수 × VKT) — **누락입력 #5** |
| E_transport(Y0), Fleet_size(Y0) | Mt, 대 | IEA CO2 from Fuel Combustion, OICA Vehicles in Use |
| segment_ratio (+범위) | — | EEA/EPA/BITRE/GFEI |
| ndc_base_year, target_year, reduction_low/high | | UNFCCC NDC Registry |
| r_fleet_S1, r_fleet_S2, r_fleet_S3 | 분수/yr | S1=IEA STEPS 수송, S2=NDC 무조건부 수송, S3=IEA NZE — **누락입력 #6** |
| r_power_S1, r_power_S2, r_power_S3 | 분수/yr | S1=STEPS 전력, S2=NDC 전력, S3=NZE — **누락입력 #7**. r_fleet과 별도 소싱 |
| r_fleet_S2_upper, r_power_S2_upper | | 조건부 NDC (감도용) |
| benchmark_status | OK / FLAG_* | FLAG는 S2에서 제외 또는 IEA 프록시 |
| target_level (1–5) | | 계약의 목적지 타깃 위계: 1=승용차/도로수송 경로 … 5=경제전체 맥락만. 프록시를 국가 타깃으로 재라벨 금지 |
| prorata_used (yes/no) | | 수송 서브타깃 부재 시 필수 공시 |
| tier, source | | |

### Sheet 4 — `Layer2_Vehicle` (판매 차량 파라미터)

키: 브랜드 × 모델 × 파워트레인

| 컬럼 | 단위 | 소스 |
|---|---|---|
| eta_ev (BEV 효율) | kWh/km | 형식승인 DB — **EEA 데이터에 이미 있음** (`certified_electricity_kwh_per_km`) |
| ice_intensity | gCO2/km | 형식승인 DB — **EEA에 이미 있음** (`certified_tailpipe_gco2_per_km`) |
| uf (PHEV, +범위 ±0.15) | 0–1 | EU WLTP UF 규정 / T&E·ICCT 실주행 — **누락입력 #8** |
| eta_elec (PHEV 전기모드) | kWh/km | charge-depleting 인증값 |
| ice_mode_intensity (PHEV 엔진모드) | gCO2/km | charge-sustaining 인증값 |
| cert_standard | WLTP/NEDC/EPA/JC08 | 보정계수 선택용 |
| realworld_correction (+범위) | 배수 | ICCT Mind the Gap 최신판 — **누락입력 #4**. EPA는 이미 보정됨→1.0 |
| correction_applied (bool), correction_source | | 이중보정 금지 가드 |
| h2_intensity (FCEV) | kgCO2e/kg | **누락입력 #9** |
| tier, source, status | | |

### Sheet 5 — `Support_Params` (수명·주행거리)

| 심볼 | 단위 | 키 | 소스 |
|---|---|---|---|
| T (수명, ±3yr) | 년 | 국가 | 국가 평균 차령 통계 — **누락입력 #3** |
| VKT D_c | km/yr | 국가 | FHWA/BITRE/EEA/DfT/KTDB, IEA 폴백=Tier C — **누락입력 #2** |
| weibull_alpha, beta (Method A용) | | 국가 | 교통부 차령조사 |
| uf_band | 0.15 기본 | | |
| realworld_range | (lo,hi) | | ICCT |

### Sheet 6 — `NDC_Extraction` (NDC 원자료 추출)

국가별: 최신 제출본 확인일, 수송/전력 서브타깃 유무, 무조건부(→S2)/조건부(→S3),
기준연도·기준배출량, 목표연도, 목표 이후 외삽 규칙, 경제전체 기준·목표 배출량(프로라타용).
2026-06 스캔 결과 **9개국 전부 수송·전력 서브타깃 없음** → 프로라타가 보편 케이스.

### Sheet 7 — `Level2_Production` (선택 — Level 2 분석 시)

모델 × 생산공장 × 배정비율, exact/estimated 플래그. 소스: 기업 IR 공장-모델 배정.
**누락입력 #1**. Level 1만 먼저 하면 이 시트 없이 진행 가능.

### Sheet 8 — `Sources` (출처 원장)

source_id, 제목, 발행처, URL(https), 발행일, 접근일, 라이선스, evidence_class, 해시.

---

## 2. 분석 프로세스별 코드 매핑

CSV 실행 경로는 이미 존재: `io/csv_adapter.py`가 시트명과 같은 `<sheet>.csv`를 읽어
xlsx 로더와 **동일 코드로** 처리 (테스트로 동일성 보장됨). 사용자 계획 3번(엑셀→CSV→
단계별 실행)은 현 구조 그대로 지원됨.

| 단계 | 무엇 | 코드 | 실행 | 산출 |
|---|---|---|---|---|
| P0 | 원천 스냅샷 수집 (해시 고정) | `data-pipeline/adapters/*.py --refresh` | 어댑터별 CLI | `data-pipeline/source-snapshots/*.json` |
| P1 | 어댑터 변환 (스냅샷→정규화 레코드) | `adapters/automotive_eea.py` 등 4개 | `build_dataset.py`가 호출 | 코호트/지표/벤치마크/경로 레코드 |
| P2 | 데이터셋 빌드 + 검증 | `data-pipeline/build_dataset.py` | `python data-pipeline/build_dataset.py` | `data/published/*.json` (11개, 정본해시 포함) |
| P3 | 재현 검증 | `data-pipeline/check_published.py` | `python data-pipeline/check_published.py` | 통과/실패 (전체 재계산 비교, tol 1e-12) |
| P4 | **lifetime TI 계산** | `ti_framework.run()` ← `io/csv_adapter.py` 또는 워크북 | `ti run <fixture.json>` (CLI: `cli.py`) | `RunResult` |
| P5 | 리포트 출력 | `report/outputs.py`, `report/plots.py` | `ti report` | CSV 5개 + JSON + 선언문 + PNG 3개 |
| P6 | 감도분석 | `core/sensitivity.py` (T±3, UF±0.15, 실주행, S2범위, 몬테카를로) | `run_sensitivity()` | 감도 밴드 |
| P7 | 공개 | web (`web/`, Next.js) + MCP (`mcp-server/`) | `npm run dev:local` / `tradeimpact-mcp` | 대시보드, MCP 쿼리 |

계산 흐름 (P4 내부, `core/aggregate.py`):

```text
Placement(국가×차량×물량)마다:
  E_ref(t)  = I_fleet(0)·(1−r_fleet)^t · VKT          [Layer 1, Method B 기본]
  E_prod(t) = ICE: I_ICE·VKT (상수)
              BEV: η·G(0)·(1−r_power)^t·VKT
              PHEV: [UF·η_elec·G(t) + (1−UF)·I_ICE_mode]·VKT
  TI_gap(t) = E_ref − E_prod                            [kgCO2e/대/yr, 양수=기여]
  TI_vehicle = Σ_{t=0}^{T−1} TI_gap(t)
  crossover = TI_gap 부호 전환 연도 (락인 신호)
코호트: TI_cohort = Σ (V × TI_vehicle) / 1000           [tCO2e]
포트폴리오: TI_portfolio(τ) = Σ_{운행중 코호트} TI_annual
```

가드 순서 (하나라도 누락 → 해당 셀 `missing` 기록, 0 아님):
units → I_fleet(0) → r_fleet → VKT → (BEV/PHEV면 G(0), r_power) → 파워트레인 파라미터.

### 재설계 시 코드 수정 목록 (데이터만으로 안 되는 것)

1. `io/schema.py` + `io/workbook.py`: `fleet_intensity_base`, `VKT`, `eta_elec`,
   `ice_mode_intensity` 컬럼 추가 + 로더 연결. VKT 행 파싱 (`_load_support`가 현재
   T만 읽음).
2. 헤더 검증 활성화: 선언된 컬럼 계약과 실제 헤더 비교, 불일치 시 `SchemaError`.
3. `_build_readiness` 실계산화: 입력 존재 여부로 상태 도출 (현재 상수).
4. `firms.json`의 `runnable` 게이트 해제 경로 연결 (readiness `available` 시).

---

## 3. 아웃풋 정의

### 최종 산출 (P5, 파일 단위)

| 파일 | 내용 | 단위 |
|---|---|---|
| `ti_cohort_summary.csv` | 기업×코호트연도×시나리오 총 TI, 방향, FLAG 제외 수 | tCO2e |
| `ti_annual_timeseries.csv` | t=0…T−1 연도별 TI (S1/S2/S3) | tCO2e/yr |
| `ti_portfolio_rolling.csv` | 롤링 포트폴리오 TI — **다년 코호트 확보 전까지 보고 제외** (§0 정합성 점검 1) | tCO2e/yr |
| `ti_decomposition.csv` | 국가별·파워트레인별 분해 (헤드라인 필수 동반) | tCO2e |
| `ti_crossover.csv` | 국가×파워트레인별 교차연도 + 대당 TI | 년, kgCO2e/대 |
| `ti_result.json` | 전체 결과 + 감도 | |
| `data_quality_declaration.txt` | Tier 선언, 누락 목록, Scope3 비상계 문구 | |
| PNG 3개 | 포트폴리오 밴드, 분해, 단일코호트 | |

### 해석 규칙

- TI > 0: 판매 포트폴리오가 판매국 NDC 달성에 기여.
- TI < 0: 정책 궤도 대비 락인 부채.
- S1–S3 밴드 폭 = 정책 리스크 노출도.
- Tier C 물량 비중 > 50% → 수치 억제, 방향만 공표 (`tier_c_threshold`).

### 보고 금지사항

S2 단독 보고 ✕ · 분해 없는 헤드라인 ✕ · 단일코호트/포트폴리오 혼동 ✕ ·
Scope 3 Cat.11 상계 ✕ · 프로라타 무공시 ✕ · 지역평균 그리드 ✕.

---

## 4. 실행 순서 제안 (사용자 계획에 매핑)

1. **[정의 — 본 문서]** 완료.
2. **[엑셀 수집]** §1의 8개 시트. 우선순위: EU27 파일럿이면 Sheet 2는 확보됨 →
   실제 수집 대상은 **VKT(27개국), T·생존곡선, EU 수송/전력 S1/S2/S3 경로,
   ICCT 보정계수, PHEV UF** 5종. Sheet 6(NDC)은 EU 단일이라 작음.
3. **[CSV 변환 → 단계별 실행]** 시트별 `<sheet>.csv` 저장 → P2→P3→P4→P5 순서로
   하나씩 실행, 단계별 산출 확인. §2 수정 목록 1–3을 먼저 반영해야 P4 진입 가능.
4. **[공개]** `check_published.py` 통과 + readiness `available` 확인 후 GitHub 푸시.
