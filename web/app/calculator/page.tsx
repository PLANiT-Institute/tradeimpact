import Calculator from "@/components/Calculator";
import { getCalculatorFirm, getFirmResult } from "@/lib/data";
import Link from "next/link";

export const metadata = { title: "NDC impact lab — Trade Impact" };

export default async function CalculatorPage({
  searchParams,
}: {
  searchParams: Promise<{ firm?: string }>;
}) {
  const { firm } = await searchParams;
  const selectedFirm = getCalculatorFirm(firm);
  const slug = selectedFirm.slug;
  const template = getFirmResult(slug).inputs;

  return (
    <main>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/#assessments">Company assessments</Link><span>/</span><span>NDC impact lab</span>
      </nav>
      <header className="lab-header">
        <div>
          <p className="eyebrow">Interactive · NDC impact sensitivity</p>
          <h1>NDC impact lab</h1>
          <p className="lede">
            Change the represented sales mix, product emissions or country assumptions
            behind the {getFirmResult(slug).firm} case. See how the {getFirmResult(slug).cohort_year}{" "}
            sales cohort contributes to or locks in emissions against national NDC commitments.
          </p>
        </div>
        <div className="lab-scope">
          <span>{selectedFirm.illustrative ? "Illustrative validation case" : "Working assessment"}</span>
          <strong>{getFirmResult(slug).firm}</strong>
          <Link href={`/report/${slug}`}>
            Return to {selectedFirm.illustrative ? "validation report" : "published assessment"} →
          </Link>
        </div>
      </header>
      <div className="lab-guidance" role="note">
        <strong>The NDC result is the core metric.</strong>
        <span>Current-policy and 1.5°C pathways are sensitivity cases. Adjust one assumption at a time, then return to the published assessment for sources and coverage.</span>
      </div>
      <Calculator template={template as never} />
    </main>
  );
}
