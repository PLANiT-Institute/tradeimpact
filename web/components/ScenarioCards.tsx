// The S1/S2/S3 triplet — always all three, S2 marked central (Guideline §4.7).
import React from "react";
import {
  compactMagnitude,
  directionClass,
  directionOf,
  ndcImpactLabel,
  plainDirection,
  plainOutcome,
  SCENARIO_COLORS as COLORS,
  SCENARIO_LABELS as TITLES,
  type Scenario,
} from "@/lib/shared";

const SUBTITLES: Record<Scenario, string> = {
  S1: "Sensitivity · slower transition",
  S2: "Core research result",
  S3: "Sensitivity · faster transition",
};

export default function ScenarioCards({
  totals,
  unit,
  directionalOnly,
}: {
  totals: Partial<Record<Scenario, number>>;
  unit: string;
  directionalOnly?: Partial<Record<Scenario, boolean>>;
}) {
  const order: Scenario[] = ["S2", "S1", "S3"];
  return (
    <div className="scenario-grid">
      {order.map((sc) => {
        const v = totals[sc];
        const direction = directionOf(v);
        const dirClass = directionClass(direction);
        const isNdc = sc === "S2";
        return (
          <div
            key={sc}
            className={`scenario-card${sc === "S2" ? " central" : ""}`}
            style={{ ["--sc" as string]: COLORS[sc] }}
          >
            <div className="sc-label-row">
              <span className="sc-code">{isNdc ? "NDC" : sc}</span>
              {isNdc && <span className="sc-headline">Primary metric</span>}
            </div>
            <h3 className="sc-title">{isNdc ? "Impact on national NDCs" : TITLES[sc]}</h3>
            <p className="sc-subtitle">{SUBTITLES[sc]}</p>
            <div
              className={`sc-value dir-${dirClass}`}
              title={
                v === undefined || directionalOnly?.[sc]
                  ? undefined
                  : `${Math.abs(v).toLocaleString("en-US")} ${unit}`
              }
            >
              {isNdc
                ? directionalOnly?.[sc] || v === undefined
                  ? ndcImpactLabel(direction)
                  : `${compactMagnitude(v)} ${unit}`
                : plainOutcome(v, directionalOnly?.[sc])}
            </div>
            <div className="sc-unit">
              {v === undefined
                ? "The supplied inputs do not produce a result"
                : directionalOnly?.[sc]
                  ? "Direction only · numeric estimate hidden"
                  : isNdc
                    ? ndcImpactLabel(direction)
                    : `${unit} gap`}
            </div>
            {v !== undefined && (
              <p className="sc-meaning">
                {isNdc
                  ? direction === "contribution"
                    ? "Products support NDC delivery"
                    : direction === "liability"
                      ? "Products lock in emissions above NDC commitments"
                      : ndcImpactLabel(direction)
                  : plainDirection(direction) === "Above pathway"
                  ? "Portfolio emissions exceed the benchmark"
                  : plainDirection(direction) === "Below pathway"
                    ? "Portfolio emissions are below the benchmark"
                    : plainDirection(direction)}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
