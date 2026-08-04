# Data Collection Status

Snapshot date: 2026-08-03 · Workbook: `TI_Data_Workbook_v0.1.xlsx` · Loaded: 11
operating-country rows, 17 official vehicle-parameter rows, and four evidence-first company
snapshots: Toyota-brand 2024 EU27 passenger-car registrations, JERA FY2024 Japan generation,
KOEN 2024 Korea generation and reported Scope 1/2 emissions, and MOL FY2024 global-fleet EEOI.

The public dataset contains source-backed operating-country fields and reporting-year company
activity metrics. There are no vehicle-lifetime greenhouse-gas estimates or reconstructed
historical cohorts.

## Automotive alignment snapshot

- Scope: `Mk=TOYOTA`, 2024 final, EEA-monitored new passenger cars, EU27.
- Registrations: 803,094; WLTP values mapped for 803,042 (99.994%).
- Registration-weighted certified WLTP intensity: 107.073 gCO2/km.
- Fixed-distance normalized tailpipe load: 85,984.351 tCO2 if every WLTP-mapped registration
  travels exactly 1,000 km. The 27 country values reconcile to this EU27 total.
- Powertrain shares are derived from EEA fuel-mode/fuel-type codes and retain the classification
  rule and registration denominator.
- Direct benchmarks: EU-wide fleet targets 93.6 gCO2/km (2025) and 49.5 gCO2/km (2030).
- Interpretation: distance to an EU-wide fleet pathway, not Toyota's manufacturer-specific
  compliance result. The normalized load is not actual annual use, lifetime, real-world,
  upstream-energy, production, or lifecycle GHG; no historical series is calculated.

## Power evidence snapshots

### JERA · Japan · FY2024

- Scope: JERA Domestic / JERA Group, FY2024, joint ventures proportionately consolidated.
- Net generation: 242 billion kWh (242 TWh), sending-end power.
- Reported generation intensity: 0.520 kgCO2e/kWh (520 kgCO2e/MWh).
- Evidence: JERA environmental data plus SOCOTEC Certification Japan's independent limited-
  assurance appendix.
- Policy context: Japan FY2030 use-end factor 250 kgCO2/MWh; FY2040 renewables 40–50% and
  thermal 30–40% of national generation.
- Interpretation: all national values are `context_only`; no JERA distance-to-target is computed
  because generator, point-of-use, and national-system boundaries differ.

### KOEN · Korea · 2024

- Reported generation: 39,660 GWh (39.66 TWh); gross/net basis is not stated.
- Reported Scope 1: 30,606,585 tCO2e. Displayed headquarters/plant rows sum 2,000 tCO2e higher.
- Reported Scope 2: 103,752 tCO2e. Displayed headquarters/plant rows sum 269 tCO2e higher.
- Evidence: KOEN ESG Data Center; no independent assurance statement was identified for this web
  table.
- Policy context: Korea's Eleventh Electricity Plan gives 145.9 MtCO2e transition-sector
  emissions in 2030 and carbon-free generation shares of 53.0% in 2030 and 70.7% in 2038.
- Interpretation: reported totals are retained; no intensity or KOEN target gap is computed. All
  national values are `context_only`.

## Shipping evidence snapshot

### MOL · Global fleet · FY2024

- Reported EEOI: 10.95 gCO2e/ton-mile on a lifecycle/Well-to-Wake GHG boundary.
- Scope: MOL and major ocean-going vessels operated by group subsidiaries in Japan and overseas;
  783 applicable vessels.
- Evidence: MOL environmental data independently assured by ClassNK; the appendix records the
  EEOI method, transport-work denominator, and assurance sampling threshold.
- Policy context: IMO 2030 carbon-intensity reduction of at least 40%, absolute-GHG reduction of
  at least 20% while striving for 30%, and zero/near-zero-GHG energy uptake of at least 5% while
  striving for 10%.
- Interpretation: all IMO values are `context_only`. MOL and IMO do not share the baseline year,
  emissions boundary, or aggregation population, so no company target gap is computed. The value
  is not allocated to individual customers and no historical series is reconstructed.

## What is sourced

- Grid intensity and NDC headline data for 11 operating-country rows.
- Sectoral S2 pathways for JP/KR/EU/UK, and current-policy S1 pathways for CA/AU.
- Seventeen model or powertrain certification rows from EEA, EPA/fueleconomy.gov, MLIT,
  and the Korea Energy Agency. These are parameter records, not company-fleet averages.

## What still blocks company calculation

| Required input | Current state | Publication rule |
|---|---|---|
| Registration volumes `V_c,v` | Toyota EU27 brand aggregate collected; exact model-level mapping remains uncollected | Require country/year/model/powertrain units from an official or licensed registry |
| Vehicle-to-registration mapping | Not present | Require exact keys or a disclosed aggregation rule; no analyst mix allocation |
| Fleet base intensity | Not present in the workbook | Require a sourced operating-country/segment baseline |
| Annual distance (VKT) | Not present | Require a current national statistic and unit |
| Vehicle lifetime `T` | Not present | Require central value and sensitivity range |
| S1/S3 pathways | Partial | Publish only source-specific rates; leave other cells empty |
| S2 sectoral path | AU/CA remain economy-wide pro-rata; US/IN/ID/SA/CN flagged | Keep warnings/flags; do not present pro-rata as an observed sector rate |

`PRORATA_IDENTITY` remains on AU and CA. It is a transparent derived benchmark with a tier
downgrade, not an independently observed transport or power pathway.

## Firm universe

The canonical list is `data/published/firms.json`, generated from
`TI_CaseStudy_Target_Companies.xlsx` and `CAP_Target_Companies_Draft.xlsx`. All firms are
currently `runnable: false` for the legacy lifetime report. Toyota, JERA, KOEN, and MOL have
`alignment_available: true` for their reporting-year evidence snapshots; Hyundai and all other
candidates remain at the evidence gate.

The internal `ti-framework/fixtures/reference_case.json` remains only for engine arithmetic
validation. It is illustrative, is not copied to `data/published`, and does not appear as a
firm, country comparison, or calculator starting point.

## Quality rule

Every numerical row must record source, unit, geography, year, and evidence tier. Empty is
not zero. Missing registration units now stop a calculation cell instead of silently
contributing zero.
