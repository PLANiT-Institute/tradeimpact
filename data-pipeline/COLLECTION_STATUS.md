# Data collection status

Snapshot date: 2026-08-05 · Public contract: `export-impact-v1`

## Toyota automotive cohort

Source scope: EEA final 2024 monitoring data, `Mk=TOYOTA`, new passenger cars first registered in
the EU27.

| Dimension | Status | Coverage |
|---|---|---:|
| Destination country | observed | 803,094 / 803,094 registrations |
| Commercial name | observed as reported | 803,092 / 803,094 |
| Powertrain group | project-classified from EEA fields | 803,094 / 803,094 |
| Certified WLTP tailpipe CO2 | observed where reported | 803,042 / 803,094 |
| Certified electricity use | observed where reported | 34,776 / 803,094 |
| Destination × name × powertrain rows | published | 660 rows |
| Production/export origin | not collected | 0 |
| Lifetime TI result | withheld | required scenario inputs incomplete |

The adapter retains 72 commercial-name strings across 27 destination countries. These are
regulatory data labels, not yet normalized model families. Destination registration does not
prove manufacturing country or export origin.

The previous fixed-1,000km certified tailpipe load was removed. Multiplying registrations by an
arbitrary distance did not answer the project's lifetime and destination-NDC question.

## Destination target hierarchy

- EU collective NDC: submitted 5 November 2025; 2035 indicative net-GHG reduction range of
  66.25%–72.5% from 1990. This is economy-wide fallback context.
- EU domestic-transport pathway: 2023 inventory base and 2030 Commission pathway imply a 4.344%
  annual decline. This is a regional all-transport proxy, not a country-specific passenger-car
  target.
- Country-specific passenger-car or road-transport pathways: not yet collected for the 27 Toyota
  destinations. These remain the preferred benchmark.

## Inputs still blocking lifetime TI

1. production/factory-to-destination mapping for Level 2 export attribution;
2. destination-country annual vehicle-kilometres travelled;
3. destination-country survival and operating-lifetime distributions;
4. real-world correction by market and powertrain;
5. passenger-car fleet service-intensity base;
6. independent S1/S2/S3 road-transport pathways for each destination;
7. independent S1/S2/S3 grid pathways for BEVs and PHEVs;
8. real-world PHEV utility factors;
9. FCEV hydrogen supply emissions intensity.

No missing field is assigned zero or a generic default in the public dataset.

## Other sector evidence

JERA, KOEN, and MOL current-period evidence adapters remain available as supporting sector
research. They are not yet exported-product cohorts and are no longer presented as equivalent to
the automotive implementation. Power, shipping, steel, and petrochemicals must each collect the
company × product/asset × destination × cohort dimensions required by their own physical method.

## Quality controls

`build_dataset.py` validates source IDs, units, coverage, cohort reconciliation, target roles, and
readiness references. `check_published.py` rebuilds the content-addressed inventory. The internal
reference fixture validates engine arithmetic only and is never published as a company result.
