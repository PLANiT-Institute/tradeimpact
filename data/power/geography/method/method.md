# geography — country codes

## What this dataset is

The ISO 3166-1 code table every other power dataset joins on: Global Energy Monitor names its
countries, Our World in Data codes them alpha-3, the model keys them alpha-2.

## Raw file and source

`raw/world_countries.json` — mledoze/world-countries `countries.json`, version 5.1.0, fetched from
its jsDelivr distribution by `script/power/geography/fetch_country_codes.py` (URL, access date and
hash in [`../../registry/raw_files.csv`](../../registry/raw_files.csv); publisher and licence in
[`../../registry/sources.csv`](../../registry/sources.csv)). Licence ODbL 1.0.

## Processed output

`processed/country_codes.csv` — `alpha2`, `alpha3`, `iso_numeric`, `name_common`,
`name_official`, one row per country with an alpha-2 code, by
`script/power/geography/extract_country_codes.py`.

## Rules

- Names are matched case-insensitively on `name_common` then `name_official`. A tracker name
  that matches neither is listed in `projects/method/country_name_overrides.csv` by hand; the
  projects extractor stops and names any that are still unmapped rather than dropping them.
