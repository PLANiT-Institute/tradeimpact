# Sector expansion plan

Trade Impact uses one evidence and query contract, but a separate activity boundary and metric
adapter for each sector. Sector adapters can share provenance, coverage, comparison, web, and MCP
infrastructure; they cannot share an emissions unit by assumption.

| Order | Sector | Operating boundary | Activity basis | First direct metric | Main boundary question |
|---:|---|---|---|---|---|
| 1 | Automotive | Registration/use country | New registrations by model and powertrain | Policy-eligible ZEV share; certified new-fleet CO2 | Brand/group, vehicle class, test regime |
| 2 | Power | Generation country and connected grid | Net MWh by plant, technology, and fuel | Generation intensity; policy-defined clean share | Generation vs consumption and cross-border flow |
| 3 | Shipping | Voyage/IMO jurisdiction | Transport work by vessel and fuel | Compatible carbon-intensity measure | Voyage vs flag state; WtW vs TtW |
| 4 | Steel | Production plant country | Crude steel tonnes by route | tCO2e/t crude steel | Route and Scope 1 vs Scope 1+2 boundary |
| 5 | Petrochemicals | Production plant country | Tonnes by chemical product | tCO2e/t of the same product | Product and joint-output allocation |

## Adapter acceptance gates

A sector becomes `pilot` only after all of the following exist:

1. a written operating-boundary decision;
2. one activity-volume source with a reviewable licence;
3. one company metric with an exact denominator;
4. one directly comparable official target, or an explicit `context_only` result;
5. activity-weighted coverage and unmatched records;
6. source records and reproducible transformation code;
7. tests for unit, scope, aggregation, and fail-closed behaviour.

It becomes `supported` only after at least two companies and two operating geographies can be
compared under the same contract without hidden allocation.

## Power pilots: JERA Japan and KOEN Korea

The first power adapter publishes JERA's independently assured FY2024 domestic-group net
generation (242 TWh, sending-end) and reported generation intensity (520 kgCO2e/MWh). The exact
company boundary, proportional joint-venture consolidation, source hashes, and assurance source
are retained. It does not infer plant or fuel mix because matching generation-by-technology data
is not disclosed on the same assured boundary.

Japan's FY2030 250 kgCO2/MWh outlook is measured at the point of use, while the FY2040 renewable
40–50% and thermal 30–40% ranges describe the national system. All three are therefore published
as `context_only`: no JERA gap, midpoint, or target verdict is calculated. A future direct
comparison still requires a generator-boundary target or a policy-defined clean-generation share
with matching eligibility and company technology data.

The second power adapter publishes KOEN's company-reported 2024 generation (39.66 TWh), Scope 1
(30.607 MtCO2e), and Scope 2 (0.104 MtCO2e). It deliberately does not publish generation
intensity: the source page does not state whether generation is gross or net, and the displayed
plant rows exceed the reported Scope 1 and Scope 2 totals by 2,000 and 269 tCO2e respectively.
Reported totals are preserved, the discrepancies are exposed, and no independent assurance is
claimed.

Korea's Eleventh Electricity Plan provides 2030 transition-sector emissions and 2030/2038
carbon-free generation shares. They remain `context_only` because they describe the national
system and have no disclosed KOEN allocation. The second company/geography acceptance threshold
is now met, but power remains a `pilot` rather than `supported` until directly comparable policy
metrics and matching company activity are available without hidden allocation.

Plant, technology, fuel, net generation, direct emissions, emissions boundary, and ownership
remain the preferred full power dataset because a company average can hide simultaneous fossil
lock-in and zero-carbon generation.

## Cross-sector product rule

Cross-sector views may compare:

- data coverage;
- share of activity assessed against direct targets;
- number and value of markets with compatible benchmarks;
- evidence classes and source freshness;
- direction within each sector's own metric.

They must not add `gCO2/km`, `kgCO2e/MWh`, `gCO2e/tonne-nm`, and `tCO2e/t` into one score without a
separately reviewed normalization methodology.
