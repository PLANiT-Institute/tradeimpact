# Estimated inputs — Toyota & Hyundai case fixtures

Every value below is a **rough, documented estimate** (owner request, 2026-07-22): good
enough for a first per-country read, honest about provenance, and to be replaced by
collected data (COLLECTION_STATUS.md is the backlog). Tier meanings per Whitepaper §5.1
(A firm-verified / B estimated from public data / C proxy). Nothing here is engine
default — all of it lives in `data-pipeline/fixtures/{toyota,hyundai}.json` and flows
through the same loader/engine as any collected data.

## What is real (not estimated)

| Input | Source | Tier |
|---|---|---|
| Grid intensity G_c(0), all markets | Ember 2024 via workbook `Layer1_NDC_benchmark` | A |
| S2 economy-wide reduction rates AU / EU / JP / KR | UNFCCC 2035 NDCs via workbook (pro-rata, D1 identity warning applies) | B |
| US = no S2 benchmark | NDC revoked — FLAG per NOTES.md D3, excluded from S2 headline | — |

## Estimated (replace when collected)

| Parameter | Values used | Rationale | Tier |
|---|---|---|---|
| r_fleet S1 (STEPS) | JP 2.4, EU 1.4, AU 1.9, KR 2.5, US 1.0 %/yr | ~0.6× the S2 pro-rata rate; transport under current policies decarbonises slower than NDC ambition | C |
| r_power S1 (STEPS) | JP 2.5, EU 4.0, AU 5.0, KR 3.0, US 2.0 %/yr | IEA STEPS direction: EU/AU grids decarbonising fast on current policy, JP/KR/US slower | C |
| r_fleet S3 (NZE) | 5.5–7 %/yr by market | IEA NZE transport pathway magnitude | C |
| r_power S3 (NZE) | 8–11 %/yr by market | IEA NZE electricity pathway magnitude | C |
| Fleet base intensity I_fleet(0) | JP 0.150, EU 0.140, AU 0.185, KR 0.165, US 0.200, CN 0.160, IN 0.130 kgCO₂e/km | In-use all-vintage fleet average: EU cleanest, AU/US ute/truck-heavy, IN small-car-dominated | C |
| Annual distance D_c | JP 9,500; EU 12,000; AU 13,800; KR 13,000; US 18,000; CN 12,000; IN 10,000 km/yr | National VKT statistics magnitudes (MLIT, EEA, BITRE, KTDB, FHWA; CN/IN regional defaults) | B/C |
| Vehicle lifetime T | 15 yr (± 3 sensitivity) | Mean fleet age magnitude, OECD markets | B |
| ICE real-world intensity | 0.16–0.22 kgCO₂e/km by market mix | Certification values + ICCT Mind-the-Gap uplift; AU/US higher (utes, trucks) | B |
| HEV real-world intensity | 0.11–0.13 kgCO₂e/km | Toyota/Hyundai hybrid fleet averages, real-world corrected | B |
| BEV efficiency η_EV | 0.17–0.19 kWh/km | bZ4X / Ioniq5 certification + real-world uplift | B |
| PHEV UF / η_elec / ICE-mode | UF 0.40–0.50; 0.19–0.21 kWh/km; 0.14–0.16 kgCO₂e/km | Regulatory UF — **structural overstatement caveat applies** (Guideline §3.5); engine reports UF−0.15 lower bound side by side | C |
| 2024 volumes V_c,v | per-fixture placements | Public annual sales reports (JADA, ACEA, VFACTS, KAMA, US press releases), rough powertrain splits | B/C |

## Scope decisions

- **Markets:** KR, JP, EU, AU (computed S2 benchmarks) + US, CN, IN (FLAG — S1/S3 only,
  excluded from the S2 headline). CN: 2035 target vs undefined peak; IN: GDP-intensity
  target. CN/IN volumes and parameters are Tier C rough splits — refine first when
  registration data is collected.
- **Hyundai** = Hyundai brand (excl. Kia/Genesis granularity); **Toyota** = Toyota brand
  (Lexus folded into mixes). Model-level collection supersedes this.
- Engine behaviour on this data: PRORATA_IDENTITY warnings on all computed markets (D1),
  US excluded from the S2 headline with reason (D3), Tier C share drives the
  directional-only check — all visible in each report's data-quality declaration.
