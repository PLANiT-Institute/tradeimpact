# Data collection status

Snapshot date: 2026-08-05 · Public contract: `export-impact-v1`

## Automotive comparison cohorts

Source scope: EEA final 2024 monitoring data, `Mk=TOYOTA` and `Mk=HYUNDAI`, new passenger cars
first registered in the EU27. Both companies use the same query and classification boundary.

| Dimension | Toyota | Hyundai |
|---|---:|---:|
| Destination registrations | 803,094 | 429,936 |
| Commercial-name mapped units | 803,092 | 429,928 |
| Powertrain-mapped units | 803,094 | 429,936 |
| Certified WLTP tailpipe mapped | 803,042 | 429,905 |
| Certified electricity-use mapped | 34,776 | 60,152 |
| Destination × name × powertrain rows | 660 | 626 |
| Commercial-name strings | 72 | 67 |
| Production/export origin | not collected | not collected |
| Lifetime TI result | withheld | withheld |

The adapter covers 27 destination countries for each company. Commercial names are regulatory
data labels, not normalized model families. Destination registration does not prove manufacturing
country or export origin. Toyota's reported European-production share and Hyundai's reported
Türkiye/Czech production share are retained as company-level context only and are not assigned to
individual registrations.

The previous fixed-1,000km certified tailpipe load was removed. Multiplying registrations by an
arbitrary distance did not answer the project's lifetime and destination-NDC question.

## Destination target hierarchy

- EU collective NDC: submitted 5 November 2025; 2035 indicative net-GHG reduction range of
  66.25%–72.5% from 1990. This is economy-wide fallback context.
- EU domestic-transport pathway: 2023 inventory base and 2030 Commission pathway imply a 4.344%
  annual decline. This is a regional all-transport proxy, not a country-specific passenger-car
  target.
- Country-specific passenger-car or road-transport pathways: not yet collected for the 27 shared
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
