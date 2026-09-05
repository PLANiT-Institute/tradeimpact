# grid — destination grid carbon intensity

## What this dataset is

The Layer 1 benchmark of the power case study: the carbon intensity of electricity generated in
each destination country, gCO2e/kWh, by year. A generating unit is measured against what the
grid it feeds emits per kWh, observed for past years and moved along the S1 and S2 pathways
(`targets/`) for future years.

## Raw file and source

`raw/owid_carbon_intensity_electricity.csv` — Our World in Data grapher export of Ember's Yearly
Electricity Data, all entities, fetched by `script/power/grid/fetch_owid_grid.py` (URL, access
date and hash in [`../../registry/raw_files.csv`](../../registry/raw_files.csv); publisher and
licence CC BY 4.0 in [`../../registry/sources.csv`](../../registry/sources.csv)). The same
publication feeds the automotive sector's US, AU, KR and JP grid series; this copy covers every
country so that any destination a project sits in has a benchmark without a second fetch.

## Processed output

`processed/grid_intensity.csv` — long format: `country` (alpha-2), `series` =
`grid_intensity`, `year`, `value`, `unit` = `gCO2_per_kWh`, `source_id`, `source_file`, by
`script/power/grid/extract_owid_grid.py`. OWID aggregates (`OWID_*` codes, World) are dropped;
ISO-3 codes with no alpha-2 in the geography table are printed and dropped.

## Tier

A — a published national series on the population the model uses (all generation in the
country), read without conversion. The whitepaper §5.1 rule is applied in
`registry/value_tiers.csv`.

## Rules

- The observed series is used as-is for calendar years it covers, for both scenarios: the two
  pathways diverge only after the latest observation.
- Ember's figure is generation-based (gCO2e per kWh generated, combustion CO2e). Transmission
  losses and upstream fuel-cycle emissions are outside it, on both sides of the comparison.
