// Typed loaders for the published dataset (data/published, copied to public/data at build).
// The web app never computes TI — it renders what the engine produced. All contract
// types live in ./shared (client-safe) and are re-exported here.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Firm, FirmResult, Meta, PublishedCountry } from "./shared";

export * from "./shared";

const DATA_DIR = join(process.cwd(), "public", "data");

function read<T>(name: string): T {
  return JSON.parse(readFileSync(join(DATA_DIR, name), "utf-8")) as T;
}

export const getFirms = (): Firm[] => read<Firm[]>("firms.json");
export const getMeta = (): Meta => read<Meta>("meta.json");
export const getCountries = (): PublishedCountry[] => read<PublishedCountry[]>("countries.json");
export const getContract = (): Record<string, string[]> =>
  read<Record<string, string[]>>("contract.json");
export const getFirmResult = (slug: string): FirmResult =>
  read<FirmResult>(`${slug}.json`);

export function getCalculatorFirm(requestedSlug?: string): Firm {
  const runnable = getFirms().filter((firm) => firm.runnable);
  const requested = runnable.find((firm) => firm.slug === requestedSlug);
  if (requested) return requested;

  const defaultFirm = runnable.find((firm) => !firm.illustrative) ?? runnable[0];
  if (!defaultFirm) throw new Error("No runnable firm is available for the calculator");
  return defaultFirm;
}
