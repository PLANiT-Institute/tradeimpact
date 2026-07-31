"use client";
// Generic cumulative line chart across sales years — one line per entity
// (e.g. firms in one country). Fixed entity→color assignment supplied by the
// caller; palette validated against the app surface (dataviz six-checks).
import { useRef, useState } from "react";

export interface CumulativeSeries {
  key: string;
  label: string;
  color: string;
  /** cumulative values, one per year (same order as `years`) */
  values: number[];
}

function compact(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "−" : value > 0 ? "+" : "";
  if (abs >= 1_000_000) return `${sign}${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}${(abs / 1_000).toFixed(0)}k`;
  return `${sign}${abs.toFixed(0)}`;
}

export default function CumulativeLines({
  years,
  series,
  ariaLabel,
  caption,
}: {
  years: number[];
  series: CumulativeSeries[];
  ariaLabel: string;
  caption?: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const rows = series.filter((s) => s.values.length === years.length);
  if (!rows.length || years.length < 2) return null;

  const W = 720;
  const H = 320;
  const M = { l: 64, r: 96, t: 14, b: 34 };
  const n = years.length;
  const all = rows.flatMap((s) => s.values);
  const lo = Math.min(0, ...all);
  const hi = Math.max(0, ...all);
  const pad = (hi - lo) * 0.08 || 1;
  const yMin = lo - pad;
  const yMax = hi + pad;
  const sx = (i: number) => M.l + (i / Math.max(n - 1, 1)) * (W - M.l - M.r);
  const sy = (v: number) => M.t + (1 - (v - yMin) / (yMax - yMin)) * (H - M.t - M.b);

  // de-overlap end labels
  const LABEL_GAP = 14;
  const ordered = [...rows].sort(
    (a, b) => sy(a.values[n - 1]) - sy(b.values[n - 1]),
  );
  const labelY = new Map<string, number>();
  let prevY = -Infinity;
  for (const s of ordered) {
    const y = Math.max(sy(s.values[n - 1]) + 4, prevY + LABEL_GAP, M.t + 10);
    labelY.set(s.key, y);
    prevY = y;
  }

  const onMove = (e: React.PointerEvent) => {
    const rect = svgRef.current!.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    const i = Math.round(((px - M.l) / (W - M.l - M.r)) * (n - 1));
    setHover(i >= 0 && i < n ? i : null);
  };

  return (
    <div>
      <div className="chart-legend">
        {rows.map((s) => (
          <span className="key" key={s.key}>
            <span className="swatch" style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </div>
      <div className="chart-wrap">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          style={{ minWidth: 460, display: "block" }}
          role="img"
          aria-label={ariaLabel}
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
        >
          <line x1={M.l} x2={W - M.r} y1={sy(0)} y2={sy(0)} stroke="var(--hairline-strong)" strokeWidth={1.2} />
          <text x={M.l - 8} y={sy(0) + 4} textAnchor="end" fontSize="12.5" fill="var(--ink-3)" fontFamily="var(--font-mono)">
            0
          </text>
          {years.map((year, i) => (
            <text key={year} x={sx(i)} y={H - 10} textAnchor="middle" fontSize="12.5" fill="var(--ink-3)" fontFamily="var(--font-mono)">
              {year}
            </text>
          ))}
          {hover !== null && (
            <line x1={sx(hover)} x2={sx(hover)} y1={M.t} y2={H - M.b} stroke="var(--hairline-strong)" strokeWidth={1} />
          )}
          {rows.map((s) => (
            <g key={s.key}>
              <polyline
                points={s.values.map((v, i) => `${sx(i)},${sy(v)}`).join(" ")}
                fill="none"
                stroke={s.color}
                strokeWidth={2}
              />
              {s.values.map((v, i) => (
                <circle key={i} cx={sx(i)} cy={sy(v)} r={hover === i ? 4.5 : 3} fill={s.color} stroke="var(--surface)" strokeWidth={2} />
              ))}
              <text
                x={sx(n - 1) + 10}
                y={labelY.get(s.key)}
                fontSize="12.5"
                fill="var(--ink-2)"
                fontFamily="var(--font-mono)"
              >
                {s.key} {compact(s.values[n - 1])}
              </text>
            </g>
          ))}
          {hover !== null && (
            <g transform={`translate(${Math.min(sx(hover) + 12, W - 210)}, ${M.t + 4})`}>
              <rect width={198} height={rows.length * 17 + 26} rx={6} fill="var(--surface-2)" stroke="var(--hairline)" />
              <text x={10} y={17} fontSize="12.5" fill="var(--ink)" fontFamily="var(--font-mono)">
                {years[hover]} · cumulative
              </text>
              {rows.map((s, row) => (
                <g key={s.key} transform={`translate(10, ${30 + row * 17})`}>
                  <circle cx={4} cy={-4} r={4} fill={s.color} />
                  <text x={14} fontSize="12.5" fill="var(--ink-2)" fontFamily="var(--font-mono)">
                    {s.key} {compact(s.values[hover])}
                  </text>
                </g>
              ))}
            </g>
          )}
        </svg>
      </div>
      {caption && <p className="panel-note">{caption}</p>}
    </div>
  );
}
