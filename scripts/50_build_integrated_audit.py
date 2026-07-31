#!/usr/bin/env python3
"""Build TI_통합파일.xlsx — the team-facing integrated audit workbook.

Full-value dump of every number behind the published TI dataset, plus a live
verification gate. Never edit the xlsx by hand; regenerate with:

    ti-framework/.venv/bin/python scripts/50_build_integrated_audit.py

Fails closed if any input file is missing. Exit code 1 if any check FAILs.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ti-framework"))
sys.path.insert(0, str(REPO / "data-pipeline"))

PUBLISHED = REPO / "data" / "published"
WORKBOOK = REPO / "ti-framework" / "data" / "TI_Data_Workbook_v0.1.xlsx"
OUT = REPO / "TI_통합파일.xlsx"

REQUIRED = [
    PUBLISHED / "meta.json",
    PUBLISHED / "firms.json",
    PUBLISHED / "countries.json",
    PUBLISHED / "contract.json",
    PUBLISHED / "toyota.json",
    PUBLISHED / "hyundai.json",
    PUBLISHED / "referenceco.json",
    WORKBOOK,
    REPO / "data-pipeline" / "ESTIMATES.md",
    REPO / "data-pipeline" / "COLLECTION_STATUS.md",
    REPO / "data-pipeline" / "SECTORAL_SOURCES.md",
    REPO / "data-pipeline" / "fixtures" / "toyota.json",
    REPO / "data-pipeline" / "fixtures" / "hyundai.json",
]

GREEN = PatternFill("solid", fgColor="C6EFCE")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
RED = PatternFill("solid", fgColor="FFC7CE")
HEADER = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Arial", bold=True, size=13)
BASE_FONT = Font(name="Arial")


def fail_closed() -> None:
    missing = [p for p in REQUIRED if not p.exists()]
    if missing:
        print("빌드 중단 — 입력 파일 누락 (재발행 필요: data-pipeline/build_dataset.py):")
        for p in missing:
            print(f"  - {p.relative_to(REPO)}")
        raise SystemExit(1)


def style_sheet(ws, header_row: int = 1, widths: dict[int, int] | None = None) -> None:
    for cell in ws[header_row]:
        if cell.value is not None:
            cell.fill = HEADER
            cell.font = HEADER_FONT
    for col in range(1, ws.max_column + 1):
        width = (widths or {}).get(col)
        if width is None:
            longest = max(
                (len(str(ws.cell(row=r, column=col).value or "")) for r in range(1, min(ws.max_row, 200) + 1)),
                default=8,
            )
            width = min(max(longest + 2, 10), 55)
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)


def write_rows(ws, header: list[str], rows: list[list], start: int = 1) -> None:
    ws.append(header) if start == 1 else None
    if start != 1:
        for j, h in enumerate(header, 1):
            ws.cell(row=start, column=j, value=h)
    for row in rows:
        ws.append([("" if v is None else v) for v in row])
    for row in ws.iter_rows():
        for cell in row:
            if cell.font == Font():
                cell.font = BASE_FONT


def run_cmd(cmd: list[str], cwd: Path) -> tuple[str, str]:
    """Return (PASS/FAIL/SKIP, last meaningful output line)."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        return "SKIP", f"명령 없음: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return "FAIL", "timeout"
    out = (proc.stdout + proc.stderr).strip().splitlines()
    tail = out[-1] if out else ""
    return ("PASS" if proc.returncode == 0 else "FAIL"), tail


