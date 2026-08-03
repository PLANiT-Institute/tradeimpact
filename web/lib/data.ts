// Typed loaders for the published dataset (data/published, copied to public/data at build).
// The web app never computes TI — it renders what the engine produced. All contract
// types live in ./shared (client-safe) and are re-exported here.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type {
  AlignmentBenchmark,
  CompanyMetric,
  Firm,
  FirmResult,
  Meta,
  PublishedCountry,
  SectorProfile,
  SourceRecord,
} from "./shared";

export * from "./shared";

const DATA_DIR = join(process.cwd(), "public", "data");

function read<T>(name: string): T {
  return JSON.parse(readFileSync(join(DATA_DIR, name), "utf-8")) as T;
}

export const getFirms = (): Firm[] => read<Firm[]>("firms.json");
export const getMeta = (): Meta => read<Meta>("meta.json");
export const getCountries = (): PublishedCountry[] => read<PublishedCountry[]>("countries.json");
export const getSectors = (): SectorProfile[] => read<SectorProfile[]>("sectors.json");
export const getCompanyMetrics = (): CompanyMetric[] =>
  read<CompanyMetric[]>("company_metrics.json");
export const getBenchmarks = (): AlignmentBenchmark[] =>
  read<AlignmentBenchmark[]>("benchmarks.json");
export const getSources = (): SourceRecord[] => read<SourceRecord[]>("sources.json");
export const getContract = (): Record<string, string[]> =>
  read<Record<string, string[]>>("contract.json");
export const getFirmResult = (slug: string): FirmResult =>
  read<FirmResult>(`${slug}.json`);
