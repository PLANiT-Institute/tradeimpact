# Trade Impact public product contract

Version: `alignment-v2` · Status: implementation contract

Trade Impact is an evidence-first company-to-market alignment platform. It connects a firm's
observed activity in an operating geography with the most directly comparable official sector
target, and then exposes broader sector and NDC pathways as context. It is designed to expand
across sectors without forcing unlike activities into one universal unit.

## Non-negotiable comparison rule

A numeric alignment margin is calculated only when all four fields match:

1. sector and activity boundary;
2. metric definition;
3. applicable geography;
4. unit.

The target relation must also be explicit:

- `at_least`: company value minus target value;
- `at_most`: target value minus company value.

In both cases a positive margin means the target is met or exceeded. A company snapshot may be
compared with a future target, but the result must be labelled as distance to target, not proof of
current regulatory compliance.

Sector-total emissions pathways and economy-wide NDC targets are `contextual` unless a separate,
source-backed method translates them to the same activity metric. Contextual benchmarks never
produce a numeric company gap. Contextual numerical ranges use `value_min` and `value_max`
together; they are neither collapsed to a midpoint nor used in alignment arithmetic.

## Public objects

| Object | Purpose | Required provenance |
|---|---|---|
| Sector profile | Defines operating boundary, activity basis, metrics, and risks | Method version |
| Company metric | One observed company/year/geography snapshot | Source IDs, derivation, evidence class |
| Benchmark | One official target or contextual pathway | Source IDs, authority status, target relation |
| Coverage | Shows mapped versus reported activity | Numerator, denominator, unit, unmatched count |
| Source | Allows evidence tracing | Publisher, URL, date, evidence class, licence |
| Alignment result | Compares an exact metric/benchmark pair | All objects above plus warnings |

## Result statuses

- `available`: a direct, unit-compatible comparison was calculated;
- `context_only`: the benchmark is relevant policy context but cannot be subtracted;
- `not_comparable`: data exists but sector, metric, geography, or unit differs;
- `not_available`: the required observation or benchmark is missing.

Missing and unmatched activity is never assigned a modelled mix. Project-derived aggregations
must retain their source rows and formula. A result is not an official statistic merely because
its inputs are official.

## Publication boundary

The first release reports reporting-year snapshots and future policy targets. It does not publish:

- vehicle-, asset-, or product-lifetime greenhouse-gas estimates;
- reconstructed company history;
- avoided-emissions claims;
- a universal cross-sector company score;
- arithmetic between a company activity metric and an incompatible sector-total NDC value.

The original lifetime calculation engine remains an internal research and arithmetic-validation
surface until its empirical inputs and sector methods pass a separate publication review.

## Machine-readable files

The reproducible dataset builder emits:

- `sectors.json`: sector boundaries and required data;
- `company_metrics.json`: source-backed snapshots;
- `benchmarks.json`: direct and contextual target records;
- `sources.json`: structured provenance;
- `countries.json`: existing operating-country pathway evidence;
- `firms.json`: candidate company universe and publication gate;
- `meta.json`: hashes, versions, inventory counts, and method contract.
