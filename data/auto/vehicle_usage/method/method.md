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

EU27: four Eurostat cubes fetched directly from the Eurostat API as JSON-stat 2.0 by
`script/auto/vehicle_usage/fetch_eurostat.py` (request URL, dataset page, access date and hash
in [`../../raw_files.csv`](../../raw_files.csv); publisher and licence in
[`../../sources.csv`](../../sources.csv)): `eurostat_road_eqs_carpda.json` (stock),
`eurostat_road_tf_veh.json` (traffic by cars registered in the country — the same population
as the stock denominator, so the only series used for distance), `eurostat_road_tf_vehmov.json`
(traffic on the territory by any car; kept as a documented series, never divided by stock),
`eurostat_road_eqs_carage.json` (stock by age class). Fetched values reproduce the previously
archived compilation exactly, which is therefore no longer kept.

United States: `fhwa_vm1_2023.xlsx` — FHWA Highway Statistics Table VM-1 (`fhwa_vm1_2023`),
vehicle-miles and registrations by vehicle class for 2023 and 2022. FHWA classes light-duty
vehicles by wheelbase, not body type: the short-WB class (cars, light vans, small SUVs) is the
closest match to the EU M1 population and is published as `car_stock` / `car_traffic` (tier B
for the definitional mismatch); the long-WB class (pickups, large SUVs) is kept as separate
`ldv_long_wb_*` series. No age-band series is in VM-1; US operating life comes from
`nhtsa_809952_passenger_car_survival.csv` — NHTSA DOT HS 809 952 Table 7 (passenger-car
survival probability and annual miles by age, 1977–2002 registrations), transcribed from the
report PDF with page reference (`nhtsa_809952`; tier C for its age) — from which the expected
and median lifetime are derived. The BTS average-age table (Table 1-26) would be the
preferred, current input; the BTS site refuses automated access, so it stays a hand-gathered
option.

Australia: `abs_motor_vehicle_census_2021.xls` — ABS Motor Vehicle Census 31 Jan 2021 data
cube (`abs_motor_vehicle_census_2021`; passenger-vehicle stock, estimated average age and fuel
mix for 2016, 2020, 2021; the final edition of the census) and
`abs_survey_motor_vehicle_use_2020.xls` — ABS Survey of Motor Vehicle Use, 12 months to 30
June 2020 (`abs_survey_motor_vehicle_use_2020`; passenger-vehicle kilometres, vehicles and
average km per vehicle for 2012–2020; the final edition of the survey). Both downloaded
directly from the ABS site (links and hashes in `raw_files.csv`).

## Processed files

| processed file | script | content |
|---|---|---|
| `vehicle_usage_eu27.csv` | `script/auto/vehicle_usage/extract_eu27_eurostat.py` | all four series, all 27 markets, 2015 onward, long format |
| `vehicle_usage_us.csv` | `script/auto/vehicle_usage/extract_fhwa_vm1.py` | US `car_stock`, `car_traffic` (short WB) and `ldv_long_wb_*`, 2022–2023 |
| `vehicle_usage_us_lifetime.csv` | `script/auto/vehicle_usage/extract_nhtsa_survival.py` | US `car_expected_lifetime_years`, `car_median_lifetime_years`, `car_lifetime_distance_km` from the NHTSA survival schedule |
| `vehicle_usage_au.csv` | `script/auto/vehicle_usage/extract_abs_mvc.py` | AU `car_stock`, `car_mean_age_years`, `car_stock_petrol/diesel/other_fuel`, 2016–2021 |
| `vehicle_usage_au_smvu.csv` | `script/auto/vehicle_usage/extract_abs_smvu.py` | AU `car_traffic` (million vkm), `car_stock_smvu`, `car_vkt_avg` (km), survey years 2012–2020 |

## Processing method

Scripts in `script/auto/vehicle_usage/`, one per raw file, each writing its own processed file
in the long format above. `fetch_eurostat.py` is the only network step for the EU27 and is run
by hand when a cube must be refreshed (raw files are pinned once obtained).

## Rules

- Just under half of the covered EU27 units sit on a proxied (tier C) distance; above the
  50 % threshold a result is published as a **direction, not a precise magnitude**.
- Missing usage input for a market → that market's result is unavailable, never defaulted.

## Korea (added 2026-09-04)

| processed file | script | content |
|---|---|---|
| `vehicle_usage_kr.csv` | `script/auto/vehicle_usage/extract_molit_registrations.py` | `stock_<segment>` (MOLIT year-end stock, all uses, 2007–2025, from the latest December workbook); `mean_age_<segment>` and `stock_age_<segment>_<band>` per December snapshot from the model-year distribution |
| `vehicle_usage_kr_traffic.csv` | `script/auto/vehicle_usage/extract_kotsa_tmacs.py` | `traffic_<segment>` (million vehicle-km, 2016–2024) and `daily_km_<segment>` from KOTSA TMACS inspection odometers |

Sources: MOLIT Vehicle Registration Statistics (`molit_vehicle_registration`,
https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=58, December workbooks downloaded
through the portal's own file endpoint by `fetch_molit_registrations.py`); KOTSA Motor
Vehicle Travel Distance Statistics
TMACS (`kotsa_tmacs_vkm`, https://tmacs.kotsa.or.kr/web/TG/TG200/TG2200/Tg1700_02.jsp?mid=S3080,
the page's JSON data call, fetched per year by `fetch_kotsa_tmacs.py`).

Rules and traps. The passenger-car class is the one defined by the Motor Vehicle Management
Act (up to ten seats); the Carnival and Staria nine- and eleven-seaters are buses and the
Porter and Bongo are goods vehicles, so each is measured against its own segment benchmark.
Distance is tier A: odometer readings grossed up to the same population as the stock (2024:
260,456 million vkm / 21.77 million cars = 11,963 km). The TMACS total row is labelled as a
mean before 2021 and as a sum from 2021, the annual ALL column is in
thousand km (not stated on the page), 2015 returns no rows, and per-vehicle distance breaks by
about 11 % in 2021. The MOLIT age sheet is a model-year distribution whose oldest band is
open-ended (2005 = 2005 and earlier), so the mean age (7.3 years in 2024) is biased low and the
derived lifetime is tier C.
