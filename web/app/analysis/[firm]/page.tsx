import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getBenchmarks,
  getCompanyMetrics,
  getFirms,
  getSources,
  type AlignmentBenchmark,
  type CompanyMetric,
} from "@/lib/data";

const POWERTRAIN_LABELS: Record<string, string> = {
  BEV: "Battery electric",
  FCEV: "Fuel-cell electric",
  PHEV: "Plug-in hybrid",
  HEV: "Hybrid",
  ICE_OTHER: "Other combustion",
};

const POWERTRAIN_COLORS: Record<string, string> = {
  BEV: "#5d9cec",
  FCEV: "#9d7bea",
  PHEV: "#36bfa0",
  HEV: "#d9a441",
  ICE_OTHER: "#ef7b5e",
};

export function generateStaticParams() {
  return getFirms()
    .filter((firm) => firm.alignment_available)
    .map((firm) => ({ firm: firm.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ firm: string }>;
}): Promise<Metadata> {
  const { firm: slug } = await params;
  const firm = getFirms().find((row) => row.slug === slug);
  return { title: firm ? `${firm.name} evidence alignment — Trade Impact` : "Analysis" };
}

function metricById(metrics: CompanyMetric[], metricId: string): CompanyMetric {
  const metric = metrics.find((row) => row.metric_id === metricId);
  if (!metric) notFound();
  return metric;
}

function formatCount(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function contextValue(benchmark: AlignmentBenchmark): string {
  if (benchmark.value_min != null && benchmark.value_max != null) {
    if (benchmark.unit === "fraction") {
      return `${(benchmark.value_min * 100).toFixed(0)}–${(benchmark.value_max * 100).toFixed(0)}%`;
    }
    return `${benchmark.value_min}–${benchmark.value_max}${benchmark.unit ? ` ${benchmark.unit}` : ""}`;
  }
  if (benchmark.value != null) {
    if (benchmark.unit === "fraction") return `${(benchmark.value * 100).toFixed(1)}%`;
    if (benchmark.unit === "MtCO2e") return `${benchmark.value.toFixed(1)} MtCO₂e`;
    if (benchmark.unit === "kgCO2/MWh") return `${benchmark.value.toFixed(0)} kgCO₂/MWh`;
    return `${benchmark.value}${benchmark.unit ? ` ${benchmark.unit}` : ""}`;
  }
  return "No numeric value";
}

function JeraAnalysis({ name, metrics }: { name: string; metrics: CompanyMetric[] }) {
  const headlineMetrics = metrics.filter(
    (row) => row.geography === "JP" && row.observation_year === 2024,
  );
  const generation = metricById(headlineMetrics, "net_generation");
  const intensity = metricById(headlineMetrics, "generation_emissions_intensity");
  const benchmarks = getBenchmarks()
    .filter((row) => row.sector === "power" && row.geography === "JP")
    .sort((a, b) => (a.target_year ?? 0) - (b.target_year ?? 0));
  const sourceIds = new Set([
    ...headlineMetrics.flatMap((row) => row.source_ids),
    ...benchmarks.flatMap((row) => row.source_ids),
  ]);
  const sources = getSources().filter((source) => sourceIds.has(source.source_id));
  const coverage = intensity.coverage.mapped_activity / intensity.coverage.reported_activity;

  return (
    <main className="alignment-report">
      <div className="alignment-breadcrumb"><Link href="/">Trade Impact</Link><span>/</span><span>Company analysis</span></div>
      <section className="alignment-hero">
        <div>
          <p className="eyebrow">Power pilot · Japan · FY2024</p>
          <h1>{name} <em>evidence boundary</em></h1>
          <p className="lede">
            Independently assured domestic-group generation and emissions intensity, placed beside
            Japan&apos;s adopted electricity outlook only where the accounting boundaries remain visible.
          </p>
        </div>
        <div className="alignment-badge"><span>Evidence status</span><strong>Independently assured</strong><small>SOCOTEC appendix · limited assurance</small></div>
      </section>

      <div className="alignment-facts" aria-label="Headline power evidence metrics">
        <div><span>Net generation</span><strong>{(generation.value / 1_000_000).toFixed(0)}</strong><small>TWh · sending-end power</small></div>
        <div><span>Generation intensity</span><strong>{intensity.value.toFixed(0)}</strong><small>kgCO₂e/MWh · reported value</small></div>
        <div><span>Evidence coverage</span><strong>{(coverage * 100).toFixed(0)}%</strong><small>of reported generation · independently assured</small></div>
      </div>

      <section className="alignment-section" id="boundary">
        <header><div><p className="eyebrow">01 / comparability gate</p><h2>Connect the evidence, <em>without crossing boundaries</em></h2></div><p>The national outlook is not subtracted from JERA&apos;s company value. The denominator, system boundary, and point in the electricity chain must match before arithmetic is allowed.</p></header>
        <div className="boundary-flow" role="img" aria-label="JERA company observation passes through a comparability gate before Japan national policy context; no direct gap is calculated">
          <article><span>Company observation</span><strong>JERA · domestic group</strong><p>242 TWh net sending-end generation<br />520 kgCO₂e/MWh</p></article>
          <i aria-hidden="true">→</i>
          <article className="gate"><span>Comparability gate</span><strong>Direct comparison blocked</strong><p>Company generation ≠ national delivered electricity or full-system mix</p></article>
          <i aria-hidden="true">→</i>
          <article><span>Policy context</span><strong>Japan · 2030/2040</strong><p>Use-end factor and national generation-mix outlook</p></article>
        </div>
      </section>

      <section className="alignment-section" id="context">
        <header><div><p className="eyebrow">02 / national outlook</p><h2>Policy signals shown as <em>context only</em></h2></div><p>These adopted or government-aligned values describe Japan&apos;s electricity system. A numeric company gap remains unavailable.</p></header>
        <div className="context-grid">
          {benchmarks.map((benchmark) => (
            <article key={benchmark.benchmark_id}>
              <div><span>{benchmark.target_year} · {benchmark.comparison_mode}</span><b>No subtraction</b></div>
              <h3>{benchmark.benchmark_type}</h3>
              <strong>{contextValue(benchmark)}</strong>
              <p>{benchmark.notes}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="alignment-section" id="evidence">
        <header><div><p className="eyebrow">03 / audit trail</p><h2>Company, assurance, and policy <em>sources stay separate</em></h2></div><p>The company webpage supplies the observations; the assurance appendix verifies them; government documents supply national context.</p></header>
        <div className="evidence-grid">
          {sources.map((source) => <article key={source.source_id}><span>{source.evidence_class.replaceAll("_", " ")}</span><h3>{source.title}</h3><p>{source.publisher}</p><a href={source.url}>Open source ↗</a><small>Accessed {source.accessed_date ?? "not recorded"}{source.snapshot_sha256 ? ` · snapshot ${source.snapshot_sha256.slice(0, 12)}…` : ""}</small></article>)}
        </div>
        <div className="method-note"><strong>Published transformations</strong><code>242 billion kWh × 1,000,000 = 242,000,000 MWh</code><code>0.520 kgCO₂e/kWh × 1,000 = 520 kgCO₂e/MWh</code><p>The reported rounded intensity is unit-converted, not recomputed from a different emissions total. Fuel mix and company target distance stay missing because matching assured data is not disclosed.</p></div>
      </section>
    </main>
  );
}

function KoenAnalysis({ name, metrics }: { name: string; metrics: CompanyMetric[] }) {
  const headlineMetrics = metrics.filter(
    (row) => row.geography === "KR" && row.observation_year === 2024,
  );
  const generation = metricById(headlineMetrics, "reported_generation");
  const scope1 = metricById(headlineMetrics, "scope1_emissions");
  const scope2 = metricById(headlineMetrics, "scope2_emissions");
  const benchmarks = getBenchmarks()
    .filter((row) => row.sector === "power" && row.geography === "KR")
    .sort((a, b) => (a.target_year ?? 0) - (b.target_year ?? 0));
  const sourceIds = new Set([
    ...headlineMetrics.flatMap((row) => row.source_ids),
    ...benchmarks.flatMap((row) => row.source_ids),
  ]);
  const sources = getSources().filter((source) => sourceIds.has(source.source_id));

  return (
    <main className="alignment-report">
      <div className="alignment-breadcrumb"><Link href="/">Trade Impact</Link><span>/</span><span>Company analysis</span></div>
      <section className="alignment-hero">
        <div>
          <p className="eyebrow">Power pilot · Republic of Korea · 2024</p>
          <h1>{name} <em>evidence boundary</em></h1>
          <p className="lede">
            Company-reported generation and Scope 1/2 totals, placed beside Korea&apos;s adopted
            electricity plan. Missing generation-basis and reconciliation evidence remain visible,
            so no emissions intensity or company target gap is inferred.
          </p>
        </div>
        <div className="alignment-badge caution"><span>Evidence status</span><strong>Company reported</strong><small>Independent assurance not identified for this web table</small></div>
      </section>

      <div className="alignment-facts" aria-label="Headline KOEN evidence metrics">
        <div><span>Reported generation</span><strong>{(generation.value / 1_000_000).toFixed(2)}</strong><small>TWh · gross/net basis not stated</small></div>
        <div><span>Reported Scope 1</span><strong>{(scope1.value / 1_000_000).toFixed(3)}</strong><small>MtCO₂e · reported total retained</small></div>
        <div><span>Reported Scope 2</span><strong>{(scope2.value / 1_000_000).toFixed(3)}</strong><small>MtCO₂e · reported total retained</small></div>
      </div>

      <section className="alignment-section" id="boundary">
        <header><div><p className="eyebrow">01 / comparability gate</p><h2>Keep the reported facts, <em>block the unsupported ratio</em></h2></div><p>The company values and national plan describe different entities and metrics. Direct arithmetic remains unavailable until KOEN discloses a compatible generation basis and company-level policy metric.</p></header>
        <div className="boundary-flow" role="img" aria-label="KOEN reported observations pass through a data quality and comparability gate before Korean national policy context; intensity and target gap are not calculated">
          <article><span>Company observation</span><strong>KOEN · reported 2024</strong><p>39.66 TWh generation<br />30.607 MtCO₂e Scope 1</p></article>
          <i aria-hidden="true">→</i>
          <article className="gate"><span>Evidence gate</span><strong>Derived intensity blocked</strong><p>Gross/net basis unstated · displayed rows do not reconcile to reported totals</p></article>
          <i aria-hidden="true">→</i>
          <article><span>Policy context</span><strong>Korea · 2030/2038</strong><p>National transition-sector emissions and carbon-free generation outlook</p></article>
        </div>
      </section>

      <section className="alignment-section" id="quality">
        <header><div><p className="eyebrow">02 / data quality</p><h2>The inconsistencies are <em>part of the result</em></h2></div><p>Reported totals are retained as observations. Plant rows are used only as a reconciliation check and are never silently substituted.</p></header>
        <div className="quality-grid">
          <article><span>Generation denominator</span><strong>Not stated</strong><p>KOEN reports 39,660 GWh, but the source page does not identify it as gross or net generation.</p></article>
          <article><span>Scope 1 row check</span><strong>−2,000 tCO₂e</strong><p>Reported total minus the sum of headquarters and five displayed plant rows.</p></article>
          <article><span>Scope 2 row check</span><strong>−269 tCO₂e</strong><p>Reported total minus the sum of headquarters and five displayed plant rows.</p></article>
        </div>
      </section>

      <section className="alignment-section" id="context">
        <header><div><p className="eyebrow">03 / national outlook</p><h2>Official targets shown as <em>context only</em></h2></div><p>The Eleventh Electricity Plan describes Korea&apos;s national power system. It is not allocated to KOEN, and no numeric company gap is calculated.</p></header>
        <div className="context-grid">
          {benchmarks.map((benchmark) => (
            <article key={benchmark.benchmark_id}>
              <div><span>{benchmark.target_year} · {benchmark.comparison_mode}</span><b>No subtraction</b></div>
              <h3>{benchmark.benchmark_type}</h3>
              <strong>{contextValue(benchmark)}</strong>
              <p>{benchmark.notes}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="alignment-section" id="evidence">
        <header><div><p className="eyebrow">04 / audit trail</p><h2>Company facts and government policy <em>stay separate</em></h2></div><p>KOEN supplies the company observations. The ministry&apos;s adopted plan supplies only the national transition context.</p></header>
        <div className="evidence-grid">
          {sources.map((source) => <article key={source.source_id}><span>{source.evidence_class.replaceAll("_", " ")}</span><h3>{source.title}</h3><p>{source.publisher}</p><a href={source.url}>Open primary source ↗</a><small>Accessed {source.accessed_date ?? "not recorded"}{source.snapshot_sha256 ? ` · snapshot ${source.snapshot_sha256.slice(0, 12)}…` : ""}</small></article>)}
        </div>
        <div className="method-note"><strong>Published transformations</strong><code>39,660 GWh × 1,000 = 39,660,000 MWh</code><code>Scope 1 and Scope 2 = KOEN reported totals; plant rows are reconciliation checks</code><code>generation_emissions_intensity = not_available</code><p>{generation.derivation}. A ratio is not published because its denominator boundary cannot be verified; national targets remain contextual because no company allocation is disclosed.</p></div>
      </section>
    </main>
  );
}

function MolAnalysis({ name, metrics }: { name: string; metrics: CompanyMetric[] }) {
  const headlineMetrics = metrics.filter(
    (row) => row.geography === "GLOBAL" && row.observation_year === 2024,
  );
  const eeoi = metricById(headlineMetrics, "shipping_eeoi");
  const benchmarks = getBenchmarks()
    .filter((row) => row.sector === "shipping" && row.geography === "GLOBAL")
    .sort((a, b) => a.benchmark_id.localeCompare(b.benchmark_id));
  const sourceIds = new Set([
    ...headlineMetrics.flatMap((row) => row.source_ids),
    ...benchmarks.flatMap((row) => row.source_ids),
  ]);
  const sources = getSources().filter((source) => sourceIds.has(source.source_id));

  return (
    <main className="alignment-report">
      <div className="alignment-breadcrumb"><Link href="/">Trade Impact</Link><span>/</span><span>Company analysis</span></div>
      <section className="alignment-hero">
        <div>
          <p className="eyebrow">Shipping pilot · International voyages · FY2024</p>
          <h1>{name} <em>transport-work boundary</em></h1>
          <p className="lede">
            One independently assured lifecycle-GHG EEOI observation for MOL&apos;s global
            operating fleet, placed beside the adopted IMO 2030 strategy without turning
            incompatible baselines into a company score.
          </p>
        </div>
        <div className="alignment-badge"><span>Evidence status</span><strong>Independently assured</strong><small>ClassNK · 783 applicable vessels</small></div>
      </section>

      <div className="alignment-facts" aria-label="Headline MOL shipping evidence metrics">
        <div><span>FY2024 EEOI</span><strong>{eeoi.value.toFixed(2)}</strong><small>gCO₂e/ton-mile · lifecycle GHG</small></div>
        <div><span>Applicable fleet</span><strong>{formatCount(eeoi.coverage.reported_activity)}</strong><small>vessels · Japan and overseas</small></div>
        <div><span>Assurance sample</span><strong>≥392</strong><small>vessels · at least 50% of lifecycle GHG</small></div>
      </div>

      <section className="alignment-section" id="boundary">
        <header><div><p className="eyebrow">01 / jurisdiction and metric gate</p><h2>International voyages, <em>not a flag-state shortcut</em></h2></div><p>Shipping activity is governed through voyage and IMO boundaries. MOL&apos;s headquarters country is not used as a proxy for where its vessels operate.</p></header>
        <div className="boundary-flow" role="img" aria-label="MOL lifecycle EEOI passes through a comparability gate before global IMO strategy context; no direct target gap is calculated">
          <article><span>Company observation</span><strong>MOL · FY2024</strong><p>10.95 gCO₂e/ton-mile<br />WtW lifecycle GHG · standard method</p></article>
          <i aria-hidden="true">→</i>
          <article className="gate"><span>Comparability gate</span><strong>Direct subtraction blocked</strong><p>FY2019 company method ≠ 2008 international-shipping average CO₂ baseline</p></article>
          <i aria-hidden="true">→</i>
          <article><span>Policy context</span><strong>IMO · 2030</strong><p>International carbon intensity, absolute GHG, and zero-energy ambitions</p></article>
        </div>
      </section>

      <section className="alignment-section" id="quality">
        <header><div><p className="eyebrow">02 / metric anatomy</p><h2>What the assured number <em>does and does not mean</em></h2></div><p>The platform preserves MOL&apos;s disclosed unit and method. It does not relabel ton-mile as tonne-nautical-mile or use the value for a customer shipment.</p></header>
        <div className="quality-grid">
          <article><span>Emissions boundary</span><strong>Well-to-Wake</strong><p>Lifecycle fuel GHG under IMO 2024 LCA guidance and FuelEU factors where applicable.</p></article>
          <article><span>Aggregation</span><strong>Standard method</strong><p>FY2019 segment changes are weighted by FY2024 segment energy use; this is not a simple company-total ratio.</p></article>
          <article><span>Use restriction</span><strong>No customer attribution</strong><p>The disclosed value reflects selected low-emission transport allocation and is not suitable for customer-specific GHG calculations.</p></article>
        </div>
      </section>

      <section className="alignment-section" id="context">
        <header><div><p className="eyebrow">03 / international outlook</p><h2>IMO ambitions shown as <em>context only</em></h2></div><p>These values describe international shipping as a whole. No MOL alignment margin is published without a matching 2008 company baseline and metric definition.</p></header>
        <div className="context-grid">
          {benchmarks.map((benchmark) => (
            <article key={benchmark.benchmark_id}>
              <div><span>{benchmark.target_year} · {benchmark.comparison_mode}</span><b>No subtraction</b></div>
              <h3>{benchmark.benchmark_type}</h3>
              <strong>{contextValue(benchmark)}</strong>
              <p>{benchmark.notes}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="alignment-section" id="evidence">
        <header><div><p className="eyebrow">04 / audit trail</p><h2>Company disclosure, assurance, and policy <em>stay separate</em></h2></div><p>MOL reports the value; ClassNK verifies the dataset, fleet, and method; IMO supplies only the international policy context.</p></header>
        <div className="evidence-grid">
          {sources.map((source) => <article key={source.source_id}><span>{source.evidence_class.replaceAll("_", " ")}</span><h3>{source.title}</h3><p>{source.publisher}</p><a href={source.url}>Open primary source ↗</a><small>Accessed {source.accessed_date ?? "not recorded"}{source.snapshot_sha256 ? ` · snapshot ${source.snapshot_sha256.slice(0, 12)}…` : ""}</small></article>)}
        </div>
        <div className="method-note"><strong>Assured method, not a project estimate</strong><code>Segment EEOI = Σ lifecycle GHG ÷ Σ(distance sailed × cargo tonnes)</code><code>FY2024 company EEOI = 10.95 gCO₂e/ton-mile · reported and assured</code><code>IMO company alignment margin = not_available</code><p>{eeoi.derivation}. Only the FY2024 observation is published; the source&apos;s historical values are not reconstructed into a company trend.</p></div>
      </section>
    </main>
  );
}

export default async function CompanyAnalysis({
  params,
}: {
  params: Promise<{ firm: string }>;
}) {
  const { firm: slug } = await params;
  const firm = getFirms().find((row) => row.slug === slug && row.alignment_available);
  if (!firm) notFound();

  const allMetrics = getCompanyMetrics().filter((row) => row.company_id === slug);
  if (slug === "jera") return <JeraAnalysis name={firm.name} metrics={allMetrics} />;
  if (slug === "koen") return <KoenAnalysis name={firm.name} metrics={allMetrics} />;
  if (slug === "mitsui") return <MolAnalysis name={firm.name} metrics={allMetrics} />;
  const headlineMetrics = allMetrics.filter(
    (row) => row.geography === "EU27" && row.observation_year === 2024,
  );
  if (!headlineMetrics.length) notFound();

  const registrations = metricById(headlineMetrics, "new_vehicle_registrations");
  const intensity = metricById(headlineMetrics, "new_vehicle_tailpipe_intensity");
  const powertrains = headlineMetrics
    .filter((row) => row.metric_id === "powertrain_sales_share")
    .sort((a, b) => b.value - a.value);
  const benchmarks = getBenchmarks()
    .filter(
      (row) =>
        row.sector === "automotive" &&
        row.geography === "EU27" &&
        row.metric_id === "new_vehicle_tailpipe_intensity",
    )
    .sort((a, b) => (a.target_year ?? 0) - (b.target_year ?? 0));
  const sources = getSources().filter((source) =>
    new Set([...intensity.source_ids, ...benchmarks.flatMap((row) => row.source_ids)]).has(
      source.source_id,
    ),
  );
  const countries = allMetrics
    .filter((row) => row.metric_id === "new_vehicle_registrations" && row.geography !== "EU27")
    .map((registration) => ({
      code: registration.geography,
      registrations: registration.value,
      intensity: allMetrics.find(
        (row) =>
          row.geography === registration.geography &&
          row.metric_id === "new_vehicle_tailpipe_intensity",
      )?.value,
    }))
    .sort((a, b) => b.registrations - a.registrations);
  const coverage = intensity.coverage.mapped_activity / intensity.coverage.reported_activity;
  const chartMax = Math.max(intensity.value, ...benchmarks.map((row) => row.value ?? 0)) * 1.08;

  return (
    <main className="alignment-report">
      <div className="alignment-breadcrumb"><Link href="/">Trade Impact</Link><span>/</span><span>Company analysis</span></div>
      <section className="alignment-hero">
        <div>
          <p className="eyebrow">Automotive pilot · European Union · 2024</p>
          <h1>{firm.name} <em>market alignment</em></h1>
          <p className="lede">
            Toyota-brand new passenger-car registrations in the EU27, compared with the adopted
            EU-wide new-car fleet CO₂ pathway on a matching WLTP gCO₂/km basis.
          </p>
        </div>
        <div className="alignment-badge"><span>Evidence status</span><strong>Source-backed</strong><small>EEA final monitoring dataset</small></div>
      </section>

      <div className="alignment-facts" aria-label="Headline evidence metrics">
        <div><span>Observed activity</span><strong>{formatCount(registrations.value)}</strong><small>new passenger-car registrations</small></div>
        <div><span>Certified intensity</span><strong>{intensity.value.toFixed(1)}</strong><small>gCO₂/km · WLTP weighted average</small></div>
        <div><span>Mapping coverage</span><strong>{(coverage * 100).toFixed(2)}%</strong><small>{formatCount(intensity.coverage.unmatched_records)} registrations lack WLTP</small></div>
      </div>

      <section className="alignment-section" id="pathway">
        <header><div><p className="eyebrow">01 / target distance</p><h2>Observed portfolio versus <em>adopted EU pathway</em></h2></div><p>Positive or negative distance is analytical context. It is not Toyota&apos;s manufacturer-specific legal compliance calculation.</p></header>
        <div className="target-panel">
          <div className="target-chart" role="img" aria-label="Toyota 2024 WLTP average of 107.1 grams CO2 per kilometre compared with EU targets of 93.6 in 2025 and 49.5 in 2030">
            <div className="target-row current"><span>2024 Toyota snapshot</span><div><i style={{ width: `${(intensity.value / chartMax) * 100}%` }} /></div><strong>{intensity.value.toFixed(1)}</strong></div>
            {benchmarks.map((benchmark) => (
              <div className="target-row" key={benchmark.benchmark_id}>
                <span>{benchmark.target_year} EU fleet target</span>
                <div><i style={{ width: `${((benchmark.value ?? 0) / chartMax) * 100}%` }} /></div>
                <strong>{benchmark.value?.toFixed(1)}</strong>
              </div>
            ))}
            <div className="target-axis"><span>0</span><span>gCO₂/km · lower is better</span><span>{Math.ceil(chartMax)}</span></div>
          </div>
          <div className="distance-cards">
            {benchmarks.map((benchmark) => {
              const distance = intensity.value - (benchmark.value ?? 0);
              return <article key={benchmark.benchmark_id}><span>Distance to {benchmark.target_year}</span><strong>{distance.toFixed(1)} <small>gCO₂/km above</small></strong><p>{benchmark.authority_status}; EU-wide fleet pathway, not a company compliance verdict.</p></article>;
            })}
          </div>
        </div>
      </section>

      <section className="alignment-section" id="mix">
        <header><div><p className="eyebrow">02 / observed composition</p><h2>Powertrain mix, <em>without an inferred fleet</em></h2></div><p>Shares reconcile to all 803,094 registrations. Categories follow the disclosed EEA fuel-mode adapter.</p></header>
        <div className="mix-panel">
          <div className="mix-bar" aria-label="Powertrain registration shares">
            {powertrains.map((row) => <span key={row.scope.powertrain} style={{ width: `${row.value * 100}%`, background: POWERTRAIN_COLORS[row.scope.powertrain] }} title={`${POWERTRAIN_LABELS[row.scope.powertrain]} ${(row.value * 100).toFixed(2)}%`} />)}
          </div>
          <div className="mix-legend">
            {powertrains.map((row) => <div key={row.scope.powertrain}><i style={{ background: POWERTRAIN_COLORS[row.scope.powertrain] }} /><span>{POWERTRAIN_LABELS[row.scope.powertrain]}</span><strong>{(row.value * 100).toFixed(2)}%</strong></div>)}
          </div>
        </div>
      </section>

      <section className="alignment-section" id="countries">
        <header><div><p className="eyebrow">03 / operating markets</p><h2>Where the registrations <em>actually occurred</em></h2></div><p>Country records preserve exposure for later national-target mapping. No national company gap is calculated until a compatible country benchmark is sourced.</p></header>
        <div className="exposure-table-wrap">
          <table className="exposure-table"><thead><tr><th>Market</th><th>Registrations</th><th>Share of EU27</th><th>WLTP gCO₂/km</th><th>Direct target</th></tr></thead><tbody>
            {countries.map((country) => <tr key={country.code}><td><strong>{country.code}</strong></td><td>{formatCount(country.registrations)}</td><td><div className="exposure-share"><i style={{ width: `${(country.registrations / registrations.value) * 100 * 4}%` }} /><span>{((country.registrations / registrations.value) * 100).toFixed(1)}%</span></div></td><td>{country.intensity?.toFixed(1) ?? "—"}</td><td><span className="pending-target">Pending comparable source</span></td></tr>)}
          </tbody></table>
        </div>
      </section>

      <section className="alignment-section" id="evidence">
        <header><div><p className="eyebrow">04 / audit trail</p><h2>Every number has <em>a traceable origin</em></h2></div></header>
        <div className="evidence-grid">
          {sources.map((source) => <article key={source.source_id}><span>{source.evidence_class.replaceAll("_", " ")}</span><h3>{source.title}</h3><p>{source.publisher}</p><a href={source.url}>Open primary source ↗</a><small>Accessed {source.accessed_date ?? "not recorded"}{source.snapshot_sha256 ? ` · snapshot ${source.snapshot_sha256.slice(0, 12)}…` : ""}</small></article>)}
        </div>
        <div className="method-note"><strong>Calculation</strong><code>Σ(registrations × WLTP gCO₂/km) ÷ Σ(mapped registrations)</code><p>{intensity.derivation}. The raw-to-aggregate query and response hashes are committed; individual registration rows are not republished.</p></div>
      </section>
    </main>
  );
}
