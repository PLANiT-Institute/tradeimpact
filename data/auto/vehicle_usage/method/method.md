# vehicle_usage — how vehicles are used in each importer market

## What this dataset is

Destination-side usage inputs (research process step 2.2): annual distance driven, vehicle
operating lifetime / survival, and the fleet stock baseline the benchmark is normalised
against (whitepaper Layer 1 denominator and lifetime summation horizon `T`).

## Required fields (processed output)

| field | type | unit | note |
|---|---|---|---|
| country | text | ISO 3166-1 alpha-2 | |
| vkt | real | km/year | annual distance per passenger car |
| vkt_tier | text | — | A observed / B derived / C proxied — disclose, never hide |
| operating_life | real | years | expected lifetime (drives `T`) |
| car_stock | real | vehicles | passenger-car fleet size, reference year attached |
| stock_year | int | year | |
| source_id | text | — | row in `method/sources.md` |

## Raw files

| file | origin | sha256 |
|---|---|---|
| `destination_eu27_inputs.json` | Archived pipeline snapshot: sourced VKT, operating life, car stock, fleet intensity base, grid intensity and S1/S2/S3 rates for all 27 EU markets, each with tier, reference year, and derivation string | `c0fdf593…c1c5ff` |

## Sources for the gaps

- US: FHWA VMT statistics; Bureau of Transportation Statistics vehicle survival tables.
- Australia: ABS Survey of Motor Vehicle Use (discontinued 2020 — last edition + BITRE).
- EU: already covered by the raw snapshot above (Odyssee-Mure / Eurostat derivations).

## Processing method

Scripts in `script/auto/vehicle_usage/`; output `processed/vehicle_usage.csv`. The EU27
snapshot is flattened as-is, keeping tier and derivation text; US and Australia rows are
added by their own scripts as collected.

## Rules

- More than half of EU27 units currently sit on a proxied (tier C) distance — any result
  built on this dataset is published as a **direction, not a precise magnitude**, until
  tiers improve.
- Missing usage input for a market → that market's result is unavailable, never defaulted.