def check_fixture_merge() -> tuple[str, str]:
    """Raw↔published gate: re-merge fixtures with the workbook and diff against
    published inputs. Catches fixture edits that were never republished."""
    from build_dataset import FIXTURES, effective_inputs, merge_workbook_benchmarks  # noqa: E402
    from ti_framework.io.fixtures import load_fixture  # noqa: E402
    from ti_framework.io.workbook import load_workbook_inputs  # noqa: E402

    wb_countries = load_workbook_inputs(WORKBOOK).countries
    diffs = []
    for slug, fixture_path in FIXTURES.items():
        fx = load_fixture(fixture_path)
        if slug != "referenceco":
            merge_workbook_benchmarks(fx, wb_countries)
        expected = effective_inputs(fx, fixture_path)
        published = json.loads((PUBLISHED / f"{slug}.json").read_text())["inputs"]
        if expected != published:
            diffs.append(slug)
    if diffs:
        return "FAIL", f"fixture↔published 불일치: {', '.join(diffs)} — build_dataset.py 재실행 필요"
    return "PASS", "fixture 3건 모두 워크북 병합 후 발행본과 일치"


def parse_md_tables(path: Path) -> list[tuple[str, list[str], list[list[str]]]]:
    """Return (section, header, rows) for every markdown table in the file."""
    tables = []
    section = path.name
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            section = line.lstrip("#").strip()
        if line.lstrip().startswith("|") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").replace(":", "").strip()) <= {"-", " "}:
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            rows = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            tables.append((section, header, rows))
            continue
        i += 1
    return tables


def flat_country(code: str, c: dict) -> list:
    return [
        code,
        c.get("name"),
        c.get("status"),
        c.get("tier"),
        c.get("flag_reason"),
        c.get("grid_intensity"),
        c.get("fleet_intensity_base"),
        c.get("vkt"),
        c["r_fleet"].get("s1"),
        c["r_fleet"].get("s2"),
        c["r_fleet"].get("s2_upper"),
        c["r_fleet"].get("s3"),
        c["r_power"].get("s1"),
        c["r_power"].get("s2"),
        c["r_power"].get("s2_upper"),
        c["r_power"].get("s3"),
        "; ".join(c.get("warnings") or []),
        c.get("source"),
    ]


COUNTRY_HEADER = [
    "코드", "국가", "상태", "Tier", "FLAG 사유", "그리드 원단위 (kgCO2e/kWh)",
    "차량군 기저 원단위 (kgCO2e/km)", "VKT (km/년)",
    "r_fleet S1", "r_fleet S2", "r_fleet S2상단", "r_fleet S3",
    "r_power S1", "r_power S2", "r_power S2상단", "r_power S3",
    "경고", "출처",
]

PLACEMENT_COLS = [
    ("country", "국가"), ("model", "모델/믹스"), ("powertrain", "파워트레인"),
    ("units", "대수"), ("tier", "Tier"),
    ("volume_tier", "물량 Tier"), ("vehicle_tier", "차량 Tier"),
    ("ice_intensity", "ICE 원단위 (kgCO2e/km)"), ("ev_efficiency", "EV 효율 (kWh/km)"),
    ("phev_uf", "PHEV UF"), ("phev_elec_efficiency", "PHEV 전기효율"),
    ("phev_ice_intensity", "PHEV ICE 원단위"),
    ("volume_source", "물량 출처"), ("vehicle_source", "차량 출처"), ("source", "출처(공통)"),
]


def placement_row(p: dict) -> list:
    return [p.get(key) for key, _ in PLACEMENT_COLS]


def firm_input_sheet(wb, title: str, payload: dict) -> None:
    ws = wb.create_sheet(title)
    inputs = payload["inputs"]
    header = [h for _, h in PLACEMENT_COLS]
    rows = [["2024"] + placement_row(p) for p in inputs["placements"]]
    for year in sorted(inputs.get("placements_by_year") or {}):
        rows += [[year] + placement_row(p) for p in inputs["placements_by_year"][year]]
    write_rows(ws, ["코호트 연도"] + header, rows)
    style_sheet(ws)


