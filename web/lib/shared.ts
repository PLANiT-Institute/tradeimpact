// Client-safe constants, types, and formatters (no node imports).
// The data-contract types below mirror ti_framework/report/outputs.py:to_json_dict —
// the emitter is the source of truth. build_dataset.py publishes the emitted key sets
// as contract.json, and tests/data-contract.test.ts asserts the *_KEYS arrays here
// (compile-time-bound to the interfaces) match it.
export type Scenario = "S1" | "S2" | "S3";
export const SCENARIOS: Scenario[] = ["S1", "S2", "S3"];

// One wording and one color per scenario, used by every chart and card.
export const SCENARIO_LABELS: Record<Scenario, string> = {
  S1: "Current policies",
  S2: "National commitments",
  S3: "1.5°C pathway",
};
export const SCENARIO_COLORS: Record<Scenario, string> = {
  S1: "var(--s1)",
  S2: "var(--s2)",
  S3: "var(--s3)",
};

// --- Published data contract (see data/published/contract.json) -------------

export interface Firm {
  slug: string;
  name: string;
  sector: string;
  country: string;
  project: "TI" | "CAP";
  runnable: boolean;
  alignment_available?: boolean;
  illustrative?: boolean;
  basis?: "source-backed" | null;
  note?: string;
  status?: string;
  selection_criteria?: string;
  ticker?: string;
  /** Cohort year of this firm's published assessment (runnable firms only). */
  cohort_year?: number;
  assessed_units?: number;
  reported_units?: number;
  coverage_ratio?: number;
  coverage_source?: string;
  coverage_scope?: string;
  /** Firm's own decarbonisation commitment, sourced in the fixture. */
  netzero?: NetZeroPlan | null;
}

export interface NetZeroPlan {
  target_year: number;
  scope: string;
  interim?: string;
  source?: string;
  announced?: string;
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
  TI_per_vehicle_kgCO2e?: number;
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
    engine_source_sha256: string;
    workbook: string;
    workbook_sha256: string;
    input_sha256: string;
    dataset_sha256: string;
  };
}

export interface PublishedCountry {
  code: string;
  name: string;
  grid_intensity?: number;
  r_fleet: Record<string, number>;
  r_power: Record<string, number>;
  status: string;
  tier: string;
  source?: string;
  warnings?: string[];
  flag_reason?: string;
}

export interface MetricDefinition {
  metric_id: string;
  label: string;
  unit: string;
  description: string;
}

export interface SectorProfile {
  sector_id: string;
  name: string;
  implementation_status: "pilot" | "next" | "planned";
  operating_boundary: string;
  activity_basis: string;
  direct_metrics: MetricDefinition[];
  descriptive_metrics: MetricDefinition[];
  contextual_pathways: string[];
  required_dimensions: string[];
  boundary_risks: string[];
}

export interface AlignmentCoverage {
  mapped_activity: number;
  reported_activity: number;
  activity_unit: string;
  unmatched_records: number;
}

export interface CompanyMetric {
  metric_id: string;
  sector: string;
  company_id: string;
  geography: string;
  observation_year: number;
  value: number;
  unit: string;
  source_ids: string[];
  evidence_class: string;
  scope: Record<string, string>;
  derivation: string;
  coverage: AlignmentCoverage;
}

export interface AlignmentBenchmark {
  benchmark_id: string;
  metric_id: string;
  sector: string;
  geography: string;
  benchmark_type: string;
  authority_status: string;
  comparison_mode: "direct" | "contextual";
  relation: "at_least" | "at_most" | "context_only";
  source_ids: string[];
  value: number | null;
  value_min?: number | null;
  value_max?: number | null;
  unit: string | null;
  target_year: number | null;
  applicable_geographies: string[];
  notes?: string;
}

export interface SourceRecord {
  source_id: string;
  title: string;
  publisher: string;
  url: string;
  evidence_class: string;
  published_date?: string | null;
  accessed_date?: string | null;
  license?: string | null;
  snapshot_sha256?: string;
  query_sha256?: string;
  notes?: string;
}

/** Sector-wide support parameters every real firm must agree on (see meta.json). */
export interface SupportContract {
  lifetime_T: number | null;
  lifetime_sens: number | null;
  uf_band: number | null;
  realworld_range: [number, number] | null;
  vkt: Record<string, number>;
}

