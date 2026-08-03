import Link from "next/link";
import { getCountryViews } from "@/lib/country";
import { getFirms, getMeta, getSectors } from "@/lib/data";

export default function Home() {
  const firms = getFirms();
  const meta = getMeta();
  const countries = getCountryViews();
  const sectors = getSectors();
  const ready = countries.filter((country) => country.benchmarkStatus === "COMPUTED").length;
  const ti = firms.filter((firm) => firm.project === "TI");
  const aligned = firms.filter((firm) => firm.alignment_available);

  return (
    <main className="story-home">
      <section className="story-hero">
        <div className="story-frame story-hero-grid">
          <div className="story-hero-copy">
            <p className="eyebrow">Trade Impact · Evidence alignment platform</p>
            <h1>See where company activity meets <em>market climate targets.</em></h1>
            <p className="lede">
              Start with observed company activity, retain the country and sector boundary,
              then compare only like-for-like metrics. Automotive and power are live pilots;
              shipping, steel, and petrochemicals use the same evidence contract next.
            </p>
            <div className="hero-actions">
              <Link className="button primary" href="/analysis/toyota">Open Toyota · EU27 pilot</Link>
              <Link className="button secondary" href="#sectors">Review sector boundaries</Link>
            </div>
            <div className="trust-row" aria-label="Dataset controls">
              <span>Observed activity only</span>
              <span>Primary sources linked</span>
              <span>Missing inputs stay missing</span>
            </div>
          </div>
          <div className="hero-figure">
            <div className="figure-heading">
              <div><span>Current evidence pilot</span><strong>Toyota-brand new cars · EU27 · 2024</strong></div>
              <span className="figure-tag">EEA final monitoring data</span>
            </div>
            <div className="hero-pilot">
              <div><strong>803,094</strong><span>registrations observed</span></div>
              <div><strong>107.1</strong><span>gCO₂/km WLTP average</span></div>
              <div><strong>99.99%</strong><span>WLTP mapping coverage</span></div>
            </div>
            <p>Portfolio pathway comparison only — not a manufacturer compliance ruling.</p>
          </div>
        </div>
      </section>

      <section className="story-facts" aria-label="Published data scope">
        <div className="story-frame story-fact-grid">
          <div><strong>{aligned.length}</strong><span>published company-market snapshot</span></div>
          <div><strong>{sectors.length}</strong><span>sector contracts registered</span></div>
          <div><strong>{meta.alignment_contract.company_metrics}</strong><span>auditable metric records</span></div>
        </div>
      </section>

      <section className="story-chapter" id="assessments">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>01</b><span>/ company-market evidence pilots</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>Three snapshots, <em>one evidence discipline.</em></h2>
                <p>
                  Toyota uses official registration records and a directly comparable EU fleet
                  pathway. JERA uses independently assured generation data. KOEN preserves
                  company-reported totals but blocks intensity calculations where the denominator
                  and row reconciliation cannot be verified.
                </p>
              </div>
              <span className="as-of">FY2024 · source-backed</span>
            </div>
          </header>
          <div className="pilot-list">
            <div className="declaration pilot-declaration">
              <div><h3>Toyota · European Union</h3><p className="panel-note">Observed registrations → certified WLTP metric → adopted EU fleet pathway.</p></div>
              <Link className="button primary" href="/analysis/toyota">Inspect automotive evidence →</Link>
            </div>
            <div className="declaration pilot-declaration">
              <div><h3>JERA · Japan</h3><p className="panel-note">Assured generation → emissions intensity → boundary-checked national context.</p></div>
              <Link className="button secondary" href="/analysis/jera">Inspect power evidence →</Link>
            </div>
            <div className="declaration pilot-declaration">
              <div><h3>KOEN · Republic of Korea</h3><p className="panel-note">Reported generation and emissions → data-quality gate → national context only.</p></div>
              <Link className="button secondary" href="/analysis/koen">Inspect KOEN evidence →</Link>
            </div>
          </div>
        </div>
      </section>

      <section className="story-chapter story-chapter-alt" id="markets">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>02</b><span>/ operating-country evidence</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>What can be reviewed <em>objectively today.</em></h2>
                <p>Each market page shows only the workbook-backed grid and scenario fields, their status, warnings, and source text.</p>
              </div>
            </div>
          </header>
          <div className="country-grid">
            {countries.map((country) => {
              const isReady = country.benchmarkStatus === "COMPUTED";
              return (
                <Link className="country-card" href={`/country/${country.code}`} key={country.code}>
                  <div className="country-card-top">
                    <span className="country-code">{country.code}</span>
                    <span className={`status-dot ${isReady ? "ready" : "flag"}`}>
                      {isReady ? "Benchmark available" : "Benchmark flagged"}
                    </span>
                  </div>
                  <strong>{country.name}</strong>
                  <p>Source-backed benchmark record · no company score</p>
                  <span className="card-link">Review evidence →</span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <section className="story-chapter" id="sectors">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>03</b><span>/ sector expansion contract</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>One method, <em>different physical denominators.</em></h2>
                <p>Every sector keeps its own operating boundary, activity basis, direct metric, and known comparability risks.</p>
              </div>
            </div>
          </header>
          <div className="sector-grid">
            {sectors.map((sector) => (
              <article className="sector-card" key={sector.sector_id}>
                <div><span>{sector.implementation_status}</span><b>{sector.sector_id}</b></div>
                <h3>{sector.name}</h3>
                <p>{sector.activity_basis}</p>
                <small>{sector.direct_metrics.map((metric) => `${metric.label} · ${metric.unit}`).join(" / ")}</small>
                {sector.sector_id === "power" ? <><Link href="/analysis/jera">Open JERA · Japan →</Link><Link href="/analysis/koen">Open KOEN · Korea →</Link></> : null}
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="story-chapter story-chapter-alt" id="method">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>04</b><span>/ publication rule</span></p>
            <div className="chapter-heading-row">
              <div><h2>Missing data is a result, <em>not a zero.</em></h2></div>
            </div>
          </header>
          <div className="principle-grid">
            <article><span>01 / source</span><h3>Traceable inputs</h3><p>Every numerical input needs a named primary or official source and a defined unit.</p></article>
            <article><span>02 / mapping</span><h3>Observed activity</h3><p>Company activity retains its country, year, technology, product, and coverage boundary.</p></article>
            <article><span>03 / comparison</span><h3>Like-for-like targets</h3><p>Arithmetic requires the same sector, metric definition, geography, and unit.</p></article>
          </div>
          <details className="directory-details">
            <summary><span>Trade Impact candidate universe</span><small>{ti.length} companies tracked</small></summary>
            <div className="directory-body firm-grid">
              {ti.map((firm) => (
                <article className="firm-card" key={firm.slug}>
                  <h3>{firm.name}</h3><p>{firm.country} · {firm.sector}</p><span>{firm.alignment_available ? "Evidence snapshot available" : "Data collection required"}</span>
                </article>
              ))}
            </div>
          </details>
        </div>
      </section>
    </main>
  );
}
