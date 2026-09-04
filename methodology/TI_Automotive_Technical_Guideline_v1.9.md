# Trade Impact (TI) Framework
## Automotive Sector — Implementation Technical Guideline

**Version 1.9 · September 2026 · PLANiT Institute**

> **What changed in v1.9 — sign convention reversed.**
> TI_gap is now `E_prod,v,c(t) − E_ref,c(t)`, the vehicle's emissions minus the fleet benchmark's, where v1.8 had the reverse. A **positive** TI is therefore emissions **added** — the lock-in liability — and a **negative** TI is emissions **avoided** against the benchmark. Nothing else in the calculation changed: every v1.8 figure is the v1.9 figure with its sign reversed. TI is reported in tonnes of CO₂e, and under the old ordering a positive number of tonnes meant tonnes *not* emitted, which reads against the grain of every emissions inventory. See whitepaper v1.6 §3.3. All interpretation text and the sign statements in §1.1, §3.3, §4.1 and Appendix F are updated accordingly.
>
> **What changed in v1.8.**
> Technology Contribution (TC) lens removed. Framework simplified to a single TI metric: TI_gap = E_ref,c(t) − E_prod,v,c(t). Layer 1A (TC baseline) removed throughout. All TC-related formulas, outputs, and data quality fields removed. Worked examples removed. Appendices retain data source references and methodological guidance only.

---

# PART 1 — MATHEMATICAL METHODOLOGY

---

## 1. Foundational Concepts

### 1.1 What the TI score measures

The TI score measures whether a firm's vehicle sales, in aggregate across all operating countries and all powertrain types, add emissions or avoid them relative to the operating countries' NDC-committed fleet decarbonisation trajectories. It is reported in tonnes of CO₂e and signed as an emissions figure: positive means tonnes added — a net carbon lock-in liability — and negative means tonnes avoided, a net climate contribution.

The unit of analysis is the **operating country** — the country where the vehicle is actually driven. The framework asks, year by year over a vehicle's operational lifetime: does this vehicle emit more or less than what the operating country's in-use fleet is committed to emitting under its NDC in that year?

If less — emissions avoided in that year, a negative TI. If more — emissions added, a positive TI and a carbon lock-in liability. The cumulative answer across the vehicle's lifetime is the per-vehicle TI. The sum across all vehicles, all operating countries, and all powertrain types — weighted by actual sales volumes — is the firm-level TI.

The framework defines two analysis levels:

**Level 1 — Operating-country basis (primary):** For each country where a firm's vehicles operate, TI measures the net climate impact of all the firm's vehicles in that country, regardless of production origin. Achievable with publicly available data.

**Level 2 — Production-country basis (extended):** For each production location, the downstream climate impact of vehicles produced there is traced across all operating countries where those vehicles operate. Requires firm disclosure of the production × operating country volume matrix.

### 1.2 Emission scope position

The framework measures the net impact on the operating country's national-level GHG inventory. BEV grid emissions are operating-country consequences of the vehicle's operation and are counted in full, regardless of scope attribution in the firm's own inventory.

| Component | What is measured | Scope in operating country | Policy lever |
|---|---|---|---|
| Layer 1 — fleet benchmark (ICE-dominated) | Fleet-average combustion emissions, all vintages | Transport Scope 1 | Fleet electrification; NDC transport target |
| Layer 1 — fleet benchmark (transitioning) | Declining ICE share + growing grid-attributed EV share | Transport Scope 1 → Power Scope 1 | Fleet turnover; EV incentives; grid decarbonisation |
| Layer 2 — sold ICE vehicle | Fuel combustion; fixed at sale-year efficiency | Transport Scope 1 | None within vehicle lifetime |
| Layer 2 — sold BEV | Grid electricity × grid carbon intensity | Power Scope 1 (= transport Scope 2 for user) | Grid decarbonisation |
| Layer 2 — sold PHEV | Composite: EV-mode grid + ICE-mode combustion | Mixed, proportional to Utility Factor | Both grid and transport targets |

### 1.3 Unit of analysis — five required parameters

Before calculation begins, define and document:

- **Firm (F):** the legal entity whose vehicle portfolio is assessed
- **Sales cohort year (Y₀):** the calendar year in which vehicles are sold and registered; t = 0 for all calculations in that cohort
- **Operating country (c):** the country where the vehicle is driven and registered; assessed independently per country; aggregated by sales volume
- **Vehicle type (v):** BEV, PHEV, or ICE/HEV — never aggregated before computing per-vehicle TI
- **Vehicle lifetime (T):** operational years in the operating country; central estimate and sensitivity bounds required

