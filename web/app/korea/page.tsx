import Link from "next/link";
import CumulativeLines from "@/components/CumulativeLines";
import DecompBars from "@/components/DecompBars";
import { getCountryView } from "@/lib/country";
import {
  directionClass,
  directionOf,
  getFirmResult,
  getFirms,
} from "@/lib/data";
import type { Direction } from "@/lib/shared";

export const metadata = { title: "한국 기업별 현황 — Trade Impact" };

function compactCarbon(value: number | undefined): string {
  if (value === undefined) return "—";
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) return `${(absolute / 1_000_000).toFixed(2)} MtCO₂e`;
  if (absolute >= 1_000) return `${(absolute / 1_000).toFixed(0)} ktCO₂e`;
  return `${absolute.toLocaleString("en-US", { maximumFractionDigits: 0 })} tCO₂e`;
}

function koImpactLabel(direction: Direction): string {
  if (direction === "contribution") return "NDC 기여";
  if (direction === "liability") return "NDC 고착";
  if (direction === "neutral") return "NDC 정합";
  return "결과 없음";
}

export default function KoreaPage() {
  const kr = getCountryView("KR");
  const firms = getFirms().filter((firm) => firm.runnable && !firm.illustrative);
  const rows = firms.map((firm) => {
    const result = getFirmResult(firm.slug);
    const s2 = result.cohorts.S2?.by_country?.KR;
    const series = (result.by_year?.series ?? []).map((year) => ({
      year: year.year,
      units: year.units_by_country?.KR ?? 0,
      s2: year.cohorts.S2?.by_country?.KR,
    }));
    const units = series.find((y) => y.year === result.cohort_year)?.units ?? 0;
    return { firm, result, s2, units, series };
  });
  const comparison = Object.fromEntries(
    rows.filter((row) => row.s2 !== undefined).map((row) => [row.result.firm, row.s2 as number]),
  );
  const maxAbs = Math.max(
    1,
    ...rows.flatMap((row) => row.series.map((y) => Math.abs(y.s2 ?? 0))),
  );
  const FIRM_COLORS: Record<string, string> = { toyota: "#3987e5", hyundai: "#d95926" };
  const years = [...new Set(rows.flatMap((row) => row.series.map((y) => y.year)))].sort();
  const cumulativeSeries = rows
    .map((row) => {
      const values: number[] = [];
      for (const point of [...row.series].sort((a, b) => a.year - b.year)) {
        if (point.s2 === undefined) return null;
        values.push((values[values.length - 1] ?? 0) + point.s2);
      }
      return values.length === years.length && years.length > 1
        ? {
            key: row.result.firm,
            label: row.result.firm,
            color: FIRM_COLORS[row.firm.slug] ?? "#199e70",
            values,
          }
        : null;
    })
    .filter((entry): entry is NonNullable<typeof entry> => entry !== null);
  const perVehicle = rows
    .filter((row) => row.s2 !== undefined && row.units > 0)
    .map(
      (row) =>
        `${row.result.firm} ${((row.s2 as number) / row.units).toFixed(1)} tCO₂e/대 ` +
        `(${row.units.toLocaleString("en-US")}대 판매)`,
    )
    .join(" · ");

  return (
    <main>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/#markets">Operating markets</Link><span>/</span><span>한국</span>
      </nav>
      <header className="lab-header">
        <div>
          <p className="eyebrow">국가 포커스</p>
          <h1>한국, 기업별로 보기</h1>
          <p className="lede">
            평가 대상 기업의 한국 판매분을 한국 2035 NDC에 대비해 측정합니다.
            초록 막대는 NDC 달성에 기여, 적갈색 막대는 배출 고착을 뜻합니다.
          </p>
        </div>
        <div className="lab-scope">
          <span>벤치마크</span>
          <strong>KR 2035 NDC</strong>
          <Link href="/country/KR">한국 시장 상세 페이지 →</Link>
        </div>
      </header>

      <dl className="korea-facts">
        <div><strong>{kr ? ((kr.rFleet?.s2 ?? 0) * 100).toFixed(2) : "—"}%/yr</strong><span>NDC 기반 수송부문 감축 속도</span></div>
        <div><strong>{kr?.gridIntensity === undefined ? "—" : `${(kr.gridIntensity * 1000).toFixed(0)} g`}</strong><span>전력 gCO₂/kWh (2024)</span></div>
        <div><strong>{kr?.vkt == null ? "—" : `${kr.vkt.toLocaleString("en-US")} km`}</strong><span>연평균 주행거리</span></div>
        <div><strong>{rows.length}</strong><span>한국에서 평가된 기업 수</span></div>
      </dl>

      <section className="simple-report-section">
        <p className="eyebrow">기업 비교 · {rows[0]?.result.cohort_year} 판매분</p>
        <h2>누가 한국 NDC를 돕고, 누가 거스르는가?</h2>
        <p className="section-lede">
          각 기업의 한국 판매분이 공통 KR 벤치마크에 대비해 갖는 수명주기 영향입니다.
          기업 간 값은 합산되지 않으며, 각각 독립적인 비교입니다.
        </p>
        <div className="quiet-panel">
          <DecompBars
            data={comparison}
            unit="tCO₂e"
            caption="tCO₂e · 초록 = NDC 기여 · 적갈색 = NDC 고착"
          />
          {perVehicle && (
            <p className="panel-note">
              대당 환산: {perVehicle} — 절대량 격차는 대부분 판매 규모 차이에서 나옵니다.
            </p>
          )}
        </div>
      </section>

      <section className="simple-report-section">
        <p className="eyebrow">시계열 변화</p>
        <h2>각 기업의 한국 영향은 어떻게 움직이고 있나</h2>
        <p className="section-lede">
          2022–{rows[0]?.result.cohort_year} 판매연도를 모두 현재 벤치마크로 측정해,
          판매량과 파워트레인 믹스 변화의 효과만 분리해 보여줍니다.
        </p>
        {cumulativeSeries.length > 0 && (
          <div className="quiet-panel">
            <CumulativeLines
              years={years}
              series={cumulativeSeries}
              ariaLabel="한국 내 기업별 누적 NDC 영향 (판매연도 기준)"
              caption="tCO₂e, 판매연도 코호트 누적 · 음수 = NDC 고착 누적"
            />
          </div>
        )}
        <div className="korea-firm-grid">
          {rows.map(({ firm, result, s2, units, series }) => {
            const direction = directionOf(s2);
            return (
              <article className="korea-firm-card" key={firm.slug}>
                <div className="korea-firm-head">
                  <h3><Link href={`/report/${firm.slug}`}>{result.firm}</Link></h3>
                  <span className={`direction-chip ${directionClass(direction)}`}>
                    {koImpactLabel(direction)}
                  </span>
                </div>
                <p className="panel-note">
                  {result.cohort_year}년 한국 판매 {units.toLocaleString("en-US")}대
                  {s2 !== undefined && ` · 수명주기 ${s2 < 0 ? "고착" : "기여"} ${compactCarbon(s2)}`}
                  {firm.netzero && ` · 기업 목표: ${firm.netzero.target_year} 탄소중립`}
                </p>
                <div>
                  {series.map((year) => {
                    const width = Math.max((Math.abs(year.s2 ?? 0) / maxAbs) * 100, 2);
                    return (
                      <div className="korea-year-row" key={year.year}>
                        <span className="mono">{year.year}</span>
                        <span className="mono">{year.units.toLocaleString("en-US")}</span>
                        <div className="korea-bar" aria-hidden="true">
                          <span className={(year.s2 ?? 0) >= 0 ? "pos" : "neg"} style={{ width: `${width}%` }} />
                        </div>
                        <span className="mono num">{compactCarbon(year.s2)}</span>
                      </div>
                    );
                  })}
                </div>
                <p className="panel-note">연도 · 판매 대수 · 수명주기 NDC 영향</p>
              </article>
            );
          })}
        </div>
        <p className="plain-footnote">
          벤치마크는 현재 버전으로 고정 — 연도 간 차이는 판매 믹스 효과만 반영합니다.
          출처·Tier는 각 기업 리포트의 Backing data 섹션 참조.
        </p>
      </section>
    </main>
  );
}
