import Link from "next/link";

export const metadata = { title: "Trade Impact Calculator — evidence gate" };

export default function CalculatorPage() {
  return (
    <main>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/">Trade Impact</Link><span>/</span><span>Calculator</span>
      </nav>
      <header className="lab-header">
        <div>
          <p className="eyebrow">Evidence gate</p>
          <h1>Calculator template withheld</h1>
          <p className="lede">
            The previous calculator started from estimated Toyota, Hyundai, or illustrative
            vehicle data. Those templates have been removed. A public calculator will return
            when it can start from a complete source-backed input set.
          </p>
        </div>
      </header>
      <div className="declaration">
        <h3>Required before calculation</h3>
        <p className="panel-note">
          Country/year/model/powertrain registration units, exact certification mapping,
          fleet baseline intensity, annual distance, vehicle lifetime, and scenario-specific
          transport and power pathways.
        </p>
      </div>
    </main>
  );
}
