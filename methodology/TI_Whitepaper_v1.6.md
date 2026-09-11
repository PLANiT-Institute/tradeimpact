# Measuring Climate Direction: The Trade Impact (TI) Framework

**Version 1.6 · September 2026 · PLANiT Institute**

> **Changes in v1.6 — sign convention reversed.** TI_gap is now `E_prod − E_ref`, the product's emissions minus the benchmark's, where v1.5 had `E_ref − E_prod`. A **positive** TI is therefore emissions **added** — the lock-in liability — and a **negative** TI is emissions **avoided** against the benchmark. Nothing else in the calculation changed: every v1.5 figure is the v1.6 figure with its sign reversed. The reason is legibility. TI is reported in tonnes of CO₂e, and under the old ordering a positive number of tonnes meant tonnes *not* emitted, which reads against the grain of every emissions inventory and was a standing source of misreading. The opposite convention is common in avoided-emissions reporting; this framework does not follow it. All interpretation text, worked signs and the disclosure guidance in §3.9 and §5 are updated accordingly.
>
> **Changes in v1.5.** Framework simplified to a single TI metric built on the NDC-derived sector benchmark. The Technology Contribution (TC) lens and the TC/NAC two-lens structure are removed. Section 2 introduces the dynamic benchmark rationale. All sector-specific content is consolidated in sector Technical Guidelines.

---

## Executive Summary

International trade and global production embed climate consequences that existing GHG accounting frameworks cannot adequately capture. When a firm sells an energy-using product in any country, the climate consequence accumulates over the product's entire operational lifetime in that country. Current frameworks either ignore this consequence or measure it without reference to where the operating country is headed under its climate commitments.

The Trade Impact (TI) Framework quantifies this climate direction. For every product a firm sells, in every country it operates in, the framework asks: does this product's emission trajectory over its operational lifetime contribute to or undermine the operating country's NDC-committed decarbonisation path?

The result is a single metric — the TI score, in tonnes of CO₂e — that is negative when a firm's product portfolio avoids emissions against a country's NDC commitment, and positive when it adds them, entrenching emissions above the committed trajectory. Aggregated across all operating countries and all product types, weighted by actual sales volumes, it produces a firm-level signal of the climate direction embedded in the firm's trade activities.

The TI Framework does not replace Scope 3 Category 11 absolute emissions reporting. It is an additional disclosure that sits alongside the absolute GHG inventory.

---

## 1. The Problem — What Current Frameworks Miss

### 1.1 Two structural gaps

**Gap 1 — No displacement signal (Scope 3 Category 11).** Scope 3 Category 11 measures absolute use-phase emissions of all products sold, with no reference to what those products replace or where the operating country's sector is headed. A firm that expands sales of clean-technology products into high-emission markets accumulates larger Scope 3 liabilities with no accounting recognition of the contribution it is making to those markets' decarbonisation.

**Gap 2 — No policy-alignment signal (Scope 4 / avoided emissions).** Scope 4 methods calculate emission reductions against a baseline, but typically use static global or generic sector averages that are blind to the operating country's actual NDC commitment. A product assessed as beneficial against a static baseline today may provide no signal about whether it is consistent with — or contradicting — the country's committed trajectory over the product's multi-year operational life.

### 1.2 What is missing

Both gaps share a root cause: existing frameworks do not measure a sold product against where the operating country's sector is committed to going. The TI Framework is built on exactly this reference point.

### 1.3 Relationship to existing frameworks

| Feature | Scope 3 Cat 11 | Scope 4 / Avoided emissions | TI Framework |
|---|---|---|---|
| Reference baseline | None — absolute footprint | Static global or sector average | Dynamic NDC-derived sector trajectory |
| Operating country awareness | None | Low | High — country-specific NDC commitment |
| Baseline evolution over time | None | None | Year-by-year along NDC path |
| Early mover signal | None | None | Yes — earlier adoption contributes more |
| Conventional product lock-in signal | None | Partial | Yes — the added quantity grows as the sector decarbonises |
| Scope position | Scope 3 (absolute liability) | Scope 4 (avoided only) | Scope 4 (added or avoided, one signed metric) |

---

## 2. The TI Framework

### 2.1 The central question

