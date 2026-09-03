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
| `ti_crossover_eu27.csv` | 4b | `build_sensitivity.py` | company × destination × model × powertrain × scenario: closed-form crossover year (years after sale and calendar year) or the reason there is none |
| `ti_sensitivity_eu27.csv` | 4b | `build_sensitivity.py` | company × scenario × dimension (lifetime ±3 y, real-world factor low/high, proxied-distance quartiles) × variant: cohort total |
| `ti_country_eu27.csv` | 5 | `aggregate_country.py` | company × destination × scenario: units, `ti_tco2e`, per-vehicle, direction |
| `ti_powertrain_eu27.csv` | 5 | `aggregate_country.py` | company × powertrain × scenario |
| `ti_company_eu27.csv` | 5 | `aggregate_country.py` | company × scenario: covered/withheld units, total, per-vehicle, direction, decomposition identity check |
| `ti_data_quality_eu27.csv` | 5b | `build_data_quality.py` | company: analysis level, benchmark method, covered/withheld units, tier-C unit share and the `directional_only` flag (guideline §5.3, threshold 50 %), central lifetime, markets by distance tier, withheld reasons, warnings |

Sign convention: positive TI = the product emits less than the destination's committed
benchmark over its lifetime (contribution); negative = lock-in liability. Unit: tCO2e over
the operating lifetime, per-vehicle values in kgCO2e.

## Verification

**Tests** (`tests/test_model.py`, run with `.venv/bin/python -m pytest`): every ICE/HEV cell
satisfies the closed-form geometric-series sum from its own published year-0 values; the
annual flow summed over years equals the cell totals; company totals equal the country and
powertrain sums; processed sales totals equal the snapshot totals; covered + withheld =
registrations.

**Independent re-derivation (2026-09-04).** A reviewer re-derived the Honda EU27 cohort from
the processed inputs with code written from the whitepaper before reading the scripts. Fed
the pipeline's destination parameters, the independent engine reproduced all 621 Honda cells
to 6 × 10⁻⁷ and the cohort totals to 3 × 10⁻⁹ — the TI equations, `t = 0..T−1` convention,
unit chain and sign are implemented as documented. The review found three input-side defects,
all fixed the same day:

1. Distance per car divided the latest traffic observation by the latest *stock*
   observation, which for LT, BE, IE and EE were different years. Now the stock of the traffic
   year is used. LT moved +20.9 % (10,110 → 12,224 km/yr), BE +5.2 %, IE +5.4 %, EE +0.4 %,
   and the EU-average proxy the 13 tier-C markets use +0.6 %.
2. The real-world sensitivity never used the documented diesel end (1.171); the low variant
   moved only HEV. It now applies the documented range 1.171–1.211 to both ICE and HEV.
3. The BEV crossover label read "before sale year" for cells that in fact never cross
   because the grid decarbonises faster than the fleet benchmark; the two cases are now named.

**Relation to the archived published result** (`archive/data/published/lifetime_results.json`).
Before fix 1 the pipeline reproduced the archived Toyota and Hyundai totals to 2 × 10⁻⁷ (the
archived run carried the same year mismatch). After it, totals are 1–13 % more negative:
Toyota S1 −1.40 → −1.59 MtCO₂e, S2 −5.96 → −6.15, S3 −13.95 → −14.14; Hyundai S1 −1.49 →
−1.57, S2 −3.72 → −3.80, S3 −7.78 → −7.86. The archive remains the regression baseline for
the *engine* (the pipeline reproduces it exactly when fed the archived parameters); it is no
longer the baseline for the *inputs*.

Two further deliberate deviations from the archive: the proxied-distance sensitivity holds
the benchmark per vehicle fixed (distance cancels in CO2 per car) and scales only the product
side, so it is narrower than the archived band; and the real-world range is applied as a
replacement of the central factor, never on top of it.

Open review items for the project lead (not code defects): LU's fleet intensity (391 g/km)
is flagged implausible and tiered C yet still drives a positive LU result — withhold or report
separately; two markets (BG, PL) show a *rising* observed per-car CO2 trend, so their S1
benchmark grows (now flagged `OBSERVED_INCREASE` in `emission_targets_eu27.csv`); the
guideline's segment-intensity ratio is not applied (all-car fleet average, conservative for
crossover-heavy portfolios); S2 grid is held flat at 2024 intensity because the EU power
target is already met on an absolute basis, which makes BEV S2 lower than BEV S1; age bands
use the 1-Jan-2025 partition while stock uses 2024.

## Run order

`script/auto/run_all.py` runs everything (extraction, `derive_eu27_rates.py`,
`build_reference.py`, `build_ti.py`, `build_sensitivity.py`, `aggregate_country.py`,
`build_data_quality.py`, `build_database.py`, then ruff and pytest) and exits non-zero at the
first failure. The model scripts can also be run individually in that order.

The last step writes `data/auto/tradeimpact_auto.sqlite` — every input, lookup, processed
dataset, output table, the source registry and raw-file provenance in one database.
