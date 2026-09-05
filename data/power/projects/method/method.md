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
- `method/technology_defaults.csv` — **HAND-TRANSCRIBED defaults, tier C**: expected lifetime,
  capacity factor and LHV efficiency by fuel and combustion technology, each with the document
  it is read from and `verified = no` until checked against it. Used only where the tracker
  publishes no unit-level heat rate or capacity factor; the result cell then carries
  `heat_rate_source = default` / `cf_source = default`.

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
