# vehicle_technology — product technology parameters

## What this dataset is

Technology-side inputs per model / powertrain (research process step 2.3; whitepaper
Layer 2): certified tailpipe intensity, electric energy consumption, real-world correction
factors, and PHEV utility factors. Together with grid intensity these produce the product
emissions trajectory `E_prod(t)`.

## Required fields (processed output)

| field | type | unit | note |
|---|---|---|---|
| company | text | — | |
| model | text | — | as in the sales dataset (join key with company + powertrain) |
| powertrain | text | — | ICE / HEV / PHEV / BEV / FCEV |
| tailpipe_gco2_km | real | gCO2/km | certified, registrations-weighted across markets; empty when no bucket reported it |
| tailpipe_units | int | vehicles | registrations behind the tailpipe value |
| energy_wh_km | real | Wh/km | certified electric energy consumption (BEV/PHEV), same weighting |
| energy_units | int | vehicles | registrations behind the energy value |
| units | int | vehicles | total registrations of the model × powertrain |
| test_cycle | text | — | WLTP / EPA / NEDC — never mixed silently |
| source_id | text | — | row in the sources table below |
| source_file | text | — | raw file the row came from |

Real-world correction factors are a separate small input keyed on test cycle × powertrain
(`method/real_world_correction.csv`, each row with its own `source_id`): WLTP values get the
EEA OBFCM factors and range; EPA label values are already 5-cycle adjusted, so their factor is
1.0 at both ends. They are applied in the model step, never folded into the certified columns.

A plug-in hybrid carries both certified legs at once — the utility-factor-weighted tailpipe and
the utility-factor-weighted electricity — and they are added, never chosen between, because each
is that carrier's contribution to the same kilometre. The weighting is the type-approval one, and
the evidence is that it overstates electric driving: ifeu and Oeko-Institut (2025), Table 1,
measure the average real-world fuel consumption of plug-in hybrids registered under the rules in
force to 2024 at over 300 % above type approval, and Table 5 puts the observed energy utility
factor at 27.5 % for Hyundai, 34.8 % for Kia and 42.8 % for Toyota across about a million
vehicles. Re-weighting on those numbers would need a type-approval utility factor per car, which
neither the European nor the US dataset publishes here, so the certified weighting stands and the
**plug-in hybrid figure is a floor with its direction stated** — the same treatment, and the same
one-sided honesty, as the battery-electric row that passes its certified consumption through.

## Raw files and sources

United States: `epa_fueleconomy_vehicles.csv` — the complete EPA/DOE fueleconomy.gov vehicle
dataset (`epa_fueleconomy_vehicles`; 50,242 model-year trims, 1984 onward, 84 columns)
downloaded verbatim from <https://www.fueleconomy.gov/feg/epadata/vehicles.csv>; EPA
combined-cycle values, so never mixed with WLTP rows without an explicit conversion.

EU27: `../sales/raw/eea_*_2024_final.json`
(shared, not copied) — certified WLTP CO2 (`Ewltp__g_km_`) and electric energy
consumption (`z__Wh_km_`) per registration, aggregated by the EEA API per country × model ×
powertrain (`source_id` `eea_co2_monitoring_2024`). Real-world correction factors:
`method/real_world_correction.csv` (`eea_obfcm_real_world_2022`). Both resolve in
[`../../sources.csv`](../../sources.csv).

## Processed files

