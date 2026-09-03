# Stages ST08–ST10 — benchmark, impact, aggregation

Steps 3 to 5 of the research process, in `script/auto/model/`. All three are running **EU27 only**
as of 2026-09-04, on the markets the data supports: `build_reference.py` and `build_ti.py` have
produced their outputs, `aggregate_country.py` exists and has not yet written its own. One thing is
built when it is needed — a benchmark for the markets that are ready, not a framework for markets
that are not.

Output column schemas and current row counts: [`../toolbox/data-schema.md`](../toolbox/data-schema.md) §6.

---

## ST08 — Reference benchmark construction

**Main goal.** Per importer and scenario, the dynamic Layer 1 benchmark
`E_ref,c(t) = I_fleet,seg,c(t) × D_c` over the vehicle lifetime — the reference every TI result is
measured against.

**Script.** `script/auto/model/build_reference.py`.

**Activity.** Select the Layer 1 method per market against guideline §6.1 and record why. Compute
the base-year fleet intensity as sector emissions ÷ (stock × distance); derive `r_fleet` per
scenario from the transport pathway and `r_power` **independently** from the power pathway
(`N-07`); record pro-rata use, target-hierarchy level and any post-target extrapolation; and flag
implausible or already-met pathways rather than adjusting them. The scenario-source field names
the document each rate actually came from, never a canonical scenario label the value did not come
from.

**Phases served.** PH1/3 (the benchmark table); PH2/2 and PH2/5 (pro-rata and non-linearity
evidence); PH4/2–3 (grid-intensity and IMO CII benchmarks).

**Consumes.** `country_emissions_eu27.csv` (ST03, ktCO2 and gCO2e/kWh), `emission_targets_eu27.csv`
(ST04, fraction per year), `vehicle_usage_eu27.csv` (ST05, vehicles and traffic), `target_set.csv`
(ST01, planned);
assumptions `A-01`, `A-02`, `A-03`, `A-07`, `A-09`, `A-11`.

**Produces.** `data/auto/output/destination_parameters_eu27.csv` (27 rows — the derived distance,
fleet intensity base, grid intensity, mean fleet age and lifetime bracket per market, each with its
tier, reference year, derivation and warnings) and `reference_trajectories_eu27.csv` (1,899 rows —
`E_ref(t)` and `G(t)` per market × scenario × year). Consumed by ST09, ST10, ST11, ST12, ST14.

**Methodology.** Whitepaper §3.1; guideline §2.1–§2.3 (Methods A, B, C), §4.7 (scenario sources),
§6.1–§6.2 (method selection and the five-step NDC verification). Failure modes and the validation
test are in [`../process/general.md`](../process/general.md) §5.

**Owners.** `climate-risk-modeller` (owner), `developer` (implementation), `math-reviewer`
(independent re-derivation of every rate and base-year quotient), `auditor` (method adequacy).

**Stop when.** Three scenarios per importer for both rates from separately named sources; method
choice, pro-rata use, target level and extrapolation recorded; flags raised rather than smoothed;
every rate re-derived by hand from the primary document.

**Repeat when.** A new NDC or pathway vintage (ST04); a change to base-year emissions, stock or
distance (ST03, ST05); a PH2 rule adoption such as a sector-split correction; a failed
cross-validation against Method C or against observed recent sector data.

**Backward moves.** A base-year intensity far outside the peer range returns to ST03 and ST05
before the benchmark is used. A market with no evaluable arithmetic returns to ST04 and ST01.
Neither is resolved by choosing a more convenient rate.

---

## ST09 — Impact computation

**Main goal.** Per model × market × powertrain × scenario: the annual TI gap over the lifetime,
the cumulative lifetime avoidance or addition, and the Crossover Point.

**Script.** `script/auto/model/build_ti.py`.

**Activity.** Build the Layer 2 trajectory per powertrain case — ICE and non-plug-in HEV fixed at
sale-year efficiency, BEV declining with the grid, PHEV as the utility-factor composite — subtract
it from the Layer 1 benchmark to get `TI_gap,v,c(t)`, sum over `t = 0 … T−1` (T terms, inclusive),
and locate the year the gap changes sign. Any cell with a missing input produces no result and is
counted as withheld with its units (`N-02`).

**Phases served.** PH1/4; PH2/3–4 (the sensitivity behaviour the propagation rule is built on);
PH3/1 (the computation the open-source model packages); PH4/2–3.

