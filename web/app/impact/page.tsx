import type { Metadata } from "next";
import Link from "next/link";
import {
  SCENARIOS,
  getDestinationInputs,
  getImpactReadiness,
  getLifetimeResults,
  getMeta,
  getSources,
} from "@/lib/data";
import { CohortSection, mt } from "@/components/cohort-report";

export const metadata: Metadata = {
  title: "Lifetime impact of the 2024 EU27 cohorts — Trade Impact",
  description:
    "Toyota and Hyundai 2024 EU27 passenger-car cohorts scored against three destination pathways, decomposed by product type and destination market.",
};

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
          <Link href="/analysis/toyota">Toyota company report →</Link>{" "}
          <Link href="/analysis/hyundai">Hyundai company report →</Link>{" "}
          <Link href="/compare/automotive">See the observed cohort behind these numbers →</Link>
        </p>
      </section>
    </main>
  );
}
