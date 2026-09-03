# vehicle_usage — how vehicles are used in each importer market

## What this dataset is

Destination-side usage inputs (research process step 2.2): annual distance driven, vehicle
operating lifetime / survival, and the fleet stock baseline the benchmark is normalised
against (whitepaper Layer 1 denominator and lifetime summation horizon `T`).

## Required fields (processed output, long format)

| field | type | unit | note |
|---|---|---|---|
| country | text | ISO 3166-1 alpha-2 | EEA convention (`GR` for Greece) |
| series | text | — | `car_stock`, `car_traffic`, `car_traffic_fallback`, `car_stock_age_<band>` |
| year | int | year | observation year |
| value | real | see `unit` | |
| unit | text | — | `vehicles`, `million_vkm` |
| source_id | text | — | row in the sources table below |
| source_file | text | — | raw file the row came from |

Derived quantities the model needs — annual distance per car (`car_traffic` × 10⁶ ÷
`car_stock`, km/year) with a tier (A when `car_traffic` is observed, C when only the
fallback series exists), and operating life from the age bands — are computed in the model
step from these rows, not stored here, so the tier is always reproducible.

## Raw files and sources

`destination_eu27_inputs.json` — one hash-pinned JSON holding four Eurostat datasets
(`road_eqs_carpda` stock, `road_tf_veh` traffic of nationally registered cars,
`road_tf_vehmov` fallback, `road_eqs_carage` age bands) plus the emissions series used by
`country_emissions`, each exactly as returned by the API on 2026-08-09. Links, licence and
hash: [`../../sources.csv`](../../sources.csv), [`../../raw_files.csv`](../../raw_files.csv).
Only `road_tf_veh` (TER_REGNAT: traffic by cars registered in the country) is used for
distance — it is the same population as the stock denominator; `road_tf_vehmov` counts all
traffic on the territory and is kept only as a documented series, never divided by stock.

## Processed files

| processed file | script | content |
|---|---|---|
| `vehicle_usage_eu27.csv` | `script/auto/vehicle_usage/extract_eu27_eurostat.py` | all four series, all 27 markets, 2015 onward, long format |

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
