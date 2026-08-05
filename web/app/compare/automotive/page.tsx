import type { Metadata } from "next";
import Link from "next/link";
import {
  getImpactReadiness,
  getProductCohorts,
  getSources,
  type ProductCohort,
} from "@/lib/data";

export const metadata: Metadata = {
  title: "Toyota vs Hyundai EU27 cohort — Trade Impact",
  description:
    "A like-for-like comparison of Toyota and Hyundai 2024 EU27 passenger-car destination cohorts.",
};

const TYPES = ["BEV", "FCEV", "PHEV", "HEV", "ICE_OTHER"] as const;
const LABELS: Record<string, string> = {
  BEV: "Battery electric",
  FCEV: "Fuel-cell electric",
  PHEV: "Plug-in hybrid",
  HEV: "Non-plug-in hybrid",
  ICE_OTHER: "Other combustion",
};
const COLORS: Record<string, string> = {
  BEV: "#5d9cec",
  FCEV: "#9d7bea",
  PHEV: "#36bfa0",
  HEV: "#d9a441",
  ICE_OTHER: "#ef7b5e",
};

function count(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function percent(value: number, total: number, digits = 2): string {
  return `${((value / total) * 100).toFixed(digits)}%`;
}

function summarize(cohort: ProductCohort) {
  const byType = Object.fromEntries(
    TYPES.map((type) => [
      type,
      cohort.records
        .filter((row) => row.product_type === type)
        .reduce((sum, row) => sum + row.units, 0),
    ]),
  );
  const byCountry = new Map<string, number>();
  const byModel = new Map<string, number>();
  for (const row of cohort.records) {
    byCountry.set(
      row.destination_geography,
      (byCountry.get(row.destination_geography) ?? 0) + row.units,
    );
    byModel.set(row.product_name, (byModel.get(row.product_name) ?? 0) + row.units);
  }
  const total = cohort.coverage.reported_units;
  const zeroTailpipe = byType.BEV + byType.FCEV;
  const dominant = Object.entries(byType).sort((a, b) => b[1] - a[1])[0];
  return {
    cohort,
    total,
    byType,
    zeroTailpipe,
    dominant,
    countries: [...byCountry.entries()].sort((a, b) => b[1] - a[1]),
    models: [...byModel.entries()].sort((a, b) => b[1] - a[1]),
  };
}

export default function AutomotiveComparison() {
  const cohorts = getProductCohorts();
  const toyotaCohort = cohorts.find((row) => row.company_id === "toyota");
  const hyundaiCohort = cohorts.find((row) => row.company_id === "hyundai");
  if (!toyotaCohort || !hyundaiCohort) return null;

  const toyota = summarize(toyotaCohort);
  const hyundai = summarize(hyundaiCohort);
  const readiness = getImpactReadiness();
  const sourceIds = new Set([
    ...(toyotaCohort.origin_context?.source_ids ?? []),
    ...(hyundaiCohort.origin_context?.source_ids ?? []),
    ...toyotaCohort.source_ids,
    ...hyundaiCohort.source_ids,
  ]);
  const sources = getSources().filter((source) => sourceIds.has(source.source_id));
  const countryCodes = [...new Set([
    ...toyota.countries.map(([code]) => code),
    ...hyundai.countries.map(([code]) => code),
  ])].sort((a, b) => {
    const aTotal = (toyota.countries.find(([code]) => code === a)?.[1] ?? 0)
      + (hyundai.countries.find(([code]) => code === a)?.[1] ?? 0);
    const bTotal = (toyota.countries.find(([code]) => code === b)?.[1] ?? 0)
      + (hyundai.countries.find(([code]) => code === b)?.[1] ?? 0);
    return bTotal - aTotal;
  });

  return (
    <main className="alignment-report comparison-report">
      <div className="alignment-breadcrumb">
        <Link href="/">Trade Impact</Link><span>/</span><span>Automotive comparison</span>
      </div>

      <section className="alignment-hero comparison-hero">
        <div>
          <p className="eyebrow">Like-for-like EEA evidence · 2024 · EU27 passenger cars</p>
          <h1>Toyota vs Hyundai <em>destination-cohort comparison</em></h1>
          <p className="lede">
            Both companies are measured with the same EEA year, status, destination scope,
            registration field, commercial-name resolution, and powertrain classifier.
          </p>
          <p className="boundary-warning">
            This is not Japan-versus-Korea export volume. It measures where branded vehicles were
            first registered in the EU27; factory and origin-country mapping is not available.
          </p>
        </div>
        <div className="alignment-badge caution">
          <span>Lifetime GHG comparison</span>
          <strong>Withheld</strong>
          <small>sales and technology can be compared; hidden GHG cannot yet</small>
        </div>
      </section>

      <section className="comparison-scoreboard" aria-label="Observed cohort comparison">
        {[toyota, hyundai].map((company) => (
          <article key={company.cohort.company_id}>
            <div className="comparison-company-head">
              <div><span>Observed destination cohort</span><h2>{company.cohort.company_name}</h2></div>
              <Link href={`/analysis/${company.cohort.company_id}`}>Open detail →</Link>
            </div>
            <strong className="comparison-total">{count(company.total)}</strong>
            <p>EU27 first registrations</p>
            <div className="comparison-kpis">
              <div><span>Zero tailpipe</span><strong>{percent(company.zeroTailpipe, company.total)}</strong></div>
              <div><span>Combustion-dependent</span><strong>{percent(company.total - company.zeroTailpipe, company.total)}</strong></div>
              <div><span>Dominant type</span><strong>{company.dominant[0]} · {percent(company.dominant[1], company.total)}</strong></div>
            </div>
            <div className="mix-bar comparison-mix" aria-label={`${company.cohort.company_name} powertrain shares`}>
              {TYPES.map((type) => (
                <span
                  key={type}
                  style={{ width: `${(company.byType[type] / company.total) * 100}%`, background: COLORS[type] }}
                  title={`${LABELS[type]} ${percent(company.byType[type], company.total)}`}
                />
              ))}
            </div>
            <div className="comparison-type-grid">
              {TYPES.map((type) => (
                <div key={type}><i style={{ background: COLORS[type] }} /><span>{LABELS[type]}</span><strong>{percent(company.byType[type], company.total)}</strong></div>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="alignment-section comparison-findings">
        <header>
          <div><p className="eyebrow">01 / observed contrast</p><h2>What can be said <em>without inventing lifetime emissions</em></h2></div>
        </header>
        <div className="capability-grid">
          <article><span>Scale</span><strong>{(toyota.total / hyundai.total).toFixed(2)}×</strong><p>Toyota has the larger observed EU27 passenger-car cohort in this exact EEA boundary.</p></article>
          <article><span>Zero-tailpipe share</span><strong>{percent(hyundai.zeroTailpipe, hyundai.total)} vs {percent(toyota.zeroTailpipe, toyota.total)}</strong><p>Hyundai versus Toyota. This is tailpipe classification, not lifecycle-zero performance.</p></article>
          <article><span>Portfolio structure</span><strong>{toyota.dominant[0]} vs {hyundai.dominant[0]}</strong><p>Toyota is hybrid-dominant; Hyundai&apos;s largest group is other combustion, with a larger BEV share.</p></article>
        </div>
      </section>

      <section className="alignment-section" id="country-comparison">
        <header>
          <div><p className="eyebrow">02 / destination comparison</p><h2>The two cohorts enter <em>different national exposure patterns</em></h2></div>
          <p>Country counts are observed registrations. Hidden GHG remains unavailable for both companies.</p>
        </header>
        <div className="exposure-table-wrap">
          <table className="exposure-table comparison-table">
            <thead><tr><th>Destination</th><th>Toyota registrations</th><th>Toyota share</th><th>Hyundai registrations</th><th>Hyundai share</th><th>Lifetime comparison</th></tr></thead>
            <tbody>
              {countryCodes.map((code) => {
                const toyotaUnits = toyota.countries.find(([key]) => key === code)?.[1] ?? 0;
                const hyundaiUnits = hyundai.countries.find(([key]) => key === code)?.[1] ?? 0;
                return (
                  <tr key={code}>
                    <td><strong>{code}</strong></td>
                    <td>{count(toyotaUnits)}</td><td>{percent(toyotaUnits, toyota.total)}</td>
                    <td>{count(hyundaiUnits)}</td><td>{percent(hyundaiUnits, hyundai.total)}</td>
                    <td><span className="pending-target">Inputs incomplete</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="alignment-section" id="origin-boundary">
        <header>
          <div><p className="eyebrow">03 / production-origin boundary</p><h2>European sales are not the same as <em>Japanese or Korean exports</em></h2></div>
          <p>Company-reported regional production shares provide context only; they do not identify the origin of each registration.</p>
        </header>
        <div className="origin-context-grid">
          {[toyotaCohort, hyundaiCohort].map((cohort) => {
            const source = sources.find((row) => cohort.origin_context?.source_ids.includes(row.source_id));
            return (
              <article key={cohort.company_id}>
                <span>{cohort.company_name}</span>
                <p>{cohort.origin_context?.notes}</p>
                {source ? <a href={source.url}>Open company production source ↗</a> : null}
              </article>
            );
          })}
        </div>
        <div className="publication-decision">
          <div><span>Required next data layer</span><strong>model × factory/country of production × destination</strong></div>
          <p>Until that mapping is sourced, the project compares branded destination cohorts—not national export performance.</p>
        </div>
      </section>

      <section className="alignment-section">
        <header>
          <div><p className="eyebrow">04 / publication gate</p><h2>Both companies face the <em>same missing-input rule</em></h2></div>
        </header>
        <div className="readiness-grid">
          {readiness.filter((row) => [toyotaCohort.cohort_id, hyundaiCohort.cohort_id].includes(row.cohort_id)).map((row) => (
            <article className="missing-inputs" key={row.cohort_id}>
              <span>{row.cohort_id.startsWith("toyota") ? "Toyota" : "Hyundai"} · {row.missing_required_inputs.length} required groups</span>
              <p>{row.publication_reason}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
