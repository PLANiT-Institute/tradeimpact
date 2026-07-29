"use client";
// Interactive calculator: adjust exposed parameters, recompute via the Python function
// wrapping ti_framework (option A — single source of truth, no TS reimplementation).
import { useCallback, useEffect, useRef, useState } from "react";
import AnnualLines from "@/components/AnnualLines";
import DecompBars from "@/components/DecompBars";
import ScenarioCards from "@/components/ScenarioCards";
import { SCENARIO_LABELS, SCENARIOS, type CohortResult, type Scenario } from "@/lib/shared";

type Inputs = {
  firm: string;
  cohort_year: number;
  countries: Record<string, CountryIn>;
  support: { lifetime_T: number; vkt: Record<string, number>; [k: string]: unknown };
  placements: PlacementIn[];
  config?: Record<string, unknown>;
  [k: string]: unknown;
};
type CountryIn = {
  name?: string;
  r_fleet: Record<string, number | null>;
  r_power: Record<string, number | null>;
  [k: string]: unknown;
};
type PlacementIn = {
  country: string;
  brand?: string;
  model?: string;
  powertrain: string;
  units?: number;
  eta_ev?: number;
  ice_intensity?: number;
  uf?: number;
  [k: string]: unknown;
};
// The compute API returns the same shape the published reports use (to_json_dict).
type Result = { cohorts: Partial<Record<Scenario, CohortResult>> };

