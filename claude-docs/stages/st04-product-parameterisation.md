# ST04 — Product parameterisation (Layer 2)

## Main goal

Produce the sold-product emission parameters per product and destination — the quantities that make
`E_prod,v,c(t)` computable — each corrected to real-world conditions exactly once and each carrying
its certification standard, tier and source.

## Activity

Extract certified intensities per product from the type-approval or registration data; apply the
correction factor for that certification standard once and record that it was applied; source the
PHEV utility factor and its sensitivity band; source the FCEV hydrogen supply intensity; source the
destination annual distance and operating lifetime with their bands. Where a parameter is missing,
mark the product type withheld with its unit count.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH1 | 2 | Certified tailpipe and electricity-consumption parameters per row; the OBFCM real-world correction; distance and lifetime per destination |
| PH3 | 2, 3, 6 | Market-calibrated UF; H₂ intensity; a BEV real-world correction if one is published; tier improvement on distance and lifetime |
| PH4 | 2 | Per-technology service parameters for the new sector |
| PH5 | 4 | The evidence for market-calibrated UF defaults replacing the generic band |

## Inputs

Consumes: `SRC-01` (certified fields), `SRC-08`/`SRC-09` (real-world correction), `SRC-10` (PHEV
real-world UF), `SRC-15` (national certification databases), `SRC-02` (distance), `SRC-04`
(mean age → lifetime); assumptions `A-05`, `A-06`, `A-11`, `A-12`, `A-13`.

Units: gCO₂/km, kWh/km, km/yr, years, kgCO₂e/kg H₂, UF as a fraction.

## Outputs

Produces: the Layer 2 fields of the engine input records (`certified_tailpipe_gco2_per_km`,
`certified_electricity_kwh_per_km`, correction factor and flag, UF and band, `vkt_*`,
`operating_lifetime_*`), and the withheld-product-type list with unit counts.

Consumed by: ST05, ST07.

## Methodology

[`../toolbox/methods/layer2-product-emissions.md`](../toolbox/methods/layer2-product-emissions.md).
Governing text: Guideline §3.3–3.5, §7.1–7.3, Appendix C (`G-05`, `G-06`, `G-07`, `G-12`).

## Owner agents

Owner `data-scientist`, with `data-collector` for the certification and real-world sources.
Review chain: `math-reviewer` (correction arithmetic, no double correction) → `tester`.

## When to stop

- Every product row in the cohort has either a complete parameter set or a withheld marker with a
  unit count.
- Each correction is applied once, with `correction_applied` and its source recorded (`G-12`).
- PHEV rows carry central and UF − 0.15 values (`G-07`, `G-09`); FCEV rows carry a sourced H₂
  intensity or are withheld.
- Distance and lifetime carry their sensitivity bands, not point values (`G-09`).

## When to repeat

- A new certification vintage or a new real-world correction edition is published.
- A market-calibrated UF is adopted (`M-04`) — this can change the PHEV sign, so the whole PHEV
  result reverts to unverified.
- An official BEV real-world consumption gap is published, retiring assumption `A-11`.
- The powertrain classification rule changes (`A-13`) — it re-keys every row.

## Backward moves

- Certified data already real-world adjusted but the correction applied anyway → back to this stage
  with the double-correction guard tested, and every affected figure reverts to unverified.
- No sourced UF for a market with material PHEV volume → the product type is withheld with its unit
  count; it is never computed on a regulatory UF presented as real-world.
- Correction factors derived for one market applied to another (Appendix F.4) → record as an
  assumption with its cost, or use local certification data instead.

## Process

[`../process/st04-product-parameterisation.md`](../process/st04-product-parameterisation.md)