def firm_result_sheet(wb, title: str, payload: dict) -> None:
    ws = wb.create_sheet(title)
    r = 1

    def block(label: str, header: list[str], rows: list[list]):
        nonlocal r
        ws.cell(row=r, column=1, value=label).font = TITLE_FONT
        r += 1
        for j, h in enumerate(header, 1):
            c = ws.cell(row=r, column=j, value=h)
            c.fill = HEADER
            c.font = HEADER_FONT
        r += 1
        for row in rows:
            for j, v in enumerate(row, 1):
                ws.cell(row=r, column=j, value="" if v is None else v).font = BASE_FONT
            r += 1
        r += 1

    cohort_year = payload["cohort_year"]
    years = list(range(cohort_year, cohort_year + len(payload["portfolio"]["S1"])))
    block(
        "포트폴리오 TI 경로 (tCO2e) — 시나리오별 연도 시리즈",
        ["연도", "S1 누적", "S2 누적", "S3 누적", "S1 연간", "S2 연간", "S3 연간"],
        [[y] + [payload["portfolio"][s][i] for s in ("S1", "S2", "S3")]
             + [payload["cohorts"][s]["annual_tCO2e"][i] for s in ("S1", "S2", "S3")]
         for i, y in enumerate(years)],
    )

    for scen in ("S1", "S2", "S3"):
        c = payload["cohorts"][scen]
        block(
            f"{scen} 코호트 요약",
            ["총 TI (tCO2e)", "방향", "방향성-한정", "제외 FLAG 시장", "경고"],
            [[c["total_tCO2e"], c["direction"], c["directional_only"],
              ", ".join(c.get("excluded_flag_markets") or []), "; ".join(c.get("warnings") or [])]],
        )
        block(
            f"{scen} 국가별 TI (tCO2e)",
            ["국가", "TI"],
            sorted(c["by_country"].items()),
        )
        block(
            f"{scen} 파워트레인별 TI (tCO2e)",
            ["파워트레인", "TI"],
            sorted(c["by_powertrain"].items()),
        )

    block(
        "크로스오버 (국가×파워트레인)",
        ["시나리오", "국가", "파워트레인", "대당 TI (kgCO2e)", "크로스오버 연차", "사유"],
        [[x["scenario"], x["country"], x["powertrain"], x["TI_per_vehicle_kgCO2e"],
          x["crossover_year"], x["reason"]] for x in payload["crossover"]],
    )

    sens_rows = []
    for dim, cases in payload["sensitivity"].items():
        if all(isinstance(v, (int, float)) for v in cases.values()):
            sens_rows.append([dim, "—", cases.get("S1"), cases.get("S2"), cases.get("S3")])
            continue
        for case, scens in cases.items():
            sens_rows.append([dim, case, scens.get("S1"), scens.get("S2"), scens.get("S3")])
    block("민감도 (총 TI, tCO2e)", ["차원", "케이스", "S1", "S2", "S3"], sens_rows)

    by_rows = []
    for entry in payload["by_year"]["series"]:
        for scen in ("S1", "S2", "S3"):
            c = entry["cohorts"][scen]
            by_rows.append([entry["year"], scen, c["total_tCO2e"],
                            c["direction"], c["directional_only"]]
                           + [f"{code}: {v:,.0f}" for code, v in sorted(c["by_country"].items())])
    block("연도별 시리즈 — " + payload["by_year"]["note"],
          ["코호트 연도", "시나리오", "총 TI (tCO2e)", "방향", "방향성-한정", "국가별 TI →"], by_rows)

    dq = payload["data_quality"]
    block("데이터 품질 선언", ["항목", "값"], [
        ["분석 레벨", dq["analysis_level"]],
        ["Layer1 방법", dq["layer1_method"]],
        ["Tier C 비중", dq.get("tier_c_share")],
        ["방향성-한정 임계 초과", dq.get("directional_only")],
        ["벤치마크 Tier", json.dumps(dq["benchmark_tiers"], ensure_ascii=False)],
        ["FLAG 시장", json.dumps(dq["flag_markets"], ensure_ascii=False)],
        ["Layer2 Tier", json.dumps(dq["layer2_tiers"], ensure_ascii=False)],
        ["누락 입력", "; ".join(dq.get("missing_inputs") or [])],
    ])

    nz = payload["inputs"].get("netzero")
    if nz:
        block("넷제로 공약 (공시 기준)", ["항목", "값"],
              [[k, v] for k, v in nz.items()])
    style_sheet(ws)
    ws.freeze_panes = None