For every product a firm sells, in every country it operates in, in every year of that product's operational life, the TI Framework asks:

> *Does this product emit more or less than what the operating country's sector is committed to emitting in that year under its NDC?*

If less — emissions avoided in that year, a negative TI. If more — emissions added, a positive TI and a lock-in liability. The cumulative answer across the product's lifetime is the per-product TI. The sum across all products, all operating countries, and all product types — weighted by actual sales volumes — is the firm-level TI.

### 2.2 Why the NDC benchmark, not a fixed product comparison

The framework's purpose is to evaluate how a firm's trade activities affect the operating country's climate commitment — and through it, global decarbonisation efforts. This purpose requires a dynamic, policy-aligned benchmark. A fixed comparison against the equivalent conventional product at the point of sale cannot serve this purpose for three reasons.

First, a nation's emissions change over time. What counts as a contribution or a liability is not fixed at the moment of sale — it evolves as the country's sector decarbonises under its NDC commitment. A product that sits comfortably below the sector average today may be well above the committed trajectory ten years into its operational life.

Second, the framework is designed to capture the temporal value of clean-technology adoption. A BEV sold when a country's fleet is predominantly ICE makes a larger contribution to that country's NDC path than the same BEV sold when the fleet has already substantially electrified. A fixed comparison misses this: it gives the same answer regardless of when the product is sold and regardless of the country's policy context.

Third, the framework needs to signal escalating lock-in. A conventional product sold today into a country with an ambitious NDC becomes progressively more problematic as the sector benchmark declines around it. A fixed comparison shows a static gap; the NDC benchmark shows a widening one — which is the accurate and policy-relevant signal.

The NDC benchmark is therefore not one choice among possible baselines. It is the only baseline consistent with the framework's purpose of evaluating trade's contribution to national and global decarbonisation efforts.

### 2.3 Two analysis levels

**Level 1 — Operating-country basis (primary):** For each country where a firm's products operate, TI measures the net climate impact of the firm's entire in-country product fleet — all product types, regardless of where they were produced. Achievable with publicly available data.

**Level 2 — Production-country basis (extended):** For each production location, the downstream climate impact of products produced there is traced across all operating countries where those products are deployed. Requires firm disclosure of the production × operating country volume matrix.

---

## 3. Mathematical Model

### 3.1 Layer 1 — NDC sector benchmark
<a id="eq-3.1-benchmark"></a>
The operating country's sector-average emission intensity per unit of service, declining along the NDC-committed path:

```
E_ref,c(t) = E_ref,c(0) × (1 − r_sector,c)^t        [kgCO₂e / product / year]
```

Where:
- `E_ref,c(0)` = base-year sector-average emission intensity in operating country c
- `r_sector,c` = annual sector benchmark reduction rate derived from the operating country's NDC
- t = years elapsed since sale (t = 0 at year of sale)

Three-scenario rates for r_sector,c:
- **S1:** Current enacted policies — IEA WEO STEPS sector trajectory
- **S2:** NDC unconditional target — UNFCCC NDC Registry
- **S3:** 1.5°C-aligned — IEA NZE sector trajectory

### 3.2 Layer 2 — Sold product emissions
<a id="eq-3.2-product"></a>
The actual use-phase emissions of the sold product of type v in operating country c at year t:

```
E_prod,v,c(t)        [kgCO₂e / product / year]
```

For conventional products: fixed at sale-year efficiency. `E_prod,v,c(t) = E_prod,v,c(0)` for all t.

For clean-technology products: declines over time as the operating country's energy system decarbonises at a rate derived independently from the energy sector NDC.

For hybrid products: a weighted composite of the above, with operating-country-specific weighting parameters.

### 3.3 Annual TI gap per product
<a id="eq-3.3-annual-gap"></a>
```
TI_gap,v,c(t) = E_prod,v,c(t) − E_ref,c(t)        [kgCO₂e / product / year]
```

Negative: the product emits less than the sector benchmark in year t — emissions avoided, a climate contribution.
Positive: the product emits more than the benchmark — emissions added, a carbon lock-in liability.

The ordering is product minus benchmark so that the metric reads as an emissions figure: a positive number of tonnes is a number of tonnes emitted.