export default function Calculator({ template }: { template: Inputs }) {
  const [inputs, setInputs] = useState<Inputs>(template);
  const [result, setResult] = useState<Result | null>(null);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const controller = useRef<AbortController | null>(null);
  const requestSequence = useRef(0);

  const recompute = useCallback((payload: Inputs) => {
    if (timer.current) clearTimeout(timer.current);
    controller.current?.abort();
    const sequence = ++requestSequence.current;
    setError("");
    setStatus("updating…");
    timer.current = setTimeout(async () => {
      const activeController = new AbortController();
      controller.current = activeController;
      setStatus("computing…");
      try {
        const res = await fetch("/api/compute", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
          signal: activeController.signal,
        });
        if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
        const nextResult = (await res.json()) as Result;
        if (sequence !== requestSequence.current) return;
        setResult(nextResult);
        setError("");
        setStatus("");
      } catch (e) {
        if (activeController.signal.aborted || sequence !== requestSequence.current) return;
        setStatus("");
        setResult(null);
        setError(
          "Compute request failed. On a local machine, start scripts/dev_compute.py and " +
            "run dev with TI_COMPUTE_URL set. Detail: " +
            String(e).slice(0, 200),
        );
      } finally {
        if (sequence === requestSequence.current) controller.current = null;
      }
    }, 350);
  }, []);

  useEffect(() => {
    recompute(template);
    return () => {
      if (timer.current) clearTimeout(timer.current);
      controller.current?.abort();
      requestSequence.current += 1;
    };
  }, [recompute, template]);

  const update = (fn: (draft: Inputs) => void) => {
    const next = structuredClone(inputs);
    fn(next);
    setInputs(next);
    recompute(next);
  };

  const reset = () => {
    const next = structuredClone(template);
    setInputs(next);
    recompute(next);
  };

  const T = inputs.support.lifetime_T;
  const totals = result
    ? (Object.fromEntries(
        SCENARIOS.filter((s) => result.cohorts[s]).map((s) => [s, result.cohorts[s]!.total_tCO2e]),
      ) as Partial<Record<Scenario, number>>)
    : {};
  const annual = result
    ? (Object.fromEntries(
        SCENARIOS.filter((s) => result.cohorts[s] && !result.cohorts[s]!.directional_only).map(
          (s) => [s, result.cohorts[s]!.annual_tCO2e],
        ),
      ) as Partial<Record<Scenario, number[]>>)
    : {};
  const directionalOnly = result
    ? (Object.fromEntries(
        SCENARIOS.filter((s) => result.cohorts[s]).map((s) => [s, result.cohorts[s]!.directional_only]),
      ) as Partial<Record<Scenario, boolean>>)
    : {};

  return (
    <div className="calc-layout">
      <aside className="calc-controls">
        <div className="calc-control-header">
          <div><span>Working assumptions</span><h3>NDC impact inputs</h3></div>
          <button type="button" className="reset-button" onClick={reset}>Reset</button>
        </div>

        <div className="control-group">
          <label>
            Vehicle lifetime <span className="val">{T} yr</span>
          </label>
          <input
            aria-label="Vehicle lifetime in years"
            type="range"
            min={8}
            max={22}
            step={1}
            value={T}
            onChange={(e) =>
              update((d) => {
                d.support.lifetime_T = Number(e.target.value);
              })
            }
          />
        </div>

        <h4 className="control-section-title">Market assumptions</h4>
        {Object.entries(inputs.countries).map(([code, c]) => (
          <details className="control-disclosure" key={code}>
            <summary><span>{c.name ?? code}</span><small>{code}</small></summary>
            <div className="control-disclosure-body">
              {(["r_fleet", "r_power"] as const).map((rk) =>
                (["s1", "s2", "s3"] as const).map((sk) => {
                  const v = c[rk]?.[sk];
                  if (v === null || v === undefined) return null;
                  return (
                    <div key={`${code}${rk}${sk}`}>
                      <label>
                        {rk === "r_fleet" ? "Fleet reduction" : "Power reduction"} · {SCENARIO_LABELS[sk.toUpperCase() as Scenario]}{" "}
                        <span className="val">{(v * 100).toFixed(2)} %/yr</span>
                      </label>
                      <input
                        aria-label={`${c.name ?? code} ${rk} ${sk} annual reduction rate`}
                        type="range"
                        min={0}
                        max={0.12}
                        step={0.001}
                        value={v}
                        onChange={(e) =>
                          update((d) => {
                            d.countries[code][rk][sk] = Number(e.target.value);
                          })
                        }
                      />
                    </div>
                  );
                }),
              )}
              <label>
                Annual distance <span className="val">{inputs.support.vkt[code] ?? "—"} km</span>
              </label>
              {inputs.support.vkt[code] !== undefined && (
                <input
                  aria-label={`${c.name ?? code} annual driving distance`}
                  type="range"
                  min={6000}
                  max={22000}
                  step={500}
                  value={inputs.support.vkt[code]}
                  onChange={(e) =>
                    update((d) => {
                      d.support.vkt[code] = Number(e.target.value);
                    })
                  }
                />
              )}
            </div>
          </details>
        ))}

        <h4 className="control-section-title">Vehicle assumptions</h4>
        {inputs.placements.map((p, i) => (
          <details className="control-disclosure" key={i}>
            <summary><span>{p.brand} {p.model}</span><small>{p.powertrain} · {p.country}</small></summary>
            <div className="control-disclosure-body">
              <label>
                Represented units <span className="val">{p.units?.toLocaleString()}</span>
              </label>
              <input
                aria-label={`${p.brand} ${p.model} represented units`}
                type="range"
                min={0}
                max={Math.max(200000, Math.ceil(((p.units ?? 0) * 1.5) / 5000) * 5000)}
                step={5000}
                value={p.units ?? 0}
                onChange={(e) =>
                  update((d) => {
                    d.placements[i].units = Number(e.target.value);
                  })
                }
              />
              {p.eta_ev !== undefined && (
                <>
                  <label>
                    EV efficiency <span className="val">{p.eta_ev.toFixed(3)} kWh/km</span>
                  </label>
                  <input
                    aria-label={`${p.brand} ${p.model} EV efficiency`}
                    type="range"
                    min={0.1}
                    max={0.3}
                    step={0.005}
                    value={p.eta_ev}
                    onChange={(e) =>
                      update((d) => {
                        d.placements[i].eta_ev = Number(e.target.value);
                      })
                    }
                  />
                </>
              )}
              {p.ice_intensity !== undefined && (
                <>
                  <label>
                    Tailpipe intensity <span className="val">{(p.ice_intensity * 1000).toFixed(0)} gCO₂/km</span>
                  </label>
                  <input
                    aria-label={`${p.brand} ${p.model} tailpipe intensity`}
                    type="range"
                    min={0.08}
                    max={0.3}
                    step={0.005}
                    value={p.ice_intensity}
                    onChange={(e) =>
                      update((d) => {
                        d.placements[i].ice_intensity = Number(e.target.value);
                      })
                    }
                  />
                </>
              )}
              {p.uf !== undefined && (
                <>
                  <label>
                    Utility factor <span className="val">{p.uf.toFixed(2)}</span>
                  </label>
                  <input
                    aria-label={`${p.brand} ${p.model} utility factor`}
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={p.uf}
                    onChange={(e) =>
                      update((d) => {
                        d.placements[i].uf = Number(e.target.value);
                      })
                    }
                  />
                </>
              )}
            </div>
          </details>
        ))}
        <div className="calc-status" aria-live="polite">{status}</div>
      </aside>

      <section className="calc-results">
        <div className="calc-result-header">
          <div><span>Impact of represented {inputs.cohort_year} sales</span><h2>National NDC result</h2></div>
          <span
            className={`live-status ${error ? "error" : status ? "busy" : ""}`}
            role="status"
            aria-live="polite"
          >
            {error ? "Service unavailable" : status || (result ? "Up to date" : "Starting engine")}
          </span>
        </div>
        {error && (
          <div className="panel" role="alert">
            <p className="calc-error" style={{ fontSize: 13 }}><strong>Calculation service unavailable.</strong> The source report is unchanged.</p>
            <details className="table-view"><summary>Technical detail</summary><p className="mono panel-note">{error}</p></details>
          </div>
        )}
        {result && (
          <>
            <ScenarioCards
              totals={totals}
              unit="tCO₂e · cohort lifetime"
              directionalOnly={directionalOnly}
            />
            <p className="panel-note">
              NDC is the primary result. Current-policy and 1.5°C cases show how sensitive
              that conclusion is to a slower or faster transition. Plug-in hybrid results
              should be read as upper-bound estimates.
            </p>
          </>
        )}
        {result && (
          <>
            {Object.keys(annual).length > 0 && (
              <>
                <h2>How the sales impact develops over product life</h2>
                <div className="panel">
                  <AnnualLines series={annual} xLabel="year since sale" yLabel="tCO₂e / yr" />
                </div>
              </>
            )}
            <h2>What drives the NDC impact</h2>
            <div className="panel">
              {result.cohorts.S2?.directional_only ? (
                <p className="panel-note">Only the NDC-impact direction can be shown because the underlying benchmark is incomplete.</p>
              ) : (
                <>
                  <h3>By NDC market</h3>
                  <DecompBars data={result.cohorts.S2?.by_country ?? {}} unit="tCO₂e" />
                  <h3>By powertrain</h3>
                  <DecompBars data={result.cohorts.S2?.by_powertrain ?? {}} unit="tCO₂e" />
                </>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
