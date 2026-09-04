# trade_flows — passenger-car trade between the exporter and importer countries

## What this dataset is

Official trade statistics for passenger cars (HS 8703) between the exporter countries (Korea,
Japan) and the importer markets (EU27 member states, United States, Australia), by HS six-digit
sub-heading — which splits petrol and diesel by engine size, non-plug-in hybrids, plug-in hybrids
and battery-electric cars. It is **country-level**, not company- or model-level: it cannot
replace the sales cohorts, but it (a) gives the powertrain mix of what each exporter ships to
each market, (b) bounds the Korean-built share of Hyundai and Kia registrations (Level 2
production origin), and (c) covers Japan and Australia without any hand-gathered file.

## Required fields (processed output)

| field | type | unit | note |
|---|---|---|---|
| reporter | text | ISO 3166-1 alpha-2 / `EU27` | who reported the flow |
| flow | text | — | `imports` (importer-reported) or `exports` (exporter-reported) |
| exporter | text | ISO 3166-1 alpha-2 | KR, JP |
| importer | text | ISO 3166-1 alpha-2 / `EU27` | EU member state or aggregate, US, AU |
| year | int | year | calendar year |
| hs6 | text | — | HS 2022 six-digit sub-heading (`method/hs_passenger_cars.csv`) |
| powertrain_class | text | — | ICE / HEV / PHEV / BEV / OTHER from the HS sub-heading |
| units | int | vehicles | number of items; empty when the reporter gave none |
| quantity_flag | text | — | `reported`, `estimated` (Comtrade estimate), `not_reported` |
| value | real | EUR or USD | trade value as reported |
| currency | text | — | `EUR` (Comext) or `USD` (Comtrade) |
| source_id | text | — | `eurostat_comext_ds045409` or `un_comtrade_public` |
| source_file | text | — | raw file behind the row |

## Raw files and sources

Fetched directly from the sources of truth by `script/auto/trade_flows/fetch_comext.py` and
`fetch_comtrade.py`; request URLs, access dates and hashes in
[`../../raw_files.csv`](../../raw_files.csv), publishers and licences in
[`../../sources.csv`](../../sources.csv).

- `comext_imports_kr.json`, `comext_imports_jp.json` — Eurostat Comext ds-045409, EU member
  states' imports from Korea / Japan, all HS 8703 sub-headings, units and euros, 2022–2025.
- `comtrade_<reporter>_<x|m>_<partner>_<year>.json` — UN Comtrade public preview API, both
  sides of each KR/JP → US/AU flow (exporter-reported exports and importer-reported imports),
  one file per year 2022–2025. Comtrade flags exporter-side quantities as estimated when the
  reporter supplies weight only; the importer-reported side is usually the firmer count.

## Processing

`extract_trade_flows.py` → `processed/trade_flows.csv`. Both sides of a flow are published;
nothing is netted or mirrored. The HS → powertrain map is `method/hs_passenger_cars.csv`.

## Rules

- Country-level only: never presented as a company or model figure.
- A missing quantity stays empty and is flagged, never filled from weight or value.
