import Link from "next/link";
import GapHero from "@/components/GapHero";
import { getCountryViews } from "@/lib/country";
import {
  directionClass,
  directionOf,
  displayTI,
  getFirmResult,
  getFirms,
  getMeta,
  impactDirectionWord,
  ndcImpactLabel,
  SCENARIOS,
  type Direction,
} from "@/lib/data";

function getAssessmentRows() {
  return getFirms()
    .filter((f) => f.runnable && !f.illustrative)
    .map((f) => {
      const r = getFirmResult(f.slug);
      const excluded = Object.keys(r.cohorts.S2?.excluded_flag_markets ?? {});
      const markets = new Set<string>();
      for (const scenario of SCENARIOS) {
        for (const code of Object.keys(r.cohorts[scenario]?.by_country ?? {})) markets.add(code);
        for (const code of Object.keys(r.cohorts[scenario]?.excluded_flag_markets ?? {})) {
          markets.add(code);
        }
      }
      const placements =
        (r.inputs?.placements as Array<{ country: string; units?: number }> | undefined) ?? [];
      const s2Units = placements
        .filter((placement) => !excluded.includes(placement.country))
        .reduce((total, placement) => total + (placement.units ?? 0), 0);
      return {
        f,
        r,
        excluded,
        markets: [...markets].sort(),
        s2: r.cohorts.S2?.total_tCO2e,
        s2Units,
      };
    });
}

type AssessmentRow = ReturnType<typeof getAssessmentRows>[number];

function compactCarbon(value: number | undefined): string {
  if (value === undefined) return "Not computable";
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) return `${(absolute / 1_000_000).toFixed(2)} MtCO₂e`;
  if (absolute >= 1_000) return `${(absolute / 1_000).toFixed(0)} ktCO₂e`;
  return `${absolute.toLocaleString("en-US", { maximumFractionDigits: 0 })} tCO₂e`;
}

function businessDirection(direction: Direction): string {
  return ndcImpactLabel(direction);
}

function basisLabel(firm: AssessmentRow["f"]): string {
  return firm.basis === "estimated" ? "Estimated" : "Collected";
}

function AssessmentCards({ rows }: { rows: AssessmentRow[] }) {
  return (
    <div className="assessment-grid">
      {rows.map(({ f, r, excluded, markets, s2, s2Units }) => {
        const direction = directionOf(s2);
        const directionalOnly = r.cohorts.S2?.directional_only;
        const coverage = f.coverage_ratio;
        return (
          <article className="assessment-card" key={f.slug}>
            <div className="assessment-card-top">
              <div>
                <p className="card-kicker">Automotive · {r.cohort_year} cohort</p>
                <h3>{r.firm}</h3>
              </div>
              <span className={`status-pill ${f.basis === "estimated" ? "estimated" : "verified"}`}>
                {basisLabel(f)}
              </span>
            </div>

            <div className="signal-panel">
              <span>Impact of {r.cohort_year} represented sales on national NDCs</span>
              <strong className={`dir-${directionClass(direction)}`}>
                {businessDirection(direction)}
              </strong>
              <b title={s2 === undefined ? undefined : `${s2.toLocaleString("en-US")} tCO₂e`}>
                {directionalOnly ? "Direction only" : compactCarbon(s2)}
              </b>
            </div>

            <dl className="assessment-metrics">
              <div>
                <dt>Sales covered</dt>
                <dd>{coverage === undefined ? "—" : `${(coverage * 100).toFixed(1)}%`}</dd>
              </div>
              <div>
                <dt>NDC markets included</dt>
                <dd>{markets.length - excluded.length}/{markets.length}</dd>
              </div>
              <div>
                <dt>Gap per vehicle</dt>
                <dd>
                  {s2 === undefined || s2Units === 0 || directionalOnly
                    ? "—"
                    : `${Math.abs(s2 / s2Units).toLocaleString("en-US", { maximumFractionDigits: 2 })} t ${impactDirectionWord(direction)}`}
                </dd>
              </div>
            </dl>

            <p className="assessment-scope">
              NDC result uses {markets.length - excluded.length} of {markets.length} represented sales markets.
              {excluded.length > 0 && <> Excludes <span className="mono">{excluded.join(", ")}</span>.</>}
            </p>
            <Link className="card-link" href={`/report/${f.slug}`}>
              Open company assessment <span aria-hidden="true">→</span>
            </Link>
          </article>
        );
      })}
    </div>
  );
}

