import type { Metadata } from "next";
import Link from "next/link";
import { getCountryView, getCountryViews } from "@/lib/country";
import { getMeta, SCENARIO_LABELS, SCENARIOS } from "@/lib/data";

export function generateStaticParams() {
  return getCountryViews().map((country) => ({ code: country.code }));
}
export const dynamicParams = false;

export async function generateMetadata({ params }: { params: Promise<{ code: string }> }): Promise<Metadata> {
  const { code } = await params;
  return { title: `${getCountryView(code)?.name ?? code} — benchmark evidence` };
}

export default async function CountryPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const country = getCountryView(code)!;
  const meta = getMeta();
  const isFlag = country.benchmarkStatus !== "COMPUTED";

  return (
    <main>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/#markets">Operating-country evidence</Link><span>/</span><span>{country.name}</span>
      </nav>
      <header className="report-header country-header">
        <div>
          <p className="eyebrow">Source-backed benchmark record</p>
          <div className="title-row">
            <h1>{country.name} <span className="country-title-code">{country.code}</span></h1>
            <span className={`status-pill ${isFlag ? "estimated" : "verified"}`}>
              {isFlag ? "Benchmark flagged" : "Benchmark available"}
            </span>
          </div>
          <p className="lede">
            This page reports the workbook-backed national benchmark inputs only. It does
            not estimate a company fleet, vehicle lifetime total, or historical trend.
          </p>
        </div>
      </header>

      <dl className="market-summary">
        <div><dt>NDC benchmark</dt><dd>{isFlag ? "Not derivable" : "Computed"}</dd></div>
        <div><dt>Company assessments</dt><dd>Not published</dd></div>
        <div><dt>Grid intensity</dt><dd>{country.gridIntensity === undefined ? "—" : `${(country.gridIntensity * 1000).toFixed(0)} gCO₂/kWh`}</dd></div>
        <div><dt>Evidence tier</dt><dd>{isFlag ? "Flagged" : "Workbook status"}</dd></div>
      </dl>

      {isFlag && (
        <div className="declaration" style={{ marginTop: 20 }}>
          <h3>No absolute NDC benchmark is published</h3>
          <p className="panel-note">{country.flagReason ?? country.benchmarkStatus}</p>
        </div>
      )}

      {country.warnings.length > 0 && (
        <ul className="panel-note" style={{ marginTop: 16 }}>
          {country.warnings.map((warning) => <li className="warn-item" key={warning}>{warning}</li>)}
        </ul>
      )}

      <section className="simple-report-section">
        <p className="eyebrow">Published fields</p>
        <h2>Transport and power pathways</h2>
        <div className="table-scroll">
          <table>
            <thead><tr><th>Scenario</th><th className="num">Fleet (%/yr)</th><th className="num">Power (%/yr)</th></tr></thead>
            <tbody>
              {SCENARIOS.map((scenario) => {
                const key = scenario.toLowerCase();
                const fleet = country.rFleet[key];
                const power = country.rPower[key];
                return <tr key={scenario}>
                  <td>{SCENARIO_LABELS[scenario]}</td>
                  <td className="num">{fleet === undefined ? "—" : (fleet * 100).toFixed(2)}</td>
                  <td className="num">{power === undefined ? "—" : (power * 100).toFixed(2)}</td>
                </tr>;
              })}
            </tbody>
          </table>
        </div>
        <p className="plain-footnote">
          Empty fields remain empty. S2 may be an economy-wide pro-rata derivation where the
          workbook warning says so; it is not presented as an observed transport-sector rate.
        </p>
      </section>

      {country.source && (
        <section className="simple-report-section">
          <p className="eyebrow">Provenance</p><h2>Workbook source record</h2>
          <p className="panel-note">{country.source}</p>
        </section>
      )}

      <div className="provenance">
        engine {meta.engine_version} #{meta.engine_source_sha256.slice(0, 12)} · dataset {meta.dataset_sha256.slice(0, 12)} · {meta.workbook} #{meta.workbook_sha256.slice(0, 12)}
      </div>
    </main>
  );
}
