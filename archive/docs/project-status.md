# 프로젝트 진행 상태 — 단계별 점검

> 2026-08-06 작성, 2026-08-09 갱신. 각 단계가 잘 되고 있는지, 무엇으로 확인하는지,
> 무엇이 막고 있는지를 한 문서로 관리한다. 상태 갱신은 이 파일에서만 한다.
>
> 1차 목표: **절대 배출량 기반 lifetime TI** — "회사가 2024년에 판 차들이 수명 동안 뿜을
> 배출량"을 판매국 정책경로와 비교. 설계는 [rebuild-spec.md](rebuild-spec.md).

---

## 진행 단계 총괄

| 단계 | 내용 | 상태 | 확인 방법 |
|---|---|---|---|
| 0 | 프로젝트 이해·해부 | ✅ 완료 | rebuild-spec.md §0 |
| 1 | 데이터셋·프로세스·아웃풋 정의 | ✅ 완료 | rebuild-spec.md §1–3 |
| 2 | 입력 데이터 수집 | ✅ 완료 | `destination_inputs.json` 27/27 결측 0 |
| 3 | 실행·검증 | ✅ 완료 | `check_published.py` → OK, `lifetime_results.json` |
| 4 | GitHub 공개 | 🟡 커밋 대기 | README 갱신 완료, 푸시 남음 |

---

## 기반 시스템 상태 (2026-08-09 실측)

| 항목 | 상태 | 증거 |
|---|---|---|
| 계산 엔진 (`ti-framework`) | ✅ 정상 | pytest 98/98 |
| 파이프라인 재현성 | ✅ 정상 | `check_published.py` → OK (전체 재계산 대조) |
| 물량 (EU27×2024, 토요타·현대) | ✅ 확보 | `product_cohorts.json` 1,286행 / 1,233,030대 |
| 인증 배출강도 | ✅ 확보 | 행별 tailpipe·전비 |
| 목적지 입력 (VKT·수명·플릿기준·그리드) | ✅ 확보 | `destination_inputs.json`, 27개국 결측 0 |
| 시나리오 경로 (r_fleet·r_power S1/S2/S3) | ✅ 확보 | 위 파일, 출처·프로라타 공시 포함 |
| lifetime TI 결과 | ✅ 공표 | `lifetime_results.json` 2개 코호트 |
| 웹·MCP | ✅ 가동 | `/impact`, MCP 도구 11종 |

---

## 수집한 입력과 그 출처

전부 공개·기계판독 소스, 해시 고정 스냅샷
(`data-pipeline/source-snapshots/destination_eu27_inputs.json`).

| 입력 | 소스 | 도출 | Tier |
|---|---|---|---|
| VKT (연간 주행거리) | Eurostat `road_tf_veh` (TER_REGNAT) | 자국등록 차량주행거리 ÷ 등록대수 | A 14개국 / C 13개국 |
| I_fleet(0) (플릿 서비스강도) | Eurostat `env_air_gge` CRF 1.A.3.b.i | 승용차 CO2 ÷ (등록대수 × VKT) | VKT tier 승계 |
| G(0) (그리드 강도) | Ember (Our World in Data 경유) | 2024 국가값, 지역평균 대체 없음 | A |
| T (운행수명) | Eurostat `road_eqs_carage` | 평균차령×1.5, 밴드 [1×, 2×] | B / C |
| r_fleet S1 | Eurostat 대당 CO2 로그선형 2015–2024 (2020–21 제외) | 국가별 관측추세 | A |
| r_fleet S2 | EC 2040 IA 수송경로 795.6→583 Mt | CAGR 4.34%/yr, 지역 프록시 | B |
| r_fleet S3 | EU 2040 −90% 프로라타 | 13.51%/yr | B |
| r_power S1 | Ember 그리드강도 로그선형 | 국가별 관측추세, r_fleet과 독립 | A |
| r_power S2 | EU 2030 −55% 프로라타 (CRF 1.A.1.a) | **이미 달성 → 0으로 고정 + 공시** | B |
| r_power S3 | EU 2040 −90% 프로라타 | 8.56%/yr | B |
| 실주행 보정 | EEA OBFCM MY2022 | 휘발유 ×1.211, 디젤 ×1.171, ICE 중간값 | A |

---

## 1차 결과 (2026-08-09)

두 코호트 모두 세 시나리오 전부에서 **부채(carbon lock-in)**. Tier-C 물량 비중이
50%를 넘어 엔진이 `directional_only`를 켬 — 방향은 보고, 크기는 억제 대상.

| 코호트 | 대수 | 커버 | S1 관측추세 | S2 공약정책 | S3 1.5°C |
|---|---|---|---|---|---|
| Toyota EU27 2024 | 803,094 | 96.9% | −1.40 Mt | −5.97 Mt | −13.95 Mt |
| Hyundai EU27 2024 | 429,936 | 95.6% | −1.49 Mt | −3.72 Mt | −7.78 Mt |

- Toyota HEV 610,881대가 S3 −10.41 Mt로 단일 최대 부채. HEV 전략은 느린 탈탄소
  시나리오에서만 성립.
- Hyundai BEV 41,582대는 세 시나리오 모두 유일한 양수(+0.80 / +0.58 / +0.33 Mt).
  단 벤치마크가 빨라질수록 우위가 줄어듦.
- 미커버분(PHEV 3.0%/4.3%, FCEV 0.09%/0.01%)은 0이 아니라 **대수·사유와 함께 보류**.

---

## 남은 한계 (공표 문구에 반영됨)

1. **VKT 프록시 13개국** (AT BG CY DK GR HU IT LU PL PT RO SK ES). 국가 교통통계
   부재. EU 평균 11,982 km/yr 적용, 측정국 사분위 밴드 10,366–13,265로 감도 공표.
   세 시나리오 모두 부호 안정.
2. **원산지 미매핑.** EU27 등록 기준이므로 "수출 영향"이 아니라 **판매 코호트 영향**.
   `origin_mapping_status: not_collected`.
3. **PHEV·FCEV 보류.** charge-depleting/sustaining 분리값과 수소 강도 미수집.
4. **롤링 포트폴리오 미공표.** 단일 코호트를 반복하면 반사실. 다년 등록 확보 시 해제.
5. **BEV 실주행 보정 없음.** 공식 BEV 전비 갭 미공표 → 인증값 그대로. ICE 대비
   BEV에 유리한 방향이므로 명시 공시.
6. **LU 플릿기준 이상치** 391 gCO2/km — 국경 급유. `FLEET_INTENSITY_IMPLAUSIBLE`
   플래그 + Tier C 강등.

---

## 재현

```bash
ti-framework/.venv/bin/python data-pipeline/adapters/destination_eu.py --refresh
ti-framework/.venv/bin/python data-pipeline/build_dataset.py
ti-framework/.venv/bin/python data-pipeline/check_published.py
ti-framework/.venv/bin/python data-pipeline/lifetime_run.py --out outputs
```
