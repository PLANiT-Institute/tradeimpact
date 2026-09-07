# projects — the generating units, from the Global Energy Monitor tracker

## What this dataset is

The unit of analysis of the power case study: one row per generating unit (or project phase)
that a Korean or Japanese company in `companies/method/companies.csv` owns, built, supplied or
financed, with the country it feeds, its fuel and technology, its capacity, its status and
commissioning year, and its coordinates for the map.

## Raw file — HAND-GATHERED

On disk since 2026-09-05: `raw/gem_global_integrated_power_2026_08_v3.xlsx` (Global Integrated
Power Tracker, August 2026, v3; 183,125 unit rows in sheet `Power facilities`), downloaded by the
project lead through the form and copied in unrenamed except for the lowercase `gem_` prefix.

`raw/gem_*.xlsx` — the **Global Energy Monitor Global Integrated Power Tracker** (or the fuel
trackers it integrates: Global Coal Plant Tracker, Global Gas Plant Tracker, Global Oil and Gas
Plant Tracker, Global Nuclear Power Tracker, the renewable trackers). Landing page and licence
(CC BY 4.0): <https://globalenergymonitor.org/projects/global-integrated-power-tracker/>.

The file **cannot be fetched by a script**: GEM releases it through a download form
(<https://globalenergymonitor.org/projects/global-integrated-power-tracker/download-data/>) that
asks for a name, an organisation and an email address, and sends or shows the link afterwards.
Download it by hand, save it unrenamed except for a lowercase `gem_` prefix (for example
`gem_global_integrated_power_tracker_2026.xlsx`) under `raw/`, and run the extractor. The
extractor records the file, its SHA-256 and the release in
[`../../registry/raw_files.csv`](../../registry/raw_files.csv) at that point. Until the file is
on disk, `run_all.py` stops at this step with `[hand]`.

## Method tables (authored in the repository)

- `method/gem_columns.csv` — our field → the tracker header candidates, in order of preference.
  GEM's headers differ between trackers and releases; the extractor takes the first candidate
  found and fails naming any required field it cannot find.
- `method/country_name_overrides.csv` — tracker country names that do not match the geography
  table's common or official name. The extractor stops and lists any name still unmapped.
- `method/technology_defaults.csv` — **HAND-TRANSCRIBED class defaults, tier C on the unit**:
  expected lifetime, capacity factor and net-calorific-value efficiency by fuel and combustion
  technology, each with a low and high band the sensitivity varies. Used only where the tracker
  publishes no unit-level heat rate or capacity factor; the result cell then carries
  `heat_rate_source = default` / `cf_source = default`. The `verified` column says what stands
  behind the row:

  | verified | meaning |
  |---|---|
  | `document` | the efficiency is checked against a heat rate read out of a document in `raw/technology_documents/` by `verify_technology_defaults.py`; the gap is published in `processed/technology_defaults_check.csv` |
  | `assumption` | no document on file states a heat rate for that technology class; the value keeps the efficiency order against the classes that are covered |
  | `publisher_page` | a zero-stack fuel whose lifetime and capacity factor are read from the publisher's page cited, not machine-checked |

  Two corrections came out of that check (2026-09-07). The IEA-ETSAP E01/E02 technology briefs
  the first version cited are **no longer served** — iea-etsap.org redirects those PDF paths to
  its home page — so the efficiency citation moved to the EIA report, which is live and
  machine-readable, and the bioenergy efficiency became the document-derived 0.268 in place of a
  transcribed 0.30. And the 40-year coal lifetime is a **project assumption**, not the Global
  Energy Monitor convention it was attributed to: GEM's own method page states 35 years for its
  lifetime CO2 estimates. 35 sits inside the 30–50 year sensitivity band; the 0.55 capacity factor
  is the global average that same page states for 2023.
- `method/technology_documents.csv` / `method/technology_document_values.csv` — the documents to
  download and, per technology class, which number in which document the transcription is checked
  against and on which heating value it is stated.
- `raw/technology_documents/` — those documents as served, with `index.csv` carrying each one's
  URL, size and SHA-256 (`fetch_technology_documents.py`).

## Processed output

`processed/projects_gem.csv` — `gem_unit_id`, `gem_location_id`, `country` (alpha-2),
`country_name`, `plant_name`, `unit_name`, `gem_type`, `fuel_type`, `fuel_detail`,
`technology`, `capacity_mw`, `status`, `start_year`, `retired_year`, `operator`, `owner`,
`parent` (both with the tracker's bracketed shares), `latitude`,
`longitude`, `capacity_factor`, `heat_rate_mj_per_kwh` (from Btu/kWh × 1.055056 / 1000),
`gem_emission_factor_kgco2_per_tj`, `wiki_url`, `matched_companies`, `source_id`, `source_file`.

## Rules

- A unit enters when the tracker's Owner or Parent text matches a company's
  `gem_owner_pattern` **and the unit sits outside that company's home country** (a Korean plant
  owned by KEPCO is a domestic holding, not a trade; the count left out is printed), **or** when
  the role register names its unit or location id. The second route is what brings in EPC,
  equipment and finance roles, which the tracker does not record.
- The tracker's `Type` (`coal`, `oil/gas`, `hydropower`, `utility-scale solar`, `wind`,
  `bioenergy`, `nuclear`, `geothermal`) is kept as `gem_type` and normalised to `fuel_type`;
  `oil/gas` is split on the first fuel listed in `Fuel (combustion only)`, which the tracker
  orders by importance. The August 2026 release publishes no unit-level heat rate or capacity
  factor, so every fossil unit is on technology defaults (tier C) until a source for those exists.
- Country names are mapped through the workbook's own sheet `Regions, area, and countries`
  (GEM standard name → ISO alpha-2), so the overrides table is only a fallback.
- `matched_companies` is orientation only; attribution comes from the role register, where the
  role, phase and share are stated with a source.
- Nothing is filtered by status here. The model excludes cancelled and shelved units and carries
  the status of the rest, so a construction-stage unit is a forward-looking liability and a
  retired unit a historical one.
- Tier: capacity, status, start year and coordinates A (tracker as published); tracker capacity
  factor and heat rate B (GEM estimates by technology and age); defaults C.
