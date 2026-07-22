# Fixtures

## `reference_case.json`

The validation reference case (build brief M5). A fully-specified, runnable cohort used to
assert engine arithmetic to ±1% against an independent hand calculation.

**The parameter values are ILLUSTRATIVE, not real-world sourced**, with one exception: the grid
carbon intensities `G_c(0)` are the real Ember-2024 values (Korea 0.41551, EU 0.21135
kgCO₂e/kWh). Everything else — fleet base intensity, NDC-derived rates, VKT, vehicle
efficiencies, UF — is chosen to exercise the equations and produce a clean, reproducible trace,
**not** to represent any actual firm, vehicle, or market.

The fixture's `expected` block was produced by a standalone raw-formula calculation that does
**not** import the engine, so the validation is a genuine two-implementation cross-check rather
than the engine confirming itself. See `validation_report.md` for the full layer-by-layer trace.

Units in fixtures are already engine-internal: grid in kgCO₂e/kWh, ICE intensity in kgCO₂e/km
(the workbook loader does the gCO₂→kgCO₂ conversion; fixtures skip it).

Run it:
```
ti validate --fixture fixtures/reference_case.json
ti report   --fixture fixtures/reference_case.json --out outputs/
```
