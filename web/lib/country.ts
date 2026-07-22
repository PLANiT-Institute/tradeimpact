// Country-centric regrouping of published engine results. Display-only: no TI is
// computed here, and firm values are never summed across firms (Whitepaper §9.2 —
// individual TI claims do not physically sum against a shared benchmark).
import { getFirmResult, getFirms, SCENARIOS, type FirmResult, type Scenario } from "./data";

export interface CountryFirmRow {
  slug: string;
  firm: string;
  byScenario: Partial<Record<Scenario, number>>; // TI_country,c per scenario
  excludedS2Reason?: string;
  crossover: FirmResult["crossover"];
}

export interface CountryView {
  code: string;
  name: string;
  benchmarkStatus: string;
  flagReason?: string;
  source?: string;
  warnings: string[];
  firms: CountryFirmRow[];
}

export function getCountryViews(): CountryView[] {
  const views = new Map<string, CountryView>();
  for (const f of getFirms().filter((x) => x.runnable)) {
    const r = getFirmResult(f.slug);
    const inputCountries =
      (r.inputs?.countries as Record<
        string,
        { name?: string; status?: string; source?: string; warnings?: string[] }
      >) ?? {};
    const codes = new Set<string>();
    for (const s of SCENARIOS) {
      for (const c of Object.keys(r.cohorts[s]?.by_country ?? {})) codes.add(c);
      for (const c of Object.keys(r.cohorts[s]?.excluded_flag_markets ?? {})) codes.add(c);
    }
    for (const code of codes) {
      const ic = inputCountries[code];
      let v = views.get(code);
      if (!v) {
        v = {
          code,
          name: ic?.name ?? code,
          benchmarkStatus: ic?.status ?? "COMPUTED",
          flagReason: r.data_quality.flag_markets[code],
          source: ic?.source,
          warnings: ic?.warnings ?? [],
          firms: [],
        };
        views.set(code, v);
      }
      const byScenario: Partial<Record<Scenario, number>> = {};
      for (const s of SCENARIOS) {
        const val = r.cohorts[s]?.by_country?.[code];
        if (val !== undefined) byScenario[s] = val;
      }
      v.firms.push({
        slug: f.slug,
        firm: r.firm,
        byScenario,
        excludedS2Reason: r.cohorts.S2?.excluded_flag_markets?.[code],
        crossover: r.crossover.filter((c) => c.country === code),
      });
    }
  }
  return [...views.values()].sort((a, b) => a.code.localeCompare(b.code));
}

export function getCountryView(code: string): CountryView | undefined {
  return getCountryViews().find((v) => v.code === code);
}
