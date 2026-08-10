// Renderers for one published lifetime result. Shared by the combined /impact report and the
// per-company /analysis/[firm] report so a cohort is presented identically wherever it appears.
// Types come from lib/shared (no node imports) — the engine emitter stays the source of truth.
import { CellScatter, type CellDomain } from "@/components/cell-scatter";
import {
  SCENARIOS,
  SCENARIO_COLORS,
  SCENARIO_LABELS,
  type DestinationInput,
  type LifetimeResult,
  type Scenario,
} from "@/lib/shared";

export const POWERTRAIN_LABELS: Record<string, string> = {
  BEV: "Battery electric",
  HEV: "Hybrid (non-plug-in)",
  ICE: "Combustion",
  PHEV: "Plug-in hybrid",
  FCEV: "Fuel cell",
};
export const POWERTRAIN_COLORS: Record<string, string> = {
  BEV: "#5d9cec",
  HEV: "#d9a441",
  ICE: "#ef7b5e",
  PHEV: "#36bfa0",
  FCEV: "#9d7bea",
};
export const TIER_LABEL: Record<string, string> = {
  A: "official primary",
  B: "official, older vintage or wider concept",
  C: "proxy — pooled or EU-average stand-in",
};

export function mt(value: number, digits = 2): string {
  return `${value >= 0 ? "+" : "−"}${Math.abs(value / 1e6).toFixed(digits)}`;
}
export function kg(value: number): string {
  return `${value >= 0 ? "+" : "−"}${Math.abs(value).toLocaleString("en-US", {
    maximumFractionDigits: 0,
  })}`;
}
export function count(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
}
export function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export type Row = { key: string; label: string; values: Record<Scenario, number> };

