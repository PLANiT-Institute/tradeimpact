# Trade Impact (TI) Framework
## Power Sector — Implementation Technical Guideline

**Version 1.0 · September 2026 · PLANiT Institute**

> **Scope of v1.0.** First guideline for the power sector: the overseas generating units that a
> firm owns, built, supplied or financed, measured against the grid of the country they feed.
> It follows the whitepaper v1.6 sign convention (TI = product emissions − benchmark emissions;
> positive is tonnes **added**) and the two-scenario architecture of the automotive guideline
> v1.9. What is specific to power — the unit of analysis, the role-based attribution, the
> emission-factor hierarchy and the phase distinction — is set out in Part 1 §1, §3 and §4.

---

# PART 1 — MATHEMATICAL METHODOLOGY

---

## 1. Foundational Concepts

### 1.1 What the TI score measures

The power TI measures whether a firm's overseas generating units, over their operating life, add
emissions to or avoid emissions from the national inventory of the country they feed, relative to
what that country's grid emits per kilowatt-hour — observed for past years and committed for
future years. It is reported in tonnes of CO₂ and signed as an emissions figure: **positive
means tonnes added** (a carbon lock-in liability), **negative means tonnes avoided**.

The question asked year by year is: does this unit emit more or less per kWh than the grid it
displaces, as that grid moves along the pathway its government has committed to? A fossil unit
is above the grid from the day it starts in most grids and moves further above it every year the
grid decarbonises; a zero-stack unit is below it by construction. The cumulative answer over the
unit's life is the unit TI; attributed to the firms that held a role on it, it is the firm TI.

### 1.2 Emission scope position

The framework measures the net effect on the **destination country's** inventory. Unit
emissions are combustion CO₂ at the stack (inventory category 1.A.1.a, public electricity); the
benchmark is the destination's generation-based grid intensity on the same boundary. Upstream
fuel-cycle emissions, transmission losses and construction emissions are outside both sides. The
firm's own Scope 3 treatment of the project (Category 15 investments, Category 11 for equipment)
is separate and is never netted against TI (§5.4).

### 1.3 Unit of analysis — five required parameters

| parameter | symbol | source |
|---|---|---|
| generating unit (or phase) in destination country *c* | *u*, *c* | Global Energy Monitor tracker |
| commissioning year and end of life | *y₀*, *y₀ + L − 1* | tracker start / retired year; default lifetime *L* by technology |
| annual generation | *G* = *P* · 8760 · *CF* · 10³ kWh | capacity *P* (MW) from the tracker; capacity factor *CF* from the tracker or a technology default |
| unit stack intensity | *I* (gCO₂/kWh) | heat rate × fuel emission factor (§3) |
| firm role, phase and share | *ρ*, *φ*, *s* | role register (§4.3) |

---

## 2. Layer 1 — Destination Grid Benchmark

### 2.1 Definition

The benchmark for unit *u* in country *c* in calendar year *y* under scenario *S* is the
grid carbon intensity *g_c^S(y)*, gCO₂/kWh, and the benchmark emissions are

$$ E_{ref,u}^{S}(y) = G_u \, g_c^{S}(y) \times 10^{-6} \quad [\text{tCO}_2] $$

ASCII: `E_ref(y) = G * g(y) / 1e6`.

### 2.2 Observed years

For every calendar year the published series covers, *g_c(y)* is the observed value, identical
in both scenarios. The pathways diverge only after the latest observation *y_obs*.

### 2.3 Scenario pathways

$$ g_c^{S}(y) = g_c(y_{obs})\,(1 - r_c^{S})^{\,y - y_{obs}} \qquad (y > y_{obs}) $$

ASCII: `g(y) = g(y_obs) * (1 - r) ** (y - y_obs)`.

**S1 — observed trajectory.** *r* from a log-linear fit `ln g = a + b·y` over 2015 to *y_obs*
excluding 2020–2021, `r = 1 − exp(b)`; at least three observations, else S1 is excluded for the
destination. A rising series gives a negative *r* and is flagged.

**S2 — committed policy.** The destination government's own target, read onto grid intensity:
`g_target = g(base) · (1 − reduction)` for a reduction target, `g(base) · target/base` for an
absolute-level target, the stated value for an intensity target; then
`r = 1 − (g_target / g(y_obs))^(1/(y_target − y_obs))`. Floored at S1 where the level is already
met or the observed trend is steeper: committed policy is never read as less ambitious than what
is observed. A business-as-usual-relative target has no absolute level and is recorded as an
exclusion. An economy-wide target applied to the grid is a pro-rata assumption, labelled and
tiered B.

There is no third scenario.

---

## 3. Layer 2 — Unit Emissions

### 3.1 Definition

$$ E_{prod,u}(y) = G_u \, I_u \times 10^{-6} \quad [\text{tCO}_2], \qquad
   I_u = HR_u \cdot EF_{f(u),c} \times 10^{-3} \quad [\text{gCO}_2/\text{kWh}] $$

