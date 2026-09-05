# targets — the two pathways for each destination grid

## What this dataset is

The annual decline rate of grid carbon intensity that moves each destination's benchmark
forward: S1 the observed trajectory, S2 the destination government's own committed pathway. No
third scenario. Same construction as the automotive sector's `emission_targets`.

## Inputs

- `grid/processed/grid_intensity.csv` — the observed series the S1 trend is fitted to and the S2
  pro-rata starts from.
- `raw/climatewatch_ndc_content.json` — Climate Watch (World Resources Institute) NDC content:
  for every country and every NDC submission, the GHG target as stated, its type (base year /
  baseline scenario / fixed level / intensity / trajectory), the target year and the sectors
  covered, read by WRI from the UNFCCC registry. Fetched from the public API by
  `script/power/targets/fetch_climatewatch_ndc.py` (URL, access date and hash in the registry;
  licence CC BY 4.0). This is what the S2 anchor of each destination is read from, so S2 no
  longer waits on a hand file.
- `raw/ndc_anchors_power.csv` — **hand rows on top**: a row here replaces the parsed row for its
  country. Used where the registry text is not the furthest stated pathway (EU member states:
  the EU 2040 target, 90 % below 1990, the same anchor as the automotive sector), where the
  destination is not a UNFCCC party (Taiwan: the national 2035 target), where a territory falls
  under another party's NDC (Guam and Puerto Rico under the United States), and for any
  destination whose parsed row says `needs_review`. Every `source_id` here needs a row in
  `registry/sources.csv`.

| field | note |
|---|---|
| country | alpha-2 |
| anchor_id | short key, for example `eu_2040_economy` |
| scope | `power` where the target is for the power sector or grid intensity; `economy` where only an economy-wide target exists |
| target_type | `reduction_from_base` (fraction below the base-year level), `absolute_level` (base_value → target_value in the same unit), `intensity_target` (target_value in gCO2/kWh); anything else is recorded but **not usable** |
| base_year, base_value, base_unit | as stated; base_value blank for reduction_from_base |
| target_year, target_value, reduction | as stated; reduction as a fraction |
| conditional | `yes` for a target conditional on international support, `no` otherwise |
| communicated | date the NDC or plan was communicated |
| source_url, source_id | the document; the source_id also needs a row in `registry/sources.csv` |
| verified | `yes` once a second reader has checked the transcription against the document |
| note | boundary, gas basket, LULUCF treatment — anything a policymaker would ask |

### How the registry text is read (`extract_ndc_anchors.py`)

The latest submission on file is used (third NDC over second over updated first over first over
INDC). A **base-year target** sentence is machine-read: the unconditional percentage where the
text distinguishes one, otherwise the lower bound of a range (upper bound kept in
`reduction_upper`); the base year is the year the text compares against; the target year is the
furthest year the text states (the project lead's rule: the pathway runs to the government's
furthest stated year — Japan's 73 % by FY2040, not its 60 % by FY2035). A **baseline-scenario**
(BAU) target has no absolute level and a **GDP-intensity** target is not an emissions level;
both are recorded as `not_usable`. **Fixed-level** and **trajectory** targets state a level in
tonnes but not the base-year emissions the pro-rata needs, so they are `needs_review` until a
hand row supplies `base_value` and `target_value`. The processed table carries `parse_status`,
the submission and the sentence read, so every S2 rate can be checked against its text.

## Processed outputs

`processed/ndc_anchors_power.csv` — one row per destination: the anchor, `parse_status`
(`parsed` | `hand` | `needs_review` | `not_usable` | `no_ndc_target_on_file`), the submission and
the target text, by `script/power/targets/extract_ndc_anchors.py`.

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
