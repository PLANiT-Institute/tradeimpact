# script/auto — all Python for the automotive case study

One directory per dataset, mirroring `data/auto/`. A script reads only from its dataset's
`raw/` (plus other datasets' `processed/` when joining), and writes only to its dataset's
`processed/` — except `model/`, which reads `processed/` across datasets and writes to
`data/auto/output/`.

```text
sales/                extract_eea_registrations.py, extract_kia_ir.py, extract_hyundai_ir.py
country_emissions/    extract_eu27_snapshot.py
emission_targets/     derive_eu27_rates.py          S1/S2/S3 r_fleet, r_power per market
vehicle_usage/        extract_eu27_eurostat.py
vehicle_technology/   extract_eea_certified.py
model/
  build_reference.py    step 3: destination parameters + dynamic benchmark E_ref(t), G(t)
  build_ti.py           step 4: lifetime TI per company x market x model x powertrain x scenario
  build_sensitivity.py  step 4b: crossover year per cell; lifetime, real-world, distance sensitivities
  aggregate_country.py  step 5: country, powertrain and company totals + decomposition check
  build_data_quality.py step 5b: guideline §5.3 data-quality declaration per company
  build_database.py     final: every CSV under data/auto -> data/auto/tradeimpact_auto.sqlite
```

`run_all.py` runs every step above in order, then `ruff check` and `pytest`, and stops at the
first failure — use it before every commit. Individual scripts run in the order listed.
`sales/fetch_eea_registrations.py <BRAND>` is the only network step and is run by hand when a
new brand is added; snapshots are pinned once obtained.

Conventions

- Python 3.11+, type hints on public functions, Google-style docstrings; math functions
  carry an `Algorithm:` section citing the whitepaper equation they implement.
- No hardcoded values: parameters come from `processed/` CSVs, each row with `source_id`.
- Deterministic: same raw inputs -> byte-identical processed outputs. No timestamps.
- Each script is runnable as `python script/auto/<dataset>/<name>.py` from the repo root.
- Missing input -> the row is dropped and counted in the script's summary output, never
  filled with zero.
