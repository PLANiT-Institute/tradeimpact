# Trade Impact (TI) Framework
## Methodological Challenges — Open Questions and Case-Study Test Plan

**Version 1.0 (draft) · June 2026 · PLANiT Institute**
*Companion to Whitepaper v1.5 and Automotive Technical Guideline v1.8. Published under GNU GPL v3.*

---

## Purpose of this document

This document is the intellectual spine of the TI case-study programme. It does two things:

1. It states each known methodological challenge precisely — what the problem is, why it threatens the validity of a TI score, and what the framework currently does about it.
2. It assigns each challenge to the case study that will test it, and specifies what a *resolution* would look like.

The principle is adversarial: every case study exists to stress one or more of these challenges to the point where the framework either holds or visibly breaks. A challenge is "resolved" only when we can state a defensible rule, show the magnitude of the residual error, and disclose it. Where a challenge cannot be resolved, the honest output is a documented limitation with a bounded error, not silence.

Treatment depth in v1.0 is **deep for automotive** (Challenges 1–4), **skeleton for shipping and power** (Challenges 5–6), to be expanded as those sector guidelines are drafted (Todo M2, M3).

A material development since the framework was last revised: the **2035 NDC cycle is now substantially complete** (Australia, EU, Japan, Korea, China, Indonesia, India submitted 2025–2026; the United States has revoked its NDC). This sharpens, rather than relaxes, every benchmark-related challenge below — see Challenge 1.

---

## Challenge 1 — Non-NDC and weak-NDC markets, and the pro-rata allocation problem

**The problem.** Layer 1 takes the operating country's NDC-committed sector trajectory as the authoritative benchmark. This assumes (a) an NDC exists, (b) it implies a transport-sector and a power-sector decarbonisation rate, and (c) that rate is a meaningful counterfactual. Across the nine priority markets, all three assumptions fail in identifiable ways.

**Why it threatens the score.** The benchmark `E_ref,c(t)` is the entire reference point of the metric. If the benchmark slope `r_fleet,c` (or `r_power,c`) is mis-set, every TI_gap, every crossover point, and the sign of the firm-level result move with it. The benchmark is not a parameter the score is robust to — it *is* the score's denominator of judgement.

**What we now know (June 2026 NDC scan).** A direct read of the latest NDCs for AU, US, EU, JP, KR, IN, ID, SA, CN returns a uniform result: **none contains an explicit, quantified transport-sector emissions sub-target, and none contains an explicit power-sector emissions sub-target.** India's NDC explicitly disclaims sector targets; India and China give non-fossil *capacity* shares, which are not emissions sub-targets. The practical consequence is that **pro-rata allocation from the economy-wide target is required for all nine markets** — i.e. the framework's default fallback (Guideline §2.3 Method B) is in fact the universal case, not the exception.

This matters because pro-rata assumes every sector decarbonises at the economy-wide rate, whereas transport reliably decarbonises *slower* than electricity. Pro-rata therefore **overstates `r_fleet,c`** (too-steep transport benchmark) and **understates ICE lock-in liability** — biasing TI scores optimistic for ICE-heavy portfolios. The bias is not a rounding issue; it is directional and it favours exactly the firms the framework is meant to scrutinise.