ASCII: `E_prod(y) = G * I / 1e6`; `I = HR * EF / 1000` with *HR* the heat rate in MJ/kWh and
*EF* the fuel emission factor in kgCO₂/TJ. *I* is fixed at commissioning: a fossil unit's
intensity does not fall over its life, which is the mechanism of the result.

### 3.2 Emission factor hierarchy

1. The destination country's **own** fuel-specific implied factor for public electricity, from
   its national inventory (UNFCCC common reporting table 1.A(a)) — tier A.
2. Otherwise the **IPCC 2006 Guidelines** default for the fuel (Volume 2, Chapter 2, Table 2.2)
   — tier C, with the 95 % bounds carried into the sensitivity.

The fuel is read from the tracker's fuel text through a documented pattern table; a unit whose
fuel matches no row is excluded with that reason.

### 3.3 Heat rate and capacity factor hierarchy

1. The tracker's unit-level estimate (heat rate in Btu/kWh × 1.055056 × 10⁻³ → MJ/kWh) — tier B.
2. Otherwise the technology default: `HR = 3.6 / η_LHV` with the default efficiency and capacity
   factor by fuel and combustion technology — tier C, each row citing its document.

### 3.4 Zero-stack and biogenic units

Nuclear, hydro, wind, solar and geothermal units have *I* = 0; their TI is `−E_ref` and negative
by construction. Bioenergy units carry a biogenic CO₂ figure, computed with the IPCC wood factor
and **reported in its own column**, never inside the fossil total, following inventory practice.

---

## 4. Layer 3 — Integration and Attribution

### 4.1 Annual gap and lifetime TI per unit

$$ TI_u^{S}(y) = E_{prod,u}(y) - E_{ref,u}^{S}(y), \qquad
   TI_u^{S} = \sum_{y = y_0}^{y_0 + L - 1} TI_u^{S}(y) $$

ASCII: `TI(y) = E_prod(y) − E_ref(y)`; `TI = Σ TI(y)` over the operating years. Years before the
first grid observation are dropped and counted, never filled. Two totals are published: the
lifetime total and the **remaining** total from the analysis year (first year after *y_obs*)
forward — the part that is still a choice.

### 4.2 Crossover

The first year with `TI(y) > 0`. For most fossil units it is the commissioning year; for a unit
that starts below its grid it is the year the grid falls past it.

### 4.3 Attribution by role — the power-specific rule

A power project has several firms in several capacities. The register records, per firm × unit ×
role, three levels of that role and the share:

| level | symbol | values |
|---|---|---|
| phase | *φ* | development, construction, investment, operation, finance |
| tier-1 role | *ρ* | developer, EPC contractor, equipment supplier, equity owner, O&M contractor, lender, ECA cover |
| tier-2 scope | *σ* | the scope as the source states it: EPC lead, EPC consortium member, civil works, port works, balance of plant, boiler supply, steam or gas turbine supply, generator supply, equity direct, equity through a parent, O&M contract, operator of record, project loan, buyer's credit, insurance cover, guarantee — or a *scope not stated* key where the source names the tier-1 role only |

with the **share** *s* the firm carried (equity fraction, contract fraction, scope fraction, debt
fraction), each with the page it was read from.

**Attribution is at tier 1**, so the unit enters a firm's account once per tier-1 role:

$$ TI_{firm,\rho,u}^{full} = TI_u, \qquad TI_{firm,\rho,u}^{weighted} = s \cdot TI_u $$

A firm whose source names several scopes of one tier-1 role on a unit — civil works and port
works under the same EPC contract — carries one row, with the most specific scope in *σ* and every
stated scope listed beside it. A blank share yields a blank weighted figure. Rows of **different
tier-1 roles are never summed** into one firm total; the firm table is keyed by firm × tier-1 role
× scenario. Because phase, role, scope and share are all columns, any later weighting convention
(equity-only, construction-only, phase-weighted, EPC-lead-only) is a query on the published table,
not a re-collection.

### 4.4 Phase distinction

Construction-side roles (EPC, equipment) and operation-side roles (equity, O&M) answer different
questions — who locked the intensity in, and who runs it against the falling grid — and finance
roles a third. The phase column keeps them apart in every output; a reader who wants only the
construction-side attribution filters on it.

### 4.5 Two-scenario reporting

Every figure is reported under S1 and S2 together. A destination with no usable S2 anchor is
reported under S1 and listed in the S2 exclusions with the reason.

---

## 5. Reporting Requirements

### 5.1 Required outputs