---

## 2. Layer 1 — Fleet Emission Benchmark

### 2.1 Definition

Layer 1 is the **moving benchmark** — the average emission intensity of the entire in-use vehicle fleet in the operating country, at the segment level, at year t. It represents all vehicles of all ages, all powertrain types, and all vintages currently being driven.

```
E_ref,c(t) = I_fleet,seg,c(t) × D_c        [kgCO₂e / vehicle / year]
```

The NDC transport trajectory is embedded within Layer 1 as the annual reduction rate r_fleet,c. Layer 1 carries its own dynamics — there is no separate trajectory layer.

### 2.2 What drives I_fleet,seg,c(t) downward

The fleet benchmark declines as three processes operate simultaneously: (1) fleet electrification, as EVs with lower emissions enter the fleet; (2) vintage turnover, as older, higher-emitting vehicles scrap out; (3) improving new entrant quality, as vehicles entering in later years are cleaner than earlier vintages. The operating country's transport NDC target captures the intended combined outcome of all three processes.

> **⚠ Caveat — Non-linearity:** The benchmark model uses a smooth exponential decline. Real fleet transitions follow S-curve dynamics. In markets with rapidly accelerating EV adoption, the exponential model may underestimate near-term benchmark decline. Flag in the data quality declaration for fast-transition markets.

### 2.3 Methods for deriving I_fleet,seg,c(t)

#### Method A — Fleet stock model
<a id="eq-g2.3a-weibull"></a>
Builds the fleet average by tracking each annual cohort of vehicles as it enters, ages, and scraps out.

**Surviving stock of vintage y at year t:**
```
S(y,t) = N_new(y) × SR(t − y)
```

**Weibull survival function:**
```
SR(age) = exp( −(age / α)^β )
```

Where α and β are market-specific Weibull shape parameters sourced from national transport statistics (see Appendix A).

**Fleet average emission intensity:**
```
I_fleet,seg,c(t) = Σ_y [ S(y,t) × I_new,seg,c(y) ] / Σ_y S(y,t)
```

New entrant intensity `I_new,seg,c(y)` is derived from the IEA WEO scenario-consistent EV penetration trajectory for year y — not from regulatory certification standards.

**Use Method A when:** Mature OECD market; fleet age distribution data available by vintage year; at least 15 years of historical fleet emission data.

#### Method B — Transport NDC trajectory
<a id="eq-g2.3b-ndc-trajectory"></a>
Treats the country's transport NDC commitment as the authoritative trajectory.

**Base year fleet-average segment intensity:**
```
I_fleet,seg,c(0) = I_all_vehicles,c(0) × segment_ratio_seg,c
I_all_vehicles,c(0) = E_transport,c(Y₀) / ( Fleet_size,c(Y₀) × D_c )
```

**NDC-implied annual fleet reduction rate:**

If an explicit transport sector target exists:
```
r_fleet,c = 1 − ( E_target,transport,c / E_base,transport,c )^( 1 / (Y_target − Y_base) )
```

If no transport sub-target — pro-rata allocation from whole-economy NDC:
```
transport_share,c = E_transport,c(Y_base) / E_total,c(Y_base)
E_target,transport,c = E_total,target,c × transport_share,c
```

**Benchmark trajectory:**
```
I_fleet,seg,c(t) = I_fleet,seg,c(0) × (1 − r_fleet,c)^t
```

Three-scenario rates: S1 from IEA STEPS transport; S2 from UNFCCC NDC unconditional target; S3 from IEA NZE transport.

> **⚠ Caveat — Pro-rata bias:** Where no transport sub-target exists, pro-rata allocation assumes all sectors decarbonise at equal rates. Transport typically decarbonises more slowly than electricity. Pro-rata overstates r_fleet,c, understating lock-in liability for ICE vehicles in affected markets. Disclose in the data quality declaration; use S1 as conservative cross-check.

**Use Method B when:** NDC available; fleet age data sparse; all non-OECD markets (default).

#### Method C — Volume-weighted two-bin approximation
<a id="eq-g2.3c-two-bin"></a>
```
I_fleet,seg,c(t) = RR_c × I_new,seg,c(t) + (1 − RR_c) × I_fleet,seg,c(t−1) × (1 + δ_scrap,c)
```

