import type { Metadata } from "next";
import Link from "next/link";
import AnnualLines from "@/components/AnnualLines";
import DecompBars from "@/components/DecompBars";
import ScenarioCards from "@/components/ScenarioCards";
import {
  directionClass,
  directionOf,
  getCountries,
  getFirmResult,
  getFirms,
  impactDirectionWord,
  ndcImpactLabel,
  SCENARIOS,
  type Direction,
  type Scenario,
} from "@/lib/data";

export function generateStaticParams() {
  return getFirms()
    .filter((firm) => firm.runnable)
    .map((firm) => ({ firm: firm.slug }));
}
export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ firm: string }>;
}): Promise<Metadata> {
  const { firm } = await params;
  return { title: `${getFirmResult(firm).firm} — TI report` };
}

export default async function Report({ params }: { params: Promise<{ firm: string }> }) {
  const { firm } = await params;
  const meta = getFirms().find((item) => item.slug === firm);
  const result = getFirmResult(firm);
  const quality = result.data_quality;
  const directionalOnly = Object.fromEntries(
    SCENARIOS.filter((scenario) => result.cohorts[scenario]).map((scenario) => [
      scenario,
      result.cohorts[scenario].directional_only,
    ]),
  ) as Partial<Record<Scenario, boolean>>;
  const numericScenarios = SCENARIOS.filter(
    (scenario) => result.cohorts[scenario] && !result.cohorts[scenario].directional_only,
  );
  const totals = Object.fromEntries(
    SCENARIOS.filter((scenario) => result.cohorts[scenario]).map((scenario) => [
      scenario,
      result.cohorts[scenario].total_tCO2e,
    ]),
  ) as Partial<Record<Scenario, number>>;
  const annual = Object.fromEntries(
    numericScenarios.map((scenario) => [scenario, result.cohorts[scenario].annual_tCO2e]),
  ) as Partial<Record<Scenario, number[]>>;
  const central = result.cohorts.S2 ?? result.cohorts.S1 ?? result.cohorts.S3;
  const centralValue = result.cohorts.S2?.total_tCO2e;
  const centralDirection = directionOf(centralValue);
  const excludedMarkets = Object.keys(result.cohorts.S2?.excluded_flag_markets ?? {});
  const markets = new Set<string>();
  for (const scenario of SCENARIOS) {
    for (const code of Object.keys(result.cohorts[scenario]?.by_country ?? {})) markets.add(code);
    for (const code of Object.keys(result.cohorts[scenario]?.excluded_flag_markets ?? {})) {
      markets.add(code);
    }
  }
  const placements =
    (result.inputs?.placements as Array<{
      country: string;
      brand?: string;
      model?: string;
      powertrain: string;
      units?: number;
      tier?: string;
      source?: string;
      vehicle_source?: string;
      volume_source?: string;
    }> | undefined) ?? [];
  const inputCountries =
    (result.inputs?.countries as Record<
      string,
      { name?: string; tier?: string; source?: string }
    > | undefined) ?? {};
  const support =
    (result.inputs?.support as { lifetime_T?: number; vkt?: Record<string, number> } | undefined) ??
    {};
  const representedUnits =
    meta?.assessed_units ??
    placements.reduce((total, placement) => total + (placement.units ?? 0), 0);
  const scenarioDirections = SCENARIOS.map((scenario) =>
    directionOf(result.cohorts[scenario]?.total_tCO2e),
  ).filter((direction) => direction !== "missing");
  const sameDirection = new Set(scenarioDirections).size === 1;
  const topPowertrain = largestAbsolute(central.by_powertrain);
  const countryNames = new Map(getCountries().map((country) => [country.code, country.name]));
  const countryImpactRows = [...markets]
    .map((code) => {
      const marketPlacements = placements.filter((placement) => placement.country === code);
      const units = marketPlacements.reduce((sum, placement) => sum + (placement.units ?? 0), 0);
      const mix = Object.entries(
        marketPlacements.reduce<Record<string, number>>((byPowertrain, placement) => {
          byPowertrain[placement.powertrain] =
            (byPowertrain[placement.powertrain] ?? 0) + (placement.units ?? 0);
          return byPowertrain;
        }, {}),
      )
        .sort((a, b) => b[1] - a[1])
        .slice(0, 2)
        .map(([powertrain, count]) =>
          `${powertrain} ${units ? Math.round((count / units) * 100) : 0}%`,
        )
        .join(" · ");
      const value = result.cohorts.S2?.by_country?.[code];
      return {
        code,
        name: countryNames.get(code) ?? code,
        units,
        mix,
        value,
        direction: directionOf(value),
        excludedReason: result.cohorts.S2?.excluded_flag_markets?.[code],
      };
    })
    .sort((a, b) => {
      if (a.value === undefined && b.value !== undefined) return 1;
      if (a.value !== undefined && b.value === undefined) return -1;
      return Math.abs(b.value ?? b.units) - Math.abs(a.value ?? a.units);
    });
  const grossCountryImpact = countryImpactRows.reduce(
    (sum, row) => sum + (row.value === undefined ? 0 : Math.abs(row.value)),
    0,
  );
  const measuredCountryRows = countryImpactRows.filter((row) => row.value !== undefined);
  const topCountry = measuredCountryRows[0];
  const lockInMarkets = measuredCountryRows.filter((row) => row.direction === "liability").length;
  const contributionMarkets = measuredCountryRows.filter(
    (row) => row.direction === "contribution",
  ).length;

  return (
    <main className="plain-report">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/#assessments">Companies</Link><span>/</span><span>{result.firm}</span>
      </nav>

      <header className="simple-report-header">
        <div>
          <p className="eyebrow">Automotive assessment · {result.cohort_year} sales cohort</p>
          <h1>{result.firm}</h1>
          <p className="lede">
            How the products and operating markets represented in the {result.cohort_year}{" "}
            sales cohort affect delivery of the relevant national NDCs.
          </p>
        </div>
        <div className="report-meta-line">
          <span>{meta?.illustrative ? "Illustrative case" : "Source-backed inputs"}</span>
          <span>{markets.size} markets</span>
          <span>{representedUnits.toLocaleString("en-US")} vehicles</span>
        </div>
      </header>

      <nav className="report-section-nav" aria-label="Report sections">
        <span>Jump to</span>
        <Link href="#finding">Finding</Link>
        <Link href="#country-impact">Markets</Link>
        <Link href="#scenarios">Sensitivities</Link>
        {!central.directional_only && <Link href="#drivers">Drivers</Link>}
        <Link href="#details">Details</Link>
      </nav>

      <section className={`key-finding ${directionClass(centralDirection)}`} id="finding">
        <div className="finding-copy">
          <p className="eyebrow">Core NDC finding</p>
          <h2>{findingTitle(result.firm, result.cohort_year, centralDirection)}</h2>
          <p>{findingExplanation(centralDirection)}</p>
        </div>
        <div className="finding-number">
          <strong>{compactCarbon(centralValue)}</strong>
          <span>{ndcResultCaption(centralDirection)}</span>
        </div>
      </section>

      <section className="answer-strip" aria-label="Assessment at a glance">
        <article>
          <span>Finding under sensitivities</span>
          <strong>{sameDirection ? "Direction holds in all 3 cases" : "The direction changes"}</strong>
          <p>{sameDirection ? "The NDC finding is not reversed by slower or faster transition assumptions." : "Open the sensitivity view to see where the conclusion changes."}</p>
        </article>
        <article>
          <span>Sales represented</span>
          <strong>{meta?.coverage_ratio === undefined ? "Not applicable" : `${(meta.coverage_ratio * 100).toFixed(1)}%`}</strong>
          <p>Share of disclosed global sales included in this assessment.</p>
        </article>
        <article>
          <span>NDC benchmark available</span>
          <strong>{markets.size - excludedMarkets.length} of {markets.size} markets</strong>
          <p>{excludedMarkets.length ? `${excludedMarkets.join(", ")} are excluded from the NDC total.` : "All assessed markets are included."}</p>
        </article>
        {meta?.netzero && (
          <article>
            <span>Company commitment</span>
            <strong>Carbon neutral by {meta.netzero.target_year}</strong>
            <p>
              {meta.netzero.scope}
              {meta.netzero.interim ? ` · ${meta.netzero.interim}` : ""}
              {meta.netzero.source && <> · <a href={meta.netzero.source}>Source</a></>}
            </p>
          </article>
        )}
      </section>

      <div className="use-result-note">
        <div>
          <strong>Use this to understand the NDC effect of the represented {result.cohort_year} sales cohort, not as a company score.</strong>
          <p>
            The result compares represented product sales with national commitments. The
            exact total depends on sales coverage.
            {meta?.illustrative && " This is an illustrative validation case, not a real-firm assessment."}
          </p>
        </div>
        <Link className="text-action" href={`/calculator?firm=${firm}`}>Test an assumption →</Link>
      </div>

      <section className="simple-report-section country-impact-section" id="country-impact">
        <p className="eyebrow">Country-by-country NDC impact</p>
        <h2>Where does the represented {result.cohort_year} sales cohort affect NDC delivery?</h2>
        <p className="section-lede">
          {topCountry ? (
            <>
              <strong>{topCountry.name}</strong> is the largest measured country driver at{" "}
              <strong>{compactCarbon(topCountry.value)}</strong> of{" "}
              {ndcImpactLabel(topCountry.direction)}. The table separates
              measured NDC effects from markets where no absolute NDC benchmark is available.
            </>
          ) : (
            "No represented sales market currently has an absolute NDC benchmark."
          )}
        </p>

        <div className="country-impact-summary" aria-label="Country impact summary">
          <div><strong>{lockInMarkets}</strong><span>NDC lock-in markets</span></div>
          <div><strong>{contributionMarkets}</strong><span>NDC contribution markets</span></div>
          <div><strong>{countryImpactRows.length - measuredCountryRows.length}</strong><span>markets without an absolute NDC result</span></div>
        </div>

        <div className="country-impact-table-wrap table-scroll">
          <table className="country-impact-table">
            <thead>
              <tr>
                <th>Sales market</th>
                <th>Represented {result.cohort_year} sales</th>
                <th>NDC effect</th>
                <th>Lifetime impact</th>
                <th className="num">Impact / product</th>
                <th><span className="sr-only">Open market</span></th>
              </tr>
            </thead>
            <tbody>
              {countryImpactRows.map((row) => {
                const share =
                  row.value === undefined || grossCountryImpact === 0
                    ? 0
                    : (Math.abs(row.value) / grossCountryImpact) * 100;
                return (
                  <tr key={row.code} className={row.value === undefined ? "country-excluded" : ""}>
                    <td data-label="Sales market">
                      <div className="country-identity">
                        <span>{row.code}</span>
                        <strong>{row.name}</strong>
                      </div>
                    </td>
                    <td data-label="Represented sales">
                      <strong>{row.units.toLocaleString("en-US")}</strong>
                      <small>{row.mix || "Product mix unavailable"}</small>
                    </td>
                    <td data-label="NDC effect">
                      {row.value === undefined ? (
                        <span className="ndc-effect unavailable">Not computable</span>
                      ) : (
                        <span className={`ndc-effect ${directionClass(row.direction)}`}>
                          {ndcImpactLabel(row.direction)}
                        </span>
                      )}
                      {row.excludedReason && <small>{row.excludedReason.replace("S2", "NDC")}</small>}
                    </td>
                    <td data-label="Lifetime impact">
                      {row.value === undefined ? (
                        <span className="muted">—</span>
                      ) : (
                        <div className="country-impact-value">
                          <strong>{compactCarbon(row.value)}</strong>
                          <div className="country-share-track" aria-hidden="true">
                            <span className={directionClass(row.direction)} style={{ width: `${Math.max(share, 1.5)}%` }} />
                          </div>
                          <small>{share.toFixed(1)}% of absolute measured impact</small>
                        </div>
                      )}
                    </td>
                    <td className="num" data-label="Impact / product">
                      {row.value === undefined || row.units === 0
                        ? "—"
                        : `${Math.abs(row.value / row.units).toLocaleString("en-US", { maximumFractionDigits: 2 })} t ${impactDirectionWord(row.direction)}`}
                    </td>
                    <td className="country-row-action"><Link className="country-row-link" href={`/country/${row.code}`} aria-label={`Open ${row.name} NDC impact`}>View →</Link></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="plain-footnote">
          Percentages use the sum of absolute measured country impacts, so contribution and
          lock-in effects are not allowed to cancel each other in the comparison.
        </p>
      </section>

      <section className="simple-report-section" id="scenarios">
        <p className="eyebrow">NDC result and sensitivities</p>
        <h2>Is the NDC finding robust to other transition assumptions?</h2>
        <p className="section-lede">
          The national NDC result is the core metric. Current-policy and 1.5°C pathways are
          shown as slower and faster sensitivities, not as equal research questions.
        </p>
        <ScenarioCards
          totals={totals}
          unit="tCO₂e · cohort lifetime"
          directionalOnly={directionalOnly}
        />
        {Object.values(directionalOnly).some(Boolean) && (
          <p className="plain-footnote">
            Some cards show direction only because proxy-based inputs are too large a share
            of the result to justify publishing a precise number.
          </p>
        )}
      </section>

      {!central.directional_only && (
        <section className="simple-report-section" id="drivers">
          <p className="eyebrow">Product mix driver</p>
          <h2>Which powertrains drive the NDC result?</h2>
          <p className="section-lede">
            The largest powertrain driver is <strong>{topPowertrain?.[0] ?? "—"}</strong>.
            Positive values contribute to NDC delivery; negative values indicate emissions lock-in.
          </p>
          <div className="quiet-panel powertrain-driver-panel">
            <DecompBars data={central.by_powertrain} unit="tCO₂e" />
          </div>
        </section>
      )}

      <section className="simple-report-section detail-section" id="details">
        <p className="eyebrow">For analysts and reviewers</p>
        <h2>Need the underlying detail?</h2>
        <p className="section-lede">Open only the part you need. These sections preserve the full technical output and governance trail.</p>

        <details className="report-detail">
          <summary><span>Annual pattern</span><small>How the gap develops over the vehicle lifetime</small></summary>
          <div className="detail-body">
            {numericScenarios.length > 0 ? (
              <AnnualLines series={annual} xLabel="year since sale" yLabel="tCO₂e / yr" />
            ) : (
              <p className="panel-note">All scenarios are direction-only, so numeric lines are hidden.</p>
            )}
            {Object.keys(result.portfolio ?? {}).length > 0 && numericScenarios.length > 0 && (
              <>
                <h3>Rolling portfolio</h3>
                <AnnualLines
                  series={Object.fromEntries(
                    numericScenarios.map((scenario) => [scenario, result.portfolio[scenario]]),
                  ) as Partial<Record<Scenario, number[]>>}
                  xLabel="year index"
                  yLabel="tCO₂e / yr"
                />
              </>
            )}
          </div>
        </details>

        <details className="report-detail">
          <summary><span>Product crossover</span><small>When cumulative product performance crosses its benchmark</small></summary>
          <div className="detail-body table-scroll">
            <table>
              <thead><tr><th>Market</th><th>Powertrain</th><th>Scenario</th><th className="num">Crossover year</th><th className="num">Gap / vehicle</th><th>Note</th></tr></thead>
              <tbody>
                {result.crossover.filter((row) => !directionalOnly[row.scenario]).map((row, index) => (
                  <tr key={index}>
                    <td className="mono">{row.country}</td><td>{row.powertrain}</td><td>{row.scenario}</td>
                    <td className="num">{row.crossover_year === null ? "—" : row.crossover_year.toFixed(1)}</td>
                    <td className="num">{cumulativeValue(row)}</td><td>{row.reason ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>

        <details className="report-detail" id="data-quality">
          <summary><span>Data quality and assumptions</span><small>Input tiers, exclusions, warnings and sources</small></summary>
          <div className="detail-body quality-body">
            <div className="quality-columns">
              <div><h3>Market benchmarks</h3>{Object.entries(quality.benchmark_tiers).map(([code, tier]) => <span className="tier-chip" key={code}>{code} · Tier {tier}</span>)}</div>
              <div><h3>Sales volumes</h3>{Object.entries(quality.volume_tiers).map(([code, tier]) => <span className="tier-chip" key={code}>{code} · Tier {tier}</span>)}</div>
            </div>
            <h3>Vehicle inputs</h3>
            <div>{Object.entries(quality.layer2_tiers).map(([label, tier]) => <span className="tier-chip" key={label}>{label} · Tier {tier}</span>)}</div>
            <h3>Model settings</h3>
            <p className="panel-note">Vehicle lifetime {quality.lifetime_T} years (±{quality.lifetime_sens} years tested) · Layer 1 method {quality.layer1_method}.</p>
            {Object.keys(quality.flag_markets).length > 0 && <><h3>Markets excluded from the central total</h3><ul>{Object.entries(quality.flag_markets).map(([code, reason]) => <li key={code}>{code}: {reason}</li>)}</ul></>}
            {quality.missing_inputs.length > 0 && <><h3>Missing inputs</h3><ul>{quality.missing_inputs.map((item) => <li key={item}>{item}</li>)}</ul></>}
            {quality.warnings.length > 0 && <><h3>Warnings</h3><ul>{quality.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></>}
          </div>
        </details>

        <details className="report-detail">
          <summary><span>Backing data and sources</span><small>Every input behind this result, with its source</small></summary>
          <div className="detail-body">
            <h3>Market benchmarks</h3>
            <div className="table-scroll">
              <table>
                <thead><tr><th>Market</th><th>Tier</th><th className="num">Annual distance</th><th>Benchmark source</th></tr></thead>
                <tbody>
                  {Object.entries(inputCountries).map(([code, country]) => (
                    <tr key={code}>
                      <td className="mono">{code}</td>
                      <td className="mono">{country.tier ?? "?"}</td>
                      <td className="num">{support.vkt?.[code] === undefined ? "—" : `${support.vkt[code].toLocaleString("en-US")} km`}</td>
                      <td>{country.source ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <h3>Represented sales rows</h3>
            <div className="table-scroll">
              <table>
                <thead><tr><th>Market</th><th>Product</th><th className="num">Units</th><th>Tier</th><th>Volume source</th><th>Vehicle source</th></tr></thead>
                <tbody>
                  {placements.map((placement, index) => (
                    <tr key={index}>
                      <td className="mono">{placement.country}</td>
                      <td>{placement.brand} {placement.model} <span className="mono">({placement.powertrain})</span></td>
                      <td className="num">{placement.units?.toLocaleString("en-US") ?? "—"}</td>
                      <td className="mono">{placement.tier ?? "?"}</td>
                      <td>{placement.volume_source ?? placement.source ?? "—"}</td>
                      <td>{placement.vehicle_source ?? placement.source ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="panel-note">
              Sector-wide assumptions: vehicle lifetime {support.lifetime_T ?? quality.lifetime_T} years ·
              per-market annual distance shown above. The collection backlog and evidence
              gate are documented in <span className="mono">data-pipeline/COLLECTION_STATUS.md</span>.
            </p>
          </div>
        </details>

        <details className="report-detail">
          <summary><span>Coverage and provenance</span><small>What is represented and how to reproduce the result</small></summary>
          <div className="detail-body">
            {meta?.illustrative && <p><strong>Illustrative case.</strong> {meta.note}</p>}
            {meta?.coverage_ratio !== undefined && <p><strong>Coverage.</strong> {meta.assessed_units?.toLocaleString("en-US")} vehicles, or {(meta.coverage_ratio * 100).toFixed(1)}% of the disclosed {result.cohort_year} global-sales denominator. {meta.coverage_scope}. {meta.coverage_source && <a href={meta.coverage_source}>Source</a>}</p>}
            <p className="mono provenance-copy">engine {result.provenance.engine_version} #{result.provenance.engine_source_sha256.slice(0, 12)} · input #{result.provenance.input_sha256.slice(0, 12)} · dataset #{result.provenance.dataset_sha256.slice(0, 12)} · workbook #{result.provenance.workbook_sha256.slice(0, 12)}</p>
          </div>
        </details>
      </section>
    </main>
  );
}

function findingTitle(firm: string, cohortYear: number, direction: Direction): string {
  if (direction === "liability") return `${firm}'s represented ${cohortYear} product sales create a net NDC lock-in impact.`;
  if (direction === "contribution") return `${firm}'s represented ${cohortYear} product sales make a net contribution to national NDC delivery.`;
  if (direction === "neutral") return `${firm}'s represented ${cohortYear} product sales are aligned with the assessed national NDC benchmarks.`;
  return "The supplied inputs do not produce an NDC impact result.";
}

function findingExplanation(direction: Direction): string {
  if (direction === "liability") return "Across the included sales markets, modeled product-lifetime emissions exceed the sales-weighted benchmarks derived from those countries' NDC commitments.";
  if (direction === "contribution") return "Across the included sales markets, modeled product-lifetime emissions are below the sales-weighted benchmarks derived from those countries' NDC commitments.";
  if (direction === "neutral") return "The represented products and sales-weighted NDC benchmarks produce no net lifetime impact gap.";
  return "Review missing inputs and excluded NDC markets before using this assessment.";
}

function ndcResultCaption(direction: Direction): string {
  if (direction === "liability") return "net emissions lock-in against national NDCs";
  if (direction === "contribution") return "net contribution to national NDCs";
  if (direction === "neutral") return "net aligned impact against national NDCs";
  return "NDC impact unavailable";
}

function compactCarbon(value: number | undefined): string {
  if (value === undefined) return "Not available";
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) return `${(absolute / 1_000_000).toFixed(2)} MtCO₂e`;
  if (absolute >= 1_000) return `${(absolute / 1_000).toFixed(0)} ktCO₂e`;
  return `${absolute.toLocaleString("en-US", { maximumFractionDigits: 0 })} tCO₂e`;
}

function largestAbsolute(values: Record<string, number>): [string, number] | undefined {
  return Object.entries(values).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];
}

function cumulativeValue(row: { TI_per_vehicle_kgCO2e?: number }): string {
  return row.TI_per_vehicle_kgCO2e === undefined
    ? "—"
    : `${row.TI_per_vehicle_kgCO2e.toLocaleString("en-US", { maximumFractionDigits: 0 })} kgCO₂e`;
}
