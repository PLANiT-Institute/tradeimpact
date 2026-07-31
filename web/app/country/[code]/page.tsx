import type { Metadata } from "next";
import Link from "next/link";
import CumulativeLines from "@/components/CumulativeLines";
import ScenarioCards from "@/components/ScenarioCards";
import { getCountryView, getCountryViews } from "@/lib/country";
import { getFirmResult, getMeta, SCENARIO_LABELS, SCENARIOS } from "@/lib/data";

// fixed firm→color assignment (same firm = same color on every page);
// palette validated against the app surface (dataviz six-checks, 2026-07-30)
const FIRM_COLORS: Record<string, string> = {
  toyota: "#3987e5",
  hyundai: "#d95926",
};
const FIRM_FALLBACK = "#199e70";

/** Per-firm cumulative S2 impact in `code` across re-run sales years. */
function firmCumulativeSeries(code: string, slugs: string[]) {
  let years: number[] | null = null;
  const series = [];
  for (const slug of slugs) {
    const result = getFirmResult(slug);
    const rows = [...(result.by_year?.series ?? [])].sort((a, b) => a.year - b.year);
    const values: number[] = [];
    for (const row of rows) {
      const value = row.cohorts.S2?.by_country?.[code];
      if (value === undefined) break;
      values.push((values[values.length - 1] ?? 0) + value);
    }
    if (values.length !== rows.length || rows.length < 2) continue;
    years ??= rows.map((row) => row.year);
    series.push({
      key: result.firm,
      label: result.firm,
      color: FIRM_COLORS[slug] ?? FIRM_FALLBACK,
      values,
    });
  }
  return { years: years ?? [], series };
}

export function generateStaticParams() {
  return getCountryViews().map((v) => ({ code: v.code }));
}
export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ code: string }>;
}): Promise<Metadata> {
  const { code } = await params;
  return { title: `${getCountryView(code)?.name ?? code} — NDC impact by firm` };
}