### 3.4 Summation convention
<a id="rule-3.4-summation"></a>
T = total number of operating years. t runs from 0 to T−1 (T terms, inclusive).

### 3.5 Per-product cumulative TI
<a id="eq-3.5-cumulative"></a>
```
TI_product,v,c,S = Σ_{t=0}^{T−1} TI_gap,v,c(t)        [kgCO₂e / product over lifetime]
```

Negative: net emissions avoided over the product's operational life — a contribution.
Positive: net emissions added over the product's operational life — a lock-in liability.

### 3.6 Single-cohort firm-level TI
<a id="eq-3.6-cohort"></a>
All products sold in cohort year Y₀, across all operating countries c and product types v:

```
TI_cohort,F,Y₀,S = Σ_v Σ_c [ V_c,v × TI_product,v,c,S ]        [tCO₂e]
```

Where V_c,v = units of product type v sold in operating country c in cohort year Y₀.

**Decomposition — mandatory:**
```
TI_cohort = Σ_c TI_country,c = Σ_v TI_type,v
```

Headline numbers without decomposition by operating country and product type are insufficient.

**Level 2 extension:**
```
TI_production,p,S = Σ_v Σ_c [ V_p,c,v × TI_product,v,c,S ]
```

Where V_p,c,v = products produced in country p of type v operating in country c.

### 3.7 Annual TI flow from a single cohort
<a id="eq-3.7-annual-flow"></a>
```
TI_annual,F,Y₀,τ,S = Σ_v Σ_c [ V_c,v × TI_gap,v,c(τ − Y₀) ]        [tCO₂e / year]
```

This time-series shows how the annual climate impact of one year's sales decisions evolves over the product lifetime. For clean-technology products, the avoided quantity typically narrows over time as the sector benchmark converges toward product emission levels. For conventional products, it turns positive — from avoided to added — as the benchmark falls below fixed emissions.

### 3.8 Rolling portfolio TI — primary disclosure metric
<a id="eq-3.8-portfolio"></a>
```
TI_portfolio,F,τ,S = Σ_{Y₀=τ−T+1}^{τ} TI_annual,F,Y₀,τ,S        [tCO₂e / year]
```

This is the firm's total annual climate impact from all products currently in operation worldwide — the number that belongs in the annual sustainability disclosure.

### 3.9 Interpretation

**Negative TI:** The firm's active product fleet emits less in aggregate than the operating countries' committed sector benchmarks. The firm's trade activities avoid emissions against those benchmarks and are contributing to NDC achievement.

**Positive TI:** The firm's active product fleet emits more than the benchmarks. Trade activities add emissions and represent a net lock-in liability relative to the countries' NDC commitments.

**Rising TI (even if still negative):** The firm's portfolio is not keeping pace with the operating countries' decarbonisation commitments. The S1–S3 spread signals the degree of policy risk exposure: a wide spread means the firm's TI position is highly sensitive to how ambitiously operating countries implement their NDCs.

---

## 4. Boundary Conditions

### 4.1 Geographic boundary — the operating country

Every operating country contributes an independent Layer 1 benchmark and independent Layer 2 energy-system parameters. The same product deployed in two different countries produces two different TI scores. Firm-level aggregation weights these by actual sales volumes in each country.

For operations outside any national jurisdiction (e.g. international shipping in international waters), a sector-specific international trajectory replaces the national NDC. See sector Technical Guidelines.

### 4.2 Production-country boundary

The production country is outside the Layer 1 and Layer 2 calculation boundary. Use-phase emissions are determined entirely by the product's efficiency characteristics and the operating country's energy system. Production country data is relevant only for Level 2 attribution analysis.

### 4.3 Temporal boundary

The TI assessment spans the product's full operational lifetime T. Results must be reported under all three scenarios (S1/S2/S3). Product lifetime T and its sensitivity range are specified in sector Technical Guidelines.

### 4.4 Product boundary

Manufacturing and end-of-life emissions are outside the TI boundary, consistent with Scope 3 Category 11. For products where manufacturing-phase emission differences are material, sector Technical Guidelines specify when lifecycle assessment (LCA) data should accompany TI reporting.

---

## 5. Data Quality and Transparency

