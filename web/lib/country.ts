// Country-centric regrouping of published engine results. Display-only: no TI is
// computed here, and firm values are never summed across firms (Whitepaper §9.2 —
// individual TI claims do not physically sum against a shared benchmark).
import {
  getCountries,
  getFirmResult,
  getFirms,
  SCENARIOS,
  type Firm,
  type FirmResult,
  type Scenario,
} from "./data";

export interface CountryFirmRow {
  slug: string;
  firm: string;
  byScenario: Partial<Record<Scenario, number>>; // TI_country,c per scenario
  directionalOnly: Partial<Record<Scenario, boolean>>;
  excludedS2Reason?: string;
  crossover: FirmResult["crossover"];
  basis?: Firm["basis"];
  assessedUnits: number;
  firmCoverage?: number;
}

export interface CountryView {
  code: string;
  name: string;
  cohortYear?: number;
  benchmarkStatus: string;
  flagReason?: string;
  source?: string;
  /** Sector benchmark parameters from the canonical country contract. */
  gridIntensity?: number;
  rFleet: Record<string, number>;
  rPower: Record<string, number>;
  warnings: string[];
  firms: CountryFirmRow[];
}

export function getCountryViews(): CountryView[] {
  const views = new Map<string, CountryView>(
    getCountries().map((country) => [
      country.code,
      {
        code: country.code,
        name: country.name,
        benchmarkStatus: country.status,
        flagReason: country.flag_reason,
        source: country.source,
        gridIntensity: country.grid_intensity,
        rFleet: country.r_fleet,
        rPower: country.r_power,
        warnings: country.warnings ?? [],
        firms: [],
      },
    ]),
  );
  const countryContract = new Map(getCountries().map((country) => [country.code, country]));
  for (const f of getFirms().filter((x) => x.runnable && !x.illustrative)) {
    const r = getFirmResult(f.slug);
    const placements =
      (r.inputs?.placements as Array<{ country: string; units?: number }> | undefined) ?? [];
    const codes = new Set<string>();
    for (const s of SCENARIOS) {
      for (const c of Object.keys(r.cohorts[s]?.by_country ?? {})) codes.add(c);
      for (const c of Object.keys(r.cohorts[s]?.excluded_flag_markets ?? {})) codes.add(c);
    }
    for (const code of codes) {
      const country = countryContract.get(code);
      if (!country) throw new Error(`published country contract missing ${code}`);
      let v = views.get(code);
      if (!v) throw new Error(`published country view missing ${code}`);
      v.cohortYear = r.cohort_year;
      const byScenario: Partial<Record<Scenario, number>> = {};
      const directionalOnly: Partial<Record<Scenario, boolean>> = {};
      for (const s of SCENARIOS) {
        const val = r.cohorts[s]?.by_country?.[code];
        if (val !== undefined) byScenario[s] = val;
        if (r.cohorts[s]) directionalOnly[s] = r.cohorts[s].directional_only;
      }
      v.firms.push({
        slug: f.slug,
        firm: r.firm,
        byScenario,
        directionalOnly,
        excludedS2Reason: r.cohorts.S2?.excluded_flag_markets?.[code],
        crossover: r.crossover.filter((c) => c.country === code),
        basis: f.basis,
        assessedUnits: placements
          .filter((placement) => placement.country === code)
          .reduce((total, placement) => total + (placement.units ?? 0), 0),
        firmCoverage: f.coverage_ratio,
      });
    }
  }
  return [...views.values()].sort((a, b) => a.code.localeCompare(b.code));
}

export function getCountryView(code: string): CountryView | undefined {
  return getCountryViews().find((v) => v.code === code);
}