Where `RR_c` = annual fleet renewal rate; `δ_scrap,c` = scrappage intensity correction. New entrant intensity from IEA WEO scenario — not from regulatory standards.

**Use Method C when:** No NDC available; or as cross-validation of Method B. Where both B and C apply, divergence greater than 30% at any analysis year requires investigation before proceeding.

---

## 3. Layer 2 — Sold Vehicle Emissions

### 3.1 Definition

Layer 2 is the actual use-phase emissions of the sold vehicle under the specific operating conditions of the destination market.

### 3.2 Volume data V_c,v

**Primary source: Operating country vehicle registration databases.** These capture all vehicles registered regardless of production origin, provide model-level granularity enabling direct powertrain identification, and represent actual operating vehicles. Key databases by country are listed in Appendix B.

**Secondary source (Tier B):** UN Comtrade HS 8703, where registration databases are unavailable. Useful for Level 2 production-country analysis. Not recommended as primary source for V_c,v.

**Level 2 volume data V_p,c,v:** Model-to-factory mapping using firm IR materials. Where a model has a single production source, operating country registration volumes directly imply production country. Where multiple factories produce the same model, allocate by factory production volume ratios from firm IR materials.

### 3.3 Case 1 — ICE and non-plug-in HEV
<a id="eq-g3.3-ice"></a>
```
E_prod,ICE,c(t) = I_export,ICE × D_c        [constant for all t]
```

`I_export,ICE` = real-world emission intensity with certification correction applied (see Appendix C).

The ICE TI_gap starts negative — emissions avoided, because a new ICE is cleaner than a fleet average that includes many older vehicles — narrows as the fleet benchmark declines, and crosses to positive. That crossing is the carbon lock-in signal: the vehicle's fixed emissions become an increasingly large addition relative to the committed fleet trajectory.

### 3.4 Case 2 — BEV
<a id="eq-g3.4-bev"></a>
```
E_prod,BEV,c(t) = η_EV × G_c(t) × D_c
G_c(t) = G_c(0) × (1 − r_power,c)^t
r_power,c = 1 − ( G_target,c / G_c(0) )^( 1 / (Y_target − Y_base) )
```

`η_EV` = real-world electrical energy efficiency [kWh/km].
`G_c(t)` = grid carbon intensity in country c at year t [kgCO₂e/kWh].
`r_power,c` is derived **independently** from `r_fleet,c` — power sector and transport sector NDC targets are separate policy variables and must never be set equal.

### 3.5 Case 3 — PHEV
<a id="eq-g3.5-phev"></a>
```
E_prod,PHEV,c(t) = [ (UF × η_elec × G_c(t)) + ((1 − UF) × I_ICE_mode) ] × D_c
```

UF = Utility Factor — the fraction of distance driven in electric mode, market-specific (see Appendix C). Mandatory sensitivity: UF ± 0.15.

> **⚠ Caveat — UF structural overstatement:** Regulatory UF values consistently overstate real-world electric driving share across all studied markets. PHEV TI contributions should be treated as upper-bound estimates. Report central and lower-bound (UF − 0.15) results side by side.

---

## 4. Layer 3 — Integration and Aggregation

### 4.1 Annual TI gap per vehicle

```
TI_gap,v,c(t) = E_prod,v,c(t) − E_ref,c(t)        [kgCO₂e / vehicle / year]
```

`E_ref,c(t)` carries no powertrain subscript — the fleet benchmark is powertrain-agnostic.
`E_prod,v,c(t)` carries subscript v — Layer 2 differs by powertrain type.

Negative: vehicle emits less than the benchmark in year t — emissions avoided, a contribution.
Positive: vehicle emits more than the benchmark — emissions added, a liability.

The ordering is vehicle minus benchmark so that the metric reads as an emissions figure: a positive number of tonnes is a number of tonnes emitted.

Plot this time-series for t = 0 to T−1. It is the most informative single visualisation of TI output.

### 4.2 Summation convention

T = total number of operating years. t runs from 0 to T−1 (T terms, inclusive).

### 4.3 Per-vehicle cumulative TI

```
TI_vehicle,v,c,S = Σ_{t=0}^{T−1} TI_gap,v,c(t)        [kgCO₂e / vehicle over lifetime]
```

### 4.4 Single-cohort firm-level TI

```
TI_cohort,F,Y₀,S = Σ_v Σ_c [ V_c,v × TI_vehicle,v,c,S ]        [tCO₂e]
```

