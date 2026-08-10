// Where a cohort's result is concentrated, cell by cell.
//
// The two required margins say which destinations and which powertrains carry the number, but
// not which *combination* does. A manufacturer deciding what to change needs the joint: a market
// can be 13% of units and one powertrain inside it can be a fifth of the whole liability.
//
// x is volume, y is lifetime TI per vehicle, so the product of the two axes is the cell's
// contribution — area is drawn to match. Each cell is a segment from S1 to S3 rather than a
// point, because the per-vehicle figure moves with the pathway while the volume does not, and
// the width of that move is the cell's policy-risk exposure (Whitepaper §3.9).
import {
  SCENARIO_COLORS,
  SCENARIO_LABELS,
  type CohortCell,
  type LifetimeResult,
  type Scenario,
} from "@/lib/shared";

const POWERTRAIN_COLORS: Record<string, string> = {
  BEV: "#5d9cec",
  HEV: "#d9a441",
  ICE: "#ef7b5e",
  PHEV: "#36bfa0",
  FCEV: "#9d7bea",
};

type Plotted = {
  key: string;
  country: string;
  powertrain: string;
  units: number;
  central: number;
  low: number;
  high: number;
  ti: number;
  share: number;
};

function collect(result: LifetimeResult): Plotted[] {
  const index = (scenario: Scenario) =>
    new Map(
      result.cohorts[scenario].by_cell.map((cell: CohortCell) => [
        `${cell.country}|${cell.powertrain}`,
        cell,
      ]),
    );
  const s1 = index("S1");
  const s3 = index("S3");
  const total = result.cohorts.S2.total_tCO2e;
  return result.cohorts.S2.by_cell
    .filter((cell) => cell.units > 0 && cell.TI_per_vehicle_kgCO2e != null)
    .map((cell) => {
      const key = `${cell.country}|${cell.powertrain}`;
      const central = cell.TI_per_vehicle_kgCO2e as number;
      return {
        key,
        country: cell.country,
        powertrain: cell.powertrain,
        units: cell.units,
        central,
        low: s1.get(key)?.TI_per_vehicle_kgCO2e ?? central,
        high: s3.get(key)?.TI_per_vehicle_kgCO2e ?? central,
        ti: cell.TI_tCO2e,
        share: total === 0 ? 0 : cell.TI_tCO2e / total,
      };
    });
}

function kg(value: number): string {
  return `${value >= 0 ? "+" : "−"}${Math.abs(Math.round(value)).toLocaleString("en-US")}`;
}

