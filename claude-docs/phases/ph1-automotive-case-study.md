# PH1 — Automotive case study

## Purpose

Produce the first empirical TI result set: for the named Korean and Japanese exporters, what
their sold vehicles do to each importing country's committed decarbonisation path over the
vehicles' operating lifetime. This phase is the framework's primary validation vehicle
(`C-11`) and the current focus of the project lead as of 2026-09-03. It carries the automotive
case study (`D-02`) and the open dataset (`D-10`), and it supplies the evidence PH2 needs to
close methodological challenges 1, 3 and 4.

**Sequencing — build one thing when it is needed.** The phase runs the five steps in order and
builds each artefact at the moment the step before it produces something to consume: no model
script, no dashboard and no database exists at 2026-09-04, and none is created ahead of its input.
The first analytical pass is correspondingly narrow — **EU27, Toyota and Hyundai, cohort 2024**, on
data already held (2026-09-04 direction). Kia, Honda, the United States and Australia stay in the
target set as later acquisition and are counted as gaps rather than assumed away. Current state per
stage is in [`../tracker.md`](../tracker.md), never here.

## Objectives

1. **Targets fixed.** Exporters, importer markets, cohort year(s), segment and vehicle
   lifetime are documented, with the market-selection criteria of guideline §6.3 evaluated
   rather than assumed.
2. **Inputs acquired and registered.** All five datasets — sales, country emissions, emission
   targets, vehicle usage, vehicle technology — exist as `processed/` tables in which every row
   carries its provenance, with gaps counted rather than filled. Coverage is judged against the
   markets in the current pass, not against the full target set.
3. **Reference benchmark built.** A dynamic sector benchmark `E_ref,c(t)` per importer per
   scenario, with `r_fleet` and `r_power` derived independently and every pro-rata,
   extrapolation and flag disclosed.
4. **Impact built.** Lifetime emission avoidance or addition per model × market × powertrain ×
   scenario, plus the annual TI flow series and the Crossover Point per cell.
5. **Aggregated to country and company.** Importer-country and exporter-company totals with
   the decomposition identity intact, tiers declared, and withheld units counted.
6. **Verified.** Every headline independently re-derived by a second route, and — for the EU27
   Toyota and Hyundai 2024 cohort — reconciled against the archived published run as a
   regression baseline.
7. **Published.** The case study written as an open-access working paper with its open dataset
   and data-quality declaration.

## Deliverables

| Charter id | Artefact | Format | Acceptance test | Milestone |
|---|---|---|---|---|
| `D-02` | Automotive case study | Working paper, open access | Results documented and publicly available; declaration per guideline §5.3 complete | Month 7 |
| `D-10` | Open dataset | CSV under `data/auto/`, schema in [`../toolbox/data-schema.md`](../toolbox/data-schema.md) | Every row traces to a catalogue row or an assumption; published without restriction (`C-02`) | Month 7 |
| `D-06` (part) | `script/auto/` pipeline | Python | Re-runs end to end from raw to output, byte-identical (`N-08`) | Month 10 |

## Entry criteria

- Charter accepted by the project lead.
- Repository restructure to `data/auto/<dataset>/{raw,processed,method}` and `script/auto/`
  complete (done 2026-09-03).
- Methodology whitepaper v1.5 and automotive guideline v1.8 present in `methodology/`.
- Each dataset's `method/method.md` written (done 2026-09-03).

## Exit criteria

- [ ] `data/auto/output/target_set.csv` written per
      [`../stages/st01-targets-and-provenance.md`](../stages/st01-targets-and-provenance.md), with
      `B-03` resolved.
- [ ] All five datasets have a `processed/` table for the markets in the current pass; every source
      behind them has a row in [`../toolbox/catalogue.md`](../toolbox/catalogue.md).
- [ ] Benchmark table covers every importer in the current pass for S1, S2 and S3, or names the
      market as flagged with the reason (`B-04` for the United States).
- [ ] TI result set covers every model × market cell with complete inputs; incomplete cells
      appear in a withheld table with unit counts (`N-02`).
- [ ] Crossover Point reported per cell, with the `C-05` range treatment resolved (`B-07`).
- [ ] Decomposition identity checked numerically (`N-06`).
- [ ] Regression against `archive/data/published/lifetime_results.json` either matches within
      the declared tolerance or the divergence is explained in [`../log/README.md`](../log/README.md).
- [ ] Every headline marked `[verified]`, not `[compute]`.
- [ ] Case study working paper and open dataset published (`C-02`).

## Stages serving this phase

| Stage | Evidences objective |
|---|---|
| [`st01`](../stages/st01-targets-and-provenance.md) | 1 |
| [`st02`](../stages/st02-06-datasets.md) … [`st06`](../stages/st02-06-datasets.md) | 2 |
| [`st07`](../stages/st01-targets-and-provenance.md) | 2 |
| [`st08`](../stages/st08-10-analysis.md) | 3 |
| [`st09`](../stages/st08-10-analysis.md) | 4 |
| [`st10`](../stages/st08-10-analysis.md) | 5 |
| [`st11`](../stages/st11-verification.md) | 6 |
| [`st14`](../stages/st12-15-outputs.md) | 7 |
| [`st12`](../stages/st12-15-outputs.md) | 3, 4 (rules the computation obeys) |

## Traceability

`D-02`, `D-10`, `D-06` (part), `C-04`, `C-05`, `C-08`, `C-11`, `N-01`…`N-09`. Exclusions in
force: `X-02`, `X-03`, `X-04`, `X-05`, `X-07`.

## What would invalidate this phase

- **No usable benchmark arithmetic in a target importer.** If a market has neither an NDC
  anchor nor an accepted proxy rule, its TI result has no reference point and the market
  leaves the headline (`B-04`).
- **Sales unobtainable at model × powertrain level under `C-08`.** United States and Australia
  volumes may sit only behind paywalls (`X-02`); a company-market cell without volumes has no
  TI, and the target set returns to ST01.
- **Tier C share too high.** If most units rest on proxied distance or technology, the honest
  output is a direction with a stated coverage ratio, not a magnitude — which changes what
  `D-02` can claim (challenges Challenge 3).
