# dashboard — the map assets the database carries

## What this dataset is

The two files the dashboard's and the report's maps are drawn from. Both are loaded into
`database/tradeimpact_auto.sqlite` (the geometry as the single-row table `map_geometry`, the codes
as `country_codes`), so a page opened from disk needs no second file and no network fetch.

## Raw files and sources

- `raw/countries-110m.json` — topojson/world-atlas `countries-110m.json` (version 2.0.2): Natural
  Earth 1:110m admin-0 country polygons as TopoJSON, feature id = ISO 3166-1 numeric. Fetched from
  its jsDelivr distribution by `script/auto/dashboard/fetch_map_assets.py`. Licence ISC
  (world-atlas); the Natural Earth data itself is public domain.
- `raw/world_countries.json` — mledoze/world-countries `countries.json` (version 5.1.0): ISO
  3166-1 alpha-2, alpha-3 and numeric codes with names, fetched by the same script. Licence ODbL
  1.0.

Both are JSON text, so they open in any editor; each is hash-recorded with its URL and access date
in [`../../registry/raw_files.csv`](../../registry/raw_files.csv), and its publisher and licence in
[`../../registry/sources.csv`](../../registry/sources.csv).

## Method output

`method/country_codes.csv` — the reduced code table (`iso_numeric`, `alpha2`, `alpha3`, `name`)
the pages join geometry ids to market and destination codes with.

## Rules

- The geometry is never edited: a country whose polygon looks wrong is a fact about the source,
  reported as such.
- Feature ids are matched to `iso_numeric` padded to three digits; a feature with no code in the
  table is drawn as land with no value, never dropped silently.
