// Two cohorts' lifetime TI per vehicle, market by market.
//
// The comparison page reports one per-vehicle number for each firm and a decomposition of the
// gap between them. Neither says where the gap is earned. Cohort totals cannot: they are
// dominated by the 1.87x difference in cohort size. Dividing each market's TI by the units
// that cohort actually placed there removes the size difference and leaves the thing being
// compared — what one of that firm's vehicles does in that market over its life.
import { type CohortCell, type DestinationInput, type LifetimeResult } from "@/lib/shared";

type MarketRow = {
  code: string;
  baseline: number;
  compared: number;
  gap: number;
  proxied: boolean;
  implausible: boolean;
};

function perVehicleByMarket(result: LifetimeResult): Map<string, number> {
  const totals = new Map<string, { ti: number; units: number }>();
  for (const cell of result.cohorts.S2.by_cell as CohortCell[]) {
    const row = totals.get(cell.country) ?? { ti: 0, units: 0 };
    row.ti += cell.TI_tCO2e;
    row.units += cell.units;
    totals.set(cell.country, row);
  }
  return new Map(
    [...totals]
      .filter(([, row]) => row.units > 0)
      .map(([code, row]) => [code, (row.ti * 1000) / row.units]),
  );
}

function kg(value: number): string {
  return `${value >= 0 ? "+" : "−"}${Math.abs(Math.round(value)).toLocaleString("en-US")}`;
}

export function MarketDumbbell({
  baseline,
  compared,
  destinations,
}: {
  baseline: LifetimeResult;
  compared: LifetimeResult;
  destinations: DestinationInput[];
}) {
  const a = perVehicleByMarket(baseline);
  const b = perVehicleByMarket(compared);
  const flags = new Map(destinations.map((row) => [row.country_code, row.warnings]));
  const rows: MarketRow[] = [...a.keys()]
    .filter((code) => b.has(code))
    .map((code) => {
      const warnings = flags.get(code) ?? [];
      return {
        code,
        baseline: a.get(code) as number,
        compared: b.get(code) as number,
        gap: (b.get(code) as number) - (a.get(code) as number),
        proxied: warnings.some((w) => w.startsWith("VKT_PROXY")),
        implausible: warnings.some((w) => w.startsWith("FLEET_INTENSITY_IMPLAUSIBLE")),
      };
    })
    .sort((x, y) => x.gap - y.gap);
  if (rows.length === 0) return null;

  const values = rows.flatMap((row) => [row.baseline, row.compared]);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0);
  const rowH = 15;
  const W = 720;
  const pad = { l: 34, r: 6, t: 22, b: 26 };
  const H = pad.t + rows.length * rowH + pad.b;
  const x = (v: number) => pad.l + ((v - min) / (max - min || 1)) * (W - pad.l - pad.r);
  const y = (i: number) => pad.t + i * rowH + rowH / 2;

  return (
    <figure className="ti-dumbbell">
      <div className="ti-legend">
        <span>
          <i className="dot-baseline" aria-hidden />
          {baseline.firm}
        </span>
        <span>
          <i className="dot-compared" aria-hidden />
          {compared.firm}
        </span>
        <span className="ti-cells-scale">
          bar colour is the direction of the difference · S2 national commitments
        </span>
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Lifetime TI per vehicle in each destination market. ${rows
          .slice(0, 3)
          .map(
            (row) =>
              `${row.code}: ${baseline.firm} ${kg(row.baseline)}, ${compared.firm} ${kg(row.compared)}`,
          )
          .join("; ")}. Sorted from the markets where ${compared.firm} does worst against ${baseline.firm} to where it does best.`}
      >
        <line x1={x(0)} y1={pad.t - 6} x2={x(0)} y2={H - pad.b} className="ti-axis" />
        <text x={x(0) + 4} y={pad.t - 10} className="ti-cells-note">
          zero — matches the destination benchmark
        </text>
        {rows.map((row, i) => (
          <g key={row.code}>
            <line
              x1={x(row.baseline)}
              y1={y(i)}
              x2={x(row.compared)}
              y2={y(i)}
              stroke={row.gap < 0 ? "var(--neg)" : "var(--pos)"}
              strokeWidth={2.5}
              opacity={0.55}
            />
            <circle cx={x(row.baseline)} cy={y(i)} r={3.4} className="ti-dot-baseline" />
            <circle cx={x(row.compared)} cy={y(i)} r={3.4} className="ti-dot-compared" />
            <text x={2} y={y(i) + 3.2} className="ti-dumbbell-label">
              {row.code}
              {row.implausible ? "†" : row.proxied ? "*" : ""}
            </text>
          </g>
        ))}
        <text x={pad.l} y={H - 8} className="ti-cells-axis-title">
          kgCO₂e per vehicle over its life
        </text>
      </svg>
      <p className="muted">
        Sorted from the markets where {compared.firm} does worst against {baseline.firm} per
        vehicle to where it does best. <strong>*</strong> the market publishes no national car
        traffic series, so both cohorts run on the EU average distance there.{" "}
        <strong>†</strong> Luxembourg&apos;s car CO₂ inventory and its registered stock cover
        different driving populations because of cross-border refuelling, which is why its
        benchmark is implausibly high and both cohorts score positive against it. The engine
        flags and tiers that market down rather than dropping it.
      </p>
    </figure>
  );
}