/** Grouped bars around a zero axis. One row per key, one bar per scenario. */
export function DivergingBars({
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
export function TrajectoryChart({ result }: { result: LifetimeResult }) {
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

/** Benchmark against product, per surviving vehicle. The crossing is the lock-in signal. */
export function CrossingChart({
  result,
  scenario,
}: {
  result: LifetimeResult;
  scenario: Scenario;
}) {
  const series = result.trajectory.scenarios[scenario];
  const points = series.benchmark.length;
  const values = [...series.benchmark, ...series.product].filter(
    (v): v is number => v != null,
  );
  const max = Math.max(...values, 1);
  const W = 320;
  const HGT = 150;
  const pad = { l: 6, r: 6, t: 16, b: 18 };
  const x = (i: number) => pad.l + (i / Math.max(points - 1, 1)) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - v / max) * (HGT - pad.t - pad.b);
  const line = (arr: (number | null)[]) =>
    arr.map((v, i) => (v == null ? null : `${x(i)},${y(v)}`)).filter(Boolean).join(" ");
  const crossing = series.benchmark.findIndex(
    (b, i) => b != null && series.product[i] != null && b < (series.product[i] as number),
  );

  return (
    <figure className="ti-crossing">
      <figcaption>
        <span className="sc-code">{scenario}</span> {SCENARIO_LABELS[scenario]}
        {crossing >= 0 ? <em> · crosses in year {crossing}</em> : <em> · never crosses</em>}
      </figcaption>
      <svg viewBox={`0 0 ${W} ${HGT}`} role="img"
        aria-label={`${SCENARIO_LABELS[scenario]}: destination benchmark against the cohort's own emissions per surviving vehicle`}>
        <line x1={pad.l} y1={HGT - pad.b} x2={W - pad.r} y2={HGT - pad.b} className="ti-axis" />
        {crossing >= 0 ? (
          <line x1={x(crossing)} y1={pad.t} x2={x(crossing)} y2={HGT - pad.b}
            stroke="var(--accent)" strokeWidth={1} strokeDasharray="3 3" />
        ) : null}
        <polyline points={line(series.benchmark)} fill="none" stroke={SCENARIO_COLORS[scenario]}
          strokeWidth={2.2} />
        <polyline points={line(series.product)} fill="none" stroke="var(--neg)" strokeWidth={1.8}
          strokeDasharray="5 3" />
      </svg>
    </figure>
  );
}

export function ScenarioHeadline({ result }: { result: LifetimeResult }) {
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

export function SensitivityRange({ result }: { result: LifetimeResult }) {
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

export function VktSensitivity({ result }: { result: LifetimeResult }) {
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

/** Ranked decomposition rows. `by_country` and `by_powertrain` are the mandatory split. */
export function decompositionRows(
  result: LifetimeResult,
  axis: "by_country" | "by_powertrain",
  limit?: number,
): Row[] {
  const keys = [...new Set(SCENARIOS.flatMap((s) => Object.keys(result.cohorts[s][axis])))];
  const rows = keys.map((key) => ({
    key,
    label: axis === "by_powertrain" ? POWERTRAIN_LABELS[key] ?? key : key,
    values: Object.fromEntries(
      SCENARIOS.map((s) => [s, result.cohorts[s][axis][key] ?? 0]),
    ) as Record<Scenario, number>,
  }));
  if (axis === "by_powertrain") return rows.sort((a, b) => a.key.localeCompare(b.key));
  const ranked = rows.sort((a, b) => Math.abs(b.values.S2) - Math.abs(a.values.S2));
  return limit == null ? ranked : ranked.slice(0, limit);
}

export function CohortSection({
  result,
  destinations,
  cellDomain,
}: {
  result: LifetimeResult;
  destinations: DestinationInput[];
  /** Supplied when more than one cohort is on the page, so the scatters share a scale. */
  cellDomain?: CellDomain;
}) {
  const byCode = new Map(destinations.map((row) => [row.country_code, row]));
  const powertrainRows = decompositionRows(result, "by_powertrain");
  const destinationRows = decompositionRows(result, "by_country", 12);

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
            {pct(result.coverage.covered_share)} of them over a units-weighted operating life of{" "}
            {result.data_quality.lifetime_T} years, with each destination running on its own
            horizon.
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
        <h3>Why the gap opens</h3>
        <p className="muted">
          The solid line is the destination fleet benchmark the cohort is measured against; the
          dashed line is what the cohort itself emits, fixed at its sale-year efficiency and
          corrected to real world. Both are per surviving vehicle, so retirement does not
          masquerade as decarbonisation. The marker is the year the benchmark passes below the
          product — everything after it is lock-in against that pathway.
        </p>
        <div className="ti-crossing-row">
          {SCENARIOS.map((s) => (
            <CrossingChart key={s} result={result} scenario={s} />
          ))}
        </div>
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
        <h3>Which market-and-powertrain combinations carry it</h3>
        <p className="muted">
          The two decompositions above are margins: they say which destinations matter and which
          products matter, but not which pairing of the two does. This is the joint. A cell far
          to the right sells in volume; a cell far below the line emits far above the benchmark
          it is measured against; a cell that is both is where the result actually comes from.
        </p>
        <CellScatter result={result} domain={cellDomain} />
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

/**
 * Guideline §5.3 data-quality declaration — the block a reporting team files alongside the
 * headline. Every field is read from the engine's own DataQuality payload, so it cannot drift
 * from the run that produced the numbers above it.
 */
export function DataQualityDeclaration({ result }: { result: LifetimeResult }) {
  const dq = result.data_quality;
  // A per-key dump runs to dozens of model names and hides the signal. The tier mix is what
  // §5.3 is asking for; the full per-key list stays one click away rather than being dropped.
  const tierRow = (label: string, tiers: Record<string, string>) => {
    const entries = Object.entries(tiers).sort(([a], [b]) => a.localeCompare(b));
    const mix = new Map<string, number>();
    for (const [, tier] of entries) mix.set(tier, (mix.get(tier) ?? 0) + 1);
    return (
      <tr key={label}>
        <th scope="row">{label}</th>
        <td>
          {entries.length === 0 ? (
            "—"
          ) : (
            <>
              {[...mix.entries()]
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([tier, n]) => `${n} × tier ${tier}`)
                .join(" · ")}{" "}
              <span className="muted">({entries.length} keys)</span>
              <details className="ti-details">
                <summary>Per-key tiers</summary>
                <p className="mono">
                  {entries.map(([key, tier]) => `${key}: ${tier}`).join(" · ")}
                </p>
              </details>
            </>
          )}
        </td>
      </tr>
    );
  };
  return (
    <div className="ti-panel ti-declaration">
      <h3>Data-quality declaration</h3>
      <p className="muted">
        Required with every reported TI output (Automotive Technical Guideline §5.3, Whitepaper
        §5.2). Emitted by the engine run, not written by hand.
      </p>
      <table className="ti-table">
        <tbody>
          <tr>
            <th scope="row">Firm · cohort year</th>
            <td>
              {dq.firm} · {dq.cohort_year}
            </td>
          </tr>
          <tr>
            <th scope="row">Analysis level</th>
            <td>
              {dq.analysis_level} — operating-country basis. Production-country attribution
              (Level 2) needs a factory-to-market volume matrix that is not disclosed.
            </td>
          </tr>
          <tr>
            <th scope="row">Layer 1 method</th>
            <td>Method {dq.layer1_method} — destination pathway trajectory</td>
          </tr>
          <tr>
            <th scope="row">Operating life T</th>
            <td>
              {dq.lifetime_T ?? "—"} years units-weighted, sensitivity ±{dq.lifetime_sens}
            </td>
          </tr>
          {tierRow("Benchmark tiers", dq.benchmark_tiers)}
          {tierRow("Product tiers", dq.layer2_tiers)}
          {tierRow("Volume tiers", dq.volume_tiers)}
          <tr>
            <th scope="row">Output type</th>
            <td>
              Single cohort. {result.portfolio_withheld?.reason ?? "Rolling portfolio published."}
            </td>
          </tr>
          <tr>
            <th scope="row">Missing inputs</th>
            <td>{dq.missing_inputs.length === 0 ? "none" : dq.missing_inputs.join("; ")}</td>
          </tr>
        </tbody>
      </table>
      <div className="ti-scenario-sources">
        {SCENARIOS.map((s) => (
          <p key={s}>
            <span className="sc-code">{s}</span> <strong>{SCENARIO_LABELS[s]}</strong> —{" "}
            {dq.scenario_sources?.[s] ?? "source not recorded"}
          </p>
        ))}
      </div>
      {dq.warnings.length ? (
        <ul className="ti-warnings">
          {dq.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
      <p className="ti-flag">
        <strong>Separation from Scope 3.</strong> Trade Impact is an additional disclosure. It is
        never netted against, and never reduces, Scope 3 Category 11 absolute emissions.
      </p>
    </div>
  );
}
