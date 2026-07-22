import type { Metadata } from "next";
import Link from "next/link";
import AnnualLines from "@/components/AnnualLines";
import DecompBars from "@/components/DecompBars";
import ScenarioCards from "@/components/ScenarioCards";
import { getFirmResult, getFirms, SCENARIOS, type Scenario } from "@/lib/data";

export function generateStaticParams() {
  return getFirms()
    .filter((f) => f.runnable)
    .map((f) => ({ firm: f.slug }));
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
  const firms = getFirms();
  const meta = firms.find((f) => f.slug === firm);
  const r = getFirmResult(firm);
  const dq = r.data_quality;

  const totals = Object.fromEntries(
    SCENARIOS.filter((s) => r.cohorts[s]).map((s) => [s, r.cohorts[s].total_tCO2e]),
  ) as Partial<Record<Scenario, number>>;
  const annual = Object.fromEntries(
    SCENARIOS.filter((s) => r.cohorts[s]).map((s) => [s, r.cohorts[s].annual_tCO2e]),
  ) as Partial<Record<Scenario, number[]>>;
  const s2 = r.cohorts.S2 ?? r.cohorts.S1 ?? r.cohorts.S3;

  return (
    <main>
      <p className="eyebrow">TI report · single cohort {r.cohort_year} · {dq.analysis_level}</p>
      <h1>{r.firm}</h1>
      {meta?.illustrative && (
        <p className="panel-note">
          <strong>Illustrative case.</strong> {meta.note} Engine arithmetic is validated to
          ±1% against an independent hand calculation; the inputs are not real-firm data.
        </p>
      )}
      {meta?.basis === "estimated" && (
        <p className="panel-note">
          <strong>Estimated inputs.</strong> {meta.note}
        </p>
      )}

      <ScenarioCards
        totals={totals}
        unit="tCO₂e · cohort lifetime"
        directionalOnly={Object.fromEntries(
          SCENARIOS.filter((s) => r.cohorts[s]).map((s) => [s, r.cohorts[s].directional_only]),
        )}
      />
      <p className="panel-note">
        Positive = the cohort emits less over its lifetime than the operating countries'
        NDC-committed benchmarks (a contribution). Negative = net carbon lock-in liability.
        The S1–S3 spread is the policy-risk exposure.
      </p>

      <h2>Annual TI flow, t = 0 … T−1</h2>
      <div className="panel">
        <AnnualLines series={annual} xLabel="t" yLabel="tCO₂e / yr" />
      </div>

      {Object.keys(r.portfolio ?? {}).length > 0 && (
        <>
          <h2>Rolling portfolio TI</h2>
          <div className="panel">
            <AnnualLines
              series={r.portfolio as Partial<Record<Scenario, number[]>>}
              xLabel="year index"
              yLabel="tCO₂e / yr"
            />
          </div>
        </>
      )}

      <h2>Decomposition — mandatory</h2>
      <div className="panel">
        <h3>By operating country (S2)</h3>
        <DecompBars data={s2.by_country} unit="tCO₂e" />
        <h3>By powertrain (S2)</h3>
        <DecompBars data={s2.by_powertrain} unit="tCO₂e" />
        <p className="panel-note">
          Identity: TI_cohort = Σ countries = Σ powertrains, per scenario. Headline numbers
          without this decomposition are insufficient (Whitepaper §3.6).
        </p>
      </div>

      <h2>Crossover t*</h2>
      <div className="panel table-scroll">
        <table>
          <thead>
            <tr>
              <th>Country</th>
              <th>Powertrain</th>
              <th>Scenario</th>
              <th className="num">t* (yr since sale)</th>
              <th className="num">TI / vehicle (kgCO₂e)</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {r.crossover.map((c, i) => (
              <tr key={i}>
                <td className="mono">{c.country}</td>
                <td className="mono">{c.powertrain}</td>
                <td className="mono">{c.scenario}</td>
                <td className="num">{c.crossover_year === null ? "—" : c.crossover_year.toFixed(1)}</td>
                <td className="num">{cum(r, c)}</td>
                <td style={{ fontSize: 13, color: "var(--ink-3)" }}>{c.reason ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Data-quality declaration</h2>
      <div className="declaration">
        <h3>Benchmark tiers (Layer 1)</h3>
        <div>
          {Object.entries(dq.benchmark_tiers).map(([c, t]) => (
            <span className="tier-chip" key={c}>
              {c} · Tier {t}
            </span>
          ))}
        </div>
        <h3>Layer 2 tiers</h3>
        <div>
          {Object.entries(dq.layer2_tiers).length ? (
            Object.entries(dq.layer2_tiers).map(([c, t]) => (
              <span className="tier-chip" key={c}>
                {c} · Tier {t}
              </span>
            ))
          ) : (
            <span className="panel-note">(none collected)</span>
          )}
        </div>
        <h3>Lifetime & scenarios</h3>
        <p className="panel-note">
          Vehicle lifetime T = {dq.lifetime_T} yr (± {dq.lifetime_sens} yr sensitivity) ·
          Layer 1 method {dq.layer1_method}.
        </p>
        <ul>
          {Object.entries(dq.scenario_sources).map(([k, v]) => (
            <li key={k} className="mono" style={{ fontSize: 13 }}>
              {k}: {v}
            </li>
          ))}
        </ul>
        {Object.keys(dq.flag_markets).length > 0 && (
          <>
            <h3>FLAG markets — excluded from the S2 headline</h3>
            <ul>
              {Object.entries(dq.flag_markets).map(([c, reason]) => (
                <li key={c} className="missing-item">
                  {c}: {reason}
                </li>
              ))}
            </ul>
          </>
        )}
        {dq.missing_inputs.length > 0 && (
          <>
            <h3>Missing inputs (not fabricated)</h3>
            <ul>
              {dq.missing_inputs.map((m) => (
                <li key={m} className="missing-item">
                  {m}
                </li>
              ))}
            </ul>
          </>
        )}
        {dq.warnings.length > 0 && (
          <>
            <h3>Warnings</h3>
            <ul>
              {dq.warnings.map((w) => (
                <li key={w} className="warn-item">
                  {w}
                </li>
              ))}
            </ul>
          </>
        )}
        <p className="panel-note" style={{ marginTop: 16 }}>
          TI is a separate additional disclosure and is never netted against Scope 3
          Category 11.
        </p>
      </div>

      <div className="provenance">
        engine {r.provenance.engine_version} @ {r.provenance.engine_git_sha.slice(0, 10)} ·{" "}
        {r.provenance.workbook} · built {r.provenance.build_date.slice(0, 10)}
      </div>

      <p style={{ marginTop: 28 }}>
        <Link href={`/calculator?firm=${firm}`}>Open this case in the calculator →</Link>
      </p>
    </main>
  );
}

function cum(r: ReturnType<typeof getFirmResult>, c: { country: string; powertrain: string; scenario: string }): string {
  // per-vehicle cumulative isn't in the crossover block; look it up from sensitivity-free
  // vehicle results embedded in crossover rows when present
  const anyC = c as { TI_per_vehicle_kgCO2e?: number };
  return anyC.TI_per_vehicle_kgCO2e === undefined
    ? "—"
    : anyC.TI_per_vehicle_kgCO2e.toLocaleString("en-US", { maximumFractionDigits: 0 });
}
