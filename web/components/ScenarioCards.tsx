// The S1/S2/S3 triplet — always all three, S2 marked central (Guideline §4.7).
import { fmtTI, SCENARIO_LABELS, SCENARIOS, type Scenario } from "@/lib/shared";

const COLORS: Record<Scenario, string> = { S1: "#b37f2e", S2: "#2d5698", S3: "#1b9e85" };

export default function ScenarioCards({
  totals,
  unit,
  directionalOnly,
}: {
  totals: Partial<Record<Scenario, number>>;
  unit: string;
  directionalOnly?: Partial<Record<Scenario, boolean>>;
}) {
  return (
    <div className="scenario-grid">
      {SCENARIOS.map((sc) => {
        const v = totals[sc];
        const pos = (v ?? 0) >= 0;
        return (
          <div
            key={sc}
            className={`scenario-card${sc === "S2" ? " central" : ""}`}
            style={{ ["--sc" as string]: COLORS[sc] }}
          >
            <div className="sc-label">
              {sc} · {SCENARIO_LABELS[sc]}
            </div>
            <div className={`sc-value ${pos ? "dir-pos" : "dir-neg"}`}>
              {v === undefined ? "—" : directionalOnly?.[sc] ? (pos ? "contribution" : "liability") : fmtTI(v)}
            </div>
            <div className="sc-unit">
              {v === undefined ? "not computable from supplied inputs" : directionalOnly?.[sc] ? "directional only — Tier C share above threshold" : unit}
            </div>
            {v !== undefined && !directionalOnly?.[sc] && (
              <span className={`direction-chip ${pos ? "pos" : "neg"}`}>
                {pos ? "net contribution" : "net lock-in liability"}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
