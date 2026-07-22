# Data Collection Status

Mirrors `ti run --workbook ti-framework/data/TI_Data_Workbook_v0.1.xlsx` (engine-reported
`missing_inputs` + warnings). Regenerate any time with:

```bash
cd ti-framework && ti run --workbook data/TI_Data_Workbook_v0.1.xlsx
```

Snapshot date: 2026-07-22 · Workbook: `TI_Data_Workbook_v0.1.xlsx` · Loaded: 9 countries, 8 vehicle rows, 8 volume rows.

## Missing / not-yet-collected inputs (collection backlog)

| Item | Sheet / market | What to collect | Source (Guideline Appendix B) |
|---|---|---|---|
| Volume data V_c,v | `Registration_Vcv` — no units collected | Model-level registrations by country, year, powertrain | VFACTS, KBA, SMMT, KAICA, SIAM, GAIKINDO, etc. |
| Vehicle parameters | `Layer2_vehicle_params` — none collected | η_EV, ICE gCO₂/km, PHEV UF, real-world correction, per model | Type-approval DBs + ICCT Mind the Gap |
| Vehicle lifetime T | `Support_params` | Central T + sensitivity per market fleet age | National transport statistics |
| S2 benchmark | US — `FLAG_NO_BENCHMARK` | No active NDC; excluded from S2 headline (NOTES.md D3) | S1/S3 via IEA STEPS/NZE if collected |
| S2 benchmark | IN — `FLAG_INTENSITY` | GDP-intensity target, not absolute path | idem |
| S2 benchmark | ID — `FLAG_BAU` | Target vs BAU projection, no base-year level | idem |
| S2 benchmark | SA — `FLAG_NO_BASELINE` | Absolute avoided target, unstated baseline | idem |
| S2 benchmark | CN — `FLAG_PEAK` | Target vs undefined peak | idem |
| S1/S3 rates | all markets | r_fleet/r_power from IEA STEPS & NZE ("TO EXTRACT") | IEA WEO |
| Fleet base intensity | all markets | I_fleet,seg,c(0) = IEA transport CO₂ ÷ (OICA fleet × VKT) | IEA / OICA / national VKT |

## Warnings (data-quality, not blockers)

`PRORATA_IDENTITY` on AU, EU, JP, KR — r_fleet = r_power = economy-wide rate
(sector-split factor 1.0, NOTES.md D1). Benchmark tier downgraded. To clear: derive
transport and power rates independently, or supply a documented sector-split factor.

## Firm universe reconciliation

Canonical firm list for the TI pipeline lives in `data-pipeline/firms.json` (built by
`build_dataset.py` from the two source workbooks):

- `TI_CaseStudy_Target_Companies.xlsx` — TI case-study candidates. **Automotive (Toyota,
  Hyundai)** are the only firms in the implemented sector; shipping (KHI, Mitsui, HHI, SHI)
  and power (JERA, TEPCO, KEPCO, KOSPO) firms map to engine stub sectors and are carried
  as `runnable: false`.
- `CAP_Target_Companies_Draft.xlsx` — CAP project (steel, petrochemical). Different
  project, no TI sector implementation; carried in the universe as `project: "CAP"`,
  `runnable: false`, for one canonical list rather than two.

No firm currently has collected registration + vehicle-parameter data, so no real-firm TI
is computable yet. `ReferenceCo` (committed fixture, illustrative parameters — see
`ti-framework/fixtures/README.md` and NOTES.md D4) is the only end-to-end runnable case
and drives the demo report until collection lands.

## Three-tier collection rule (Whitepaper §5.1)

Record `Source` and `Tier` (A measured / B modelled / C proxy) for every row. Empty cell ≠
zero: the loader records gaps in `missing_inputs` and downgrades confidence; it never
defaults.
