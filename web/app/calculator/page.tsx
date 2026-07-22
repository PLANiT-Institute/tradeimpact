import Calculator from "@/components/Calculator";
import { getFirmResult, getFirms } from "@/lib/data";

export const metadata = { title: "TI calculator" };

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
      <h1>TI calculator</h1>
      <p className="lede" style={{ marginBottom: 28 }}>
        Start from the {getFirmResult(slug).firm} case and move the parameters the
        methodology exposes — scenario rates, lifetime, distance, efficiencies, utility
        factor. Every recompute reports the full S1/S2/S3 triplet.
      </p>
      <Calculator template={template as never} />
    </main>
  );
}
