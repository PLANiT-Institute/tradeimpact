"use client";
// Multi-scenario line chart with crosshair + tooltip. Renders engine time-series only.
import { useMemo, useRef, useState } from "react";
import type { Scenario } from "@/lib/shared";

const COLORS: Record<Scenario, string> = { S1: "#b37f2e", S2: "#2d5698", S3: "#1b9e85" };
const LABELS: Record<Scenario, string> = { S1: "S1 STEPS", S2: "S2 NDC", S3: "S3 NZE" };

export default function AnnualLines({
  series,
  xLabel,
  yLabel,
  x0 = 0,
}: {
  series: Partial<Record<Scenario, number[]>>;
  xLabel: string;
  yLabel: string;
  x0?: number;
}) {
  const W = 720;
  const H = 300;
  const M = { l: 64, r: 16, t: 12, b: 34 };
  const [hover, setHover] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const keys = (Object.keys(series) as Scenario[]).filter((k) => series[k]?.length);
  const n = Math.max(...keys.map((k) => series[k]!.length), 1);
  const all = keys.flatMap((k) => series[k]!);
  const lo = Math.min(0, ...all);
  const hi = Math.max(0, ...all);
  const pad = (hi - lo) * 0.06 || 1;
  const yMin = lo - pad;
  const yMax = hi + pad;

  const sx = (i: number) => M.l + (i / Math.max(n - 1, 1)) * (W - M.l - M.r);
  const sy = (v: number) => M.t + (1 - (v - yMin) / (yMax - yMin)) * (H - M.t - M.b);

  const ticks = useMemo(() => {
    const step = niceStep((yMax - yMin) / 5);
    const first = Math.ceil(yMin / step) * step;
    const out: number[] = [];
    for (let v = first; v <= yMax; v += step) out.push(v);
    return out;
  }, [yMin, yMax]);

  const onMove = (e: React.PointerEvent) => {
    const rect = svgRef.current!.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    const i = Math.round(((px - M.l) / (W - M.l - M.r)) * (n - 1));
    setHover(i >= 0 && i < n ? i : null);
  };

  return (
    <div>
      <div className="chart-legend">
        {keys.map((k) => (
          <span className="key" key={k}>
            <span className="swatch" style={{ background: COLORS[k] }} />
            {LABELS[k]}
          </span>
        ))}
      </div>
      <div className="chart-wrap">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          style={{ minWidth: 520, display: "block" }}
          role="img"
          aria-label={`${yLabel} by ${xLabel}, scenarios ${keys.join(", ")}`}
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
        >
          {ticks.map((v) => (
            <g key={v}>
              <line
                x1={M.l}
                x2={W - M.r}
                y1={sy(v)}
                y2={sy(v)}
                stroke={v === 0 ? "#46586e" : "#e4e8ee"}
                strokeWidth={v === 0 ? 1.2 : 1}
              />
              <text x={M.l - 8} y={sy(v) + 4} textAnchor="end" fontSize="11" fill="#6b7c90">
                {compact(v)}
              </text>
            </g>
          ))}
          {[0, Math.floor((n - 1) / 2), n - 1].map((i) => (
            <text key={i} x={sx(i)} y={H - 10} textAnchor="middle" fontSize="11" fill="#6b7c90">
              {x0 + i}
            </text>
          ))}
          <text x={8} y={H - 10} textAnchor="start" fontSize="11" fill="#6b7c90">
            {xLabel}
          </text>
          {keys.map((k) => (
            <path
              key={k}
              d={series[k]!.map((v, i) => `${i ? "L" : "M"}${sx(i)},${sy(v)}`).join("")}
              fill="none"
              stroke={COLORS[k]}
              strokeWidth={2}
              strokeLinejoin="round"
            />
          ))}
          {hover !== null && (
            <g>
              <line x1={sx(hover)} x2={sx(hover)} y1={M.t} y2={H - M.b} stroke="#9aa5b1" strokeDasharray="3 3" />
              {keys.map((k) =>
                series[k]![hover] === undefined ? null : (
                  <circle key={k} cx={sx(hover)} cy={sy(series[k]![hover])} r={4} fill={COLORS[k]} stroke="#fff" strokeWidth={2} />
                ),
              )}
              <TooltipBox
                x={sx(hover)}
                w={W}
                rows={keys.map((k) => ({
                  color: COLORS[k],
                  label: LABELS[k],
                  value: series[k]![hover],
                }))}
                title={`${xLabel} ${x0 + hover}`}
              />
            </g>
          )}
        </svg>
      </div>
      <details className="table-view">
        <summary>Table view</summary>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>{xLabel}</th>
                {keys.map((k) => (
                  <th className="num" key={k}>
                    {LABELS[k]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: n }, (_, i) => (
                <tr key={i}>
                  <td className="num">{x0 + i}</td>
                  {keys.map((k) => (
                    <td className="num" key={k}>
                      {series[k]![i]?.toLocaleString("en-US", { maximumFractionDigits: 0 }) ?? "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

function TooltipBox({
  x,
  w,
  title,
  rows,
}: {
  x: number;
  w: number;
  title: string;
  rows: { color: string; label: string; value: number | undefined }[];
}) {
  const bw = 168;
  const bh = 24 + rows.length * 18;
  const bx = x + bw + 14 > w ? x - bw - 14 : x + 14;
  return (
    <g transform={`translate(${bx},14)`} pointerEvents="none">
      <rect width={bw} height={bh} rx={4} fill="#16243d" opacity={0.94} />
      <text x={10} y={17} fontSize="11" fill="#c8d2de" fontFamily="var(--font-mono)">
        {title}
      </text>
      {rows.map((r, i) => (
        <g key={r.label} transform={`translate(10,${32 + i * 18})`}>
          <rect width={9} height={9} y={-8} rx={2} fill={r.color} />
          <text x={15} fontSize="11.5" fill="#fff" fontFamily="var(--font-mono)">
            {r.label}  {r.value === undefined ? "—" : compact(r.value)}
          </text>
        </g>
      ))}
    </g>
  );
}

function compact(v: number): string {
  const a = Math.abs(v);
  const s = v < 0 ? "−" : "";
  if (a >= 1e6) return `${s}${(a / 1e6).toFixed(1)}M`;
  if (a >= 1e3) return `${s}${(a / 1e3).toFixed(0)}k`;
  return `${s}${a.toFixed(0)}`;
}

function niceStep(raw: number): number {
  const mag = Math.pow(10, Math.floor(Math.log10(raw || 1)));
  const r = raw / mag;
  return (r >= 5 ? 10 : r >= 2 ? 5 : r >= 1 ? 2 : 1) * mag;
}
