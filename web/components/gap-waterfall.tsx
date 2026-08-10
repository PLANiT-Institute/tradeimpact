// Bridge from one cohort's per-vehicle TI to another's, one bar per source of the difference.
// A waterfall is the only chart shape that shows *offsetting* effects honestly: two terms that
// help and one that more than cancels them read as three bars, where a stacked bar or a pair of
// totals would show only the net.
import { SCENARIO_COLORS, SCENARIO_LABELS, type CohortComparison } from "@/lib/shared";

type Step = {
  key: string;
  label: string;
  /** Bar spans [from, to] on the value axis. Totals span [0, to]. */
  from: number;
  to: number;
  kind: "total" | "step";
};

function steps(comparison: CohortComparison, names: Record<string, string>): Step[] {
  const baseline = comparison.per_vehicle[comparison.baseline_cohort];
  const compared = comparison.per_vehicle[comparison.compared_cohort];
  const ordered: [string, string, number][] = [
    ["destination_mix", "Destination mix", comparison.terms.destination_mix],
    ["powertrain_mix", "Powertrain mix", comparison.terms.powertrain_mix],
    ["product_intensity", "Product intensity", comparison.terms.product_intensity],
    ["residual", "Residual", comparison.residual],
  ];
  const out: Step[] = [
    {
      key: "baseline",
      label: names[comparison.baseline_cohort],
      from: 0,
      to: baseline,
      kind: "total",
    },
  ];
  let running = baseline;
  for (const [key, label, value] of ordered) {
    out.push({ key, label, from: running, to: running + value, kind: "step" });
    running += value;
  }
  out.push({
    key: "compared",
    label: names[comparison.compared_cohort],
    from: 0,
    to: compared,
    kind: "total",
  });
  return out;
}

function kg(value: number): string {
  return `${value >= 0 ? "+" : "−"}${Math.abs(Math.round(value)).toLocaleString("en-US")}`;
}

export function GapWaterfall({
  comparison,
  names,
}: {
  comparison: CohortComparison;
  names: Record<string, string>;
}) {
  const bars = steps(comparison, names);
  const values = bars.flatMap((bar) => [bar.from, bar.to]).concat(0);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;

  const W = 720;
  const H = 300;
  const pad = { l: 4, r: 4, t: 26, b: 46 };
  const slot = (W - pad.l - pad.r) / bars.length;
  const barW = Math.min(slot * 0.56, 74);
  const x = (i: number) => pad.l + slot * i + (slot - barW) / 2;
  const y = (v: number) => pad.t + (1 - (v - min) / span) * (H - pad.t - pad.b);

  return (
    <figure className="ti-waterfall">
      <figcaption>
        <span className="sc-code">{comparison.scenario}</span> {SCENARIO_LABELS[comparison.scenario]}
        {" · "}
        <em>
          {names[comparison.compared_cohort]} ends {kg(comparison.gap)} kgCO₂e per vehicle from{" "}
          {names[comparison.baseline_cohort]}
        </em>
      </figcaption>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={bars
          .map((bar) =>
            bar.kind === "total"
              ? `${bar.label} ${kg(bar.to)} kgCO2e per vehicle`
              : `${bar.label} ${kg(bar.to - bar.from)}`,
          )
          .join(", ")}
      >
        <line x1={pad.l} y1={y(0)} x2={W - pad.r} y2={y(0)} className="ti-axis" />
        {bars.map((bar, i) => {
          const top = Math.min(y(bar.from), y(bar.to));
          const height = Math.max(Math.abs(y(bar.to) - y(bar.from)), 1.5);
          const helps = bar.to > bar.from;
          const fill =
            bar.kind === "total"
              ? SCENARIO_COLORS[comparison.scenario]
              : helps
                ? "var(--pos)"
                : "var(--neg)";
          const amount = bar.kind === "total" ? bar.to : bar.to - bar.from;
          return (
            <g key={bar.key}>
              {i > 0 && bars[i - 1].kind === "step" && bar.kind === "step" ? (
                <line
                  x1={x(i - 1) + barW}
                  y1={y(bar.from)}
                  x2={x(i)}
                  y2={y(bar.from)}
                  className="ti-waterfall-link"
                />
              ) : null}
              <rect
                x={x(i)}
                y={top}
                width={barW}
                height={height}
                fill={fill}
                opacity={bar.kind === "total" ? 0.95 : 0.8}
                rx={2}
              />
              <text
                x={x(i) + barW / 2}
                y={top - 7}
                textAnchor="middle"
                className={`ti-waterfall-value ${amount >= 0 ? "pos" : "neg"}`}
              >
                {kg(amount)}
              </text>
              {/* The svg carries the full reading in aria-label; these are visual only, and
                  a screen reader would otherwise run the wrapped words together. */}
              <text
                x={x(i) + barW / 2}
                y={H - pad.b + 18}
                textAnchor="middle"
                className="ti-waterfall-label"
                aria-hidden
              >
                {bar.label.split(" ").map((word, line) => (
                  <tspan key={word} x={x(i) + barW / 2} dy={line === 0 ? 0 : 13}>
                    {word}
                  </tspan>
                ))}
              </text>
            </g>
          );
        })}
      </svg>
      <p className="muted">
        Bars are kgCO₂e per covered vehicle over the operating life. Green raises the position,
        orange lowers it. The two end bars are the published cohort results; the four between them
        are what turns one into the other.
      </p>
    </figure>
  );
}