export interface Meta {
  engine: string;
  engine_version: string;
  engine_source_sha256: string;
  workbook: string;
  workbook_sha256: string;
  compute_service_sha256: string;
  dataset_sha256: string;
  support_contract: SupportContract;
  target_sources_sha256: Record<string, string>;
  alignment_inputs_sha256: Record<string, string>;
  alignment_contract: {
    version: string;
    sectors_registered: number;
    direct_benchmarks: number;
    contextual_benchmarks: number;
    company_metrics: number;
    rule: string;
  };
  collection_status: {
    countries_loaded: number;
    missing_inputs: string[];
    warnings: string[];
  };
}

// Runtime key lists for the contract test. `satisfies` binds each array to its
// interface at compile time; the exhaustiveness asserts below fail the build if a
// key is added to an interface but not listed here (or vice versa).
export const FIRM_RESULT_KEYS = [
  "cohort_year",
  "cohorts",
  "crossover",
  "data_quality",
  "firm",
  "inputs",
  "portfolio",
  "provenance",
  "sensitivity",
] as const satisfies readonly (keyof FirmResult)[];

export const COHORT_KEYS = [
  "annual_tCO2e",
  "by_country",
  "by_powertrain",
  "direction",
  "directional_only",
  "excluded_flag_markets",
  "total_tCO2e",
  "warnings",
] as const satisfies readonly (keyof CohortResult)[];

export const DATA_QUALITY_KEYS = [
  "analysis_level",
  "benchmark_tiers",
  "cohort_year",
  "firm",
  "flag_markets",
  "layer1_method",
  "layer2_tiers",
  "lifetime_T",
  "lifetime_sens",
  "missing_inputs",
  "scenario_sources",
  "volume_tiers",
  "warnings",
] as const satisfies readonly (keyof DataQuality)[];

// Exhaustiveness: `keyof T` must be assignable to the array's element union.
type _ExhaustiveFirmResult = keyof FirmResult extends (typeof FIRM_RESULT_KEYS)[number]
  ? true
  : never;
type _ExhaustiveCohort = keyof CohortResult extends (typeof COHORT_KEYS)[number] ? true : never;
type _ExhaustiveDataQuality = keyof DataQuality extends (typeof DATA_QUALITY_KEYS)[number]
  ? true
  : never;
const _exhaustive: [_ExhaustiveFirmResult, _ExhaustiveCohort, _ExhaustiveDataQuality] = [
  true,
  true,
  true,
];
void _exhaustive;

// --- Formatters -------------------------------------------------------------

export function fmtTI(v: number): string {
  const sign = v > 0 ? "+" : v < 0 ? "−" : "";
  return `${sign}${Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export type Direction = "contribution" | "liability" | "neutral" | "missing";

export function directionOf(v: number | undefined): Direction {
  if (v === undefined) return "missing";
  if (v > 0) return "contribution";
  if (v < 0) return "liability";
  return "neutral";
}

export function directionClass(direction: Direction): "pos" | "neg" | "neu" {
  if (direction === "contribution") return "pos";
  if (direction === "liability") return "neg";
  return "neu";
}

export function displayTI(v: number | undefined, directionalOnly = false): string {
  const direction = directionOf(v);
  if (direction === "missing") return "—";
  return directionalOnly ? direction : fmtTI(v as number);
}

export function plainDirection(direction: Direction): string {
  if (direction === "contribution") return "Below pathway";
  if (direction === "liability") return "Above pathway";
  if (direction === "neutral") return "On pathway";
  return "Not available";
}

export function compactMagnitude(v: number): string {
  const absolute = Math.abs(v);
  if (absolute >= 1_000_000) return `${(absolute / 1_000_000).toFixed(2)}M`;
  if (absolute >= 1_000) return `${(absolute / 1_000).toFixed(0)}k`;
  return absolute.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

export function plainOutcome(v: number | undefined, directionalOnly = false): string {
  const direction = directionOf(v);
  if (direction === "missing") return "Not available";
  if (directionalOnly) return plainDirection(direction);
  if (direction === "neutral") return "On pathway";
  return `${compactMagnitude(v as number)} ${direction === "contribution" ? "below" : "above"}`;
}

export function ndcImpactLabel(direction: Direction): string {
  if (direction === "contribution") return "NDC contribution";
  if (direction === "liability") return "NDC lock-in";
  if (direction === "neutral") return "NDC aligned";
  return "NDC result unavailable";
}

export function impactDirectionWord(direction: Direction): string {
  if (direction === "contribution") return "contribution";
  if (direction === "liability") return "lock-in";
  if (direction === "neutral") return "aligned";
  return "unavailable";
}
