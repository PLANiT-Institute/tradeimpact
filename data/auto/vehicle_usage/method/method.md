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

United States: `fhwa_vm1_2023.xlsx` — FHWA Highway Statistics Table VM-1 (`fhwa_vm1_2023`),
vehicle-miles and registrations by vehicle class for 2023 and 2022. FHWA classes light-duty
vehicles by wheelbase, not body type: the short-WB class (cars, light vans, small SUVs) is the
closest match to the EU M1 population and is published as `car_stock` / `car_traffic` (tier B
for the definitional mismatch); the long-WB class (pickups, large SUVs) is kept as separate
`ldv_long_wb_*` series. No age-band series is in VM-1, so US operating life needs another
source before a US result can run: BTS National Transportation Statistics Table 1-26 (average
age of automobiles and light trucks in operation) is the intended input for the same
mean-age → lifetime rule used for the EU27; the BTS site refused automated access on
2026-09-04, so the table is a hand-gathered file (drop the xlsx into the Drive folder
`Trade/Arc_Trade_Data/Auto/` and it is pinned like the IR workbooks).

Australia: still to collect — ABS Motor Vehicle Census (stock, last edition 31 Jan 2021) and
BITRE yearbook (passenger-vehicle km); both are report-shaped downloads.

## Processed files

| processed file | script | content |
|---|---|---|
| `vehicle_usage_eu27.csv` | `script/auto/vehicle_usage/extract_eu27_eurostat.py` | all four series, all 27 markets, 2015 onward, long format |
| `vehicle_usage_us.csv` | `script/auto/vehicle_usage/extract_fhwa_vm1.py` | US `car_stock`, `car_traffic` (short WB) and `ldv_long_wb_*`, 2022–2023 |

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
