# NOTES — assumptions, doc conflicts, open items

This file logs every assumption made by the engine, every place the source documents
conflict, and every default fallback. Source-of-truth precedence (per the build brief):
**the methodology docs win over code and over the build prompt**; conflicts are recorded
here rather than silently resolved.

Source docs:
- `TI_Whitepaper_v1.5.md`
- `TI_Automotive_Technical_Guideline_v1.8.md`
- `TI_Methodological_Challenges_v1.md`
- `TI_Data_Workbook_v0.1.xlsx`, `TI_CaseStudy_Reference_DB_v0.1.xlsx`

---

## 1. Confirmed build decisions (resolved with the project owner, 2026-06-29)

These four decisions were confirmed before coding. Each resolves a genuine doc conflict
or an explicitly-open methodological item.

### D1 — `r_fleet,c` vs `r_power,c` when only an economy-wide rate exists
**Conflict.** Guideline Appendix E + §3.4 state the two rates must *never* be set equal and
must be derived independently. But the workbook and reference DB carry only a single
**economy-wide** pro-rata rate per market (S2), with the transport/power sector split marked
"pending / open item" and S1/S3 marked "TO EXTRACT from IEA".

**Decision (D1).** When no independent `r_power,c` is supplied, the engine defaults
`r_fleet,c = r_power,c = economy-wide rate` (pro-rata sector-split factor = 1.0) **and**:
- emits a prominent `PRORATA_IDENTITY` data-quality warning on the result,
- downgrades the affected benchmark confidence tier,
- exposes the **sector-split correction** switch (`sector_split`, default off) as the
  documented mechanism to break the identity (see §3 below).

This is the only choice that runs on the real workbook today; the warning makes the
violation explicit rather than hidden.

### D2 — S2 selection from a reduction *range*, and placement of the conditional target
**Conflict.** Guideline §6.2 says "unconditional for S2; conditional for S3", but the
three-scenario table (Guideline §4.7) defines S3 = IEA NZE, not the conditional NDC.

**Decision (D2).** S2 central = the **unconditional (low)** reduction rate. The
**conditional (high)** rate becomes an S2 **sensitivity upper bound**, not S3.
S3 remains strictly the IEA NZE sector trajectory, supplied as a separate input.
(So Korea 53–61% → S2 central from 53%, S2 upper-sensitivity from 61%.)

### D3 — FLAG-market rule
**Open item.** Challenge 1 states the unquantifiable-benchmark rule "cannot be left to
analyst discretion" but does not fix one.

**Decision (D3).** FLAG markets (US = no NDC; IN = intensity target; ID = BAU baseline;
SA = no baseline; CN = undefined peak) are **excluded from the S2 headline TI** and reported
in a separate "benchmark-not-derivable" section, each with a recorded flag reason. S1/S3 are
still computed for them **where IEA STEPS/NZE rates are supplied**. No silent S2 default is
ever fabricated. Implemented behind a config switch (`flag_market_rule = "exclude" |
"iea_proxy"`), default `"exclude"`.

### D4 — Validation approach
**Reality.** Worked examples were removed in Guideline v1.8 and the workbook vehicle
parameters are all "TO COLLECT", so no externally-authoritative worked example exists.

**Decision (D4).** Validation is **engine-vs-independent-hand-calculation** over committed
fixtures (Korean BEV, Korean ICE, a multi-market cohort) built from documented, *illustrative*
parameter values. The ±1% acceptance test proves engine arithmetic correctness, not the
real-world accuracy of the inputs. Fixture inputs are flagged illustrative in
`fixtures/README.md`.

---

## 2. Unit conventions (assumptions)

- Internal per-vehicle-year emissions are **kgCO₂e/vehicle/year**; firm totals are **tCO₂e**
  (÷1000 applied at aggregation).
- Grid intensity loaded as gCO₂/kWh → converted to **kgCO₂e/kWh (÷1000)** on load
  (per Reference DB D3 note).
- ICE intensity loaded as gCO₂/km → converted to **kgCO₂e/km (÷1000)** on load.
- `r_*` rates supplied as **%/yr** in the workbook are converted to fractions (÷100) on load;
  rates already in fractional form are detected (value < 1) and passed through. This heuristic
  is logged per field.
- All exponential-decline rates are applied as `value(t) = value(0) × (1 − r)^t`, `t = 0..T−1`.

## 3. Optional methodological switches (default OFF, per build brief §5)

- `sector_split` — scales economy-wide → transport `r_fleet` (and independently power
  `r_power`) by a documented differential factor, to address the universal pro-rata bias
  (Challenge 1). Corrected vs uncorrected reported side by side. Default factor 1.0 (off).
- `s_curve` — logistic benchmark as an alternative to the exponential, for fast-transition
  markets (Challenge B / Whitepaper §9.5). Default off (exponential).
- `monte_carlo` — joint propagation of declared input ranges → confidence band on
  TI_cohort / TI_portfolio (Challenge 3). Includes a Tier-C-share threshold above which only
  a directional ("contribution"/"liability") label is emitted instead of a number. Default off.

## 4. Crossover (t\*) treatment
<a id="rule-n4-crossover"></a>
- ICE/HEV (constant vs exponential benchmark): closed form
  `t* = ln(E_prod / (I₀·D)) / ln(1 − r_fleet)`.
- BEV (two exponentials): closed form
  `t* = ln(I₀ / (η_EV·G₀)) / ln((1 − r_power)/(1 − r_fleet))`;
  degenerate when `r_fleet == r_power` (parallel lines — no finite crossover) → reported as
  `None` with reason.
- PHEV (constant + exponential mix): no simple closed form → numeric bisection over t.

## 5. Missing-data behaviour

Empty / "TO COLLECT" / "TO EXTRACT" / "FLAG" workbook cells are loaded as `None`, never as a
fabricated default. Any computation requiring a `None` input is skipped and recorded in the
result's `missing_inputs` list and the data-quality declaration, rather than crashing.

## 6. Scope / phasing

- Implemented now: automotive, Level 1 (operating-country basis), full Layer 1/2/3 + CLI +
  validation.
- Interfaces only (stubs, not implemented): Level 2 production×operating attribution
  (`core/level2.py`), shipping (IMO CII) and power (grid-intensity) Layer 1/2 plugins
  (`sectors/`). Base classes are designed so these slot in without touching Layer 3.

## 7. Outstanding doc conflicts / items still open

- **2026-07-30 update:** JP/KR/EU/UK now carry independently derived sectoral S2 rates in
  the workbook (official government sectoral pathways — sectoral-sources.md), so the D1
  pro-rata identity no longer applies there. It still applies to AU/CA S2 (no official
  sectoral NDC decomposition exists; their official sectoral projections are
  current-policy and feed S1). **D2 caveat:** the sectoral pathways are single central
  paths — no sectoral decomposition of the conditional NDC range exists, so `s2_upper`
  is not populated for sectoral-S2 markets.
- The sector-split correction factor's *derivation* (IEA WEO sector pathways) is not in the
  workbook; the switch is implemented but the factor must be supplied by the analyst.
- Public S1/S3 fields remain empty unless a country-specific source is present (CA/AU S1
  are official projections). Illustrative S1/S3 values exist only in the internal engine
  validation fixture and are not public assessments.
- Base-year fleet intensity `I_fleet,seg,c(0)` and segment ratio require IEA transport CO₂ ÷
  (OICA fleet × VKT), none of which are in the workbook. Public company reports are
  withheld until these fields are sourced; only the internal validation fixture supplies
  illustrative values.