function FirmTable({ rows }: { rows: AssessmentRow[] }) {
  const cohortYear = rows[0]?.r.cohort_year;
  return (
    <div className="panel table-scroll comparison-table">
      <table>
        <thead>
          <tr>
            <th>Firm</th>
            <th>Markets</th>
            <th className="num">NDC impact</th>
            <th className="num">Current-policy sensitivity</th>
            <th className="num">1.5°C sensitivity</th>
            <th className="num">NDC / vehicle</th>
            <th>NDC direction</th>
            <th>Coverage</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ f, r, excluded, markets, s2, s2Units }) => {
            const direction = directionOf(s2);
            return (
              <tr key={f.slug}>
                <td><Link href={`/report/${f.slug}`}><strong>{r.firm}</strong></Link></td>
                <td className="mono" style={{ fontSize: 12.5 }}>
                  {markets.join(" ")}
                  {excluded.length > 0 && <span className="muted"> (excl. {excluded.join(" ")})</span>}
                </td>
                {(["S2", "S1", "S3"] as const).map((scenario) => (
                  <td className="num" key={scenario}>
                    {displayTI(
                      r.cohorts[scenario]?.total_tCO2e,
                      r.cohorts[scenario]?.directional_only,
                    )}
                  </td>
                ))}
                <td className="num">
                  {s2 === undefined || s2Units === 0 || r.cohorts.S2.directional_only
                    ? "—"
                    : `${(s2 / s2Units).toLocaleString("en-US", { maximumFractionDigits: 2 })} t`}
                </td>
                <td><span className={`direction-chip ${directionClass(direction)}`}>{businessDirection(direction)}</span></td>
                <td className="num">{f.coverage_ratio === undefined ? "—" : `${(f.coverage_ratio * 100).toFixed(1)}%`}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="panel-note">
        NDC impact is the sales-weighted lifetime gap between products sold in {cohortYear} and
        each operating country&apos;s NDC-derived benchmark. Current-policy and 1.5°C
        results are sensitivities. Firm values are not summable.
      </p>
    </div>
  );
}