**Decomposition — mandatory:**
```
TI_cohort = Σ_c TI_country,c = Σ_v TI_powertrain,v
```

### 4.5 Annual TI flow from a single cohort

```
TI_annual,F,Y₀,τ,S = Σ_v Σ_c [ V_c,v × TI_gap,v,c(τ − Y₀) ]        [tCO₂e / year]
```

### 4.6 Rolling portfolio TI — primary disclosure metric

```
TI_portfolio,F,τ,S = Σ_{Y₀=τ−T+1}^{τ} TI_annual,F,Y₀,τ,S        [tCO₂e / year]
```

This is the firm's total annual climate impact from all vehicles currently in operation worldwide.

### 4.7 Three-scenario architecture
<a id="rule-g4.7-three-scenarios"></a>
All results reported under three scenarios. Each scenario specifies r_fleet,c and r_power,c independently:

| Scenario | Label | r_fleet,c source | r_power,c source |
|---|---|---|---|
| S1 | Low — current policies | IEA WEO STEPS transport | IEA WEO STEPS electricity |
| S2 | Central — NDC | UNFCCC NDC unconditional transport | UNFCCC NDC power sector |
| S3 | High — 1.5°C | IEA NZE transport | IEA NZE electricity |

Never report S2 alone. Always report S1, S2, S3.

---

## 5. Reporting Requirements

### 5.1 Required outputs

1. **TI_cohort,F,Y₀,S** — single-cohort total lifetime TI [tCO₂e], S1/S2/S3
2. **TI_annual time-series** — annual TI for the cohort, t = 0 to T−1 [tCO₂e/yr], S1/S2/S3
3. **TI_portfolio,F,τ,S** — rolling portfolio annual TI [tCO₂e/yr], S1/S2/S3
4. **Decomposition by operating country and powertrain** — mandatory alongside all headline numbers

### 5.2 Mandatory sensitivity parameters
<a id="rule-g5.2-sensitivity"></a>
| Parameter | Sensitivity range |
|---|---|
| Vehicle lifetime T | T ± 3 years minimum |
| Utility Factor UF (PHEV) | UF ± 0.15 |
| Real-world correction factor | Range per Appendix C |
| NDC scenario | S1, S2, S3 all reported |
| Segment intensity ratio | Range per Appendix A |

### 5.3 Data quality declaration template
<a id="rule-g5.3-declaration"></a>
```
Firm: [F] | Cohort year: [Y₀] | Analysis level: [Level 1 / Level 2]

Layer 1 — fleet benchmark:
  Method: [A/B/C] | I_fleet,seg,c(0): [value] kgCO₂e/km | Segment ratio: [value, source]
  r_fleet,c: S1=[v1] | S2=[v2] | S3=[v3] %/yr | Source: [NDC document, date]

Layer 2:
  BEV: η_EV [value] kWh/km | G_c(0) [value] kgCO₂e/kWh | r_power [S1/S2/S3]
  ICE: I_export,ICE [value] kgCO₂e/km | Correction applied: [standard, factor]
  PHEV: UF [value] | η_elec [value] kWh/km | I_ICE_mode [value] kgCO₂e/km

Volume: V_c,BEV [value] | V_c,PHEV [value] | V_c,ICE [value]
  Source: [registration database, year] | Tier: [A/B]

Results:
  TI_cohort (S1/S2/S3): [v1] / [v2] / [v3] tCO₂e
  TI_annual t=0 (S2): [value] tCO₂e/yr
  TI_annual t=T (S2): [value] tCO₂e/yr — trend: [narrowing / widening / stable]
```

### 5.4 Separation from Scope 3

TI must never net out or reduce the firm's Scope 3 Category 11 absolute emissions. TI is a separate additional disclosure only.

---

---

# PART 2 — ANALYSIS PATHWAY SELECTION

---

## 6. Selecting the Layer 1 Method

### 6.1 Method selection criteria
<a id="rule-g6.1-bc-divergence"></a>
**Use Method A when:** Mature OECD market; fleet age distribution data available by vintage year; at least 15 years of historical fleet emission data; IEA WEO scenario projections used for new entrant intensity.

**Use Method B when:** Fleet age data unavailable or sparse; developing or emerging market; quantified transport NDC or whole-economy NDC exists. Default for all non-OECD markets.

**Use Method C when:** Method B cannot be applied (no NDC); or as cross-validation of Method B. Divergence >30% with Method B at any analysis year requires investigation.

### 6.2 NDC source verification (Method B)

