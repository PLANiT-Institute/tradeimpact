# script/power — the power-sector pipeline

Trade impact of Korean and Japanese companies' overseas power projects. Method and rules:
[`data/power/output/method.md`](../../data/power/output/method.md); the mathematics:
[`methodology/TI_Power_Technical_Guideline_v1.0.md`](../../methodology/TI_Power_Technical_Guideline_v1.0.md).

Every script runs from the repository root with `.venv/bin/python`. `run_all.py` runs them in
order and stops at the first failure; it exits 3 and prints `[hand]` when a step needs a file
that only a person can obtain.

| step | script | reads | writes |
|---|---|---|---|
| fetch | `geography/fetch_country_codes.py` | jsDelivr world-countries | `geography/raw/world_countries.json` |
| fetch | `grid/fetch_owid_grid.py` | OWID grapher CSV | `grid/raw/owid_carbon_intensity_electricity.csv` |
| fetch | `emission_factors/fetch_ipcc_defaults.py` | IPCC 2006 GL Vol 2 Ch 2 PDF | `emission_factors/raw/…pdf` |
| fetch | `geography/fetch_map_geometry.py` | jsDelivr world-atlas | `geography/raw/countries-110m.json` |
| extract | `geography/extract_country_codes.py` | raw JSON | `geography/processed/country_codes.csv` |
| extract | `grid/extract_owid_grid.py` | raw CSV, codes | `grid/processed/grid_intensity.csv` |
| extract | `emission_factors/extract_emission_factors.py` | IPCC transcription (verified against the PDF), national factors (hand) | `emission_factors/processed/emission_factors.csv` |
| extract | `projects/extract_gem_tracker.py` | GEM tracker xlsx (**hand**), column map, overrides, companies, roles | `projects/processed/projects_gem.csv` |
| extract | `roles/extract_gem_ownership.py` | projects (owner and parent strings), companies | `roles/processed/gem_ownership.csv` (equity rows with shares) |
| extract | `roles/extract_roles.py` | role register (**hand**, pending), vocabulary, companies | `roles/processed/project_roles.csv` |
| fetch | `targets/fetch_climatewatch_ndc.py` | Climate Watch API | `targets/raw/climatewatch_ndc_content.json` |
| extract | `targets/extract_ndc_anchors.py` | Climate Watch content, hand overrides, projects | `targets/processed/ndc_anchors_power.csv` |
| derive | `targets/derive_power_rates.py` | grid, projects, anchors | `targets/processed/emission_targets_power.csv` + exclusions |
| model | `model/build_reference_power.py` | grid, rates, projects, defaults | `output/reference_power.csv` |
| model | `model/build_ti_power.py` | projects, defaults, factors, reference | `output/ti_power_annual.csv`, `ti_power_by_unit.csv`, `ti_power_excluded.csv` |
| model | `model/aggregate_roles.py` | register, GEM ownership, by-unit results, scope | `output/ti_power_by_role.csv`, `ti_power_company.csv` |
| model | `model/build_sensitivity_power.py` | by-unit results, reference, defaults, factors | `output/ti_power_sensitivity.csv` |
| model | `model/build_database.py` | every CSV, value tiers, geometry | `database/tradeimpact_power.sqlite` |
| report | `report/build_report.py` + `template.html` | (constants only; the page reads the database) | `report/ti_power_report.html` |

Shared helpers: `model/power_io.py` (paths, CSV, the hand-file exit), `script/registry.py`
(provenance registries) and the loaders of `script/auto/model/build_database.py`, shared with the
automotive sector. `data/power/registry/scope.csv` sets which destinations are extracted and
whether a company's home country counts. Serve the results with
`.venv/bin/python script/auto/serve_dashboard.py --root power --port 8766`.
