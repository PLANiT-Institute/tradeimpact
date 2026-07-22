import Link from "next/link";
import GapHero from "@/components/GapHero";
import { getFirms, getMeta } from "@/lib/data";

export default function Home() {
  const firms = getFirms();
  const meta = getMeta();
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

      <h2>TI case-study firms</h2>
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
                {f.runnable ? (f.illustrative ? "REPORT · illustrative" : "REPORT") : "awaiting data"}
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