### 5.1 Three-tier data quality hierarchy
<a id="rule-5.1-tiers"></a>
**Tier A (Firm-verified):** Direct product-level or market-level data from firm sustainability reports, CDP responses, or verified ESG databases.

**Tier B (Estimated):** Cross-referenced from operating-country deployment registries, firm regional disclosures, and market data.

**Tier C (Proxy-based, fallback only):** Applied only when Tier A and Tier B sources are exhausted. Criteria-based representative product selection with documented rationale.

### 5.2 Mandatory transparency requirements

Every reported TI output must carry:
- Data tier for Layer 1 (NDC benchmark) and Layer 2 (product emissions) independently
- Analysis level: Level 1 or Level 2
- NDC scenario (S1/S2/S3) with source document and version cited
- Volume data source and tier
- Product operational lifetime T and sensitivity bounds
- Whether results represent single-cohort or rolling portfolio
- Decomposition by operating country and by product type — mandatory

### 5.3 Separation from Scope 3
<a id="rule-5.3-no-netting"></a>
TI must never net out or reduce the firm's reported Scope 3 Category 11 absolute emissions. TI is a separate additional disclosure only.

---

## 6. Sector Coverage

The TI Framework applies to any sector where firms sell energy-using products that operate over multi-year lifetimes in defined geographic markets. The core formulas (Sections 3.3–3.8) apply without modification across sectors. What varies by sector is the specification of the Layer 1 benchmark trajectory, Layer 2 emission parameters, product lifetime T, and the relevant operating-country data sources — all defined in sector-specific Technical Guidelines.

| Sector | Layer 1 NDC benchmark | Technical Guideline |
|---|---|---|
| Road transport (passenger vehicles) | Operating country in-use fleet emission intensity trajectory (transport NDC) | TI Automotive Technical Guideline |
| Maritime (commercial shipping) | IMO GHG Strategy Carbon Intensity Indicator (CII) trajectory | TI Shipping Technical Guideline (forthcoming) |
| Power generation | Operating country grid emission intensity trajectory (power sector NDC) | TI Power Technical Guideline (forthcoming) |
| Industrial equipment | Operating country industrial sector emission intensity trajectory | TI Industry Technical Guideline (forthcoming) |

---

## 7. Outputs and Disclosure Format

### 7.1 Required outputs

1. **TI_cohort,F,Y₀,S** — single-cohort total lifetime TI [tCO₂e], S1/S2/S3
2. **TI_annual time-series** — annual TI for the single cohort, t = 0 to T−1 [tCO₂e/yr], S1/S2/S3
3. **TI_portfolio,F,τ,S** — rolling portfolio annual TI [tCO₂e/yr], S1/S2/S3
4. **Decomposition by operating country and product type** — mandatory alongside all headline numbers

### 7.2 Recommended presentation

- **Headline chart:** Rolling portfolio TI time-series with S1/S2/S3 band, showing trajectory over time.
- **Decomposition charts:** TI by operating country and by product type — identifies where the firm's portfolio climate impact is concentrated.
- **Single-cohort time-series:** Annual TI for the most recent cohort, t = 0 to T−1. Shows how the current year's sales decisions play out over their full lifetime.
- **Data quality table:** Tier declarations for all inputs.

---

## 8. Open-Source Architecture

All methodology documents, sector Technical Guidelines, and reference data are published under GNU GPL v3 at transitionarc.climatearc.org. The platform accepts both public data-based Level 1 analysis and firm-disclosed Level 2 production × operating country data.

---

## 9. Limitations and Caveats

### 9.1 NDC quality and the implementation gap

TI relies on NDC trajectories as the authoritative sector benchmark. A minority of NDCs include explicit sector sub-targets; most require pro-rata allocation of whole-economy targets, which assumes all sectors decarbonise at equal rates. This overstates sector benchmark decline speed in markets without explicit sector targets, overstating the avoided quantity and understating lock-in liability for conventional products.

A gap exists between stated NDC ambitions and enacted policy. TI S2 results represent the policy-committed trajectory, not the policy-implemented trajectory. S1 (current policies, IEA STEPS) provides a more conservative bound and should always be reported alongside S2.

### 9.2 Attribution across multiple producers

