// Client-safe constants, types, and formatters (no node imports).
export type Scenario = "S1" | "S2" | "S3";
export const SCENARIOS: Scenario[] = ["S1", "S2", "S3"];
export const SCENARIO_LABELS: Record<Scenario, string> = {
  S1: "Low — current policies (STEPS)",
  S2: "Central — NDC",
  S3: "High — 1.5°C (NZE)",
};

export function fmtTI(v: number): string {
  const sign = v > 0 ? "+" : v < 0 ? "−" : "";
  return `${sign}${Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}
