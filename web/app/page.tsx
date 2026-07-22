import Link from "next/link";
import GapHero from "@/components/GapHero";
import { getCountryViews } from "@/lib/country";
import { fmtTI, getFirmResult, getFirms, getMeta, SCENARIOS } from "@/lib/data";

function FirmTable() {
  const rows = getFirms()
    .filter((f) => f.runnable && !f.illustrative)
    .map((f) => ({ f, r: getFirmResult(f.slug) }));
  return (
    <div className="panel table-scroll">
      <table>
        <thead>
          <tr>
            <th>Firm</th>
            <th>Markets</th>
            <th className="num">S1 STEPS</th>
            <th className="num">S2 NDC (headline)</th>
            <th className="num">S3 NZE</th>
            <th>Direction (S2)</th>
            <th>Basis</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ f, r }) => {
            const excl = Object.keys(r.cohorts.S2?.excluded_flag_markets ?? {});
            const markets = new Set<string>();
            for (const s of SCENARIOS)
              for (const c of Object.keys(r.cohorts[s]?.by_country ?? {})) markets.add(c);
            const s2 = r.cohorts.S2?.total_tCO2e;
            return (
              <tr key={f.slug}>
                <td>
                  <Link href={`/report/${f.slug}`}>
                    <strong>{r.firm}</strong>
                  </Link>
                </td>
                <td className="mono" style={{ fontSize: 12.5 }}>
                  {[...markets].join(" ")}
                  {excl.length > 0 && (
                    <span style={{ color: "var(--ink-3)" }}> (S2 excl. {excl.join(" ")})</span>
                  )}
                </td>
                {SCENARIOS.map((s) => (
                  <td className="num" key={s}>
                    {r.cohorts[s] ? fmtTI(r.cohorts[s].total_tCO2e) : "—"}
                  </td>
                ))}
                <td>
                  <span className={`direction-chip ${(s2 ?? 0) >= 0 ? "pos" : "neg"}`}>
                    {(s2 ?? 0) >= 0 ? "net contribution" : "net lock-in liability"}
                  </span>
                </td>
                <td style={{ fontSize: 13, color: "var(--ink-3)" }}>
                  {f.basis === "estimated" ? "Tier B/C estimates" : "collected"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="panel-note" style={{ marginTop: 10 }}>
        tCO₂e over the 2024 cohort&apos;s lifetime. Values are per-firm comparisons
        against shared benchmarks — not summable across firms (Whitepaper §9.2).
      </p>
    </div>
  );
}

export default function Home() {
  const firms = getFirms();
  const meta = getMeta();
  const countries = getCountryViews();
  const ti = firms.filter((f) => f.project === "TI");
  const cap = firms.filter((f) => f.project === "CAP");

  return (
    <main>
      <section className="hero">
        <div>
          <p className="eyebrow">Firm-level climate direction</p>
          <h1>Does this product help — or lock in emissions?</h1>
          <p className="lede">
            For every product a firm sells, in every country it operates in, in every year
            of the product's life, the Trade Impact framework asks one question: does it
            emit more or less than what the operating country committed to under its NDC?
            The gap, summed over lifetimes and weighted by sales, is the TI score.
          </p>
        </div>
        <GapHero />
      </section>

      <div className="provenance">
        engine {meta.engine_version} @ {meta.engine_git_sha.slice(0, 10)} · {meta.workbook} (
        {meta.workbook_sha256}) · built {meta.build_date.slice(0, 10)} ·{" "}
        {meta.collection_status.missing_inputs.length} inputs still to collect
      </div>

      <h2>Firm assessments</h2>
      <p className="panel-note">
        The core output: each firm evaluated on the data available today, against every
        operating country&apos;s committed path. FLAG markets (no derivable NDC benchmark)
        are excluded from the S2 headline, never silently defaulted.
      </p>
      <FirmTable />

      <h3 style={{ marginTop: 36 }}>All case-study candidates</h3>
      <p className="panel-note">
        Firms marked <span className="mono">awaiting data</span> have no collected
        registration or vehicle-parameter data yet — the framework never fabricates a
        missing input, so no score is shown until collection lands (see the data
        pipeline's collection status).
      </p>
      <div className="firm-grid">
        {ti.map((f) => {
          const inner = (
            <>
              <div className="fc-name">{f.name}</div>
              <div className="fc-sub">
                {f.sector} · {f.country}
              </div>
              <div className={`fc-state ${f.runnable ? "ready" : "waiting"}`}>
                {f.runnable
                  ? f.illustrative
                    ? "REPORT · illustrative"
                    : f.basis === "estimated"
                      ? "REPORT · estimated"
                      : "REPORT"
                  : "awaiting data"}
              </div>
            </>
          );
          return f.runnable ? (
            <Link className="firm-card" href={`/report/${f.slug}`} key={f.slug}>
              {inner}
            </Link>
          ) : (
            <div className="firm-card" key={f.slug}>
              {inner}
            </div>
          );
        })}
      </div>

      <h2>By operating country</h2>
      <p className="panel-note">
        The country-first read: each firm&apos;s net effect on that country&apos;s
        NDC-committed path, side by side (never summed — Whitepaper §9.2).
      </p>
      <div className="firm-grid">
        {countries.map((c) => (
          <Link className="firm-card" href={`/country/${c.code}`} key={c.code}>
            <div className="fc-name">
              {c.name} <span className="mono" style={{ color: "var(--ink-3)" }}>{c.code}</span>
            </div>
            <div className="fc-sub">
              {c.firms.length} firm{c.firms.length > 1 ? "s" : ""} assessed
            </div>
            <div className={`fc-state ${c.benchmarkStatus === "COMPUTED" ? "ready" : "waiting"}`}>
              {c.benchmarkStatus === "COMPUTED" ? "NDC BENCHMARK" : "FLAG — no S2 benchmark"}
            </div>
          </Link>
        ))}
      </div>

      <h2>CAP candidates (separate project)</h2>
      <p className="panel-note">
        Steel and petrochemical candidates from the Capital Allocation Pathway draft —
        carried in the same universe for one canonical firm list; no TI sector guideline
        exists for these yet.
      </p>
      <div className="firm-grid">
        {cap.map((f) => (
          <div className="firm-card" key={f.slug}>
            <div className="fc-name">{f.name}</div>
            <div className="fc-sub">
              {f.sector} · {f.country} {f.ticker ? `· ${f.ticker}` : ""}
            </div>
            <div className="fc-state waiting">awaiting data</div>
          </div>
        ))}
      </div>
    </main>
  );
}
