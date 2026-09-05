# targets — the two pathways for each destination grid

## What this dataset is

The annual decline rate of grid carbon intensity that moves each destination's benchmark
forward: S1 the observed trajectory, S2 the destination government's own committed pathway. No
third scenario. Same construction as the automotive sector's `emission_targets`.

## Inputs

- `grid/processed/grid_intensity.csv` — the observed series the S1 trend is fitted to and the S2
  pro-rata starts from.
- `raw/ndc_anchors_power.csv` — **HAND-GATHERED, header-only until filled.** One row per
  destination: the committed target the S2 rate is read from, transcribed from the NDC or the
  national plan as communicated to the UNFCCC, with the link.

| field | note |
|---|---|
| country | alpha-2 |
| anchor_id | short key, for example `vn_ndc_2030_unconditional` |
| scope | `power` where the target is for the power sector or grid intensity; `economy` where only an economy-wide target exists |
| target_type | `reduction_from_base` (fraction below the base-year level), `absolute_level` (base_value → target_value in the same unit), `intensity_target` (target_value in gCO2/kWh), `bau_reduction` (below a business-as-usual projection: recorded, but **not usable** — no absolute anchor) |
| base_year, base_value, base_unit | as stated; base_value blank for reduction_from_base |
| target_year, target_value, reduction | as stated; reduction as a fraction |
| conditional | `yes` for a target conditional on international support, `no` otherwise; use the unconditional target where both exist and record the conditional one on a second row |
| communicated | date the NDC or plan was communicated |
| source_url, source_id | the UNFCCC NDC registry entry or the national document; the source_id also needs a row in `registry/sources.csv` |
| verified | `yes` once a second reader has checked the transcription against the document |
| note | boundary, gas basket, LULUCF treatment — anything a policymaker would ask |

## Processed outputs

`processed/emission_targets_power.csv` — `country`, `scenario`, `rate` (= `r_power`), `value`
(annual fractional decline), `target_level`, `base_year`, `target_year`, `derivation`,
`source_id`, by `script/power/targets/derive_power_rates.py`.

`processed/emission_targets_power_exclusions.csv` — `country`, `scenario`, `reason`: every
destination × scenario that has no rate and why. A unit in such a destination is reported under
the scenarios that exist and listed as excluded for the other; never a silent gap.

## Algorithm

S1: `ln g = a + b·y` fitted over the observed years 2015 onward excluding 2020–2021 (pandemic
years), `r = 1 − exp(b)`; at least three observations or S1 is excluded. A rising grid gives a
negative rate and is flagged `OBSERVED_INCREASE`.

S2: the target level is read on the grid-intensity series — `g_target = g(base) × (1 −
reduction)` for a reduction target, `g(base) × target_value / base_value` for an absolute-level
target, `target_value` itself for an intensity target — and the rate is the compound decline
from the latest observation to that level at the target year,
`r = 1 − (g_target / g(latest))^(1 / (target_year − latest_year))`. Where the target level is
already met by the observation (`PATHWAY_ALREADY_MET`) or the S1 trend is steeper, S2 is
floored at S1: committed policy is never read as less ambitious than what is observed. An
economy-wide target applied to grid intensity is a pro-rata assumption and is labelled
`economy_prorata`; the tier is B.

## Rules

- A BAU-relative target cannot anchor a pathway without the BAU projection and is recorded as an
  exclusion with that reason, so the reader can see which destinations (typically Vietnam,
  Indonesia, Bangladesh under earlier NDCs) lack a usable commitment.
- Where a destination communicated a later NDC with a different base year, the newer document
  is used and the older recorded in `note`.
