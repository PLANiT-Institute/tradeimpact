import Link from "next/link";
import DecompBars from "@/components/DecompBars";
import { getCountryView } from "@/lib/country";
import {
  directionClass,
  directionOf,
  getFirmResult,
  getFirms,
  ndcImpactLabel,
} from "@/lib/data";

export const metadata = { title: "Korea — Trade Impact" };

function compactCarbon(value: number | undefined): string {
  if (value === undefined) return "—";
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) return `${(absolute / 1_000_000).toFixed(2)} MtCO₂e`;
  if (absolute >= 1_000) return `${(absolute / 1_000).toFixed(0)} ktCO₂e`;
  return `${absolute.toLocaleString("en-US", { maximumFractionDigits: 0 })} tCO₂e`;
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

  return (
    <main>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/#markets">Operating markets</Link><span>/</span><span>Korea</span>
      </nav>
      <header className="lab-header">
        <div>
          <p className="eyebrow">Country focus</p>
          <h1>Korea, firm by firm</h1>
          <p className="lede">
            Every assessed company&apos;s sales in Korea, measured against Korea&apos;s
            2035 NDC. Green bars help delivery; rust bars lock emissions in.
          </p>
        </div>
        <div className="lab-scope">
          <span>Benchmark</span>
          <strong>KR 2035 NDC</strong>
          <Link href="/country/KR">Full Korea market page →</Link>
        </div>
      </header>

      <dl className="korea-facts">
        <div><strong>{kr ? ((kr.rFleet?.s2 ?? 0) * 100).toFixed(2) : "—"}%/yr</strong><span>NDC-derived reduction pace</span></div>
        <div><strong>{kr?.gridIntensity === undefined ? "—" : `${(kr.gridIntensity * 1000).toFixed(0)} g`}</strong><span>grid CO₂ per kWh (2024)</span></div>
        <div><strong>{kr?.vkt == null ? "—" : `${kr.vkt.toLocaleString("en-US")} km`}</strong><span>average driven per year</span></div>
        <div><strong>{rows.length}</strong><span>companies assessed in Korea</span></div>
      </dl>

      <section className="simple-report-section">
        <p className="eyebrow">Company comparison · {rows[0]?.result.cohort_year} sales</p>
        <h2>Who helps Korea&apos;s NDC, who works against it?</h2>
        <p className="section-lede">
          Lifetime impact of each company&apos;s Korean sales against the shared KR
          benchmark. Values are not summed across firms — each is its own comparison.
        </p>
        <div className="quiet-panel">
          <DecompBars data={comparison} unit="tCO₂e" />
        </div>
      </section>

      <section className="simple-report-section">
        <p className="eyebrow">Change over time</p>
        <h2>How each company&apos;s Korea impact is moving</h2>
        <p className="section-lede">
          Sales years 2022–{rows[0]?.result.cohort_year}, all measured against today&apos;s
          benchmark, so the bars show what changing sales volume and powertrain mix did.
        </p>
        <div className="korea-firm-grid">
          {rows.map(({ firm, result, s2, units, series }) => {
            const direction = directionOf(s2);
            return (
              <article className="korea-firm-card" key={firm.slug}>
                <div className="korea-firm-head">
                  <h3><Link href={`/report/${firm.slug}`}>{result.firm}</Link></h3>
                  <span className={`direction-chip ${directionClass(direction)}`}>
                    {ndcImpactLabel(direction)}
                  </span>
                </div>
                <p className="panel-note">
                  {units.toLocaleString("en-US")} vehicles sold in Korea in {result.cohort_year}
                  {s2 !== undefined && ` · ${compactCarbon(s2)} lifetime ${s2 < 0 ? "lock-in" : "contribution"}`}
                  {firm.netzero && ` · company target: carbon neutral ${firm.netzero.target_year}`}
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
                <p className="panel-note">year · vehicles sold · lifetime NDC impact</p>
              </article>
            );
          })}
        </div>
        <p className="plain-footnote">
          Benchmarks held at the current vintage; differences between years isolate the
          sales-mix effect. Sources and tiers: each company report → Backing data.
        </p>
      </section>
    </main>
  );
}