Three further failure modes:
- **No usable base→target arithmetic.** Saudi Arabia's NDC states an absolute "278 MtCO₂e avoided" against an *unstated* baseline; China's 2035 target is expressed against an undefined emissions "peak"; Indonesia's headline is against a BAU projection, not a base-year level. For these, the Guideline formula `r = 1 − (E_target/E_base)^(1/Δy)` cannot be evaluated from the NDC alone.
- **Revoked / absent NDC.** The US has no active NDC as of June 2026. A market with no NDC has no S2 benchmark at all.
- **Ambition ≠ implementation.** S2 encodes stated ambition; the enacted-policy path (S1, IEA STEPS) can diverge sharply, especially where the NDC is conditional (India, Saudi Arabia, Indonesia's upper band).

**What the framework currently does.** Method B with pro-rata allocation; a caveat instructing analysts to disclose pro-rata use and report S1 (STEPS) as a conservative cross-check; Method C (two-bin) as a no-NDC fallback and a >30% divergence trip-wire against Method B.

**What is still open.**
1. Pro-rata is universal, so the pro-rata bias is universal. A generic caveat is not enough — we need a **transport-vs-economy decarbonisation differential** (a sector-split correction factor) that can be applied where no sub-target exists, ideally derived from IEA WEO sector pathways rather than assumed.
2. For "unquantifiable benchmark" markets (SA, CN-vs-peak, ID-vs-BAU, US-none), we need a stated decision rule: fall back to S1/S3 IEA sector trajectories as the *primary* S2 proxy, or exclude the market from headline TI and report it separately? These cannot be left to analyst discretion if results are to be comparable across firms.
3. We need a published, per-market **benchmark-confidence tier** so a reader can see that, e.g., an Australian benchmark (clean base-year arithmetic, but pro-rata) is more trustworthy than a Saudi one (no baseline at all).

**How the case studies test it.** The automotive Level 1 case study (CA3) runs Korea and Japan — both now have clean 2035 base→target arithmetic (KR 53–61% vs 2018; JP 60% vs FY2013) but **both require pro-rata** for transport. Running S1/S2/S3 side by side will quantify how much of the TI result is an artefact of the pro-rata assumption versus a real signal. Extending the same vehicles into India and Indonesia (CA3 sensitivity) stresses the unquantifiable-benchmark and conditional-target cases directly.

**Resolution criterion.** A documented sector-split correction with a stated derivation and a bounded residual error, plus an explicit decision rule for unquantifiable-benchmark markets, such that two analysts handed the same firm and markets produce the same benchmark to within the declared tolerance.

---

## Challenge 2 — Multi-factory production allocation (Level 2)

**The problem.** Level 2 traces the use-phase impact of vehicles back to the factory that built them, via the production × operating-country volume matrix `V_p,c,v`. When a model is built in one plant, operating-country registrations imply production origin cleanly. When the same model is built in several plants serving overlapping markets — the norm for global OEMs — the mapping becomes an allocation, not an observation.

**Why it threatens the score.** Level 2 is the framework's claim to attribute climate direction to *production decisions*, which is what makes it relevant to industrial and trade policy. If `V_p,c,v` is largely estimated, the production-country TI is an estimate dressed as an attribution, and a firm could contest any specific plant's number.

**What the framework currently does.** Maps models to factories from firm IR materials; where multiple factories build a model, allocates by factory production-volume ratios from IR disclosures (Guideline §3.2, §8 Step 3). Documents where the mapping is exact vs estimated.

**What is still open.** The precision gap created by volume-ratio allocation is unquantified. Volume-ratio allocation implicitly assumes a factory's output is distributed across destination markets in proportion to its share of total model production — which is false whenever plants are regional (e.g. a domestic plant serving the home market and an export plant serving everyone else). We have no rule for when the allocation error is small enough to report a plant-level number versus when only a producer-region aggregate is defensible.

**How the case studies test it.** CA4 attempts Level 2 for one Japanese and one Korean OEM using IR factory-model assignments, and is instructed to document, model by model, where the mapping is exact versus estimated and what precision gap that creates. This produces the first empirical read on how often clean attribution is even possible for a global automaker.

**Resolution criterion.** A stated threshold rule (report plant-level vs region-level) tied to a measured allocation-error bound, plus a transparency field recording the exact/estimated split per model.

---

## Challenge 3 — Proxy methods for Tier C data, and sensitivity to data tier

**The problem.** The framework's three-tier data hierarchy (A firm-verified / B estimated / C proxy) is honest about provenance but silent about consequence. A TI score built largely on Tier C inputs (representative-model proxies, regional default VKT, IEA regional Weibull defaults) may carry an uncertainty band wide enough to flip its sign, yet it is reported on the same axis as a Tier A result.

**Why it threatens the score.** Comparability across firms is the point of a disclosure metric. If Firm X's positive TI rests on Tier A data and Firm Y's rests on Tier C proxies, ranking them is not meaningful unless the uncertainty is propagated and shown.

**What the framework currently does.** Requires a per-layer tier declaration and mandatory sensitivity ranges (T ± 3 yr, UF ± 0.15, real-world correction range, S1/S2/S3). Tiers are disclosed but not converted into a combined uncertainty band on the headline number.

**What is still open.** There is no method for propagating input-tier uncertainty into a confidence interval on TI_cohort / TI_portfolio. Sensitivity is run parameter-by-parameter, not jointly, so the reported ranges understate combined uncertainty. We also lack guidance on a maximum Tier-C share beyond which a headline TI should be suppressed in favour of a "directional only" label.

**How the case studies test it.** The emerging-market extensions in CA3 (India, Indonesia) are deliberately Tier-B/C heavy — sparse registration granularity, default VKT, regional fleet parameters. Comparing their uncertainty behaviour against the Tier-A/B Japan and Korea base cases gives the empirical basis for a propagation rule and a Tier-C suppression threshold.

**Resolution criterion.** A reproducible uncertainty-propagation procedure (e.g. Monte Carlo over declared input ranges) yielding a confidence band on the headline TI, and a stated Tier-C share above which only a directional result is published.

---

## Challenge 4 — Non-passenger and mixed segments; PHEV and the Utility Factor

**The problem.** Two distinct automotive sub-problems sit here. First, the framework is specified for passenger vehicles; light-commercial, two/three-wheelers (dominant in India and Indonesia), and heavy vehicles have different fleet benchmarks and lifetimes and are not yet covered. Second, PHEVs depend on the Utility Factor (UF) — the share of distance driven electrically — which regulatory values systematically overstate.

**Why it threatens the score.** Segment mis-coverage forces emerging-market analyses to either exclude the dominant vehicle class or shoehorn it into passenger-car parameters. The UF problem is sharper: PHEV TI contributions are linear in UF, so a regulatory UF that is 0.15–0.30 too high converts a PHEV from a modest liability into an apparent contribution — a direct route to greenwashing if uncorrected.

**What the framework currently does.** Restricts scope to passenger vehicles; treats PHEV with an explicit UF caveat, mandatory UF ± 0.15 sensitivity, and a requirement to report central and lower-bound (UF − 0.15) results side by side, flagging PHEV contributions as upper-bound estimates.

**What is still open.** No segment extension exists for two/three-wheelers or LCVs, which makes India/Indonesia passenger-only analyses unrepresentative of the actual road fleet. The UF treatment is a sensitivity band, not a market-calibrated correction; we do not yet anchor UF to a real-world dataset (T&E, ICCT) per market.

**How the case studies test it.** The Korea/Japan auto case (CA3) includes PHEV-heavy and BEV-heavy contrasts and will report the UF lower-bound explicitly, testing whether the PHEV sign is robust to the UF correction. Company selection (CA1) is instructed to choose contrasting powertrain mixes precisely so the UF and segment effects are visible rather than averaged away.

**Resolution criterion.** Market-calibrated UF defaults sourced from real-world studies (replacing the generic ± 0.15 band with a per-market central value plus residual band), and a documented decision on whether emerging-market analyses report passenger-only with a stated coverage ratio or await a two/three-wheeler segment extension.

---

## Challenge 5 — Shipping: vessel-vs-flag-state operating-country boundary *(skeleton — to expand under Todo M2)*

**The problem.** TI's unit of analysis is the operating country, defined for road transport as where the vehicle is driven. A ship has no single operating country: it is registered under a flag state, owned in another, and operates across international waters and many national EEZs over a voyage. The framework's geographic boundary, and therefore which NDC (if any) supplies Layer 1, is ambiguous for maritime.

**Why it threatens the score.** The Layer 1 benchmark for shipping cannot be a national NDC in the road-transport sense. The Whitepaper anticipates this by substituting the **IMO GHG Strategy Carbon Intensity Indicator (CII) trajectory** for the national NDC in international waters — but this swaps the framework's core NDC-anchored logic for an international-regulator anchor, which is a conceptual change, not just a parameter swap.

**Open questions (to be developed in the Shipping Technical Guideline).**
- Boundary definition: flag-state as the operating country vs voyage-weighted multi-country attribution, and the sensitivity of TI to that choice.
- Benchmark source: IMO CII trajectory as Layer 1, and how it reconciles (or conflicts) with the national NDCs of the countries a vessel actually serves.
- Layer 2 by vessel type and fuel (HFO, LNG, methanol, ammonia), including well-to-wake vs tank-to-wake accounting for alternative fuels.

**How the case study will test it.** CS3 runs one Japanese and one Korean shipbuilder under two boundary treatments — flag-state and voyage-weighted — and quantifies the TI sensitivity to the boundary choice. That sensitivity is the headline deliverable for this challenge.

**Resolution criterion.** A stated boundary rule with a measured TI sensitivity to the alternative, and a defensible reconciliation of the IMO CII benchmark with the framework's NDC logic.

---

## Challenge 6 — Power generation: grid interconnection and mixed-portfolio aggregation *(skeleton — to expand under Todo M3)*

**The problem.** For a power-generation firm, the "product" is electricity and the operating country's Layer 1 benchmark is the grid emission-intensity trajectory. Two structural issues arise: interconnected grids cross borders (so a plant's output is consumed under multiple national benchmarks), and a single firm typically operates a mixed portfolio (coal, gas, nuclear, renewables) whose assets sit on opposite sides of the benchmark simultaneously.

