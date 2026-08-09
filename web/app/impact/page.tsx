import type { Metadata } from "next";
import Link from "next/link";
import {
  SCENARIOS,
  SCENARIO_COLORS,
  SCENARIO_LABELS,
  getDestinationInputs,
  getImpactReadiness,
  getLifetimeResults,
  getMeta,
  getSources,
  type DestinationInput,
  type LifetimeResult,
  type Scenario,
} from "@/lib/data";

export const metadata: Metadata = {
  title: "Lifetime impact of the 2024 EU27 cohorts — Trade Impact",
  description:
    "Toyota and Hyundai 2024 EU27 passenger-car cohorts scored against three destination pathways, decomposed by product type and destination market.",
};

const POWERTRAIN_LABELS: Record<string, string> = {
  BEV: "Battery electric",
  HEV: "Hybrid (non-plug-in)",
  ICE: "Combustion",
  PHEV: "Plug-in hybrid",
  FCEV: "Fuel cell",
};
const POWERTRAIN_COLORS: Record<string, string> = {
  BEV: "#5d9cec",
  HEV: "#d9a441",
  ICE: "#ef7b5e",
  PHEV: "#36bfa0",
  FCEV: "#9d7bea",
};
const TIER_LABEL: Record<string, string> = {
  A: "official primary",
  B: "official, older vintage or wider concept",
  C: "proxy — pooled or EU-average stand-in",
};

function mt(value: number, digits = 2): string {
  return `${value >= 0 ? "+" : "−"}${Math.abs(value / 1e6).toFixed(digits)}`;
}
function kg(value: number): string {
  return `${value >= 0 ? "+" : "−"}${Math.abs(value).toLocaleString("en-US", {
    maximumFractionDigits: 0,
  })}`;
}
function count(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
}
function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

type Row = { key: string; label: string; values: Record<Scenario, number> };