| table | grain | content |
|---|---|---|
| `ti_power_annual` | unit × scenario × year | generation, grid, both sides, gap, cumulative |
| `ti_power_by_unit` | unit × scenario | inputs used with their sources and tiers, lifetime and remaining TI, crossover, coordinates |
| `ti_power_by_role` | firm × tier-1 role × unit × scenario | full and share-weighted TI, phase, tier-2 scope(s), share, origin, source |
| `ti_power_company` | firm × tier-1 role × scenario | sums per role, both weightings, scopes on file, units with and without a share |
| `ti_power_excluded` | unit | reason no result exists |
| `emission_targets_power` (+ exclusions) | destination × scenario | rate, anchor, derivation |

### 5.2 Mandatory sensitivity parameters

Four dimensions, each varied one at a time and only for the units whose value is a class default:

| dimension | band | applies to |
|---|---|---|
| operating lifetime | the technology default's low and high years | units with no published retirement year |
| capacity factor | the technology default's low and high | units with no published capacity factor |
| thermal efficiency | the technology default's low and high net-calorific-value efficiency, which moves the heat rate 3.6/η and so the unit's intensity | units with no published heat rate |
| fuel emission factor | the IPCC 95 % lower and upper bound | fossil units on an IPCC default factor |

Where a national emission factor exists, national vs IPCC is the fifth comparison. Results are
reported as ranges around the central value; **no variant is a new central value**.

Every class default has to be checked against a document a reader can open. The efficiency check
is machine-run: the heat rate is read out of the cited report's own text, converted from the
higher heating value the report uses to the net calorific value the IPCC factors are stated on,
and compared with the transcription, with the gap published per class. A class the documents on
file do not cover is labelled an assumption rather than a citation.

### 5.3 Data quality declaration

Per unit: Layer 1 tier (grid series, A), Layer 2 tier (worst of capacity factor, heat rate,
emission factor), and the worst of both. Per firm × role: the share of units on default heat
rate, on default capacity factor and on IPCC default factors, and the share of role rows whose
share is blank.

### 5.4 Separation from Scope 3

TI is additional to the firm's Scope 3 inventory (Category 15 for equity, Category 11 for
equipment sold, Category 1/2 for construction services) and is never netted against it.

---

# PART 2 — ANALYSIS PATHWAY SELECTION

## 6. Selecting the destination benchmark

Use the destination's national generation-based intensity series (Ember via Our World in Data)
for every destination; a sub-national grid is used only where the unit feeds an isolated system
and a published series exists for it. Verify the S2 anchor against the NDC as communicated to the
UNFCCC registry, record base year, gas basket, boundary, conditionality and communication date,
and prefer the unconditional target where both exist.

## 7. Selecting Layer 2 parameters

Take the tracker's unit-level heat rate and capacity factor where published; otherwise the
technology default, and say so on the row. Use the national factor where the inventory publishes
one for the fuel; otherwise the IPCC default. Never mix a national factor for one fuel with a
non-inventory factor for another in the same country without recording both bases.

## 8. Data collection pipeline

1. **Project registry** — Global Energy Monitor Global Integrated Power Tracker (download form;
   hand file). Keep the tracker ids; they are the join key for everything else.
2. **Role register** — per firm × unit × tier-1 role from the GEM wiki page, the firm's release, the
   lender's project page; one source link per row; blank share where unpublished.
3. **Benchmark** — grid series (scripted fetch) and committed anchors (hand transcription).
4. **Factors** — IPCC chapter (scripted fetch, transcription verified against the PDF text) and
   national implied factors (hand transcription).
5. **Calculation** — the pipeline in `script/power/`, which pauses and names any hand file that is
   missing rather than producing a partial result.

---

# APPENDICES

## Appendix A — Symbol reference

| symbol | meaning | unit |
|---|---|---|
| *P* | unit capacity | MW |
| *CF* | capacity factor | — |
| *G* | annual generation | kWh/year |
| *HR* | heat rate (LHV) | MJ/kWh |
| *η* | LHV efficiency; *HR* = 3.6/*η* | — |
| *EF* | fuel emission factor | kgCO₂/TJ |
| *I* | unit stack intensity | gCO₂/kWh |
| *g_c^S(y)* | destination grid intensity, scenario *S* | gCO₂/kWh |
| *r_c^S* | annual fractional decline of *g* | 1/year |
| *L* | operating lifetime | years |
| *y₀* | commissioning year | — |
| *ρ, σ, φ, s* | tier-1 role, tier-2 scope, phase, share | —, —, —, fraction |

## Appendix B — Common errors

- Summing a firm's roles into one number ("KEPCO's projects") — the roles overlap on the same
  units and the figure double counts. Report per tier-1 role.
- Counting a unit twice against one firm because a source names two scopes of the same tier-1 role
  (an EPC contract's civil works and its port works). The scopes are detail on one role row, not
  two roles.
- Filling a blank share with 1 or with an average — a blank stays blank.
- Reading a BAU-relative NDC as a pathway — it has no level to read.
- Counting bioenergy CO₂ in the fossil total.
- Filling grid years before the first observation with the first observed value — drop and count
  them.
- Using a national average factor for a coal type the inventory factor does not cover, without
  saying so.
