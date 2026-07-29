import Calculator from "@/components/Calculator";
import { getCalculatorFirm, getFirmResult } from "@/lib/data";
import Link from "next/link";

export const metadata = { title: "Trade Impact Calculator" };

export default async function CalculatorPage({
  searchParams,
}: {
  searchParams: Promise<{ firm?: string }>;
}) {
  const { firm } = await searchParams;
  const selectedFirm = getCalculatorFirm(firm);
  const slug = selectedFirm.slug;
  const result = getFirmResult(slug);
  const template = result.inputs;

  return (
    <main>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/#assessments">Company assessments</Link><span>/</span><span>Trade Impact Calculator</span>
      </nav>
      <header className="lab-header">
        <div>
          <p className="eyebrow">Interactive</p>
          <h1>Trade Impact Calculator</h1>
          <p className="lede">
            Start from the published {result.firm} numbers, then change anything —
            how many EVs are sold, how far people drive, how fast grids get cleaner.
            The climate result updates as you move.
          </p>
        </div>
        <div className="lab-scope">
          <span>{selectedFirm.illustrative ? "Illustrative validation case" : "Based on"}</span>
          <strong>{result.firm} · {result.cohort_year}</strong>
          <Link href={`/report/${slug}`}>
            See the full {result.firm} report →
          </Link>
        </div>
      </header>
      <Calculator template={template as never} />
    </main>
  );
}