Before applying Method B:
1. Confirm this is the most recent NDC submission (UNFCCC NDC Registry)
2. Does an explicit transport sub-target exist, or is pro-rata allocation required?
3. Is the stated target unconditional or conditional? Use unconditional for S2; conditional for S3.
4. What is the base year and base-year emission level?
5. What is the target year? Apply the same derived annual rate for years beyond the target year — document this extrapolation.

### 6.3 Operating country selection

1. Identify countries using operating country registration databases. Rank by annual new registration volume.
2. Select countries covering at least 70% of the firm's total global sales volume; minimum 3 markets.
3. Include at least one high grid-intensity and one low grid-intensity market.
4. Each selected market must have: (a) a submitted UNFCCC NDC; (b) national grid carbon intensity data from Ember or IEA; (c) an accessible registration database.

### 6.4 Vehicle lifetime T selection

Base T on the operating country's mean fleet age (from national transport statistics or Appendix A). Always run sensitivity at T ± 3 years.

---

## 7. Selecting Layer 2 Parameters

### 7.1 Vehicle emission parameter hierarchy

1. Firm discloses bilateral sales volumes by model and powertrain → Tier A
2. Firm discloses regional powertrain sales mix + product lineup → Tier B
3. Neither → Tier C (fallback, from operating country certification database)

Check ESG databases (Refinitiv, Bloomberg ESG, CDP) before concluding firm data is unavailable.

### 7.2 Real-world corrections

Apply certification standard-specific correction factors to convert certified emission values to real-world conditions. Correction factors are published in the ICCT annual *Mind the Gap* report. Do not apply more than one correction to the same data point. Where operating-country certification data is already real-world adjusted, apply no further correction.

### 7.3 PHEV UF selection

Use the operating country's regulatory UF where available. Apply the real-world adjusted default from Appendix C where regulatory data is absent or charging infrastructure is limited. Always run sensitivity at UF ± 0.15.

### 7.4 Grid carbon intensity

Use country-specific values from Ember Global Electricity Review. Regional or global averages are not acceptable. Derive r_power,c independently from r_fleet,c — power and transport sector targets are separate policy variables.

---

## 8. Data Collection Pipeline

### Phase 1 — Volume data

**Step 1:** Download brand-level annual registrations from operating country databases. Rank markets by volume. Select per Section 6.3.
Output: total vehicle registrations by brand, country, year.

**Step 2:** Map each registered model to its powertrain type (BEV / PHEV / HEV / ICE). Sum V_c,v per country.
Output: V_c,v — vehicles of type v registered in operating country c in cohort year Y₀.

**Step 3 (Level 2 only):** Identify the production factory for each model using firm IR factory-model assignment disclosures. Allocate by factory production volume ratios where a model is produced in multiple factories.
Output: V_p,c,v — vehicles produced in country p of type v operating in country c.

### Phase 2 — Layer 1 parameters

**Step 4:** Collect national road transport CO₂ (IEA), total in-use fleet size (OICA), and annual VKT from national transport statistics. Compute I_all_vehicles,c(0). Apply segment ratio from Appendix A.
Output: I_fleet,seg,c(0) per operating country.

**Step 5:** Download NDC for each operating country from UNFCCC NDC Registry. Extract transport sector target or apply pro-rata per Section 6.2. Derive r_fleet,c for S1, S2, S3.
Output: r_fleet,c [S1, S2, S3] per operating country.

### Phase 3 — Layer 2 parameters

**Step 6:** BEV η_EV — from operating country type approval database; apply certification correction per Appendix C.

**Step 7:** ICE I_export,ICE — from operating country type approval database; apply correction per Appendix C.

**Step 8:** PHEV parameters — I_ICE_mode from charge-sustaining certified CO₂ with correction; η_elec from charge-depleting energy with correction; UF from Appendix C.

**Step 9:** G_c(0) from Ember Global Electricity Review. r_power,c from NDC power sector target — derived independently from r_fleet,c. Three scenarios [S1/S2/S3].

### Phase 4 — Calculation

**Step 10:** Compute TI_gap,v,c(t) for t = 0 to T−1, all three scenarios.

**Step 11:** Aggregate to firm level — TI_cohort, TI_annual, TI_portfolio. Decompose by country and powertrain.

**Step 12:** Sensitivity analysis — vary parameters per Section 5.2.

---

---

# APPENDICES

---

## Appendix A — Fleet Parameter Reference