TI measures one firm's portfolio in isolation. If multiple firms all report negative TI — avoided emissions — simultaneously, individual claims do not physically sum — each firm's TI is a comparative metric against a shared benchmark, not a physical attribution of sector-level changes.

### 9.3 Manufacturing emissions excluded

TI measures use-phase emissions only. For clean-technology products where manufacturing emissions are material, the use-phase advantage may take time to overcome the manufacturing-phase emission premium. Sector Technical Guidelines specify when LCA supplementation is required.

### 9.4 Secondary markets and lifetime variability

The framework assumes products operate in the assessed operating country for the full modelled lifetime T. Policy-driven early retirement and secondary-market transfer to other countries are not currently captured.

### 9.5 Benchmark smoothing in fast-transition markets

The exponential benchmark model may underestimate near-term benchmark decline in markets with rapidly accelerating clean-technology adoption. Cross-validation with observed sector data is recommended in such markets.

---

## 10. References

The framework's literature base is the register at [`reference/references.csv`](../reference/references.csv),
which holds every work cited here together with what it states, where TI departs from it, and a
link that is machine-checked on every run. [`reference/landscape.md`](../reference/landscape.md)
sets out the families of approach and where TI sits among them. This section names the works this
whitepaper leans on; the register is the home for the citation itself.

**The absolute inventory TI sits beside.** GHG Protocol's Corporate Value Chain (Scope 3)
Standard and its 2013 technical guidance define Category 11 and require that any avoided-emissions
estimate be reported separately from the inventory rather than deducted from it
(`ghgp_scope3_standard` §9.5). IFRS S2 is where a listed company publishes the result
(`ifrs_s2`).

**The counterfactual machinery.** The GHG Protocol's Project Protocol and Policy and Action
Standard are the formal analogues of TI's benchmark (`ghgp_project_protocol`,
`ghgp_policy_action_standard`); the Protocol's Actions and Market Instruments work proposes the
separate consequential statement TI would report under (`ghgp_ami_white_paper`). The
attributional-consequential distinction is set out in `brander_attributional_consequential`.

**Avoided emissions and its critics.** `wri_comparative_emissions_impacts`,
`wbcsd_avoided_emissions_v2` and `carbone4_nzi_pillar_b` are the reference texts;
`young_ferris_scope4_claims`, `okeeffe_brander_avoided_landscape` and `okeeffe_brander_comparison`
are the critique TI must answer. The Science Based Targets initiative excludes product-level
avoided emissions from recognition outright (`sbti_corporate_net_zero_v2`).

**The destination benchmark, as others build it.** The multilateral banks compute project
emissions net of a country grid baseline (`ifi_ghg_accounting_renewables`) and test operations
against the destination's own NDC (`mdb_paris_alignment_direct_investment`); the Clean Development
Mechanism standardised the displaced-grid emission factor two decades ago
(`cdm_tool07_grid_emission_factor`).

**Carbon lock-in.** `seto_carbon_lock_in`, `tong_committed_emissions`, `davis_future_co2`,
`davis_socolow_commitment_accounting` and `cui_coal_plant_lifetimes`.

**Trade, export and embodied carbon.** `oecd_co2_embodied_trade` and
`davis_caldeira_consumption_based` for the family TI is confused with,
`steininger_consumption_based` and `afionis_consumption_based_future` for its critique, and
`newman_used_vehicle_exports`, `guo_overseas_coal_emissions` and `carbon_majors` for the export
and producer-side work closest to TI's own question.

**The benchmark's own sources.** `unfccc_ndc_registry` and `iea_weo_2024`.

> **Citation correction (September 2026).** Earlier versions of this section attributed *Making
> things (that don't exist) count: a study of Scope 4 emissions accounting claims* to Bjørn, Lloyd
> and Matthews in the *Journal of Industrial Ecology*, with a DOI belonging to an unrelated paper
> on building-stock modelling. The work is by Young-Ferris, Malik, Calderbank and Jacob-John,
> published in *Accounting, Auditing and Accountability Journal* 38(1), 60-89, 2024. The register
> carries the corrected entry as `young_ferris_scope4_claims`, and the link checker that found the
> error runs over every reference.

---

*End of Whitepaper v1.6 — PLANiT Institute, September 2026.*
*Published at transitionarc.climatearc.org under GNU GPL v3.*