/** Grouped bars around a zero axis. One row per key, one bar per scenario. */
function DivergingBars({
  rows,
  unit,
  colorOf,
  height = 30,
}: {
  rows: Row[];
  unit: "Mt" | "kg";
  colorOf?: (key: string) => string;
  height?: number;
}) {
  const values = rows.flatMap((row) => SCENARIOS.map((s) => row.values[s] ?? 0));
  const extent = Math.max(...values.map(Math.abs), 1);
  const barH = height / SCENARIOS.length - 2;
  const rowH = height + 16;
  const width = 100; // percentage-space viewBox keeps the chart fluid
  const zero = width / 2;
  const scale = (v: number) => (v / extent) * (width / 2 - 1);
  const fmt = (v: number) => (unit === "Mt" ? `${mt(v)} Mt` : `${kg(v)} kg`);

  return (
    <div className="ti-chart">
      <div className="ti-legend">
        {SCENARIOS.map((s) => (
          <span key={s}>
            <i style={{ background: SCENARIO_COLORS[s] }} aria-hidden />
            {s} · {SCENARIO_LABELS[s]}
          </span>
        ))}
      </div>
      {rows.map((row) => (
        <div className="ti-chart-row" key={row.key}>
          <div className="ti-chart-label">
            {colorOf ? <i style={{ background: colorOf(row.key) }} aria-hidden /> : null}
            <span>{row.label}</span>
          </div>
          <svg
            viewBox={`0 0 ${width} ${rowH}`}
            preserveAspectRatio="none"
            className="ti-chart-svg"
            role="img"
            aria-label={`${row.label}: ${SCENARIOS.map(
              (s) => `${SCENARIO_LABELS[s]} ${fmt(row.values[s] ?? 0)}`,
            ).join(", ")}`}
          >
            <line x1={zero} y1={0} x2={zero} y2={rowH} className="ti-axis" />
            {SCENARIOS.map((s, i) => {
              const v = row.values[s] ?? 0;
              const w = Math.abs(scale(v));
              return (
                <rect
                  key={s}
                  x={v >= 0 ? zero : zero - w}
                  y={i * (barH + 2) + 2}
                  width={Math.max(w, 0.2)}
                  height={barH}
                  fill={SCENARIO_COLORS[s]}
                  opacity={v >= 0 ? 0.95 : 0.75}
                />
              );
            })}
          </svg>
          <div className="ti-chart-values">
            {SCENARIOS.map((s) => (
              <span key={s} className={(row.values[s] ?? 0) >= 0 ? "pos" : "neg"}>
                {fmt(row.values[s] ?? 0)}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/** Annual TI per vehicle-year across the cohort's operating life, one line per scenario. */
function TrajectoryChart({ result }: { result: LifetimeResult }) {
  const series = SCENARIOS.map((s) => ({
    scenario: s,
    values: result.cohorts[s].annual_tCO2e,
  }));
  const horizon = Math.max(...series.map((s) => s.values.length));
  const all = series.flatMap((s) => s.values);
  const max = Math.max(...all, 0);
  const min = Math.min(...all, 0);
  const span = max - min || 1;
  const W = 560;
  const H = 220;
  const pad = { l: 8, r: 8, t: 12, b: 22 };
  const x = (i: number) => pad.l + (i / Math.max(horizon - 1, 1)) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - (v - min) / span) * (H - pad.t - pad.b);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="ti-trajectory" role="img"
      aria-label={`Annual trade impact for ${result.firm} over ${horizon} years, three scenarios`}>
      <line x1={pad.l} y1={y(0)} x2={W - pad.r} y2={y(0)} className="ti-axis" />
      <text x={pad.l} y={y(0) - 4} className="ti-axis-note">
        zero — product matches the destination benchmark
      </text>
      {series.map(({ scenario, values }) => (
        <polyline
          key={scenario}
          fill="none"
          stroke={SCENARIO_COLORS[scenario]}
          strokeWidth={2}
          points={values.map((v, i) => `${x(i)},${y(v)}`).join(" ")}
        />
      ))}
      {[0, Math.floor(horizon / 2), horizon - 1].map((i) => (
        <text key={i} x={x(i)} y={H - 6} textAnchor="middle" className="ti-axis-note">
          {`year ${i}`}
        </text>
      ))}
    </svg>
  );
}

function ScenarioHeadline({ result }: { result: LifetimeResult }) {
  const covered = result.coverage.covered_units;
  return (
    <div className="scenario-grid ti-headline">
      {SCENARIOS.map((s) => {
        const cohort = result.cohorts[s];
        return (
          <article
            key={s}
            className={`scenario-card${s === "S2" ? " central" : ""}`}
            style={{ ["--sc" as string]: SCENARIO_COLORS[s] }}
          >
            <div className="sc-label-row">
              <span className="sc-code">{s}</span>
              <span className="sc-label">{SCENARIO_LABELS[s]}</span>
            </div>
            <p className={`sc-value ${cohort.total_tCO2e >= 0 ? "pos" : "neg"}`}>
              {mt(cohort.total_tCO2e)}
              <small> MtCO₂e</small>
            </p>
            <p className="sc-sub">
              {kg((cohort.total_tCO2e * 1000) / covered)} kgCO₂e per vehicle ·{" "}
              {cohort.total_tCO2e >= 0 ? "contribution" : "carbon lock-in"}
            </p>
            {cohort.directional_only ? (
              <p className="ti-directional">
                Direction only — more than half the affected units rest on a proxied input, so
                the magnitude is not a reportable figure.
              </p>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

function SensitivityRange({ result }: { result: LifetimeResult }) {
  const sweep = result.sensitivity?.lifetime as
    | Record<string, Record<Scenario, number>>
    | undefined;
  if (!sweep) return null;
  return (
    <table className="ti-table">
      <caption>
        Operating life sensitivity. The horizon is bracketed by the observed mean fleet age, so
        the band is data, not a guess.
      </caption>
      <thead>
        <tr>
          <th scope="col">Pathway</th>
          <th scope="col">Short life (T−3)</th>
          <th scope="col">Central</th>
          <th scope="col">Long life (T+3)</th>
          <th scope="col">Sign stable</th>
        </tr>
      </thead>
      <tbody>
        {SCENARIOS.map((s) => {
          const lo = sweep.T_minus?.[s];
          const mid = sweep.T_central?.[s];
          const hi = sweep.T_plus?.[s];
          const signs = [lo, mid, hi].filter((v) => v != null).map((v) => Math.sign(v as number));
          const stable = new Set(signs).size === 1;
          return (
            <tr key={s}>
              <th scope="row">
                <span className="sc-code">{s}</span> {SCENARIO_LABELS[s]}
              </th>
              <td className="num">{lo == null ? "—" : `${mt(lo)} Mt`}</td>
              <td className="num">{mid == null ? "—" : `${mt(mid)} Mt`}</td>
              <td className="num">{hi == null ? "—" : `${mt(hi)} Mt`}</td>
              <td>{stable ? "yes" : "no — direction flips"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

type VktSweep = {
  status: string;
  proxied_destinations: string[];
  proxied_unit_share: number;
  central_km_per_year: number;
  low_km_per_year: number;
  high_km_per_year: number;
  low_distance: Record<Scenario, number>;
  high_distance: Record<Scenario, number>;
  sign_stable: Record<Scenario, boolean>;
  note: string;
};

function VktSensitivity({ result }: { result: LifetimeResult }) {
  const sweep = result.sensitivity?.vkt_proxy as VktSweep | undefined;
  if (!sweep || sweep.status !== "available") return null;
  return (
    <table className="ti-table">
      <caption>
        Distance sensitivity. {sweep.proxied_destinations.length} destinations (
        {pct(sweep.proxied_unit_share)} of covered units) publish no car traffic series and run
        on {count(sweep.central_km_per_year)} km/yr. The band is the lower and upper quartile of
        the distances member states actually measure — {count(sweep.low_km_per_year)}–
        {count(sweep.high_km_per_year)} km/yr. {sweep.note}
      </caption>
      <thead>
        <tr>
          <th scope="col">Pathway</th>
          <th scope="col">Short distance</th>
          <th scope="col">Central</th>
          <th scope="col">Long distance</th>
          <th scope="col">Sign stable</th>
        </tr>
      </thead>
      <tbody>
        {SCENARIOS.map((s) => (
          <tr key={s}>
            <th scope="row">
              <span className="sc-code">{s}</span> {SCENARIO_LABELS[s]}
            </th>
            <td className="num">{mt(sweep.low_distance[s])} Mt</td>
            <td className="num">{mt(result.cohorts[s].total_tCO2e)} Mt</td>
            <td className="num">{mt(sweep.high_distance[s])} Mt</td>
            <td>{sweep.sign_stable[s] ? "yes" : "no — direction flips"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function CohortSection({
  result,
  destinations,
}: {
  result: LifetimeResult;
  destinations: DestinationInput[];
}) {
  const covered = result.coverage.covered_units;
  const byCode = new Map(destinations.map((row) => [row.country_code, row]));

  const powertrains = [
    ...new Set(SCENARIOS.flatMap((s) => Object.keys(result.cohorts[s].by_powertrain))),
  ].sort();
  const powertrainRows: Row[] = powertrains.map((key) => ({
    key,
    label: POWERTRAIN_LABELS[key] ?? key,
    values: Object.fromEntries(
      SCENARIOS.map((s) => [s, result.cohorts[s].by_powertrain[key] ?? 0]),
    ) as Record<Scenario, number>,
  }));

  const destinationRows: Row[] = [
    ...new Set(SCENARIOS.flatMap((s) => Object.keys(result.cohorts[s].by_country))),
  ]
    .map((code) => ({
      key: code,
      label: code,
      values: Object.fromEntries(
        SCENARIOS.map((s) => [s, result.cohorts[s].by_country[code] ?? 0]),
      ) as Record<Scenario, number>,
    }))
    .sort((a, b) => Math.abs(b.values.S2) - Math.abs(a.values.S2))
    .slice(0, 12);

  return (
    <section className="ti-cohort" id={result.coverage.company_id}>
      <header className="ti-cohort-head">
        <div>
          <p className="eyebrow">{result.cohort_id}</p>
          <h2>
            {result.firm} · {result.cohort_year} EU27 cohort
          </h2>
          <p className="lede">
            {count(result.coverage.total_units)} first registrations. The lifetime result covers{" "}
            {pct(result.coverage.covered_share)} of them over a {result.data_quality.lifetime_T}
            -year units-weighted operating life, with each destination running on its own horizon.
          </p>
        </div>
      </header>

      <ScenarioHeadline result={result} />

      <div className="ti-panel">
        <h3>Which products carry the result</h3>
        <p className="muted">
          The decomposition is mandatory: TI_cohort equals the sum over destinations and the sum
          over product types
          {result.decomposition_identity_holds ? " — verified on this run." : " — IDENTITY FAILED."}
        </p>
        <DivergingBars
          rows={powertrainRows}
          unit="Mt"
          colorOf={(key) => POWERTRAIN_COLORS[key] ?? "var(--ink-3)"}
        />
      </div>

      <div className="ti-panel">
        <h3>Annual contribution over the operating life</h3>
        <p className="muted">
          Each line is the yearly gap between the destination fleet benchmark and this cohort. A
          line that starts above zero and crosses below it is a lock-in signal: the product was
          competitive at sale and stops being so as the benchmark tightens.
        </p>
        <TrajectoryChart result={result} />
      </div>

      <div className="ti-panel">
        <h3>Where the exposure sits</h3>
        <p className="muted">Top 12 destinations by national commitments (S2) exposure.</p>
        <DivergingBars rows={destinationRows} unit="Mt" height={18} />
        <details className="ti-details">
          <summary>Destination input quality</summary>
          <table className="ti-table">
            <thead>
              <tr>
                <th scope="col">Market</th>
                <th scope="col">Distance km/yr</th>
                <th scope="col">Fleet baseline gCO₂/km</th>
                <th scope="col">Grid gCO₂/kWh</th>
                <th scope="col">Life yr</th>
                <th scope="col">Worst tier</th>
              </tr>
            </thead>
            <tbody>
              {destinationRows.map((row) => {
                const d = byCode.get(row.key);
                if (!d) return null;
                const worst = [
                  d.vkt_tier,
                  d.fleet_intensity_tier,
                  d.grid_intensity_tier,
                  d.operating_lifetime_tier,
                ]
                  .filter(Boolean)
                  .sort()
                  .at(-1);
                return (
                  <tr key={row.key}>
                    <th scope="row">{row.key}</th>
                    <td className="num">{count(d.vkt_km_per_year ?? 0)}</td>
                    <td className="num">
                      {d.fleet_intensity_base_gco2_per_km?.toFixed(0) ?? "—"}
                    </td>
                    <td className="num">{d.grid_intensity_gco2_per_kwh?.toFixed(0) ?? "—"}</td>
                    <td className="num">
                      {d.operating_lifetime_years ?? "—"}{" "}
                      <small className="muted">
                        ({d.operating_lifetime_low_years}–{d.operating_lifetime_high_years})
                      </small>
                    </td>
                    <td>
                      <span className={`tier tier-${worst}`}>{worst}</span>{" "}
                      <small className="muted">{TIER_LABEL[worst ?? ""] ?? ""}</small>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </details>
      </div>

      <div className="ti-panel">
        <h3>How far the result can move</h3>
        <SensitivityRange result={result} />
        <VktSensitivity result={result} />
      </div>

      <div className="ti-panel ti-gaps">
        <h3>What is not in this number</h3>
        <ul>
          {Object.entries(result.coverage.withheld_product_types).map(([type, entry]) => (
            <li key={type}>
              <strong>
                {POWERTRAIN_LABELS[type] ?? type}: {count(entry.units)} units (
                {pct(entry.share)})
              </strong>{" "}
              withheld, not zeroed. {entry.reason}
            </li>
          ))}
          <li>
            Real-world correction applied once, at input build:{" "}
            {Object.entries(result.coverage.real_world_correction.factors)
              .map(([key, value]) => `${key} ×${value.toFixed(3)}`)
              .join(", ")}
            . {result.coverage.real_world_correction.note}
          </li>
          <li>
            Registrations are not mapped to production origin, so this is a destination-cohort
            impact and never an export claim.
          </li>
        </ul>
      </div>
    </section>
  );
}

export default function ImpactPage() {
  const results = getLifetimeResults();
  const readiness = getImpactReadiness();
  const destinations = getDestinationInputs();
  const meta = getMeta();
  const sources = getSources();
  const ordered = Object.values(results).sort(
    (a, b) => b.coverage.total_units - a.coverage.total_units,
  );
  const usedSourceIds = new Set(destinations.flatMap((row) => row.source_ids));
  const inputSources = sources.filter((row) => usedSourceIds.has(row.source_id));
  const pathwayWarning = destinations[0]?.warnings.find((w) =>
    w.startsWith("PATHWAY_ALREADY_MET"),
  );

  return (
    <main className="plain-report ti-impact">
      <section id="headline">
        <p className="eyebrow">Lifetime result · export-impact-v1</p>
        <h1>
          Both 2024 cohorts are already behind the trajectory their destination markets are on —
          and the gap widens with every step up in ambition.
        </h1>
        <p className="lede">
          Measured against the trend European car fleets are <em>actually</em> realising, each
          cohort is a net liability over its operating life. Measured against what those
          governments have committed to, the liability roughly triples; against a 1.5°C-aligned
          path it grows again by several times. The spread between the three is the policy-risk
          exposure, which is why they are published together and never separately.
        </p>
        <div className="ti-compare-strip">
          {ordered.map((result) => (
            <a key={result.cohort_id} href={`#${result.coverage.company_id}`}>
              <strong>{result.firm}</strong>
              <span>
                {SCENARIOS.map((s) => (
                  <em key={s} className={result.cohorts[s].total_tCO2e >= 0 ? "pos" : "neg"}>
                    {mt(result.cohorts[s].total_tCO2e, 1)}
                  </em>
                ))}
              </span>
              <small>S1 · S2 · S3, MtCO₂e</small>
            </a>
          ))}
        </div>
      </section>

      <section id="reading">
        <h2>Reading rules</h2>
        <ul className="ti-rules">
          <li>
            <strong>S1 — current policies.</strong> The destination&apos;s own observed trend in
            CO₂ per registered car, fitted 2015–2024 with the pandemic years dropped. An outturn,
            not a promise.
          </li>
          <li>
            <strong>S2 — national commitments.</strong> The EU domestic-transport pathway to 2030
            and the pro-rata power pathway. A regional proxy applied to every member state, which
            the record discloses rather than relabels as a country target.
          </li>
          <li>
            <strong>S3 — 1.5°C pathway.</strong> The recommended EU 2040 target of −90% against
            1990, pro-rated to transport and power.
          </li>
          <li>
            A positive number means the cohort emits less over its life than the destination
            benchmark it displaces. A negative number is carbon lock-in against that pathway.
          </li>
          <li>
            Trade Impact is an additional disclosure. It is never netted against Scope 3 Category
            11.
          </li>
        </ul>
        {pathwayWarning ? (
          <p className="ti-flag">
            <strong>Pathway flag.</strong> {pathwayWarning}
          </p>
        ) : null}
      </section>

      {ordered.map((result) => (
        <CohortSection key={result.cohort_id} result={result} destinations={destinations} />
      ))}

      <section id="provenance">
        <h2>Provenance</h2>
        <p className="muted">
          Every input above resolves to one of these snapshots. The dataset hash pins the whole
          published set; <code>check_published.py</code> recomputes it from the snapshots and
          fails if a single number drifts.
        </p>
        <ul className="ti-sources">
          {inputSources.map((source) => (
            <li key={source.source_id}>
              <a href={source.url} rel="noreferrer noopener" target="_blank">
                {source.title}
              </a>{" "}
              <small className="muted">
                {source.publisher} · accessed {source.accessed_date}
              </small>
            </li>
          ))}
        </ul>
        <p className="provenance mono">
          engine {meta.engine_version} · dataset {meta.dataset_sha256.slice(0, 16)} · readiness{" "}
          {readiness.map((row) => `${row.cohort_id}=${row.status}`).join(", ")}
        </p>
        <p>
          <Link href="/compare/automotive">See the observed cohort behind these numbers →</Link>
        </p>
      </section>
    </main>
  );
}