All values must be sourced from national transport statistics or cited empirical studies at the time of analysis. Do not use defaults from prior analyses without verifying currency.

**Fleet average base-year emission intensity I_all_vehicles,c(0)**
Source: IEA CO₂ from Fuel Combustion (national road transport CO₂) ÷ (OICA Vehicles in Use × national VKT).

**Segment intensity ratio (SUV/crossover)**
Source: EEA CO₂ monitoring data (EU); US EPA Automotive Trends (USA); BITRE/IEA GFEI (Australia and other markets); national equivalents where available. Document source year.

**Fleet survival function — Weibull parameters (α, β)**
Source: National transport ministry fleet age surveys; EEA (EU); US DOT NHTS (USA); BITRE (Australia); OICA. For markets without survey data, use IEA Tracking Transport regional defaults and declare as Tier C.

**Fleet renewal rate RR_c**
Source: OICA Production Statistics.

**Scrappage intensity correction δ_scrap,c**
Source: National transport statistics or IEA regional defaults. Document source and tier.

> **⚠ Caveat:** Weibull parameters and fleet renewal rates are unavailable for many developing markets. Uncertainty is high in these cases. Apply the full T ± 3 year sensitivity range and seek country-specific data from national transport ministries where available.

---

## Appendix B — Data Sources

### B.1 Vehicle registration databases (primary source for V_c,v)

| Country | Database | Granularity | Access |
|---|---|---|---|
| Australia | VFACTS (FCAI) | Model level — BEV/PHEV/HEV/ICE | Free, monthly |
| Germany | KBA (Kraftfahrt-Bundesamt) | Model level | Free, annual |
| United Kingdom | SMMT | Model level | Free, monthly |
| United States | WardsAuto / IHS Markit | Model level | Subscription |
| South Korea | KAICA | Model level | Free |
| India | SIAM | Segment level | Free |
| Indonesia | GAIKINDO | Brand level | Free |
| France | AAA Data / CCFA | Model level | Partial free |
| Canada | DesRosiers / Statistics Canada | Segment level | Partial free |

### B.2 Supplementary data sources

| Dataset | Use in framework | URL | Cost |
|---|---|---|---|
| UN Comtrade HS 8703 | Level 2 production flows; fallback V_c,v | comtrade.un.org | Free |
| IEA CO₂ from Fuel Combustion | National transport CO₂ — Layer 1 base | iea.org | Partial free |
| IEA World Energy Outlook | STEPS and NZE trajectories (S1, S3) | iea.org | Free summary |
| IEA Global EV Data Explorer | EV share by country | iea.org | Free |
| Ember Global Electricity Review | G_c(0) country grid carbon intensity | ember-climate.org | Free |
| UNFCCC NDC Registry | r_fleet,c and r_power,c source | unfccc.int/NDCREG | Free |
| Climate Action Tracker | NDC ambition and implementation assessment | climateactiontracker.org | Free |
| OICA Vehicles in Use | Fleet_size,c | oica.net | Free |
| OICA Production Statistics | Fleet renewal rate RR_c | oica.net | Free |
| EU Type Approval database | WLTP certified values — Layer 2 | ec.europa.eu/clima | Free |
| US EPA FuelEconomy.gov | EPA values — Layer 2 | fueleconomy.gov | Free |
| Korea KEA | Korean-market certification — Layer 2 | energy.or.kr | Free |
| Japan MLIT | Japanese-market certification — Layer 2 | mlit.go.jp | Free |
| CDP / Refinitiv / Bloomberg ESG | Firm sustainability disclosures — Tier A/B | cdp.net | Partial free |
| ICCT Mind the Gap | Real-world correction factors | theicct.org | Free |
| Transport & Environment | PHEV real-world UF research | transportenvironment.org | Free |

---

## Appendix C — Layer 2 Parameter Guidance

### C.1 Real-world correction factors

Certified emission values must be corrected to real-world conditions before use in Layer 2. Correction factors by certification standard (WLTP, NEDC, US EPA, JC08/WLTC) are published by ICCT in the annual *Mind the Gap* report. Verify against the most recent edition at the time of analysis.

Key rules:
- Do not apply more than one correction to the same data point
- Where operating-country type approval data is already real-world adjusted (e.g. US EPA), apply no correction
- Where data is sourced from local certification authorities (Japan MLIT, Korea KEA), verify whether real-world correction has already been applied

### C.2 PHEV Utility Factor

