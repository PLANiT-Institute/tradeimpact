import type { Metadata } from "next";
import Link from "next/link";
import {
  SCENARIOS,
  SCENARIO_LABELS,
  getCohortComparison,
  getDestinationInputs,
  getImpactReadiness,
  getLifetimeResults,
  getProductCohorts,
  getSources,
  type ProductCohort,
  type Scenario,
} from "@/lib/data";
import { DivergingBars, POWERTRAIN_LABELS, kg, mt, type Row } from "@/components/cohort-report";
import { MarketDumbbell } from "@/components/market-dumbbell";

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
  const results = getLifetimeResults();
  const lifetimeOf = (cohort: ProductCohort) => results[cohort.cohort_id];
  const comparison = getCohortComparison();
  const destinationInputs = getDestinationInputs();
  const byScenario = Object.fromEntries(comparison.map((row) => [row.scenario, row]));
  // Each term under all three pathways. Reading them together is what shows that the two
  // favourable terms grow with ambition while the unfavourable one does not move at all.
  const gapRows: Row[] = (
    [
      ["destination_mix", "Destination mix"],
      ["powertrain_mix", "Powertrain mix"],
      ["product_intensity", "Product intensity"],
      ["residual", "Residual"],
      ["gap", "Net per-vehicle gap"],
    ] as const
  ).map(([key, label]) => ({
    key,
    label,
    values: Object.fromEntries(
      SCENARIOS.map((s) => [
        s,
        key === "gap"
          ? byScenario[s].gap
          : key === "residual"
            ? byScenario[s].residual
            : byScenario[s].terms[key],
      ]),
    ) as Record<Scenario, number>,
  }));
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
          <span>Lifetime TI · S2 national commitments</span>
          <strong>
            {mt(lifetimeOf(toyotaCohort).cohorts.S2.total_tCO2e, 1)} vs{" "}
            {mt(lifetimeOf(hyundaiCohort).cohorts.S2.total_tCO2e, 1)} Mt
          </strong>
          <small>
            Toyota vs Hyundai. Cohort sizes differ, so compare the per-vehicle figures below.
          </small>
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
            <div className="comparison-kpis">
              {SCENARIOS.map((s) => {
                const result = lifetimeOf(company.cohort);
                const perVehicle =
                  (result.cohorts[s].total_tCO2e * 1000) / result.coverage.covered_units;
                return (
                  <div key={s}>
                    <span>{s} · per vehicle</span>
                    <strong className={perVehicle >= 0 ? "pos" : "neg"}>
                      {kg(perVehicle)} kg
                    </strong>
                  </div>
                );
              })}
            </div>
          </article>
        ))}
      </section>

      <section className="alignment-section" id="lifetime-comparison">
        <header>
          <div><p className="eyebrow">00 / lifetime result</p><h2>Same boundary, same pathways, <em>two different lock-in profiles</em></h2></div>
          <p>
            Per-vehicle lifetime TI removes the cohort-size difference, so what remains is the
            portfolio decision itself. Both are reported under all three pathways; neither is
            reported alone.
          </p>
        </header>
        <div className="exposure-table-wrap">
          <table className="exposure-table comparison-table">
            <thead>
              <tr>
                <th>Pathway</th>
                <th>Toyota total</th><th>Toyota per vehicle</th>
                <th>Hyundai total</th><th>Hyundai per vehicle</th>
              </tr>
            </thead>
            <tbody>
              {SCENARIOS.map((s) => (
                <tr key={s}>
                  <td><strong>{s}</strong> {SCENARIO_LABELS[s]}</td>
                  {[toyotaCohort, hyundaiCohort].map((cohort) => {
                    const result = lifetimeOf(cohort);
                    const totalTi = result.cohorts[s].total_tCO2e;
                    const perVehicle = (totalTi * 1000) / result.coverage.covered_units;
                    return [
                      <td key={`${cohort.company_id}-total`} className={totalTi >= 0 ? "pos" : "neg"}>
                        {mt(totalTi)} Mt
                      </td>,
                      <td key={`${cohort.company_id}-per`} className={perVehicle >= 0 ? "pos" : "neg"}>
                        {kg(perVehicle)} kg
                      </td>,
                    ];
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="table-footnote">
          Coverage differs: {percent(lifetimeOf(toyotaCohort).coverage.covered_units, toyota.total)} of
          the Toyota cohort and{" "}
          {percent(lifetimeOf(hyundaiCohort).coverage.covered_units, hyundai.total)} of the Hyundai
          cohort are priced. PHEV and FCEV units are withheld with their counts on both sides, so
          the two figures rest on the same rule.
        </p>
      </section>

      <section className="alignment-section" id="gap-sources">
        <header>
          <div>
            <p className="eyebrow">00b / where the per-vehicle gap comes from</p>
            <h2>A cleaner powertrain mix, <em>spent on higher-emitting vehicles</em></h2>
          </div>
          <p>
            Hyundai sells seven times Toyota&apos;s battery-electric share and lands in the
            gentler destination mix, and still finishes further behind per vehicle. Splitting
            the gap into the three decisions behind it — which markets, which powertrains, which
            vehicles — shows why: the first two help, and the third more than spends them. It
            also shows which of the three depends on how ambitious the pathway is. Both
            favourable terms move with the scenario; the unfavourable one is the same number
            under all three, because nine in ten covered units emit at a rate fixed on the day
            they were sold and the benchmark they are measured against is common to both.
          </p>
        </header>
        <DivergingBars rows={gapRows} unit="kg" height={34} />
        <p className="muted ti-gap-note">
          Bars are kgCO₂e per covered vehicle over the operating life. Right of the axis means
          Hyundai gains against Toyota on that count; left means it loses. The first four rows
          add up to the fifth. Toyota&apos;s own result is{" "}
          {kg(byScenario.S2.per_vehicle[toyotaCohort.cohort_id])} kg per vehicle under S2 and
          Hyundai&apos;s is {kg(byScenario.S2.per_vehicle[hyundaiCohort.cohort_id])} kg.
        </p>
        <div className="exposure-table-wrap">
          <table className="exposure-table comparison-table">
            <caption>
              Per-vehicle lifetime TI inside each powertrain, and each cohort&apos;s share of
              covered units. The product-intensity term is this table, weighted.
            </caption>
            <thead>
              <tr>
                <th>Powertrain</th>
                <th>Toyota share</th><th>Toyota per vehicle (S2)</th>
                <th>Hyundai share</th><th>Hyundai per vehicle (S2)</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(byScenario.S2.by_powertrain).map(([powertrain, rows]) => (
                <tr key={powertrain}>
                  <td><strong>{POWERTRAIN_LABELS[powertrain] ?? powertrain}</strong></td>
                  {[toyotaCohort, hyundaiCohort].flatMap((cohort) => {
                    const row = rows[cohort.cohort_id];
                    const value = row?.ti_per_vehicle;
                    return [
                      <td key={`${cohort.company_id}-share`}>
                        {row ? percent(row.unit_share, 1) : "—"}
                      </td>,
                      <td
                        key={`${cohort.company_id}-ti`}
                        className={value == null ? undefined : value >= 0 ? "pos" : "neg"}
                      >
                        {value == null ? "—" : `${kg(value)} kg`}
                      </td>,
                    ];
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="table-footnote">
          The three terms use weights averaged across the two cohorts, which is what makes them
          sum to the gap; whatever interaction is left over is published as the residual rather
          than absorbed into a term. Reproduced by{" "}
          <code>data-pipeline/compare_cohorts.py</code> and re-checked on every dataset build.
        </p>
      </section>

      <section className="alignment-section comparison-findings">
        <header>
          <div><p className="eyebrow">01 / observed contrast</p><h2>What the registration record shows <em>before any lifetime model runs</em></h2></div>
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
          <p>
            Country counts are observed registrations; the last two columns are the lifetime TI
            those registrations carry under national commitments (S2). Totals follow cohort
            size, so the chart below divides each market by the units placed in it — the
            like-for-like reading of what one vehicle does there.
          </p>
        </header>
        <MarketDumbbell
          baseline={lifetimeOf(toyotaCohort)}
          compared={lifetimeOf(hyundaiCohort)}
          destinations={destinationInputs}
        />
        <div className="exposure-table-wrap">
          <table className="exposure-table comparison-table">
            <thead><tr><th>Destination</th><th>Toyota registrations</th><th>Toyota share</th><th>Toyota TI (S2)</th><th>Hyundai registrations</th><th>Hyundai share</th><th>Hyundai TI (S2)</th></tr></thead>
            <tbody>
              {countryCodes.map((code) => {
                const toyotaUnits = toyota.countries.find(([key]) => key === code)?.[1] ?? 0;
                const hyundaiUnits = hyundai.countries.find(([key]) => key === code)?.[1] ?? 0;
                const toyotaTi = lifetimeOf(toyotaCohort).cohorts.S2.by_country[code];
                const hyundaiTi = lifetimeOf(hyundaiCohort).cohorts.S2.by_country[code];
                return (
                  <tr key={code}>
                    <td><strong>{code}</strong></td>
                    <td>{count(toyotaUnits)}</td><td>{percent(toyotaUnits, toyota.total)}</td>
                    <td className={toyotaTi == null ? undefined : toyotaTi >= 0 ? "pos" : "neg"}>
                      {toyotaTi == null ? <span className="pending-target">not covered</span> : `${mt(toyotaTi, 3)} Mt`}
                    </td>
                    <td>{count(hyundaiUnits)}</td><td>{percent(hyundaiUnits, hyundai.total)}</td>
                    <td className={hyundaiTi == null ? undefined : hyundaiTi >= 0 ? "pos" : "neg"}>
                      {hyundaiTi == null ? <span className="pending-target">not covered</span> : `${mt(hyundaiTi, 3)} Mt`}
                    </td>
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
          <div><p className="eyebrow">04 / publication gate</p><h2>Both companies face the <em>same publication rule</em></h2></div>
          <p>
            The same gate decided both results: publish the share of the cohort whose inputs are
            sourced, withhold the rest by product type with its unit count, and never substitute a
            zero for a missing input.
          </p>
        </header>
        <div className="readiness-grid">
          {readiness.filter((row) => [toyotaCohort.cohort_id, hyundaiCohort.cohort_id].includes(row.cohort_id)).map((row) => (
            <article className={row.missing_required_inputs.length ? "missing-inputs" : "ready-inputs"} key={row.cohort_id}>
              <span>
                {row.cohort_id.startsWith("toyota") ? "Toyota" : "Hyundai"} ·{" "}
                {row.missing_required_inputs.length
                  ? `${row.missing_required_inputs.length} required groups outstanding`
                  : `${((row.covered_unit_share ?? 0) * 100).toFixed(1)}% of units covered`}
              </span>
              <p>{row.publication_reason}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
