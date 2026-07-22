"use client";
// Interactive calculator: adjust exposed parameters, recompute via the Python function
// wrapping ti_framework (option A — single source of truth, no TS reimplementation).
import { useCallback, useEffect, useRef, useState } from "react";
import AnnualLines from "@/components/AnnualLines";
import DecompBars from "@/components/DecompBars";
import ScenarioCards from "@/components/ScenarioCards";
import { SCENARIOS, type Scenario } from "@/lib/shared";

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
type Result = {
  cohorts: Record<
    Scenario,
    {
      total_tCO2e: number;
      directional_only: boolean;
      by_country: Record<string, number>;
      by_powertrain: Record<string, number>;
      annual_tCO2e: number[];
    }
  >;
};

export default function Calculator({ template }: { template: Inputs }) {
  const [inputs, setInputs] = useState<Inputs>(template);
  const [result, setResult] = useState<Result | null>(null);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const recompute = useCallback((payload: Inputs) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      setStatus("computing…");
      try {
        const res = await fetch("/api/compute", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
        setResult(await res.json());
        setError("");
        setStatus("");
      } catch (e) {
        setStatus("");
        setError(
          "Compute API unreachable. On a local machine, start scripts/dev_compute.py and " +
            "run dev with TI_COMPUTE_URL set. Detail: " +
            String(e).slice(0, 200),
        );
      }
    }, 350);
  }, []);

  useEffect(() => {
    recompute(inputs);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const update = (fn: (draft: Inputs) => void) => {
    const next = structuredClone(inputs);
    fn(next);
    setInputs(next);
    recompute(next);
  };

  const T = inputs.support.lifetime_T;
  const totals = result
    ? (Object.fromEntries(
        SCENARIOS.filter((s) => result.cohorts[s]).map((s) => [s, result.cohorts[s].total_tCO2e]),
      ) as Partial<Record<Scenario, number>>)
    : {};
  const annual = result
    ? (Object.fromEntries(
        SCENARIOS.filter((s) => result.cohorts[s]).map((s) => [s, result.cohorts[s].annual_tCO2e]),
      ) as Partial<Record<Scenario, number[]>>)
    : {};

  return (
    <div className="calc-layout">
      <aside className="calc-controls">
        <h3 style={{ marginTop: 0 }}>Parameters</h3>

        <label>
          Vehicle lifetime T <span className="val">{T} yr</span>
        </label>
        <input
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

        {Object.entries(inputs.countries).map(([code, c]) => (
          <div key={code}>
            <h3 style={{ marginTop: 20 }}>{c.name ?? code}</h3>
            {(["r_fleet", "r_power"] as const).map((rk) =>
              (["s1", "s2", "s3"] as const).map((sk) => {
                const v = c[rk]?.[sk];
                if (v === null || v === undefined) return null;
                return (
                  <div key={`${code}${rk}${sk}`}>
                    <label>
                      {rk === "r_fleet" ? "fleet" : "power"} {sk.toUpperCase()}{" "}
                      <span className="val">{(v * 100).toFixed(2)} %/yr</span>
                    </label>
                    <input
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
              annual distance D_c <span className="val">{inputs.support.vkt[code] ?? "—"} km</span>
            </label>
            {inputs.support.vkt[code] !== undefined && (
              <input
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
        ))}

        <h3 style={{ marginTop: 20 }}>Vehicles</h3>
        {inputs.placements.map((p, i) => (
          <div key={i}>
            <label style={{ color: "var(--navy)", fontWeight: 600 }}>
              {p.brand} {p.model} · {p.powertrain} ({p.country})
            </label>
            <label>
              units <span className="val">{p.units?.toLocaleString()}</span>
            </label>
            <input
              type="range"
              min={0}
              max={200000}
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
                  η_EV <span className="val">{p.eta_ev.toFixed(3)} kWh/km</span>
                </label>
                <input
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
                  I_ICE <span className="val">{(p.ice_intensity * 1000).toFixed(0)} gCO₂/km</span>
                </label>
                <input
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
                  Utility Factor <span className="val">{p.uf.toFixed(2)}</span>
                </label>
                <input
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
        ))}
        <div className="calc-status">{status}</div>
      </aside>

      <section>
        {error && (
          <div className="panel">
            <p className="calc-error mono" style={{ fontSize: 13 }}>
              {error}
            </p>
          </div>
        )}
        <ScenarioCards totals={totals} unit="tCO₂e · cohort lifetime" />
        <p className="panel-note">
          Recomputed by the same ti_framework engine that builds the static reports — the
          browser never does the math. PHEV results are upper-bound estimates (UF caveat).
        </p>
        {result && (
          <>
            <h2>Annual TI flow</h2>
            <div className="panel">
              <AnnualLines series={annual} xLabel="t" yLabel="tCO₂e / yr" />
            </div>
            <h2>Decomposition (S2)</h2>
            <div className="panel">
              <h3>By operating country</h3>
              <DecompBars data={result.cohorts.S2?.by_country ?? {}} unit="tCO₂e" />
              <h3>By powertrain</h3>
              <DecompBars data={result.cohorts.S2?.by_powertrain ?? {}} unit="tCO₂e" />
            </div>
          </>
        )}
      </section>
    </div>
  );
}
