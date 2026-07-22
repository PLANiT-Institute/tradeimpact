// Typed loaders for the published dataset (data/published, copied to public/data at build).
// The web app never computes TI — it renders what the engine produced.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Scenario } from "./shared";

export * from "./shared";

export interface Firm {
  slug: string;
  name: string;
  sector: string;
  country: string;
  project: "TI" | "CAP";
  runnable: boolean;
  illustrative?: boolean;
  note?: string;
  status?: string;
  selection_criteria?: string;
  ticker?: string;
}

export interface CohortResult {
  total_tCO2e: number;
  direction: string;
  directional_only: boolean;
  by_country: Record<string, number>;
  by_powertrain: Record<string, number>;
  annual_tCO2e: number[];
  excluded_flag_markets: Record<string, string>;
  warnings: string[];
}

export interface Crossover {
  country: string;
  powertrain: string;
  scenario: Scenario;
  crossover_year: number | null;
  reason: string | null;
}

export interface DataQuality {
  firm: string;
  cohort_year: number;
  analysis_level: string;
  layer1_method: string;
  benchmark_tiers: Record<string, string>;
  layer2_tiers: Record<string, string>;
  volume_tiers: Record<string, string>;
  lifetime_T: number | null;
  lifetime_sens: number;
  scenario_sources: Record<string, string>;
  missing_inputs: string[];
  warnings: string[];
  flag_markets: Record<string, string>;
}

export interface FirmResult {
  firm: string;
  cohort_year: number;
  cohorts: Record<Scenario, CohortResult>;
  portfolio: Record<Scenario, number[]>;
  crossover: Crossover[];
  data_quality: DataQuality;
  sensitivity?: Record<string, unknown>;
  inputs?: Record<string, unknown>;
  provenance: {
    engine_version: string;
    engine_git_sha: string;
    workbook: string;
    build_date: string;
  };
}

export interface Meta {
  engine: string;
  engine_version: string;
  engine_git_sha: string;
  workbook: string;
  workbook_sha256: string;
  build_date: string;
  collection_status: {
    countries_loaded: number;
    missing_inputs: string[];
    warnings: string[];
  };
}

const DATA_DIR = join(process.cwd(), "public", "data");

function read<T>(name: string): T {
  return JSON.parse(readFileSync(join(DATA_DIR, name), "utf-8")) as T;
}

export const getFirms = (): Firm[] => read<Firm[]>("firms.json");
export const getMeta = (): Meta => read<Meta>("meta.json");
export const getFirmResult = (slug: string): FirmResult =>
  read<FirmResult>(`${slug}.json`);

export function fmtTI(v: number): string {
  const sign = v > 0 ? "+" : v < 0 ? "−" : "";
  return `${sign}${Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}
