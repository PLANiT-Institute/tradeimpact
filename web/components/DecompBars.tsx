// Horizontal sign-colored bars for the mandatory decomposition. Server-rendered SVG;
// per-mark identity carried by row labels + direct value labels (color = sign only).
import { fmtTI } from "@/lib/shared";

const POS = "var(--pos)";
const NEG = "var(--neg)";

export default function DecompBars({
  data,
  unit,
  caption,
}: {
  data: Record<string, number>;
  unit: string;
  caption?: string;
}) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return <p className="panel-note">No decomposition available.</p>;
  const maxAbs = Math.max(...entries.map(([, v]) => Math.abs(v)), 1);

  const W = 680;
  const rowH = 34;
  const H = entries.length * rowH + 22;
  const labelW = 96;
  const zero = labelW + ((W - labelW - 90) * maxAbs) / (2 * maxAbs) + 0; // symmetric domain
  const scale = (W - labelW - 90) / (2 * maxAbs);

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ minWidth: 430, display: "block" }} role="img" aria-label={`Contribution to the NDC impact result, ${unit}`}>
        <line x1={zero} x2={zero} y1={4} y2={H - 16} stroke="var(--ink-3)" strokeWidth={1.2} />
        {entries.map(([key, v], i) => {
          const y = i * rowH + 10;
          const w = Math.abs(v) * scale;
          const x = v >= 0 ? zero + 2 : zero - 2 - w;
          const color = v >= 0 ? POS : NEG;
          return (
            <g key={key}>
              <title>{`${key}: ${fmtTI(v)} ${unit}`}</title>
              <text x={labelW - 10} y={y + 15} textAnchor="end" fontSize="13.5" fill="var(--ink-2)" fontFamily="var(--font-mono)">
                {key}
              </text>
              <rect x={x} y={y} width={Math.max(w, 1.5)} height={16} fill={color} rx={3} />
              <text
                x={v >= 0 ? zero + w + 8 : zero - w - 8}
                y={y + 13}
                textAnchor={v >= 0 ? "start" : "end"}
                fontSize="13"
                fill="var(--ink)"
                fontFamily="var(--font-mono)"
              >
                {fmtTI(v)}
              </text>
            </g>
          );
        })}
        <text x={W - 4} y={H - 4} textAnchor="end" fontSize="12" fill="var(--ink-3)">
          {caption ?? `${unit} · green = NDC contribution · rust = NDC lock-in`}
        </text>
      </svg>
    </div>
  );
}