**Why it threatens the score.** A company-level average can mask a portfolio that is half well below and half well above the benchmark — the aggregation hides exactly the lock-in signal the framework exists to surface. The grid-attribution boundary (generation-country vs consumption-country) is the power-sector analogue of Challenge 2.

**Open questions (to be developed in the Power Technical Guideline).**
- Layer 1: operating-country grid intensity trajectory from IEA WEO / national power-sector pathway — and which country's grid applies for cross-border interconnected output.
- Layer 2 per generation technology, and whether the benchmark comparison is struck at technology level or company level (Appendix E warns against company-level-only comparison).
- Non-dispatchable vs dispatchable assets and how crossover-point logic behaves for an asset that displaces marginal rather than average generation.

**How the case study will test it.** CP3 runs one Japanese and one Korean power company with deliberately mixed portfolios and tests how the framework handles coal + gas + nuclear + renewables under one firm, isolating the aggregation-masking effect.

**Resolution criterion.** A stated aggregation rule (technology-level benchmarking with mandatory decomposition) and a grid-attribution boundary rule with measured sensitivity.

---

## Cross-cutting issue A — Counterfactual, additionality, and the relationship to Scope 4

This is not a sixth sector challenge; it is the conceptual objection a peer reviewer or a GHG Protocol working group will raise first, and it cuts across every challenge above.