def main() -> int:
    fail_closed()

    meta = json.loads((PUBLISHED / "meta.json").read_text())
    firms = json.loads((PUBLISHED / "firms.json").read_text())
    countries = json.loads((PUBLISHED / "countries.json").read_text())
    payloads = {slug: json.loads((PUBLISHED / f"{slug}.json").read_text())
                for slug in ("toyota", "hyundai", "referenceco")}

    py = REPO / "ti-framework" / ".venv" / "bin" / "python"
    checks = [
        ("발행 데이터 전량 재계산 (check_published.py)",
         *run_cmd([str(py), "data-pipeline/check_published.py"], REPO)),
        ("이론↔코드↔테스트 동기화 (check_sync.py)",
         *run_cmd([str(py), "scripts/check_sync.py"], REPO)),
        ("엔진 테스트 스위트 (pytest)",
         *run_cmd([str(py), "-m", "pytest", "-q"], REPO / "ti-framework")),
        ("fixture↔발행본 재병합 대조 (이 스크립트 내장 게이트)",
         *check_fixture_merge()),
        ("웹 데이터 계약 테스트 (npm test)",
         *run_cmd(["npm", "test"], REPO / "web")),
    ]

    wb = Workbook()

    # 00_개요
    ws = wb.active
    ws.title = "00_개요"
    overview = [
        ["TI 통합 파일 (Trade Impact — 통합 데이터 감사 워크북)", ""],
        ["", ""],
        ["생성일", date.today().isoformat()],
        ["생성 스크립트", "scripts/50_build_integrated_audit.py (수기 편집 금지 — 스크립트로만 재생성)"],
        ["재생성 명령", "ti-framework/.venv/bin/python scripts/50_build_integrated_audit.py"],
        ["대상 데이터셋", f"data/published/ (engine {meta['engine_version']}, workbook {meta['workbook']})"],
        ["", ""],
        ["이 파일은 무엇인가", "발행된 TI 데이터셋 뒤의 모든 숫자(원본 워크북, 국가 벤치마크, 기업별 투입·결과, 추정치와 출처, 수집 백로그)를 한 파일에 전량 수록한 감사용 스냅샷. 웹/보고서 숫자는 전부 여기로 추적 가능."],
        ["색상 범례", "초록 = 기계 검증 완료 · 노랑 = 작성자/팀 확인 필요 · 빨강 = 검증 실패"],
        ["", ""],
        ["시트 안내", ""],
        ["01_검증결과", "빌드 시점에 실제 실행한 검증 게이트 결과"],
        ["02_해시증빙", "발행본 무결성 해시 (엔진 소스, 워크북, 입력, 데이터셋)"],
        ["03_국가벤치마크", "11개국 NDC 벤치마크 전량 (출처·Tier·경고 포함)"],
        ["04_지원파라미터", "부문 공통 파라미터 (VKT, 수명, UF 밴드, 실주행 보정)"],
        ["05_기업유니버스", "TI/CAP 대상기업 전체 목록과 실행 가능 여부"],
        ["06~11_기업별", "Toyota / Hyundai / ReferenceCo — 투입 전량 + 결과 전량"],
        ["12_추정치출처", "ESTIMATES.md 전체 표 — 모든 추정치와 근거·출처"],
        ["13_수집백로그", "COLLECTION_STATUS.md — 미수집 항목과 데이터 경고"],
        ["14_부문별출처", "SECTORAL_SOURCES.md — 부문별 NDC 경로·차량 파라미터 공식 출처 (2026-07-30 수집·반영)"],
        ["WB_*", "원본 데이터 워크북 시트 전량 덤프"],
        ["99_체크리스트", "팀 확인란 (노랑 칸에 확인일·서명 기입)"],
        ["", ""],
        ["ReferenceCo 주의", "예시용 검증 픽스처 — 국가 비교·기업 평가 헤드라인에서 제외됨 (NOTES.md D4)"],
    ]
    for row in overview:
        ws.append(row)
    ws["A1"].font = Font(name="Arial", bold=True, size=15)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = BASE_FONT
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 110

    # 01_검증결과
    ws = wb.create_sheet("01_검증결과")
    write_rows(ws, ["검증 게이트", "결과", "상세 (마지막 출력 라인)"],
               [[name, status, detail] for name, status, detail in checks])
    for i, (_, status, _) in enumerate(checks, 2):
        fill = GREEN if status == "PASS" else (YELLOW if status == "SKIP" else RED)
        for j in range(1, 4):
            ws.cell(row=i, column=j).fill = fill
    style_sheet(ws, widths={1: 45, 2: 8, 3: 90})

    # 02_해시증빙
    ws = wb.create_sheet("02_해시증빙")
    prov_rows = [
        ["engine_version", meta["engine_version"], "엔진 패키지 버전"],
        ["engine_source_sha256", meta["engine_source_sha256"], "ti_framework 소스 트리 해시"],
        ["workbook", meta["workbook"], "원본 데이터 워크북 파일명"],
        ["workbook_sha256", meta["workbook_sha256"], "워크북 파일 해시"],
        ["dataset_sha256", meta["dataset_sha256"], "발행 데이터셋 전체 해시"],
        ["compute_service_sha256", meta["compute_service_sha256"], "공개 계산 API (api/compute.py) 해시"],
        ["generated_utc", meta.get("generated_utc"), "발행 시각 (UTC)"],
    ] + [[f"target_sources_sha256.{k}", v, "대상기업 원본 워크북 해시"]
         for k, v in meta.get("target_sources_sha256", {}).items()]
    write_rows(ws, ["항목", "값", "설명"], prov_rows)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.fill = GREEN
    style_sheet(ws, widths={1: 45, 2: 70, 3: 40})

    # 03_국가벤치마크
    ws = wb.create_sheet("03_국가벤치마크")
    write_rows(ws, COUNTRY_HEADER, [flat_country(c["code"], c) for c in countries])
    style_sheet(ws)

    # 04_지원파라미터
    ws = wb.create_sheet("04_지원파라미터")
    sc = meta["support_contract"]
    rows = [
        ["차량 수명 T (년)", sc["lifetime_T"], "전 시장 공통, ±민감도"],
        ["수명 민감도 ± (년)", sc["lifetime_sens"], ""],
        ["실주행 보정 범위", str(sc["realworld_range"]), "인증치 대비 배수"],
        ["PHEV UF 하한 밴드", sc["uf_band"], "규제 UF − 밴드 = 하한 병기 (Guideline §3.5)"],
    ] + [[f"VKT — {code}", v, "km/년"] for code, v in sorted(sc["vkt"].items())]
    write_rows(ws, ["파라미터", "값", "비고"], rows)
    style_sheet(ws, widths={1: 30, 2: 20, 3: 50})

    # 05_기업유니버스
    ws = wb.create_sheet("05_기업유니버스")
    write_rows(
        ws,
        ["기업명", "슬러그", "프로젝트", "섹터", "국가", "실행 가능", "예시용", "코호트 연도", "비고"],
        [[f.get("name"), f.get("slug"), f.get("project"), f.get("sector"), f.get("country"),
          f.get("runnable"), f.get("illustrative", False), f.get("cohort_year"), f.get("note")]
         for f in firms],
    )
    style_sheet(ws)

    # 기업별 투입/결과
    firm_input_sheet(wb, "06_Toyota_투입", payloads["toyota"])
    firm_result_sheet(wb, "07_Toyota_결과", payloads["toyota"])
    firm_input_sheet(wb, "08_Hyundai_투입", payloads["hyundai"])
    firm_result_sheet(wb, "09_Hyundai_결과", payloads["hyundai"])
    firm_input_sheet(wb, "10_RefCo_투입(예시)", payloads["referenceco"])
    firm_result_sheet(wb, "11_RefCo_결과(예시)", payloads["referenceco"])

    # 12_추정치출처 / 13_수집백로그
    for sheet_name, md in (
        ("12_추정치출처", REPO / "data-pipeline" / "ESTIMATES.md"),
        ("13_수집백로그", REPO / "data-pipeline" / "COLLECTION_STATUS.md"),
        ("14_부문별출처", REPO / "data-pipeline" / "SECTORAL_SOURCES.md"),
    ):
        ws = wb.create_sheet(sheet_name)
        r = 1
        ws.cell(row=r, column=1, value=f"원문: {md.relative_to(REPO)} (전체 표 자동 추출)").font = TITLE_FONT
        r += 2
        for section, header, rows in parse_md_tables(md):
            ws.cell(row=r, column=1, value=section).font = Font(name="Arial", bold=True, size=11)
            r += 1
            for j, h in enumerate(header, 1):
                c = ws.cell(row=r, column=j, value=h)
                c.fill = HEADER
                c.font = HEADER_FONT
            r += 1
            for row in rows:
                for j, v in enumerate(row, 1):
                    ws.cell(row=r, column=j, value=v).font = BASE_FONT
                r += 1
            r += 1
        for col in range(1, ws.max_column + 1):
            ws.column_dimensions[get_column_letter(col)].width = 40
        if sheet_name == "13_수집백로그":
            ws.cell(row=r, column=1, value="엔진 보고 누락 입력 (meta.json collection_status)").font = Font(name="Arial", bold=True, size=11)
            r += 1
            for item in meta["collection_status"]["missing_inputs"]:
                cell = ws.cell(row=r, column=1, value=item)
                cell.font = BASE_FONT
                cell.fill = YELLOW
                r += 1
            r += 1
            ws.cell(row=r, column=1, value="엔진 보고 경고").font = Font(name="Arial", bold=True, size=11)
            r += 1
            for item in meta["collection_status"]["warnings"]:
                cell = ws.cell(row=r, column=1, value=item)
                cell.font = BASE_FONT
                cell.fill = YELLOW
                r += 1

    # WB_* 원본 워크북 덤프
    src = load_workbook(WORKBOOK, data_only=True)
    for sheet in src.worksheets:
        ws = wb.create_sheet(f"WB_{sheet.title}"[:31])
        for row in sheet.iter_rows(values_only=True):
            ws.append(list(row))
        if ws.max_row >= 1:
            style_sheet(ws)

    # 99_체크리스트
    ws = wb.create_sheet("99_체크리스트")
    checklist = [
        "01_검증결과 시트의 모든 게이트가 PASS인지 확인",
        "03_국가벤치마크 출처(UNFCCC NDC, Ember 2024)가 최신인지 확인",
        "12_추정치출처의 Tier C 추정치 중 수집 데이터로 교체 가능한 항목 점검",
        "13_수집백로그 항목별 담당자 지정",
        "CA VKT (NRCan 2009, 노후) 대체 출처 탐색 결과 기록",
        "Hyundai CN 미배치(감사 가능한 물량 부재) 유지 여부 재확인",
        "웹 게시본 숫자 스팟체크 (report/[firm] ↔ 07/09 결과 시트)",
    ]
    write_rows(ws, ["항목", "확인자", "확인일", "비고"], [[c, "", "", ""] for c in checklist])
    for i in range(2, len(checklist) + 2):
        for j in (2, 3, 4):
            ws.cell(row=i, column=j).fill = YELLOW
    style_sheet(ws, widths={1: 70, 2: 15, 3: 15, 4: 40})

    wb.save(OUT)

    failed = [name for name, status, _ in checks if status == "FAIL"]
    print(f"저장: {OUT.relative_to(REPO)} ({len(wb.sheetnames)} 시트)")
    for name, status, detail in checks:
        print(f"  [{status}] {name} — {detail}")
    if failed:
        print("검증 실패 게이트 존재 — 워크북의 01_검증결과 시트 확인")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
