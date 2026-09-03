# script/auto — all Python for the automotive case study

One directory per dataset, mirroring `data/auto/`. A script reads only from its dataset's
`raw/` (plus other datasets' `processed/` when joining), and writes only to its dataset's
`processed/` — except `model/`, which reads `processed/` across datasets and writes to
`data/auto/output/`.

```text
sales/                raw sales/registration files -> processed/sales.csv
country_emissions/    inventories + grid series    -> processed/country_emissions.csv
emission_targets/     NDC + sector standards       -> processed/emission_targets.csv
vehicle_usage/        VKT, lifetime, stock         -> processed/vehicle_usage.csv
vehicle_technology/   intensities, RW correction   -> processed/vehicle_technology.csv
model/
  build_reference.py    step 3: dynamic sector benchmark per importer x scenario
  build_ti.py           step 4: lifetime avoidance/addition per model x market x scenario
  aggregate_country.py  step 5: country and company totals + decomposition check
```

Conventions

- Python 3.11+, type hints on public functions, Google-style docstrings; math functions
  carry an `Algorithm:` section citing the whitepaper equation they implement.
- No hardcoded values: parameters come from `processed/` CSVs, each row with `source_id`.
- Deterministic: same raw inputs -> byte-identical processed outputs. No timestamps.
- Each script is runnable as `python script/auto/<dataset>/<name>.py` from the repo root.
- Missing input -> the row is dropped and counted in the script's summary output, never
  filled with zero.
