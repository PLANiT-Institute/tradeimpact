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
| extract | `geography/extract_country_codes.py` | raw JSON | `geography/processed/country_codes.csv` |
| extract | `grid/extract_owid_grid.py` | raw CSV, codes | `grid/processed/grid_intensity.csv` |
| extract | `emission_factors/extract_emission_factors.py` | IPCC transcription (verified against the PDF), national factors (hand) | `emission_factors/processed/emission_factors.csv` |
| extract | `projects/extract_gem_tracker.py` | GEM tracker xlsx (**hand**), column map, overrides, companies, roles | `projects/processed/projects_gem.csv` |
| extract | `roles/extract_roles.py` | role register (**hand**), vocabulary, companies | `roles/processed/project_roles.csv` |
| derive | `targets/derive_power_rates.py` | grid, projects, NDC anchors (hand) | `targets/processed/emission_targets_power.csv` + exclusions |
| model | `model/build_reference_power.py` | grid, rates, projects, defaults | `output/reference_power.csv` |
| model | `model/build_ti_power.py` | projects, defaults, factors, reference | `output/ti_power_annual.csv`, `ti_power_by_unit.csv`, `ti_power_excluded.csv` |
| model | `model/aggregate_roles.py` | roles, by-unit results | `output/ti_power_by_role.csv`, `ti_power_company.csv` |

Shared helpers: `model/power_io.py` (paths, CSV, the hand-file exit) and `script/registry.py`
(provenance registries, shared with the automotive sector).
