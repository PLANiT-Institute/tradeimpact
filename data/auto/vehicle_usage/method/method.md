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

## Raw files

| file | source | how obtained | sha256 |
|---|---|---|---|
| `destination_eu27_inputs.json` | Eurostat, four datasets (links in the sources table) plus Ember grid intensity via Our World in Data; the file also carries the emissions series used by `country_emissions` | downloaded by the archived adapter (`archive/data-pipeline/adapters/destination_eu.py`) on 2026-08-09 into one hash-pinned JSON; each series is stored exactly as returned by the Eurostat API | `c0fdf593…c1c5ff` |

## Sources

| source_id | dataset | link |
|---|---|---|
| `eurostat_road_eqs_carpda` | Passenger cars by motor energy (stock, `mot_nrg=TOTAL`) | <https://ec.europa.eu/eurostat/databrowser/view/road_eqs_carpda/default/table?lang=en> |
| `eurostat_road_tf_veh` | Road traffic performance by vehicle type, cars, national territory, million vehicle-km | <https://ec.europa.eu/eurostat/databrowser/view/road_tf_veh/default/table?lang=en> |
| `eurostat_road_tf_vehmov` | Road traffic performance (vehicle movements), cars — fallback where `road_tf_veh` is empty | <https://ec.europa.eu/eurostat/databrowser/view/road_tf_vehmov/default/table?lang=en> |
| `eurostat_road_eqs_carage` | Passenger cars by age class | <https://ec.europa.eu/eurostat/databrowser/view/road_eqs_carage/default/table?lang=en> |

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
