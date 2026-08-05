import Link from "next/link";
import {
  getImpactReadiness,
  getMeta,
  getProductCohorts,
  getSectors,
} from "@/lib/data";

export default function Home() {
  const meta = getMeta();
  const cohorts = getProductCohorts();
  const readiness = getImpactReadiness()[0];
  const sectors = getSectors();
  const destinations = new Set(
    cohorts.flatMap((cohort) => cohort.records.map((record) => record.destination_geography)),
  ).size;
  const observedUnits = cohorts.reduce(
    (sum, cohort) => sum + cohort.coverage.reported_units,
    0,
  );

  return (
    <main className="story-home impact-home">
      <section className="story-hero impact-hero">
        <div className="story-frame story-hero-grid">
          <div className="story-hero-copy">
            <p className="eyebrow">Trade Impact · exported-product climate exposure</p>
            <h1>
              A product is sold once. Its emissions shape a destination&apos;s climate path
              <em> for years.</em>
            </h1>
            <p className="lede">
              Trade Impact follows a company&apos;s sold-product cohort into the country where it
              operates, models its use-phase emissions over its service life, and tests that
              trajectory against the destination&apos;s sector pathway and NDC.
            </p>
            <div className="hero-actions">
              <Link className="button primary" href="/compare/automotive">
                Compare Toyota and Hyundai
              </Link>
              <Link className="button secondary" href="#method">
                See the calculation boundary
              </Link>
            </div>
            <div className="trust-row" aria-label="Method controls">
              <span>Observed sales first</span>
              <span>Destination-specific pathways</span>
              <span>Missing assumptions stay missing</span>
            </div>
          </div>
          <div className="hero-figure impact-thesis-card">
            <p className="eyebrow">Core analytical chain</p>
            <ol className="impact-chain" aria-label="Trade Impact analytical chain">
              <li><span>01</span><strong>Company cohort</strong><small>units sold in year Y₀</small></li>
              <li><span>02</span><strong>Product technology</strong><small>emissions channel and efficiency</small></li>
              <li><span>03</span><strong>Destination use</strong><small>distance, survival, energy system</small></li>
              <li><span>04</span><strong>NDC trajectory</strong><small>sector target first, fallback disclosed</small></li>
              <li><span>05</span><strong>TI result</strong><small>contribution or carbon lock-in</small></li>
            </ol>
          </div>
        </div>
      </section>

      <section className="story-facts" aria-label="Current automotive cohort coverage">
        <div className="story-frame story-fact-grid four">
          <div><strong>{observedUnits.toLocaleString("en-US")}</strong><span>observed 2024 registrations</span></div>
          <div><strong>{cohorts.length}</strong><span>company cohorts on one boundary</span></div>
          <div><strong>{destinations}</strong><span>destination countries mapped</span></div>
          <div><strong>{meta.impact_contract.published_lifetime_results}</strong><span>lifetime results released before evidence gate</span></div>
        </div>
      </section>

      <section className="story-chapter" id="purpose">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>01</b><span>/ why this exists</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>Corporate inventories do not show <em>where sold products lock in emissions.</em></h2>
                <p>
                  Use of sold products can appear in Scope 3 Category 11, but the ordinary company
                  total does not explain which destination inherits the emissions, which national
                  pathway is affected, or whether today&apos;s product remains compatible as that
                  pathway tightens. Trade Impact adds that destination-and-time lens; it never
                  subtracts from Scope 3.
                </p>
              </div>
            </div>
          </header>
          <div className="principle-grid impact-principles">
            <article><span>Company decision</span><h3>What was sold?</h3><p>Observed cohort volume is retained by product, technology, destination, and year.</p></article>
            <article><span>Physical consequence</span><h3>How does it operate?</h3><p>Fuel, electricity, distance, survival, and real-world performance define the use-phase path.</p></article>
            <article><span>Policy consequence</span><h3>What path must the market meet?</h3><p>A destination-sector pathway is preferred; broader regional or economy-wide targets are disclosed fallbacks.</p></article>
          </div>
        </div>
      </section>

      <section className="story-chapter story-chapter-alt" id="pilot">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>02</b><span>/ first implementation</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>Toyota and Hyundai now form a <em>like-for-like destination comparison.</em></h2>
                <p>
                  Official EEA monitoring data resolves both 2024 brand cohorts into
                  {` ${meta.impact_contract.cohort_records.toLocaleString("en-US")} `}
                  destination × commercial-name × powertrain records on the same boundary. This
                  establishes where vehicles entered use and what technology they carry. It does
                  not prove Japanese or Korean export origin.
                </p>
              </div>
              <span className="as-of">EEA final · 2024</span>
            </div>
          </header>
          <div className="pilot-list">
            {cohorts.map((cohort) => (
              <div className="declaration pilot-declaration impact-pilot-card" key={cohort.cohort_id}>
                <div>
                  <span className="status-chip observed">Observed</span>
                  <h3>{cohort.company_name} · EU27 passenger cars</h3>
                  <p className="panel-note">{cohort.coverage.reported_units.toLocaleString("en-US")} registrations · destination → product → use-phase input gate.</p>
                </div>
                <Link className="button secondary" href={`/analysis/${cohort.company_id}`}>Inspect cohort →</Link>
              </div>
            ))}
            <div className="declaration pilot-declaration impact-pilot-card">
              <div><span className="status-chip observed">Comparable boundary</span><h3>Toyota vs Hyundai</h3><p className="panel-note">Sales scale, technology mix, destination exposure, and origin-data caveats.</p></div>
              <Link className="button primary" href="/compare/automotive">Open comparison →</Link>
            </div>
            <div className="readiness-line">
              <strong>Current publication decision</strong>
              <span>Lifetime TI withheld</span>
              <p>{readiness.publication_reason}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="story-chapter" id="sectors">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>03</b><span>/ sector expansion</span></p>
            <div className="chapter-heading-row">
              <div>
                <h2>One question, <em>sector-specific physics.</em></h2>
                <p>
                  Automotive is the first complete data-shape pilot. Power, shipping, steel, and
                  petrochemicals reuse the company × product × destination × cohort contract, but
                  each keeps its own service denominator, use-phase channel, lifetime, and policy
                  pathway. There is no forced cross-sector unit.
                </p>
              </div>
            </div>
          </header>
          <div className="sector-grid">
            {sectors.map((sector) => (
              <article className="sector-card" key={sector.sector_id}>
                <div><span>{sector.sector_id === "automotive" ? "active cohort pilot" : "method expansion"}</span><b>{sector.sector_id}</b></div>
                <h3>{sector.name}</h3>
                <p>{sector.activity_basis}</p>
                <small>Operating boundary · {sector.operating_boundary}</small>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="story-chapter story-chapter-alt" id="method">
        <div className="story-frame story-frame-wide">
          <header className="story-chapter-head">
            <p className="chapter-index"><b>04</b><span>/ calculation and evidence gate</span></p>
            <div className="chapter-heading-row">
              <div><h2>The formula is simple. <em>The evidence burden is not.</em></h2></div>
            </div>
          </header>
          <div className="formula-stack">
            <code>E<sub>ref,c</sub>(t) − E<sub>product,v,c</sub>(t) = annual contribution or lock-in</code>
            <code>Σ<sub>t=0…T−1</sub> annual gap × sold units = cohort TI</code>
            <code>Σ<sub>destination c</sub> = company result, always decomposable back to c and product v</code>
          </div>
          <div className="principle-grid">
            <article><span>Observed</span><h3>Never model what can be measured</h3><p>Sales, product class, destination, and certified performance retain their original source and coverage.</p></article>
            <article><span>Scenario</span><h3>Every assumption is named</h3><p>Lifetime, use, survival, real-world adjustment, and energy pathways require sources and sensitivity ranges.</p></article>
            <article><span>Derived</span><h3>No result before the gate</h3><p>A missing input produces an unavailable result—not zero, not a midpoint, and not an invented history.</p></article>
          </div>
        </div>
      </section>
    </main>
  );
}