The Utility Factor (UF) represents the fraction of total distance driven in electric mode. Regulatory UF values are defined by: EU — WLTP Utility Factor (Regulation (EU) 2017/1151); USA — SAE J2841; China — GB/T 32694.

For markets without regulatory UF data, use real-world adjusted defaults from Transport & Environment or ICCT real-world PHEV studies. Always run sensitivity at UF ± 0.15. Report central and lower-bound results explicitly — regulatory UF consistently overstates real-world electric driving share.

### C.3 Annual driving distance D_c

Source: national VKT statistics (FHWA — USA; BITRE — Australia; EEA Transport in Figures — EU; DfT — UK; KTDB — South Korea; IEA Tracking Transport — other markets). Declare as Tier C where national VKT data is unavailable.

---

## Appendix D — Symbol Reference

| Symbol | Description | Unit |
|---|---|---|
| TI_cohort,F,Y₀,S | Total lifetime TI of firm F's cohort year Y₀, scenario S | tCO₂e |
| TI_annual,F,Y₀,τ,S | Annual TI from cohort Y₀ in calendar year τ, scenario S | tCO₂e/yr |
| TI_portfolio,F,τ,S | Rolling portfolio TI in calendar year τ, scenario S | tCO₂e/yr |
| TI_vehicle,v,c,S | Cumulative lifetime TI per vehicle, type v, country c, scenario S | kgCO₂e |
| TI_gap,v,c(t) | Annual TI gap: E_prod,v,c(t) − E_ref,c(t); positive = added, negative = avoided | kgCO₂e/vehicle/yr |
| E_ref,c(t) | Layer 1: fleet benchmark emissions in country c at year t | kgCO₂e/vehicle/yr |
| E_prod,v,c(t) | Layer 2: sold vehicle emissions in country c at year t | kgCO₂e/vehicle/yr |
| I_fleet,seg,c(t) | Fleet-average segment emission intensity at year t | kgCO₂e/km |
| I_all_vehicles,c(0) | All-vehicle fleet-average intensity, base year | kgCO₂e/km |
| I_new,seg,c(y) | Average intensity of new entrants in vintage year y (NDC-consistent) | kgCO₂e/km |
| I_export,ICE | Real-world emission intensity of sold ICE vehicle (fixed) | kgCO₂e/km |
| I_ICE_mode | PHEV charge-sustaining mode emission intensity | kgCO₂e/km |
| SR(age) | Vehicle survival rate — Weibull: exp(−(age/α)^β) | 0–1 |
| α, β | Weibull shape parameters | years; dimensionless |
| RR_c | Fleet renewal rate | 0–1 |
| δ_scrap,c | Scrappage intensity correction | per year |
| r_fleet,c | Annual fleet benchmark reduction rate (transport NDC) | %/yr |
| r_power,c | Annual grid intensity reduction rate (power sector NDC) | %/yr |
| η_EV | BEV real-world energy efficiency | kWh/km |
| η_elec | PHEV EV-mode real-world energy efficiency | kWh/km |
| G_c(t) | Grid carbon intensity in country c at year t | kgCO₂e/kWh |
| G_c(0) | Base year grid carbon intensity | kgCO₂e/kWh |
| D_c | Average annual VKT per vehicle in country c | km/yr |
| V_c,v | Registrations of type v in operating country c in cohort Y₀ | vehicles |
| V_p,c,v | Level 2: vehicles produced in p of type v operating in c | vehicles |
| T | Vehicle operational lifetime (t = 0 to T−1, T terms total) | years |
| t | Years elapsed since sale (t = 0 at sale year) | years |
| τ | Calendar year | year |
| UF | PHEV Utility Factor | 0–1 |
| Y₀ | Sales cohort base year | year |
| S1 / S2 / S3 | Scenarios: Low (current policies) / Central (NDC) / High (1.5°C) | — |

---

## Appendix E — Common Errors

