import type { Metadata } from "next";
import Link from "next/link";
import ScenarioCards from "@/components/ScenarioCards";
import { getCountryView, getCountryViews } from "@/lib/country";
import { getMeta, SCENARIOS } from "@/lib/data";

export function generateStaticParams() {
  return getCountryViews().map((v) => ({ code: v.code }));
}
export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ code: string }>;
}): Promise<Metadata> {
  const { code } = await params;
  return { title: `${getCountryView(code)?.name ?? code} — NDC impact by firm` };
}

export default async function CountryPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const v = getCountryView(code)!;
  const meta = getMeta();
  const isFlag = v.benchmarkStatus !== "COMPUTED";

  return (
    <main>
      <p className="eyebrow">Operating-country view · cohort 2024</p>
      <h1>
        {v.name} <span style={{ color: "var(--ink-3)" }}>· {v.code}</span>
      </h1>
      <p className="lede">
        Each firm's net effect on {v.name}&apos;s NDC-committed decarbonisation path —
        positive contributes to the commitment, negative is carbon lock-in against it.
      </p>

      {isFlag ? (
        <div className="declaration" style={{ marginTop: 20 }}>
          <h3>No S2 benchmark derivable</h3>
          <p className="panel-note">
            {v.flagReason ?? v.benchmarkStatus} — excluded from every firm&apos;s S2
            headline (NOTES.md D3). S1 (current policies) and S3 (NZE) are still computed
            where rates are supplied.
          </p>
        </div>
      ) : (
        v.warnings.length > 0 && (
          <p className="panel-note" style={{ marginTop: 16 }}>
            <span className="warn-item">{v.warnings[0]}</span>
          </p>
        )
      )}
      {v.source && (
        <p className="panel-note" style={{ marginTop: 8 }}>
          Benchmark source: {v.source}
        </p>
      )}

      {v.firms.map((f) => (
        <section key={f.slug}>
          <h2>
            <Link href={`/report/${f.slug}`}>{f.firm}</Link>
          </h2>
          {f.excludedS2Reason && (
            <p className="panel-note">
              S2: excluded — {f.excludedS2Reason}. S1/S3 shown where computed.
            </p>
          )}
          <ScenarioCards totals={f.byScenario} unit={`tCO₂e in ${v.code} · cohort lifetime`} />
          {f.crossover.length > 0 && (
            <details className="table-view">
              <summary>Per-vehicle crossover in {v.code}</summary>
              <div className="table-scroll" style={{ marginTop: 8 }}>
                <table>
                  <thead>
                    <tr>
                      <th>Powertrain</th>
                      <th>Scenario</th>
                      <th className="num">t* (yr)</th>
                      <th className="num">TI / vehicle (kgCO₂e)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {f.crossover.map((c, i) => (
                      <tr key={i}>
                        <td className="mono">{c.powertrain}</td>
                        <td className="mono">{c.scenario}</td>
                        <td className="num">
                          {c.crossover_year === null ? "—" : c.crossover_year.toFixed(1)}
                        </td>
                        <td className="num">
                          {(c as { TI_per_vehicle_kgCO2e?: number }).TI_per_vehicle_kgCO2e?.toLocaleString(
                            "en-US",
                            { maximumFractionDigits: 0 },
                          ) ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </section>
      ))}

      <p className="panel-note" style={{ marginTop: 40 }}>
        Firm values are comparative metrics against {v.name}&apos;s shared benchmark and
        are <strong>not summed across firms</strong> — individual TI claims do not
        physically add up to a sector-level change (Whitepaper §9.2).
      </p>

      <div className="provenance">
        engine {meta.engine_version} @ {meta.engine_git_sha.slice(0, 10)} · {meta.workbook} ·
        built {meta.build_date.slice(0, 10)}
      </div>
    </main>
  );
}
