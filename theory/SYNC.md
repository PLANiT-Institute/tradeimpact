# Theory ↔ code sync contract

Two-way map between the methodology documents and the engine. Checked by
`scripts/check_sync.py` (CI): every row needs all three columns to exist — the anchor in
the theory doc, the `[anchor]` token in the cited code file's docstrings, and the test.
A theory rule with no code + test, or a code token with no table row, fails the build.
Conflicts are never resolved here — they go to `ti-framework/NOTES.md` with a dated
decision (D1–D4), which this file points to.

Docs: `Whitepaper & Guidelines/TI_Whitepaper_v1.5.md` (WP),
`Whitepaper & Guidelines/TI_Automotive_Technical_Guideline_v1.8.md` (GL),
`ti-framework/NOTES.md` (N). Code and tests live under `ti-framework/`.

| Theory anchor | Code | Test |
|---|---|---|
| [eq-3.1-benchmark] WP §3.1 benchmark decline | `ti_framework/layer1/automotive.py` | `tests/test_layer1.py::test_method_b_exponential_decline` |
| [eq-g2.3b-ndc-trajectory] GL §2.3 Method B | `ti_framework/layer1/automotive.py` | `tests/test_layer1.py::test_method_b_series_length` |
| [eq-g2.3a-weibull] GL §2.3 Method A Weibull stock | `ti_framework/layer1/automotive.py` | `tests/test_layer1.py::test_method_a_fleet_stock_average` |
| [eq-g2.3c-two-bin] GL §2.3 Method C two-bin | `ti_framework/layer1/automotive.py` | `tests/test_layer1.py::test_method_c_two_bin_recursion` |
| [rule-g6.1-bc-divergence] GL §6.1 B/C >30% trip-wire (validation utility — production runs Method B only until Method C inputs are collected) | `ti_framework/layer1/automotive.py` | `tests/test_layer1.py::test_bc_divergence_flag` |
| [eq-3.2-product] WP §3.2 sold-product emissions | `ti_framework/layer2/automotive.py` | `tests/test_layer2.py::test_grid_trajectory_declines` |
| [eq-g3.3-ice] GL §3.3 ICE fixed at sale | `ti_framework/layer2/automotive.py` | `tests/test_layer2.py::test_ice_is_constant` |
| [eq-g3.4-bev] GL §3.4 BEV grid-declining | `ti_framework/layer2/automotive.py` | `tests/test_layer2.py::test_bev_tracks_grid` |
| [eq-g3.5-phev] GL §3.5 PHEV UF composite | `ti_framework/layer2/automotive.py` | `tests/test_layer2.py::test_phev_composite_midpoint` |
| [eq-3.3-annual-gap] WP §3.3 annual TI gap | `ti_framework/core/gap.py` | `tests/test_gap_crossover.py::test_gap_series_basic` |
| [rule-3.4-summation] WP §3.4 t = 0..T−1, T terms | `ti_framework/core/cumulative.py` | `tests/test_gap_crossover.py::test_gap_T_equals_1` |
| [eq-3.5-cumulative] WP §3.5 per-product cumulative | `ti_framework/core/cumulative.py` | `tests/test_gap_crossover.py::test_cumulative_sum` |
| [eq-3.6-cohort] WP §3.6 cohort TI + decomposition identity | `ti_framework/core/aggregate.py` | `tests/test_aggregate.py::test_decomposition_identity_holds` |
| [eq-3.7-annual-flow] WP §3.7 annual TI flow | `ti_framework/core/aggregate.py` | `tests/test_validation.py::test_cohort_totals_within_1pct` |
| [eq-3.8-portfolio] WP §3.8 rolling portfolio | `ti_framework/core/portfolio.py` | `tests/test_scenarios_sensitivity.py::test_rolling_portfolio_steady_state_equivalence` |
| [rule-g4.7-three-scenarios] GL §4.7 S1/S2/S3, never S2 alone | `ti_framework/core/scenarios.py` | `tests/test_scenarios_sensitivity.py::test_run_produces_three_scenarios` |
| [rule-g5.2-sensitivity] GL §5.2 mandatory sensitivities | `ti_framework/core/sensitivity.py` | `tests/test_scenarios_sensitivity.py::test_uf_sweep_lower_bound_reduces_phev_contribution` |
| [rule-g5.3-declaration] GL §5.3 data-quality declaration | `ti_framework/report/outputs.py` | `tests/test_scenarios_sensitivity.py::test_run_data_quality_declaration_present` |
| [rule-5.1-tiers] WP §5.1 three-tier hierarchy | `ti_framework/report/outputs.py` | `tests/test_aggregate.py::test_tier_c_directional_suppression` |
| [rule-5.3-no-netting] WP §5.3 never net against Scope 3 | `ti_framework/report/outputs.py` | `tests/test_scenarios_sensitivity.py::test_run_data_quality_declaration_present` |
| [rule-n4-crossover] N §4 crossover closed forms | `ti_framework/core/crossover.py` | `tests/test_gap_crossover.py::test_crossover_ice_closed_form` |

## Conflict log pointers

- D1 pro-rata identity (`r_fleet` = `r_power` fallback + warning) — NOTES.md §1 D1
- D2 S2 from unconditional rate; conditional → S2 upper sensitivity — NOTES.md §1 D2
- D3 FLAG-market rule (exclude from S2 headline) — NOTES.md §1 D3
- D4 validation vs illustrative fixtures — NOTES.md §1 D4

## Process

- Changing an anchored theory section → `check_sync.py` still passes only if the anchor
  survives; renaming/removing an anchor breaks the build until the table and code move too.
- Adding an equation to the theory → add the anchor, the implementing code token, the
  test, and a table row.
- Code that implements theory without a `[anchor]` token in its module/class/function
  docstring is a defect once its anchor exists in the table.
