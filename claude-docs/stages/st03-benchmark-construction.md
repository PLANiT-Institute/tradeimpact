# ST03 — Benchmark construction (Layer 1)

## Main goal

Produce, per destination and per scenario, the NDC-derived sector benchmark that the sold product is
measured against: the base-year intensity `I_fleet,seg,c(0)` and the annual reduction rates
`r_fleet,c` and `r_power,c` for S1, S2 and S3 — the two rates always derived independently.

## Activity

Select the Layer 1 method (A stock model / B NDC trajectory / C two-bin) against the criteria in
`G-02`; compute the base-year intensity from the sector inventory, stock and distance; derive the
scenario rates from the policy documents; record whether pro-rata allocation was used and at which
target-hierarchy level the pathway sits; flag implausible values rather than smoothing them.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH1 | 2 | `r_fleet` and `r_power` S1/S2/S3 for all 27 destinations, each with source and pro-rata disclosure |
| PH3 | 4, 6 | Country passenger-car pathways replacing the regional proxy; tier improvement |
| PH4 | 1, 4 | The power-sector grid trajectory and the shipping IMO CII trajectory as Layer 1 |
| PH5 | 1, 6 | The sector-split correction and the S-curve-versus-exponential error bound |

## Inputs

Consumes: `SRC-02` (distance), `SRC-03` (sector inventory), `SRC-05` (grid intensity), `SRC-06`
(EU pathway), `SRC-07`/`SRC-11` (NDCs), `SRC-12` (IEA STEPS/NZE), `SRC-13` (stock),
`SRC-20`…`SRC-24` (national sector pathways), `SRC-19` (IMO, PH4); assumptions `A-01`, `A-02`,
`A-03`, `A-07`, `A-08`, `A-09`, `A-10`, `A-14`; upstream ST02 records.

Units: intensity gCO₂/km (automotive) or gCO₂e/kWh (power); rates as a fraction per year.

## Outputs

Produces: the Layer 1 fields of `destination_inputs.json` (`fleet_intensity_base_gco2_per_km`,
`r_fleet_s1/s2/s3`, `r_power_s1/s2/s3`, `prorata_used`, `target_level`, `warnings`) and the
benchmark rows of `pathways.json`.

Consumed by: ST05, ST07.

## Methodology

[`../toolbox/methods/layer1-benchmark.md`](../toolbox/methods/layer1-benchmark.md) and
[`../toolbox/methods/scenario-architecture.md`](../toolbox/methods/scenario-architecture.md).
Governing text: Guideline §2.3, §6.1–6.2 (`G-02`, `G-03`), Whitepaper §3.1 (`W-02`).

## Owner agents

Owner `climate-risk-modeller` (policy pathway derivation) with `data-scientist` (arithmetic).
Review chain: `math-reviewer` (rate derivation, independence of the two rates) → `tester` →
`auditor` (disclosure adequacy).

## When to stop

- Every destination has `r_fleet` and `r_power` for all three scenarios, from separately named
  sources.
- Pro-rata use is recorded per destination, with the S1 conservative cross-check present (`G-03`).
- The target-hierarchy level is recorded per destination and no proxy is labelled a country target.
- Implausible base-year values are flagged and tier-downgraded, not adjusted.
- Where both Method B and Method C are available, divergence is below the 30% trip-wire or the
  divergence is investigated and recorded (`G-02`).

## When to repeat

- A new NDC or sector pathway is published for any destination in scope.
- A sector-split correction or FLAG-market rule is adopted in PH5 (`M-01`) — this moves every
  benchmark and therefore every published figure.
- The base-year inventory, stock or distance input changes (the base intensity is a quotient of all
  three).
- A fast-transition market fails the S-curve cross-validation (`M-08`).

## Backward moves

- No usable base→target arithmetic in the NDC (undefined baseline, BAU reference, revoked NDC) →
  the FLAG-market rule applies and the market leaves the S2 headline (`A-03`); the rule itself is
  a PH5 open item (`B-02`).
- Base-year intensity implausible (the Luxembourg cross-border refuelling case) → ST02 for a tier
  downgrade and a warning, never a quiet correction.
- Only an economy-wide rate available with no independent power rate → assumption `A-01` applies
  with its warning, and the phase records that `G-06` is satisfied only nominally.

## Process

[`../process/st03-benchmark-construction.md`](../process/st03-benchmark-construction.md)
