// The signature figure: a declining NDC benchmark against a fixed ICE line and a
// declining BEV curve — the shaded gap *is* the TI metric. Illustrative shape only.
export default function GapHero() {
  const W = 460;
  const H = 300;
  const N = 15;
  const bench = (t: number) => 60 + 150 * Math.pow(0.916, t); // emission units, declining
  const bev = (t: number) => 40 + 60 * Math.pow(0.94, t);
  const iceV = 150;
  const sx = (t: number) => 40 + (t / (N - 1)) * (W - 60);
  const sy = (v: number) => 262 - v; // higher emissions -> higher on the chart

  const line = (f: (t: number) => number) =>
    Array.from({ length: N }, (_, t) => `${sx(t)},${sy(f(t))}`).join(" ");
  // contribution area: between benchmark (above) and BEV (below)
  const bevArea =
    `M${Array.from({ length: N }, (_, t) => `${sx(t)},${sy(bench(t))}`).join("L")}` +
    `L${Array.from({ length: N }, (_, t) => `${sx(N - 1 - t)},${sy(bev(N - 1 - t))}`).join("L")}Z`;
  // liability area: ICE above the benchmark once the benchmark declines past it
  const crossT = Array.from({ length: N }, (_, t) => t).find((t) => bench(t) < iceV) ?? N - 1;
  const liab =
    `M${sx(crossT - 1)},${sy(iceV)}L${sx(N - 1)},${sy(iceV)}` +
    `L${Array.from({ length: N - crossT + 1 }, (_, i) => {
      const t = N - 1 - i;
      return `${sx(t)},${sy(Math.min(bench(t), iceV))}`;
    }).join("L")}Z`;

  return (
    <svg className="gap-hero-chart" viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="An NDC-derived sector benchmark declines over time; a combustion vehicle locks in emissions above it while an electric vehicle contributes below it">
      <path className="gap-area contribution" d={bevArea} />
      <path className="gap-area lockin" d={liab} />
      <polyline className="gap-line benchmark" points={line(bench)} fill="none" strokeWidth={2.5} />
      <line className="gap-line lockin" x1={sx(0)} y1={sy(iceV)} x2={sx(N - 1)} y2={sy(iceV)} strokeWidth={2} />
      <polyline className="gap-line contribution" points={line(bev)} fill="none" strokeWidth={2} />
      <line className="gap-axis" x1={40} y1={H - 30} x2={W - 20} y2={H - 30} />
      <text className="gap-label benchmark" x={sx(1)} y={sy(bench(0)) - 10} fontSize="12" fontFamily="var(--font-mono)">
        NDC sector benchmark
      </text>
      <text className="gap-label lockin" x={sx(N - 1)} y={sy(iceV) - 8} fontSize="12" textAnchor="end" fontFamily="var(--font-mono)">
        Combustion · lock-in
      </text>
      <text className="gap-label contribution" x={sx(N - 1)} y={sy(bev(N - 1)) + 18} fontSize="12" textAnchor="end" fontFamily="var(--font-mono)">
        Electric · contribution
      </text>
      <text className="gap-label axis" x={40} y={H - 12} fontSize="11">
        t = 0 (sale)
      </text>
      <text className="gap-label axis" x={W - 20} y={H - 12} fontSize="11" textAnchor="end">
        t = T−1
      </text>
    </svg>
  );
}
