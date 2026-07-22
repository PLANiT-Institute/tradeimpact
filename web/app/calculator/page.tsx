import Calculator from "@/components/Calculator";
import { getFirmResult, getFirms } from "@/lib/data";

export const metadata = { title: "Assumption explorer — TI" };

export default async function CalculatorPage({
  searchParams,
}: {
  searchParams: Promise<{ firm?: string }>;
}) {
  const { firm } = await searchParams;
  const runnable = getFirms().filter((f) => f.runnable);
  const slug = runnable.some((f) => f.slug === firm) ? firm! : runnable[0].slug;
  const template = getFirmResult(slug).inputs;

  return (
    <main>
      <p className="eyebrow">Interactive · engine-computed</p>
      <h1>Assumption explorer</h1>
      <p className="lede" style={{ marginBottom: 28 }}>
        This is not the assessment — the assessments live on the report pages, built from
        the published dataset. Use this to test how the {getFirmResult(slug).firm} result
        moves when an assumption moves: scenario rates, lifetime, distance, efficiencies,
        utility factor. Every recompute reports the full S1/S2/S3 triplet.
      </p>
      <Calculator template={template as never} />
    </main>
  );
}