The TI benchmark is a *policy-trajectory* counterfactual ("what the operating country committed to emit"), not a *market-displacement* counterfactual ("what this sale displaced"). That is a deliberate and defensible choice — it is what lets the metric capture the temporal value of early adoption and escalating lock-in. But it means TI is **not** an avoided-emissions / Scope 4 number and must never be read as one. The avoided-emissions literature (WBCSD Avoided Emissions Guidance; Bjørn et al. 2024 on Scope 4 accounting claims) is built on displacement baselines and additionality tests that TI does not perform.

The framework's defence — that TI is a comparative trajectory metric, never netted against Scope 3, always reported as a separate additional disclosure — is correct but currently stated briefly. Reviewers will press on three points: (1) why a policy-commitment baseline is a legitimate reference when the commitment may not be met (answered partly by always reporting S1 enacted-policy alongside S2); (2) whether a firm reporting positive TI is making an implicit additionality claim it cannot support (the non-summation caveat, §9.2 of the Whitepaper, addresses this but should be elevated); (3) how TI relates to, rather than competes with, Scope 4 reporting. M6 (the consolidated challenges-response paper) should carry an explicit, literature-anchored positioning section, because this is the objection most likely to sink the journal submission if left thin.

---

## Cross-cutting issue B — Benchmark non-linearity (S-curve vs exponential)

Methods B and C model the benchmark as a smooth exponential decline; real fleet and grid transitions follow S-curves. In fast-transition markets (notably the EU and China for both fleet and grid, and Korea for grid), the exponential understates near-term benchmark decline, which **understates** ICE lock-in liability in precisely the markets transitioning fastest. The framework flags this in the data-quality declaration but does not offer an S-curve benchmark option. The automotive case study should cross-validate the exponential benchmark against observed recent sector data for at least one fast-transition market (EU or China grid) to bound the error, with an S-curve benchmark variant noted as a candidate methodological extension if the error proves material.

---

## Summary — challenge-to-case-study map

| # | Challenge | Primary case-study test | Sector depth (v1.0) | Resolution = |
|---|-----------|------------------------|---------------------|--------------|
| 1 | Non/weak-NDC markets; universal pro-rata bias | CA3 (KR/JP base; IN/ID extension) | Deep | Sector-split correction + decision rule for unquantifiable benchmarks |
| 2 | Multi-factory production allocation | CA4 Level 2 | Deep | Threshold rule tied to measured allocation-error bound |
| 3 | Tier-C proxy uncertainty propagation | CA3 emerging-market extensions | Deep | Uncertainty band on headline TI + Tier-C suppression threshold |
| 4 | Non-passenger segments; PHEV UF | CA1/CA3 (powertrain contrast) | Deep | Market-calibrated UF defaults + segment coverage decision |
| 5 | Shipping boundary (flag vs voyage) | CS3 (two boundary treatments) | Skeleton (M2) | Boundary rule + measured TI sensitivity |
| 6 | Power grid interconnection + mixed portfolio | CP3 (mixed-fleet firm) | Skeleton (M3) | Technology-level aggregation rule + attribution boundary |
| A | Counterfactual / Scope 4 positioning | M6 synthesis + journal discussion | Cross-cutting | Literature-anchored positioning section |
| B | Benchmark non-linearity (S-curve) | CA3 cross-validation (fast-transition market) | Cross-cutting | Bounded error + optional S-curve variant |

---

*Draft v1.0 — to be revised once peer-reviewer feedback on Whitepaper v1.5 / Guideline v1.8 is incorporated, and expanded for shipping (M2) and power (M3). PLANiT Institute, June 2026.*