**Consumes.** `reference_trajectories_eu27.csv` and `destination_parameters_eu27.csv` (ST08),
`sales_eea_eu27_2024.csv` (ST02, vehicles), `vehicle_technology_eea_2024.csv` and
`method/real_world_correction.csv` (ST06, gCO2/km, Wh/km, multiplier); assumptions `A-02`,
`A-04`, `A-05`, `A-06`, `A-08`.

**Produces.** `data/auto/output/ti_by_model_eu27.csv` (3,321 rows — per cell and scenario, with
`e_prod_year0`, `e_ref_year0`, per-vehicle and total TI), `ti_annual_eu27.csv` (150 rows — the
annual TI flow with surviving vehicles) and `ti_withheld_eu27.csv` (179 rows — every cell that
produced no result, with its unit count and reason). **Crossover year is not yet an output** — it
is required by `D-01`'s Month 7 activity and is the next addition here (`F-06`). Consumed by ST10,
ST11, ST13, ST14.

**Methodology.** Whitepaper §3.2–§3.5, §3.7; guideline §3.3–§3.5, §4.1–§4.3. Crossover closed
forms reuse the archived engine's derivation (`archive/ti-framework/NOTES.md` §4) as prior work
rather than re-inventing it.

**Owners.** `data-scientist` and `developer` (implementation), `climate-risk-modeller` (parameter
choices), `math-reviewer` (independent re-derivation of each headline cell by a second route),
`tester` (analytical-solution tests), `auditor`.

**Stop when.** Every cell in the target set has a result or a withheld row; all three scenarios
present (`N-05`); the T-term summation convention verified against an analytical case; crossover
reported per cell with the `C-05` range treatment applied or `B-07` named as blocking it.

**Repeat when.** Any consumed input changes; a Layer 2 case is corrected; T, the utility factor or
a correction factor changes; PH2 adopts a rule.

**Backward moves.** A PHEV cell with no sourced utility factor returns to ST06 and is withheld,
never defaulted. A cell whose sign flips under the mandatory sensitivities is reported as
directionally indeterminate and does not become a headline.

---

## ST10 — Country and company aggregation

**Main goal.** Importer-country and exporter-company totals with the decomposition identity
intact, tiers declared and withheld units visible.

**Script.** `script/auto/model/aggregate_country.py` — written, not yet run to output.

**Activity.** Sum `V_c,v × TI_product,v,c,S` to country, powertrain and company level; check the
identity `TI_cohort = Σ_c TI_country = Σ_v TI_type` numerically rather than by construction; attach
the per-layer data-quality declaration (guideline §5.3); and report withheld units beside every
total so a reader sees what the total does not cover. Region-level sales rows
(`destination_level = region`, which the Kia IR workbook forces) are aggregated separately and
never merged into a country total.

**Phases served.** PH1/5; PH3/2 (what the dashboard presents); PH4/2–3.

**Consumes.** `ti_by_model_eu27.csv`, `ti_annual_eu27.csv`, `ti_withheld_eu27.csv` (ST09);
`destination_parameters_eu27.csv` (ST08) for the tier declaration.

**Produces.** `data/auto/output/ti_country_eu27.csv`, `ti_powertrain_eu27.csv`,
`ti_company_eu27.csv`, and the data-quality declaration. Consumed by ST11, ST13, ST14.

**Methodology.** Whitepaper §3.6–§3.8; guideline §4.4–§4.6, §5.1, §5.3.

**Owners.** `data-scientist` (owner), `developer`, `math-reviewer` (identity and re-derivation),
`auditor`.

**Stop when.** The identity holds to the declared tolerance; every total carries units covered and
withheld, both tier declarations and all three scenarios; region-level rows are reported
separately.

**Repeat when.** Any ST09 re-run; a tier change in ST05 or ST06; a target-set change in ST01.

**Backward moves.** An identity failure returns to ST09 and is never reconciled by adjusting a
total. A total whose withheld share could change its sign is reported as directional only, which
sends the claim wording back to ST14.

**Known gap — rolling portfolio TI.** The whitepaper calls `TI_portfolio` the "primary disclosure
metric" (§3.8) and it needs T years of sales cohorts. Only single-cohort data exists (EEA 2024,
plus IR workbooks for later years), so this output is **unserved** and is carried as a finding in
[`../tracker.md`](../tracker.md) rather than approximated from one cohort.