export default function Home() {
  const firms = getFirms();
  const meta = getMeta();
  const countries = getCountryViews();
  const rows = getAssessmentRows();
  const ti = firms.filter((f) => f.project === "TI");
  const cap = firms.filter((f) => f.project === "CAP");
  const representedUnits = rows.reduce((total, row) => total + (row.f.assessed_units ?? 0), 0);
  const cohortYear = rows[0]?.r.cohort_year;
  const benchmarkReady = countries.filter((country) => country.benchmarkStatus === "COMPUTED").length;
  const inputBasis = rows.every((row) => row.f.basis === "estimated")
    ? "Estimated inputs"
    : rows.every((row) => row.f.basis !== "estimated")
      ? "Collected inputs"
      : "Mixed input bases";

  return (
    <main className="story-home">
      <section className="story-hero">
        <div className="story-frame story-hero-grid">
          <div className="story-hero-copy">
            <p className="eyebrow">Trade Impact · Automotive</p>
            <h1>
              How do represented products <em>shape national NDC delivery?</em>
            </h1>
            <p className="lede">
              Trade Impact compares the lifetime emissions of a represented sales cohort
              with each operating market&apos;s NDC-derived sector trajectory. The result
              shows whether those products contribute to delivery or lock in emissions
              against it.
            </p>
            <div className="hero-actions">
              <Link className="button primary" href="#assessments">Read the {cohortYear} assessments</Link>
              <Link className="button secondary" href="/calculator">Open the NDC impact lab</Link>
            </div>
            <div className="trust-row" aria-label="Dataset controls">
              <span>Engine computed</span>
              <span>Coverage disclosed</span>
              <span>Inputs traceable</span>
            </div>
          </div>
          <div className="hero-figure">
            <div className="figure-heading">
              <div>
                <span>How the metric works</span>
                <strong>Product emissions vs. NDC benchmark</strong>
              </div>
              <span className="figure-tag">Illustrative shape</span>
            </div>
            <GapHero />
            <p>Contribution below the benchmark · lock-in above it</p>
          </div>
        </div>
      </section>

      <section className="story-facts" aria-label="Published assessment scope">
        <div className="story-frame story-fact-grid">
          <div><strong>{rows.length}</strong><span>published company assessments</span></div>
          <div><strong>{(representedUnits / 1_000_000).toFixed(1)}m</strong><span>{cohortYear} vehicles represented</span></div>
          <div><strong>{benchmarkReady} / {countries.length}</strong><span>markets with a computable NDC benchmark</span></div>
        </div>
      </section>

      <section className="story-chapter" id="assessments">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>01</b><span>/ the {cohortYear} sales cohort</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>The direction is visible at <em>company level.</em></h2>
                <p>
                  “NDC contribution” means the represented products emit less than the
                  NDC-derived benchmark over their lifetime. “NDC lock-in” means they emit more.
                </p>
              </div>
              <span className="as-of">Cohort {cohortYear} · {inputBasis}</span>
            </div>
          </header>
          <AssessmentCards rows={rows} />
          <details className="comparison-details">
            <summary>
              <span>Open the complete scenario comparison</span>
              <small>Core NDC impact, current-policy and 1.5°C sensitivities</small>
            </summary>
            <FirmTable rows={rows} />
          </details>
        </div>
      </section>

      <section className="story-chapter story-chapter-alt" id="markets">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>02</b><span>/ the market lens</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>One portfolio meets <em>many national pathways.</em></h2>
                <p>
                  The same product mix can have a different NDC effect in each sales market.
                  Country pages show the benchmark, represented companies and exclusions
                  behind the result.
                </p>
              </div>
            </div>
          </header>
          <div className="country-grid">
            {countries.map((country) => {
              const ready = country.benchmarkStatus === "COMPUTED";
              return (
                <Link className="country-card" href={`/country/${country.code}`} key={country.code}>
                  <div className="country-card-top">
                    <span className="country-code">{country.code}</span>
                    <span className={`status-dot ${ready ? "ready" : "flag"}`}>
                      {ready ? "Benchmark ready" : "Benchmark unavailable"}
                    </span>
                  </div>
                  <strong>{country.name}</strong>
                  <p>{country.firms.length} compan{country.firms.length === 1 ? "y" : "ies"} assessed</p>
                  <span className="card-link">Review NDC impact →</span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <section className="story-chapter">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>03</b><span>/ the measurement discipline</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>Every result carries <em>its assumptions.</em></h2>
                <p>
                  Trade Impact keeps the model, coverage and evidence boundary attached
                  to the number. A result is useful only when a reader can see what produced it.
                </p>
              </div>
            </div>
          </header>
          <div className="principle-grid">
            <article>
              <span>01 / compute</span>
              <h3>Computed, not typed</h3>
              <p>Published values are generated by the shared TI engine and checked against the packaged dataset.</p>
            </article>
            <article>
              <span>02 / coverage</span>
              <h3>Boundaries stay visible</h3>
              <p>Included sales, unavailable benchmarks and excluded markets remain attached to every assessment.</p>
            </article>
            <article>
              <span>03 / sensitivity</span>
              <h3>One core result, two tests</h3>
              <p>The NDC result is primary; current-policy and 1.5°C pathways test whether its direction holds.</p>
            </article>
          </div>
          <div className="story-actions">
            <Link className="button primary" href="/calculator">Test the assumptions →</Link>
            <a className="button secondary" href="https://transitionarc.climatearc.org">Read the methodology</a>
          </div>
        </div>
      </section>

      <section className="story-chapter story-chapter-alt">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>04</b><span>/ the evidence boundary</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>Publish the result. <em>Expose the gaps.</em></h2>
                <p>
                  A company enters the published set only when the required evidence can
                  produce a documented assessment. The wider universe remains visible as research in progress.
                </p>
              </div>
            </div>
          </header>
          <details className="directory-details">
            <summary>
              <span>Research pipeline and candidate universe</span>
              <small>{ti.length + cap.length} companies tracked across TI and CAP</small>
            </summary>
            <div className="directory-body">
              <h3>Trade Impact candidates</h3>
              <p className="panel-note">A report is published only when documented inputs are available. Missing data is never fabricated.</p>
              <div className="firm-grid">
                {ti.map((firm) => {
                  const content = <><div className="fc-name">{firm.name}</div><div className="fc-sub">{firm.sector} · {firm.country}</div><div className={`fc-state ${firm.runnable ? "ready" : "waiting"}`}>{firm.runnable ? firm.illustrative ? "Illustrative validation" : "Assessment available" : "Awaiting inputs"}</div></>;
                  return firm.runnable ? <Link className="firm-card" href={`/report/${firm.slug}`} key={firm.slug}>{content}</Link> : <div className="firm-card" key={firm.slug}>{content}</div>;
                })}
              </div>
              <h3>Capital Allocation Pathway candidates</h3>
              <div className="firm-grid">
                {cap.map((firm) => <div className="firm-card" key={firm.slug}><div className="fc-name">{firm.name}</div><div className="fc-sub">{firm.sector} · {firm.country} {firm.ticker ? `· ${firm.ticker}` : ""}</div><div className="fc-state waiting">Separate methodology · awaiting inputs</div></div>)}
              </div>
            </div>
          </details>
          <div className="provenance governance-line">
            <strong>Data governance</strong> · engine {meta.engine_version} #{meta.engine_source_sha256.slice(0, 12)} · dataset {meta.dataset_sha256.slice(0, 12)} · workbook #{meta.workbook_sha256.slice(0, 12)} · {meta.collection_status.missing_inputs.length} inputs in collection backlog
          </div>
        </div>
      </section>
    </main>
  );
}