| Error | Why wrong | Correct |
|---|---|---|
| Setting r_fleet,c = r_power,c | Transport and power sectors decarbonise at different rates under different policy mechanisms | Derive independently: r_fleet,c from transport NDC; r_power,c from power sector NDC |
| Using a static or global-average benchmark for Layer 1 | A static benchmark cannot capture the temporal value of early adoption or the escalating lock-in of conventional products | Use operating-country NDC-derived fleet trajectory |
| Using regional or global average for G_c(0) | Grid intensity varies enormously across countries; averages are analytically misleading | Country-specific Ember value for each operating country |
| Reporting TI as a single number without decomposition | The headline hides which markets and powertrains are driving the result | Always accompany headline TI with decomposition by operating country and powertrain type |
| Reporting single-scenario TI only | Single-scenario results do not convey NDC implementation sensitivity | Always report S1, S2, S3. Label S2 as central. |
| Reporting single-cohort and rolling portfolio interchangeably | Single-cohort = consequence of one year's decisions; rolling portfolio = all active cohorts simultaneously | Label clearly which output type is reported |
| Netting TI against Scope 3 | TI is a comparative trajectory metric, not an offset or credit | Separate additional disclosure only. Never subtracted from Scope 3 Category 11. |
| Pro-rata NDC allocation without caveat | Assumes equal decarbonisation rates across sectors — inconsistent with observed patterns | Disclose pro-rata use; use S1 as conservative cross-check |
| Applying ageing uplift as a fixed multiplier without verifying current fleet age data | Uplift factors change as fleet composition evolves | Source I_all_vehicles,c(0) directly from IEA transport CO₂ ÷ (OICA fleet × VKT) where possible |

---

## Appendix F — Methodological Caveats

**F.1 NDC quality and pro-rata allocation bias**
Where transport sub-targets are absent, pro-rata allocation overstates transport sector benchmark decline speed. Transport typically decarbonises more slowly than electricity. This overstates the added quantity — the TI lock-in liability — for ICE vehicles in affected markets. Disclose; use S1 as conservative cross-check.

**F.2 PHEV Utility Factor structural overstatement**
Regulatory UF values consistently overstate real-world electric driving share, so a PHEV's avoided quantity is an upper bound and its added quantity a lower bound. Treat PHEV TI as a bound, not an estimate.

**F.3 Exponential model non-linearity**
Methods B and C model benchmark evolution as a smooth exponential decline. Real EV adoption follows S-curve dynamics. In markets with rapidly accelerating EV adoption, the model may underestimate near-term benchmark decline.

**F.4 Real-world correction factor scope**
ICCT correction factors are derived primarily from European monitoring data. Applicability to Korean- and Japanese-market specifications sold outside Europe is not fully verified. Use local certification data directly where available.

**F.5 Fleet survival parameters for data-scarce markets**
Weibull parameters are unavailable for many developing markets. High uncertainty; apply full T ± 3 year sensitivity and use higher-tier data when available.

**F.6 Manufacturing emissions excluded**
TI measures use-phase emissions only. Manufacturing-phase emission differences are not captured. Supplement with LCA data where manufacturing emissions are material.

---

## Appendix G — References

GHG Protocol (2011). *Corporate Value Chain (Scope 3) Accounting and Reporting Standard.* World Resources Institute / WBCSD.

GHG Protocol (2013). *Technical Guidance for Calculating Scope 3 Emissions, Chapter 11.* World Resources Institute.

Seto, K.C. et al. (2016). Carbon lock-in: types, causes, and policy implications. *Annual Review of Environment and Resources*, 41, 425–452. https://doi.org/10.1146/annurev-environ-110615-085934

Tong, D. et al. (2019). Committed emissions from existing energy infrastructure jeopardize 1.5 °C climate target. *Nature*, 572, 373–377. https://doi.org/10.1038/s41586-019-1364-3

Davis, S.J., Caldeira, K. and Matthews, H.D. (2010). Future CO₂ emissions and climate change from existing energy infrastructure. *Science*, 329(5997), 1330–1333. https://doi.org/10.1126/science.1188566

ICCT (2020). *Real-world usage of plug-in hybrid electric vehicles.* https://theicct.org

Transport & Environment (2024). *Smoke screen: the growing PHEV emissions scandal.* https://www.transportenvironment.org

Gao, Y. et al. (2023). Electric vehicle lifecycle carbon emission reduction: a review. *Carbon Neutralization*, 2(5), 528–550. https://doi.org/10.1002/cnl2.81

ICCT (2023). *Mind the Gap 2023.* https://theicct.org

IEA (2024). *Global EV Outlook 2024.* https://www.iea.org/reports/global-ev-outlook-2024

ITF-OECD (2019). *Transport in Nationally Determined Contributions.* https://www.itf-oecd.org

Ember (2024). *Global Electricity Review 2024.* https://ember-climate.org

UNFCCC NDC Registry. https://unfccc.int/NDCREG

---

*End of document. Version 1.8 — PLANiT Institute, May 2026.*
*Published at transitionarc.climatearc.org under GNU GPL v3.*
