# output — model results (research process steps 3–5)

Written only by `script/auto/model/`. Every file is regenerated from the processed datasets;
nothing here is edited by hand. EU27 × 2024 × {Toyota, Hyundai} is the first cohort set.

| file | step | script | grain |
|---|---|---|---|
| `destination_parameters_eu27.csv` | 3 | `build_reference.py` | importer market: distance (km/yr, tier, band), car stock, car CO2, fleet intensity base (gCO2/km, tier), grid intensity (gCO2/kWh), mean car age, operating lifetime (central/low/high), warnings, source ids |
| `reference_trajectories_eu27.csv` | 3 | `build_reference.py` | market × scenario × t: `e_ref_kgco2_per_vehicle` (benchmark per vehicle-year), `grid_kgco2_per_kwh` |
| `ti_by_model_eu27.csv` | 4 | `build_ti.py` | company × destination × model × powertrain × scenario: units, lifetime, distance + tier, real-world factor, year-0 product and benchmark emissions, `ti_per_vehicle_kgco2e`, `ti_tco2e` |
| `ti_annual_eu27.csv` | 4 | `build_ti.py` | company × scenario × t: annual TI flow (tCO2e) and surviving vehicles |
| `ti_withheld_eu27.csv` | 4 | `build_ti.py` | units carrying no result and why (PHEV: no utility factor; FCEV: no hydrogen intensity; no certified value) |
| `ti_country_eu27.csv` | 5 | `aggregate_country.py` | company × destination × scenario: units, `ti_tco2e`, per-vehicle, direction |
| `ti_powertrain_eu27.csv` | 5 | `aggregate_country.py` | company × powertrain × scenario |
| `ti_company_eu27.csv` | 5 | `aggregate_country.py` | company × scenario: covered/withheld units, total, per-vehicle, direction, decomposition identity check |

Sign convention: positive TI = the product emits less than the destination's committed
benchmark over its lifetime (contribution); negative = lock-in liability. Unit: tCO2e over
the operating lifetime, per-vehicle values in kgCO2e.

## Verification

The pipeline reproduces the previously published EU27 2024 result
(`archive/data/published/lifetime_results.json`) to a relative error below 2 × 10⁻⁷ on every
company × scenario total, and every destination × powertrain cell agrees to rounding.
Destination parameters (distance, fleet intensity, grid, lifetime, tiers) match
`archive/data/published/destination_inputs.json` exactly for all 27 markets.

## Run order

```bash
.venv/bin/python script/auto/emission_targets/derive_eu27_rates.py
.venv/bin/python script/auto/model/build_reference.py
.venv/bin/python script/auto/model/build_ti.py
.venv/bin/python script/auto/model/aggregate_country.py
.venv/bin/python script/auto/model/build_database.py
```

The last step writes `data/auto/tradeimpact_auto.sqlite` — every input, lookup, processed
dataset, output table, the source registry and raw-file provenance in one database.
