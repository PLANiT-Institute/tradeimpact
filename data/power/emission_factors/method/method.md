# emission_factors — CO2 per unit of fuel burned

## What this dataset is

The Layer 2 factor that turns a generating unit's fuel use into CO2: kg CO2 per TJ of fuel, by
fuel. Rule set by the project lead on 2026-09-05: **a unit's factor is the destination
country's own fuel-specific factor where one is on file, and the IPCC 2006 default otherwise.**
Both live in one table with a `basis` column; the model applies the order.

## Raw files and sources

- `raw/ipcc_2006_v2_ch2_stationary_combustion.pdf` — 2006 IPCC Guidelines, Volume 2, Chapter 2,
  fetched by `script/power/emission_factors/fetch_ipcc_defaults.py` (link, access date and hash
  in [`../../registry/raw_files.csv`](../../registry/raw_files.csv)). Table 2.2 gives the defaults
  and their 95 % bounds for energy industries.
- `method/ipcc_2006_table_2_2.csv` — **hand transcription** of Table 2.2 (fuel, default, lower,
  upper, biogenic flag) plus `gem_fuel_pattern`, a regex that maps the tracker's fuel text to a
  fuel row. The extractor verifies every number against the PDF's own text and stops if one is
  not found, so a typo cannot reach the model.
- `method/national_documents.csv` and `raw/national_documents/` — the inventory reports and legal
  instruments the destinations' own factors are read from, fetched by
  `fetch_national_documents.py`, with each document's URL, byte count, SHA-256 **and licence** in
  `raw/national_documents/index.csv`.
- `raw/national_emission_factors.csv` — **HAND-READ from those documents**, one row per country ×
  fuel: the factor, its `basis`, the `source_key` of the document, the `table_reference`, the
  number **as the document prints it** (`document_value`), the `conversion` that turns it into
  kg CO2/TJ, and the `quote` — the document's own table line. The extractor rejects a row whose
  document is not on disk, whose URL does not match the index, whose country is not the
  document's, whose quote is not in the document's text, whose printed number is not in the quote,
  or whose conversion does not reproduce the factor. Where the register has no row for a country ×
  fuel, the IPCC default applies and the result cell says so.

## Processed output

`processed/emission_factors.csv` — `country` (`''` for the default that applies to any
country), `fuel_id`, `ef_kgco2_per_tj`, `ef_low_kgco2_per_tj`, `ef_high_kgco2_per_tj`, `basis`
(`national` | `national_adopted` | `ipcc_default`), `biogenic`, `source_id`, `source_url`, `tier`.

## Tiers

- `national` — A: the country measured it and publishes it as country-specific.
- `national_adopted` — B: the country's own instrument publishes the IPCC value as its factor.
  The number is the default; the provenance is national, and it is a statement the country stands
  behind rather than a gap we filled.
- `ipcc_default` — C: a global default standing in for a country that states none. The bounds are
  carried so the sensitivity can vary the factor over the IPCC range.

## What each destination publishes (2026-09-07)

Desk research over the destinations that carry the most capacity in the result set. The access
route matters: the **UNFCCC Data Interface is behind a bot wall and would not have helped anyway**,
because it carries implied emission factors for Annex I Parties only — for non-Annex I Parties it
holds emissions and activity data but no factors. Everything below came from the national
ministry or the legal instrument itself.

| Destination | What it publishes | Basis here |
|---|---|---|
| China | 2025 provincial inventory guidelines, Table 2.2: one carbon content for **all coal burnt in electricity and heat**, 26.7 tC/TJ on a net calorific value basis (97,900 kg CO2/TJ at 44/12), and 15.3 tC/TJ for natural gas | country-specific (coal), adopted (gas) |
| Indonesia | Energy ministry's 2020 energy-sector inventory, Table 1: one **local** coal factor 99,718 and gas 57,600, plus fuel oil and diesel, each naming the study behind it | country-specific |
| Malaysia | TNB Research's 2021 study for the electricity sector, Table F.3: measured on **all nine coal power stations** over 2017-2019, coal 93,131 / 96,551 / 103,509 and gas 50,151, with lower and upper values | country-specific |
| South Africa | 10th National Inventory Report, gazetted 2026, Table 3.12: country-specific Tier 2 factors beside the defaults | country-specific |
| Taiwan | Ministry announcement of 5 February 2024, Appendix 1: the factors, with a note that they are taken from the 2006 IPCC Guidelines Table 2.2 | adopted |
| Viet Nam | Decision 2626/QD-BTNMT of 10 October 2022, Appendix I: Tier 1 factors for energy industries. **Anthracite and sub-bituminous only** — no "other bituminous" entry, so Viet Nam's bituminous units keep the IPCC default. Article 2 says the list is updated when a country-specific factor exists, so the ministry itself states none does yet | adopted |
| Morocco | National Inventory Report of December 2024, Table 30: one factor for **all solid fuels** in energy industries, 96.10 t/TJ, flat 2010-2022 | adopted |

Two values were deliberately **not** taken:

- **South Africa's "other bituminous" 76,710** is 18.9 % below the IPCC default. The report's own
  narrative enumerates which country-specific factors deviate from the default and by how much,
  and never mentions bituminous coal; the solid-fuel country-specific values carry no source
  footnote, while the liquid and gas ones do. A 19 % deviation with no explanation is a
  transcription or units question, not a finding, so the row is left out and the note records why.
  (No unit in the result set burns South African bituminous, so nothing turns on it.)
- **Chile's coal factors are published per coal origin** (Australia 92,456, Canada 95,556,
  Colombia 93,960, United States 93,328, New Zealand 93,821, Chilean Mina Invierno 99,140,
  Indonesia 100,575), measured under the green-tax sampling regime and covering over 88 % of the
  coal burnt for power. We do not know which coal each unit burns, and averaging origins would
  invent a number the country never published, so Chile's two units keep the IPCC default.

**No factor publicly stated, verdict recorded rather than left unexplained:** Bangladesh,
the Philippines, Saudi Arabia, Qatar, the United Arab Emirates and India for gas. Their inventory
submissions live only behind the UNFCCC wall, their ministries publish inventory totals rather
than factor annexes, and the IPCC Emission Factor Database holds no non-default entry for their
combustion fuels. Those units carry the IPCC default at tier C, and that is the ceiling until a
document turns up.

The IPCC Emission Factor Database is a useful finding aid but is **not** used as a source: its
copyright forbids compiling derivative works from it, and its records are third-party submissions
each under its own upstream terms. Where it pointed at a primary document, that document was
fetched and read instead.

## Rules

- Biogenic CO2 (wood, biomass) is computed and reported in its own column, never inside the fossil
  total, following inventory practice.
- Fuel matching runs on the tracker's fuel text in the order of the table; the first pattern
  that matches wins, so specific fuels (lignite, sub-bituminous) sit above the generic coal row.