export default async function CountryPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const v = getCountryView(code)!;
  const meta = getMeta();
  const isFlag = v.benchmarkStatus !== "COMPUTED";
  const cumulative = isFlag
    ? { years: [], series: [] }
    : firmCumulativeSeries(code, v.firms.map((f) => f.slug));

  return (
    <main>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/#markets">Operating markets</Link><span>/</span><span>{v.name}</span>
      </nav>
      <header className="report-header country-header">
        <div>
          <p className="eyebrow">Product sales vs. NDC · cohort {v.cohortYear}</p>
          <div className="title-row">
            <h1>{v.name} <span className="country-title-code">{v.code}</span></h1>
            <span className={`status-pill ${isFlag ? "estimated" : "verified"}`}>
              {isFlag ? "NDC benchmark unavailable" : "NDC benchmark ready"}
            </span>
          </div>
          <p className="lede">
            {isFlag
              ? `${v.name}'s current NDC does not yield an absolute product benchmark. Current-policy and 1.5°C sensitivities remain visible while the core NDC result stays excluded.`
              : `See how represented products sold by each company contribute to or lock in emissions against ${v.name}'s NDC commitment.`}
          </p>
        </div>
      </header>

      <dl className="market-summary">
        <div><dt>NDC benchmark</dt><dd>{isFlag ? "Unavailable for absolute impact" : "Computed"}</dd></div>
        <div><dt>Companies assessed</dt><dd>{v.firms.length}</dd></div>
        <div><dt>Annual distance</dt><dd>{v.vkt == null ? "—" : `${v.vkt.toLocaleString("en-US")} km`}</dd></div>
        <div><dt>Comparison rule</dt><dd>Firm values are not summed</dd></div>
      </dl>

      {isFlag ? (
        <div className="declaration" style={{ marginTop: 20 }}>
          <h3>No absolute NDC impact can be calculated</h3>
          <p className="panel-note">
            {v.flagReason ?? v.benchmarkStatus} — this market is excluded from every
            firm&apos;s core NDC result. Current-policy and 1.5°C sensitivities are still
            calculated where rates are supplied.
          </p>
        </div>
      ) : (
        v.warnings.length > 0 && (
          <ul className="panel-note" style={{ marginTop: 16 }}>
            {v.warnings.map((warning) => (
              <li className="warn-item" key={warning}>{warning}</li>
            ))}
          </ul>
        )
      )}
      {v.source && (
        <p className="panel-note" style={{ marginTop: 8 }}>
          Benchmark source: {v.source}
        </p>
      )}

      <details className="table-view" style={{ marginTop: 16 }}>
        <summary>Sector benchmark parameters (transport · power)</summary>
        <div className="table-scroll" style={{ marginTop: 8 }}>
          <table>
            <thead>
              <tr>
                <th>Scenario</th>
                <th className="num">Transport fleet reduction (%/yr)</th>
                <th className="num">Power sector reduction (%/yr)</th>
              </tr>
            </thead>
            <tbody>
              {SCENARIOS.map((s) => {
                const key = s.toLowerCase();
                const fleet = v.rFleet?.[key];
                const power = v.rPower?.[key];
                return (
                  <tr key={s}>
                    <td>{SCENARIO_LABELS[s]}{s === "S2" ? " (NDC)" : ""}</td>
                    <td className="num">{fleet === undefined ? "—" : (fleet * 100).toFixed(2)}</td>
                    <td className="num">{power === undefined ? "—" : (power * 100).toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="panel-note" style={{ marginTop: 8 }}>
          Grid intensity {v.gridIntensity === undefined ? "—" : `${(v.gridIntensity * 1000).toFixed(0)} gCO₂/kWh`} ·
          annual driving distance {v.vkt == null ? "—" : `${v.vkt.toLocaleString("en-US")} km`}.
          Transport rates benchmark ICE/HEV products; power rates drive the grid trajectory behind BEV/PHEV products.
        </p>
      </details>

      {cumulative.series.length > 0 && (
        <section className="market-firm-section">
          <h2>Cumulative NDC impact by firm</h2>
          <p className="panel-note">
            Each firm&apos;s {cumulative.years[0]}–{cumulative.years[cumulative.years.length - 1]} sales
            cohorts in {v.code}, run against today&apos;s benchmark and accumulated — the slope shows
            whether a firm&apos;s yearly contribution is growing or easing. Lines are independent
            comparisons, not shares of one total.
          </p>
          <div className="quiet-panel">
            <CumulativeLines
              years={cumulative.years}
              series={cumulative.series}
              ariaLabel={`Cumulative S2 NDC impact in ${v.code} by firm across sales years`}
              caption="tCO₂e, cumulative across sales-year cohorts · negative = NDC lock-in accumulating"
            />
          </div>
        </section>
      )}

      {v.firms.map((f) => (
        <section className="market-firm-section" key={f.slug}>
          <h2>
            <Link href={`/report/${f.slug}`}>{f.firm}</Link>
          </h2>
          <p className="panel-note">
            {f.basis === "estimated" ? "Estimated-input assessment" : "Collected-input assessment"}
            {` · ${f.assessedUnits.toLocaleString("en-US")} vehicles represented in ${v.code}`}
            {f.firmCoverage !== undefined
              ? ` · ${(f.firmCoverage * 100).toFixed(1)}% global-sales coverage across all assessed markets`
              : ""}
          </p>
          {f.excludedS2Reason && (
            <p className="panel-note">
              NDC impact excluded — {f.excludedS2Reason}. Sensitivity cases are shown where computed.
            </p>
          )}
          <ScenarioCards
            totals={f.byScenario}
            unit={`tCO₂e in ${v.code} · cohort lifetime`}
            directionalOnly={f.directionalOnly}
          />
          {f.crossover.some((c) => !f.directionalOnly[c.scenario]) && (
            <details className="table-view">
              <summary>Per-vehicle crossover in {v.code}</summary>
              <div className="table-scroll" style={{ marginTop: 8 }}>
                <table>
                  <thead>
                    <tr>
                      <th>Powertrain</th>
                      <th>Scenario</th>
                      <th className="num">t* (yr)</th>
                      <th className="num">Impact / vehicle (kgCO₂e)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {f.crossover.filter((c) => !f.directionalOnly[c.scenario]).map((c, i) => (
                      <tr key={i}>
                        <td className="mono">{c.powertrain}</td>
                        <td className="mono">{c.scenario}</td>
                        <td className="num">
                          {c.crossover_year === null ? "—" : c.crossover_year.toFixed(1)}
                        </td>
                        <td className="num">
                          {c.TI_per_vehicle_kgCO2e?.toLocaleString(
                            "en-US",
                            { maximumFractionDigits: 0 },
                          ) ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </section>
      ))}

      <p className="panel-note" style={{ marginTop: 40 }}>
        Firm values are comparative metrics against {v.name}&apos;s shared benchmark and
        are <strong>not summed across firms</strong> — individual TI claims do not
        physically add up to a sector-level change (Whitepaper §9.2). Absolute totals also
        scale with each firm&apos;s represented sales volume and are not a normalized ranking.
      </p>

      <div className="provenance">
        engine {meta.engine_version} #{meta.engine_source_sha256.slice(0, 12)} · dataset {meta.dataset_sha256.slice(0, 12)} · {meta.workbook} #{meta.workbook_sha256.slice(0, 12)}
      </div>
    </main>
  );
}
