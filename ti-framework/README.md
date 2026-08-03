# TI Framework — alignment contract and calculation research engine

The public product API is `ti_framework.alignment`: a sector-neutral, evidence-first contract that
compares observed company metrics with official targets only when sector, metric, geography, and
unit match. It currently registers automotive, power, shipping, steel, and petrochemicals; see
[`../docs/PRODUCT_CONTRACT.md`](../docs/PRODUCT_CONTRACT.md).

The remainder of this document describes the original automotive lifetime calculation engine. It
is retained for methodology research and arithmetic validation, but no estimated company result or
reconstructed historical cohort is published from it.

Open-source calculation engine for the **Trade Impact (TI) Framework**, a firm-level metric
that scores whether a company's products help or hinder each operating country's NDC-committed
decarbonisation path, over each product's operational lifetime.

For every product a firm sells, in every country it operates in, in every year of that
product's life, TI asks: *does this product emit more or less than what the operating country's
sector is committed to emitting that year under its NDC?* Less → a contribution; more → a carbon
lock-in liability. Summed across countries and powertrains, weighted by sales volume, it is a
firm-level signal of the climate direction embedded in the firm's trade.

> TI is a **separate additional disclosure** that sits alongside Scope 3 Category 11. It is
> **never** netted against Scope 3.

This engine implements the **automotive** sector fully (Layer 1 → Layer 2 → Layer 3, three
scenarios, mandatory decomposition and sensitivities, Level 1 operating-country basis). Shipping
and power are interface stubs; Level 2 production attribution is a stub. The source of truth is
the methodology in `Whitepaper & Guidelines/` — see `NOTES.md` for every assumption and doc
conflict.

## Install

```bash
cd ti-framework
pip install -e ".[dev]"
```
Python 3.11+. Runtime deps: numpy, pandas, matplotlib, openpyxl.

## Quickstart

```bash
# Validate the engine against the reference fixture (±1% vs independent hand-calc)
ti validate --fixture fixtures/reference_case.json

# Run + write CSV/JSON + plots
ti report --fixture fixtures/reference_case.json --out outputs/

# Inspect the real (mostly-empty) data workbook: shows what's collected vs missing,
# and the pro-rata identity / FLAG-market handling — without fabricating inputs
ti run --workbook "../TI_Data_Workbook_v0.1.xlsx"
```

### Library use

```python
from ti_framework import run, EngineConfig, Scenario, Placement
from ti_framework.io.fixtures import load_fixture

fx = load_fixture("fixtures/reference_case.json")
result = run(fx.firm, fx.cohort_year, fx.placements, fx.countries, fx.support, fx.config)

print(result.cohorts[Scenario.S2].total)            # TI_cohort, tCO2e
print(result.cohorts[Scenario.S2].by_country)        # mandatory decomposition
print(result.cohorts[Scenario.S2].by_powertrain)
```

## Architecture

```
Layer 1 (Benchmark)        Layer 2 (ProductEmissions)        Layer 3 (sector-agnostic core)
─────────────────────      ──────────────────────────        ───────────────────────────────
E_ref,c(t)=I_fleet(t)·D    ICE/HEV  E=I_ICE·D                 gap = E_ref − E_prod
 A: Weibull stock          BEV      E=η·G_c(t)·D              cumulative → cohort (Σ_c=Σ_v)
 B: NDC pro-rata (default) PHEV     UF composite              annual flow → rolling portfolio
 C: two-bin (+B/C check)   G_c(t)=G_c(0)(1−r_power)^t         crossover t* (closed/numeric)
```

- **Pluggable sectors.** `layer1/base.py:Benchmark` and `layer2/base.py:ProductEmissions` are
  the interfaces Layer 3 computes against. Automotive implements them; `sectors/shipping.py`
  and `sectors/power.py` are stubs that subclass the same contracts so they slot into the
  unchanged core.
- **Three scenarios** (`Scenario.S1/S2/S3`), each with its own `r_fleet,c` and `r_power,c`
  (STEPS / NDC / NZE). Never report S2 alone.
- **`r_power,c` is independent of `r_fleet,c`.** Where only an economy-wide pro-rata rate
  exists, the engine defaults them equal **with a loud `PRORATA_IDENTITY` warning and a tier
  downgrade**, and exposes a sector-split correction switch to break the identity (NOTES.md D1).

## Key behaviours

| Topic | Behaviour |
|---|---|
| **FLAG markets** (US no-NDC, IN intensity, ID BAU, SA no-baseline, CN peak) | Excluded from the S2 headline and reported separately with a reason; S1/S3 computed where IEA rates are supplied. Switchable to an IEA-proxy rule. Never a silent default. |
| **Partial data** | Empty / "TO COLLECT" / "FLAG" cells load as `None`; any computation needing them is skipped and recorded in `missing_inputs`, never fabricated. |
| **Sensitivities** | T ± 3 yr, UF ± 0.15 (central + lower bound side by side), real-world correction range, full S1/S2/S3 spread. |
| **Optional switches** (default off) | sector-split correction (corrected vs uncorrected), S-curve benchmark, Monte Carlo band with a Tier-C-share directional-only threshold. |

## Outputs

`ti report` writes to the output directory:
`ti_cohort_summary.csv`, `ti_annual_timeseries.csv`, `ti_portfolio_rolling.csv`,
`ti_decomposition.csv`, `ti_crossover.csv`, `ti_result.json`,
`data_quality_declaration.txt` (Guideline §5.3), and three plots
(`portfolio_band.png`, `decomposition.png`, `single_cohort.png`).

## Validation

See [`validation_report.md`](validation_report.md). The engine reproduces an independent
hand calculation of a Korean-BEV / Korean-ICE / multi-market cohort to within ±1% (exact to
floating point), and the decomposition identity holds for every scenario.

## Development

```bash
pytest            # 52 tests, every equation + edge cases (T=1, zero volume, missing NDC, UF=0/1, ...)
ruff check ti_framework tests
mypy ti_framework
```
CI (`.github/workflows/ci.yml`) runs all three on Python 3.11 and 3.12.

## Scope and phasing

- **Implemented:** automotive, Level 1, full engine + CLI + validation.
- **Stubs (interfaces only):** Level 2 production×operating attribution (`core/level2.py`),
  shipping (IMO CII) and power (grid-intensity) plugins (`sectors/`).

## License

GNU General Public License v3 — see [`LICENSE`](LICENSE). © 2026 PLANiT Institute.
Published at transitionarc.climatearc.org.