| processed file | script | content |
|---|---|---|
| `vehicle_technology_eea_2024.csv` | `script/auto/vehicle_technology/extract_eea_certified.py` | one row per company × destination × model × powertrain for the companies in scope (EU27 2024; WLTP); rows without a certified value are kept with an empty value and withheld downstream |
| `epa_trends_powertrain_share_my2024.csv` | `script/auto/vehicle_technology/extract_epa_trends.py` | one row per make × nameplate × powertrain from the EPA Automotive Trends MY2024 carline file: certification production volume (deduplicated on CAFE manufacturer, division, carline code and model-type index), share within the nameplate, volume-weighted label combined MPG; nameplates mapped through `method/epa_carline_map.csv` to the labels the company sales releases use. Supplies the powertrain split the releases withhold (assumption A-US-PT in `output/method.md`); production volumes are never a cohort |
| `vehicle_technology_kr_kea.csv` | `script/auto/vehicle_technology/extract_kea_fuel_economy.py` | one row per company × model × powertrain from the KEA label fuel-economy file (passenger-car rows, converter-built rows excluded): trim-mean tailpipe gCO2/km derived from label km/L with `method/fuel_carbon_factors.csv` (gasoline 2,348, diesel 2,689, LPG 1,511 gCO2/L), BEV Wh/km = 1000 / label km/kWh, FCEV Wh/km = 33,700 / label km/kg (the hydrogen's energy content, `method/hydrogen_supply.csv`); Korean base names mapped to the IR labels by `method/kr_model_map.csv`; `test_cycle = KR_5CYCLE` (label values are 5-cycle corrected, real-world factor 1.0). PHEV rows carry no value and are withheld downstream |
| `vehicle_technology_us_epa.csv` | `script/auto/vehicle_technology/extract_epa_fueleconomy.py` | one row per company × model year (2024–2025) × EPA model name × powertrain for the companies in scope; EPA combined-cycle CO2 (g/mile → g/km) and electricity (kWh/100 mi → Wh/km), unweighted mean over trims with the trim count; `base_model` is the join key to model-level sales |

## Sources

- EU: the EEA registration snapshots in `../sales/raw/` carry certified WLTP values per
  row — the primary EU technology source, already joined to volumes.
- Real-world correction: ICCT lab-to-road series (`References/ICCT_2018_LabToRoad.pdf`,
  `ICCT_2024_realworld_CO2_Europe_Jan2024.pdf` in the Drive folder).
- PHEV utility factors: ifeu/Oeko-Institut (2025), registered as `ifeu_phev_2025`, is the
  disclosure behind the plug-in hybrid floor. What would replace the floor with a figure: a
  type-approval utility factor per vehicle — the EPA fuel-economy file does publish one
  (`combinedUF`), the EEA monitoring dataset does not — paired with the observed factor above.
- US: EPA certification data by model.

## Processing method

Scripts in `script/auto/vehicle_technology/`; output `processed/vehicle_technology.csv`.
Certified values stay certified in this dataset. The real-world correction is applied
**once**, in the model step (`script/auto/model/build_ti.py`), reading the factor and its
range per powertrain from `method/real_world_correction.csv`; the factor used is recorded on
every result row (`real_world_factor` in `ti_by_model.csv`), so it can never be applied
twice.

## Rules

- Test cycles are never mixed across markets without an explicit, sourced conversion.
- A model with no sourced technology row contributes no result — its units are reported as
  withheld with their count, never absorbed.

## Korea (added 2026-09-04)

Sources: Korea Energy Agency, Vehicle Label Fuel Economy Information
(`kea_fuel_economy_labels`, https://www.data.go.kr/data/15083023/fileData.do, no restriction on
use, fetched by
`fetch_kea_fuel_economy.py`); fuel carbon factors from EPA (`epa_ghg_typical_vehicle`,
`epa_emission_factors_hub`). The NIER per-manufacturer fleet CO2 table 2012–2020
(`nier_manufacturer_fleet_co2`) is pinned as a cross-check only (2-cycle regulatory basis).

Traps. The KEA file has no CO2 and no fuel column: powertrain and fuel are parsed from the trim
string: a hybrid or plug-in marker, an electric marker or a charging range for
battery-electric, a diesel marker, or LPG. The combined-fuel-economy column mixes km/L and
km/kWh; battery-electric rows are identified by the charging-range column.
The file is a live snapshot of trims on sale (no model year). Deriving CO2 from the 5-cycle label
value gives the EPA-comparable figure, not the 2-cycle regulatory CO2 that Korean compliance
documents show (roughly 20 % lower).

## Hydrogen (`method/hydrogen_supply.csv`)

A fuel-cell car emits nothing at the tailpipe, which would make it look costless against any
benchmark. What it actually costs is the electricity behind its hydrogen, so it is assessed the
way a battery car already is: on the destination's own grid, not on hydrogen the destination does
not yet have.

| parameter | value | what it is |
|---|---|---|
| `h2_energy_wh_per_kg` | 33,700 Wh/kg | the gasoline-gallon-equivalent basis of the EPA label, which the Korean km/kg label is converted onto so both markets sit on one scale |
| `electrolysis_wh_per_kg` | 51,200 Wh/kg | IRENA (2020) *Green hydrogen cost reduction*, p.11: an alkaline electrolyser at nominal capacity is 65 % efficient, an LHV of 51.2 kWh/kgH₂ |

The ratio of the two (1.52 Wh of electricity per Wh of hydrogen) multiplies the certified value
before the grid intensity is applied, in `build_ti.py`. **Station compression to 700 bar, storage
and delivery are not included**, so the electricity per kilometre is a floor and every fuel-cell
figure understates its own emissions. Layer 2 is therefore never better than tier C for a
fuel-cell cell, however well measured the label is. Green hydrogen is not assumed: a destination
whose grid is clean gets a clean fuel-cell result without being given one it has not built.
