import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getDestinationPathways,
  getFirms,
  getImpactReadiness,
  getProductCohorts,
  getSources,
  type ProductCohortRecord,
} from "@/lib/data";

const POWERTRAIN_LABELS: Record<string, string> = {
  BEV: "Battery electric",
  FCEV: "Fuel-cell electric",
  PHEV: "Plug-in hybrid",
  HEV: "Non-plug-in hybrid",
  ICE_OTHER: "Other combustion",
};

const POWERTRAIN_COLORS: Record<string, string> = {
  BEV: "#5d9cec",
  FCEV: "#9d7bea",
  PHEV: "#36bfa0",
  HEV: "#d9a441",
  ICE_OTHER: "#ef7b5e",
};

type CountrySummary = {
  code: string;
  units: number;
  zevUnits: number;
  combustionDependentUnits: number;
  tailpipeMappedUnits: number;
  tailpipeNumerator: number;
};

type ModelSummary = {
  name: string;
  units: number;
  types: Set<string>;
};

export function generateStaticParams() {
  return [{ firm: "toyota" }, { firm: "hyundai" }];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ firm: string }>;
}): Promise<Metadata> {
  const { firm } = await params;
  const companyName = firm === "toyota" ? "Toyota" : firm === "hyundai" ? "Hyundai" : null;
  return {
    title: companyName
      ? `${companyName} 2024 destination cohort — Trade Impact`
      : "Trade Impact analysis",
  };
}