export function CellScatter({ result }: { result: LifetimeResult }) {
  const cells = collect(result);
  if (cells.length === 0) return null;

  const W = 720;
  const H = 360;
  const pad = { l: 52, r: 34, t: 16, b: 42 };
  const maxUnits = Math.max(...cells.map((c) => c.units));
  const values = cells.flatMap((c) => [c.low, c.central, c.high]);
  const yMax = Math.max(...values, 0);
  const yMin = Math.min(...values, 0);
  const maxTi = Math.max(...cells.map((c) => Math.abs(c.ti)), 1);

  // Volume spans four orders of magnitude across cells, so a linear axis would stack almost
  // every cell against the left edge and hide the small-but-terrible ones.
  const x = (units: number) =>
    pad.l + (Math.log10(Math.max(units, 1)) / Math.log10(maxUnits)) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - (v - yMin) / (yMax - yMin || 1)) * (H - pad.t - pad.b);
  const r = (ti: number) => 2.5 + 13 * Math.sqrt(Math.abs(ti) / maxTi);

  const ranked = [...cells].sort((a, b) => Math.abs(b.ti) - Math.abs(a.ti));
  const ticks = [10, 100, 1_000, 10_000, 100_000].filter((t) => t <= maxUnits * 1.4);
  const powertrains = [...new Set(cells.map((c) => c.powertrain))].sort();

  return (
    <figure className="ti-cells">
      <div className="ti-legend">
        {powertrains.map((pt) => (
          <span key={pt}>
            <i style={{ background: POWERTRAIN_COLORS[pt] ?? "var(--ink-3)" }} aria-hidden />
            {pt}
          </span>
        ))}
        <span className="ti-cells-scale">bubble area ∝ share of the cohort result</span>
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Each destination and powertrain cell of the ${result.firm} cohort, plotted by volume against lifetime TI per vehicle. Largest contributors: ${ranked
          .slice(0, 4)
          .map(
            (c) =>
              `${c.country} ${c.powertrain}, ${Math.round(c.units).toLocaleString("en-US")} units, ${kg(c.central)} kgCO2e per vehicle, ${(c.share * 100).toFixed(1)} percent of the cohort result`,
          )
          .join("; ")}`}
      >
        <line x1={pad.l} y1={y(0)} x2={W - pad.r} y2={y(0)} className="ti-axis" />
        {/* Left of the plot, where the volume axis starts and no cell can sit. The right
            edge is where the largest cells and their badges land. */}
        <text x={pad.l + 2} y={y(0) - 6} className="ti-cells-note">
          zero — matches the destination benchmark
        </text>
        {ticks.map((tick) => (
          <g key={tick}>
            <line
              x1={x(tick)}
              y1={pad.t}
              x2={x(tick)}
              y2={H - pad.b}
              className="ti-cells-grid"
            />
            <text x={x(tick)} y={H - pad.b + 15} textAnchor="middle" className="ti-cells-note">
              {tick.toLocaleString("en-US")}
            </text>
          </g>
        ))}
        <text x={pad.l} y={H - pad.b + 32} className="ti-cells-axis-title">
          units sold in that market (log scale)
        </text>
        <text
          x={0}
          y={0}
          transform={`translate(14 ${pad.t + (H - pad.t - pad.b) / 2}) rotate(-90)`}
          textAnchor="middle"
          className="ti-cells-axis-title"
        >
          kgCO₂e per vehicle over its life
        </text>

        {ranked
          .slice()
          .reverse()
          .map((cell) => {
            const color = POWERTRAIN_COLORS[cell.powertrain] ?? "var(--ink-3)";
            return (
              <g key={cell.key}>
                <line
                  x1={x(cell.units)}
                  y1={y(cell.low)}
                  x2={x(cell.units)}
                  y2={y(cell.high)}
                  stroke={color}
                  strokeWidth={1}
                  opacity={0.45}
                />
                <circle
                  cx={x(cell.units)}
                  cy={y(cell.central)}
                  r={r(cell.ti)}
                  fill={color}
                  opacity={0.5}
                  stroke={color}
                  strokeWidth={0.8}
                />
              </g>
            );
          })}
        {/* The heaviest cells sit on top of each other, so they carry a numbered badge and
            the reading goes in the list below rather than in colliding in-chart labels. */}
        {ranked.slice(0, 4).map((cell, i) => (
          <g key={cell.key}>
            <circle
              cx={x(cell.units) + r(cell.ti) * 0.72 + 7}
              cy={y(cell.central) - r(cell.ti) * 0.72 - 7}
              r={7.5}
              className="ti-cells-badge"
            />
            <text
              x={x(cell.units) + r(cell.ti) * 0.72 + 7}
              y={y(cell.central) - r(cell.ti) * 0.72 - 4}
              textAnchor="middle"
              className="ti-cells-badge-text"
            >
              {i + 1}
            </text>
          </g>
        ))}
      </svg>
      <p className="muted">
        Every dot is one destination and one powertrain. The vertical line through it runs from{" "}
        <span className="sc-code" style={{ color: SCENARIO_COLORS.S1 }}>
          S1
        </span>{" "}
        {SCENARIO_LABELS.S1.toLowerCase()} to{" "}
        <span className="sc-code" style={{ color: SCENARIO_COLORS.S3 }}>
          S3
        </span>{" "}
        {SCENARIO_LABELS.S3.toLowerCase()}, with the dot at{" "}
        <span className="sc-code" style={{ color: SCENARIO_COLORS.S2 }}>
          S2
        </span>
        ; a long line is a cell whose standing depends heavily on how far the destination
        actually goes.
      </p>
      <ol className="ti-cells-top">
        {ranked.slice(0, 4).map((cell) => (
          <li key={cell.key}>
            <i style={{ background: POWERTRAIN_COLORS[cell.powertrain] ?? "var(--ink-3)" }} />
            <strong>
              {cell.country} {cell.powertrain}
            </strong>
            <span>{Math.round(cell.units).toLocaleString("en-US")} units</span>
            <span className={cell.central >= 0 ? "pos" : "neg"}>
              {kg(cell.central)} kg/vehicle
            </span>
            <em>{(Math.abs(cell.share) * 100).toFixed(1)}% of the result</em>
          </li>
        ))}
      </ol>
    </figure>
  );
}