function formatCount(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function pct(numerator: number, denominator: number, digits = 2): string {
  return `${((numerator / denominator) * 100).toFixed(digits)}%`;
}

function aggregateCountries(records: ProductCohortRecord[]): CountrySummary[] {
  const byCountry = new Map<string, CountrySummary>();
  for (const record of records) {
    const current = byCountry.get(record.destination_geography) ?? {
      code: record.destination_geography,
      units: 0,
      zevUnits: 0,
      combustionDependentUnits: 0,
      tailpipeMappedUnits: 0,
      tailpipeNumerator: 0,
    };
    current.units += record.units;
    if (record.product_type === "BEV" || record.product_type === "FCEV") {
      current.zevUnits += record.units;
    } else {
      current.combustionDependentUnits += record.units;
    }
    if (record.certified_tailpipe_gco2_per_km != null) {
      current.tailpipeMappedUnits += record.tailpipe_mapped_units;
      current.tailpipeNumerator +=
        record.certified_tailpipe_gco2_per_km * record.tailpipe_mapped_units;
    }
    byCountry.set(record.destination_geography, current);
  }
  return [...byCountry.values()].sort((a, b) => b.units - a.units);
}

function aggregateModels(records: ProductCohortRecord[]): ModelSummary[] {
  const byModel = new Map<string, ModelSummary>();
  for (const record of records) {
    const current = byModel.get(record.product_name) ?? {
      name: record.product_name,
      units: 0,
      types: new Set<string>(),
    };
    current.units += record.units;
    current.types.add(record.product_type);
    byModel.set(record.product_name, current);
  }
  return [...byModel.values()].sort((a, b) => b.units - a.units);
}

export default async function CompanyAnalysis({
  params,
}: {
  params: Promise<{ firm: string }>;
}) {
  const { firm: slug } = await params;
  if (slug !== "toyota" && slug !== "hyundai") notFound();

  const firm = getFirms().find((row) => row.slug === slug);
  const cohort = getProductCohorts().find((row) => row.company_id === slug);
  if (!firm || !cohort) notFound();

  const readiness = getImpactReadiness().find(
    (row) => row.cohort_id === cohort.cohort_id,
  );
  if (!readiness) notFound();

  const pathways = getDestinationPathways();
  const sectorPathway = pathways.find((row) => row.comparison_role === "sector_proxy");
  const ndcPathway = pathways.find((row) => row.comparison_role === "fallback_context");
  if (!sectorPathway || !ndcPathway) notFound();

  const total = cohort.coverage.reported_units;
  const countries = aggregateCountries(cohort.records);
  const models = aggregateModels(cohort.records);
  const typeUnits = Object.fromEntries(
    Object.keys(POWERTRAIN_LABELS).map((type) => [
      type,
      cohort.records
        .filter((record) => record.product_type === type)
        .reduce((sum, record) => sum + record.units, 0),
    ]),
  );
  const zeroTailpipeUnits = typeUnits.BEV + typeUnits.FCEV;
  const combustionDependentUnits = total - zeroTailpipeUnits;
  const [dominantType, dominantUnits] = Object.entries(typeUnits).sort(
    (a, b) => b[1] - a[1],
  )[0];
  const topCountry = countries[0];
  const topModels = models.slice(0, 10);
  const sourceIds = new Set([
    ...cohort.source_ids,
    ...(cohort.origin_context?.source_ids ?? []),
    ...pathways.flatMap((pathway) => pathway.source_ids),
  ]);
  const sources = getSources().filter((source) => sourceIds.has(source.source_id));

  return (
    <main className="alignment-report cohort-report">
      <div className="alignment-breadcrumb">
        <Link href="/">Trade Impact</Link><span>/</span><span>Destination cohort</span>
      </div>

      <section className="alignment-hero cohort-hero">
        <div>
          <p className="eyebrow">Automotive pilot · 2024 sales cohort · 27 destinations</p>
          <h1>{cohort.company_name} <em>sold-product destination exposure</em></h1>
          <p className="lede">
            This analysis starts with the vehicles that entered use in each EU country, classifies
            their technology, and prepares the evidence chain needed to estimate how their
            use-phase emissions will support or obstruct destination climate pathways over time.
          </p>
          <p className="boundary-warning">
            Destination is observed; export origin is not. EEA first registrations do not prove
            where a vehicle was manufactured or that it crossed a border.
          </p>
        </div>
        <div className="alignment-badge caution">
          <span>Lifetime TI status</span>
          <strong>Withheld</strong>
          <small>{readiness.missing_required_inputs.length} required input groups remain</small>
        </div>
      </section>

      <div className="alignment-facts" aria-label={`${cohort.company_name} cohort facts`}>
        <div><span>Observed cohort</span><strong>{formatCount(total)}</strong><small>destination registrations</small></div>
        <div><span>Product resolution</span><strong>{models.length}</strong><small>commercial names · {cohort.records.length} evidence rows</small></div>
        <div><span>Zero-tailpipe share</span><strong>{pct(zeroTailpipeUnits, total)}</strong><small>BEV + FCEV · descriptive, not lifecycle zero</small></div>
      </div>

      <section className="alignment-section" id="logic">
        <header>
          <div><p className="eyebrow">01 / analytical logic</p><h2>From one sale to a <em>multi-year NDC consequence</em></h2></div>
          <p>The framework keeps company action, physical operation, and destination policy as separate evidence layers.</p>
        </header>
        <div className="cohort-flow" role="img" aria-label="Observed sales cohort passes through product classification, destination use, lifetime emissions and NDC comparison">
          <article className="done"><span>Observed</span><strong>Company cohort</strong><p>{formatCount(total)} {cohort.company_name}-brand registrations in 2024</p></article>
          <i>→</i>
          <article className="done"><span>Observed</span><strong>Product × destination</strong><p>{models.length} names · {countries.length} markets · 5 powertrain groups</p></article>
          <i>→</i>
          <article className="pending"><span>Inputs incomplete</span><strong>Lifetime use path</strong><p>distance × survival × real-world product emissions</p></article>
          <i>→</i>
          <article className="pending"><span>Proxy only</span><strong>Destination pathway</strong><p>country sector target → regional sector proxy → NDC fallback</p></article>
        </div>
        <div className="formula-stack compact">
          <code>Annual TI<sub>v,c</sub>(t) = destination benchmark<sub>c</sub>(t) − product emissions<sub>v,c</sub>(t)</code>
          <code>Cohort TI = Σ<sub>country c</sub> Σ<sub>product v</sub> sold units<sub>c,v</sub> × Σ<sub>life t</sub> Annual TI<sub>v,c</sub>(t)</code>
        </div>
      </section>

      <section className="alignment-section" id="portfolio">
        <header>
          <div><p className="eyebrow">02 / portfolio capability</p><h2>Technology mix shows <em>what kind of emissions are locked in</em></h2></div>
          <p>A powertrain label is not a climate score. It determines which physical and policy inputs the lifetime model must use.</p>
        </header>
        <div className="mix-panel">
          <div className="mix-bar" aria-label="Powertrain registration shares">
            {Object.entries(typeUnits).map(([type, units]) => (
              <span key={type} style={{ width: `${(units / total) * 100}%`, background: POWERTRAIN_COLORS[type] }} title={`${POWERTRAIN_LABELS[type]} ${pct(units, total)}`} />
            ))}
          </div>
          <div className="mix-legend">
            {Object.entries(typeUnits).sort((a, b) => b[1] - a[1]).map(([type, units]) => (
              <div key={type}><i style={{ background: POWERTRAIN_COLORS[type] }} /><span>{POWERTRAIN_LABELS[type]}</span><strong>{pct(units, total)}</strong></div>
            ))}
          </div>
        </div>
        <div className="capability-grid">
          <article><span>Zero tailpipe</span><strong>{formatCount(zeroTailpipeUnits)}</strong><p>{pct(zeroTailpipeUnits, total)} BEV + FCEV. Electricity or hydrogen supply emissions still belong in the use-phase model.</p></article>
          <article><span>Combustion-dependent</span><strong>{formatCount(combustionDependentUnits)}</strong><p>{pct(combustionDependentUnits, total)} PHEV + HEV + other combustion. Hybrid is not classified as zero-emission.</p></article>
          <article><span>Dominant technology</span><strong>{dominantType} · {pct(dominantUnits, total)}</strong><p>The dominant powertrain determines the main use-phase emissions channel and the inputs required for a defensible lifetime comparison.</p></article>
        </div>
      </section>

      <section className="alignment-section" id="destinations">
        <header>
          <div><p className="eyebrow">03 / destination exposure</p><h2>Where the 2024 cohort will <em>enter national inventories</em></h2></div>
          <p>This ranking is sales exposure, not estimated greenhouse gas. Emissions ranking stays withheld until country-use inputs are sourced.</p>
        </header>
        <div className="destination-summary">
          <div className="impact-ranking" role="img" aria-label={`Top destination shares of ${cohort.company_name} registrations`}>
            <div className="impact-ranking-head"><span>Top destinations</span><span>Share of observed cohort</span></div>
            {countries.slice(0, 7).map((country) => (
              <div className="impact-row" key={country.code}>
                <strong>{country.code}</strong>
                <div><i style={{ width: `${(country.units / topCountry.units) * 100}%` }} /></div>
                <span>{pct(country.units, total)}</span>
              </div>
            ))}
          </div>
          <div className="target-hierarchy">
            <article><span>Preferred</span><strong>Country passenger-car / road pathway</strong><p>Not yet collected for the 27 destinations.</p></article>
            <article><span>Available proxy</span><strong>EU domestic transport · 2030</strong><p>{sectorPathway.annual_reduction_rate ? `${(sectorPathway.annual_reduction_rate * 100).toFixed(2)}% annual decline` : "—"}; all domestic transport, not passenger cars alone.</p></article>
            <article><span>Fallback context</span><strong>EU collective NDC · 2035</strong><p>{ndcPathway.reduction_min != null && ndcPathway.reduction_max != null ? `${(ndcPathway.reduction_min * 100).toFixed(2)}–${(ndcPathway.reduction_max * 100).toFixed(1)}% net reduction vs 1990` : "—"}</p></article>
          </div>
        </div>
        <div className="exposure-table-wrap">
          <table className="exposure-table">
            <thead><tr><th>Destination</th><th>Registrations</th><th>Cohort share</th><th>Zero-tailpipe</th><th>Combustion-dependent</th><th>Certified WLTP</th><th>Lifetime TI</th></tr></thead>
            <tbody>
              {countries.map((country) => {
                const intensity = country.tailpipeMappedUnits
                  ? country.tailpipeNumerator / country.tailpipeMappedUnits
                  : null;
                return (
                  <tr key={country.code}>
                    <td><strong>{country.code}</strong></td>
                    <td>{formatCount(country.units)}</td>
                    <td>{pct(country.units, total)}</td>
                    <td>{pct(country.zevUnits, country.units)}</td>
                    <td>{pct(country.combustionDependentUnits, country.units)}</td>
                    <td>{intensity?.toFixed(1) ?? "—"} gCO₂/km</td>
                    <td><span className="pending-target">Inputs incomplete</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="alignment-section" id="products">
        <header>
          <div><p className="eyebrow">04 / product evidence</p><h2>Commercial names are now visible, <em>not inferred from a brand average</em></h2></div>
          <p>EEA commercial-name strings are preserved as reported. They still require model-family normalization before model-to-factory export mapping.</p>
        </header>
        <div className="exposure-table-wrap">
          <table className="exposure-table product-table">
            <thead><tr><th>Commercial name</th><th>Registrations</th><th>Cohort share</th><th>Observed powertrains</th></tr></thead>
            <tbody>
              {topModels.map((model) => (
                <tr key={model.name}>
                  <td><strong>{model.name}</strong></td>
                  <td>{formatCount(model.units)}</td>
                  <td>{pct(model.units, total)}</td>
                  <td>{[...model.types].sort().map((type) => POWERTRAIN_LABELS[type]).join(" · ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="table-footnote">Top 10 of {models.length} observed commercial names. Full records remain available through the published JSON and MCP.</p>
      </section>

      <section className="alignment-section" id="gate">
        <header>
          <div><p className="eyebrow">05 / calculation gate</p><h2>What is known, and <em>what must be sourced next</em></h2></div>
          <p>The project exposes readiness before it exposes a headline result.</p>
        </header>
        <div className="readiness-grid">
          <article className="ready-inputs"><span>Observed and published</span><ul>{readiness.observed_inputs.map((item) => <li key={item}>{item}</li>)}</ul></article>
          <article className="missing-inputs"><span>Required before lifetime TI</span><ul>{readiness.missing_required_inputs.map((item) => <li key={item}>{item}</li>)}</ul></article>
        </div>
        <div className="publication-decision">
          <div><span>Publication decision</span><strong>No lifetime emissions or TI score yet</strong></div>
          <p>{readiness.publication_reason}</p>
        </div>
      </section>

      <section className="alignment-section" id="evidence">
        <header>
          <div><p className="eyebrow">06 / evidence trail</p><h2>Observed activity, policy proxy, and NDC <em>stay distinguishable</em></h2></div>
        </header>
        <div className="evidence-grid">
          {sources.map((source) => (
            <article key={source.source_id}>
              <span>{source.evidence_class.replaceAll("_", " ")}</span>
              <h3>{source.title}</h3>
              <p>{source.publisher}</p>
              <a href={source.url}>Open source ↗</a>
              <small>Accessed {source.accessed_date ?? "not recorded"}{source.snapshot_sha256 ? ` · snapshot ${source.snapshot_sha256.slice(0, 12)}…` : ""}</small>
            </article>
          ))}
        </div>
        <div className="method-note">
          <strong>Current derivations</strong>
          <code>Powertrain share = classified registrations ÷ all cohort registrations</code>
          <code>Country WLTP = Σ(mapped registrations × certified gCO₂/km) ÷ mapped registrations</code>
          <code>Lifetime TI = not published while readiness.status = inputs_incomplete</code>
          <p>{cohort.origin_mapping_note}</p>
          {cohort.origin_context ? <p><strong>Company-reported production context:</strong> {cohort.origin_context.notes}</p> : null}
        </div>
      </section>
    </main>
  );
}
