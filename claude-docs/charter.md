# Research charter — Trade Impact (TI)

**Truth source.** There is no external contract. The governing documents are the methodology set,
in this precedence order:

| id prefix | Document | Role |
|---|---|---|
| `W-` | [`methodology/TI_Whitepaper_v1.5.md`](../methodology/TI_Whitepaper_v1.5.md) (May 2026) | The framework. Wins over code, over the project contract's looser points, and over this charter. |
| `G-` | [`methodology/TI_Automotive_Technical_Guideline_v1.8.md`](../methodology/TI_Automotive_Technical_Guideline_v1.8.md) (May 2026) | Sector rules for automotive. |
| `M-` | [`methodology/TI_Methodological_Challenges_v1.md`](../methodology/TI_Methodological_Challenges_v1.md) (v1.0 draft, June 2026) | The open problems and what counts as resolving each. |
| `C-` | [`docs/product-contract.md`](../docs/product-contract.md) (`export-impact-v1`) | Project-internal implementation contract. Subordinate to `W-`/`G-`, but **binding where it is stricter** (recorded in [`docs/rebuild-spec.md`](../docs/rebuild-spec.md) §0). |

Every phase, stage, method and deliverable in this set cites these ids. An item that cites none is
either scope creep or a missing traceability row.

Charter date: 2026-09-03. Rewrite this document — do not annotate it — when any of the four
governing documents changes version.

---

## 1. Research purpose

The central question, in the framework's own words (`W-01`, Whitepaper §2.1):

> *Does this product emit more or less than what the operating country's sector is committed to
> emitting in that year under its NDC?*

Asked for every product a firm sells, in every country it operates in, in every year of that
product's operational life; summed over the lifetime, then over products and countries weighted by
actual sales volumes, to give a firm-level signal of the climate direction embedded in the firm's
trade activity.

The engagement exists to make that question answerable **from evidence** — not to produce a score.
A number that cannot be traced to a pinned source snapshot or a numbered assumption is not an
output of this project.

## 2. The metric

| id | Definition | Source |
|---|---|---|
| `W-02` | `E_ref,c(t) = E_ref,c(0) × (1 − r_sector,c)^t` — Layer 1, the NDC-derived dynamic sector benchmark | WP §3.1 |
| `W-03` | `E_prod,v,c(t)` — Layer 2, actual use-phase emissions of the sold product | WP §3.2 |
| `W-04` | `TI_gap,v,c(t) = E_ref,c(t) − E_prod,v,c(t)`; positive = contribution, negative = lock-in liability | WP §3.3 |
| `W-05` | `t` runs 0…T−1, T terms inclusive | WP §3.4 |
| `W-06` | `TI_product,v,c,S = Σ_{t=0}^{T−1} TI_gap,v,c(t)` | WP §3.5 |
| `W-07` | `TI_cohort,F,Y₀,S = Σ_v Σ_c [V_c,v × TI_product,v,c,S]`, with the decomposition identity `TI_cohort = Σ_c TI_country,c = Σ_v TI_type,v` **mandatory** | WP §3.6 |
| `W-08` | `TI_annual,F,Y₀,τ,S` — annual flow from one cohort | WP §3.7 |
| `W-09` | `TI_portfolio,F,τ,S` — rolling portfolio, named the **primary disclosure metric** | WP §3.8 |
| `W-22` | Level 1 operating-country basis (primary) / Level 2 production-country basis (extended) | WP §2.3 |

The metric is a **comparative trajectory metric against a policy commitment**. It is not an
avoided-emissions number, not a displacement counterfactual, and not an additionality claim
(`M-07`).

Automotive specialisation of the same equations: `G-05` ICE fixed at sale-year efficiency (GL §3.3),
`G-06` BEV against a declining grid with `r_power,c` derived **independently** of `r_fleet,c`
(GL §3.4), `G-07` PHEV as a UF-weighted composite (GL §3.5), `G-02` Layer 1 Methods A/B/C with the
B-vs-C >30% trip-wire (GL §2.3, §6.1).

## 3. Scope

| Sector | State | Boundary and benchmark | Ids |
|---|---|---|---|
| Automotive, passenger cars | **Live.** EU27 2024 cohorts published | Registration/use country; in-use fleet intensity trajectory | `W-17`, `G-01`…`G-16` |
| Power generation | Staged. Snapshots exist (JERA, KOEN); not a cohort pilot | Connected grid / consumption market; grid intensity trajectory | `W-17`, `M-06`, `C-06` |
| Shipping | Staged. Snapshot exists (MOL); boundary unresolved | Voyage/served market and IMO jurisdiction; IMO CII in place of a national NDC | `W-10`, `M-05`, `C-06` |
| Steel, petrochemicals | Not started | Per sector method | `C-06` |

Sequence and acceptance gates: [`docs/sector-expansion.md`](../docs/sector-expansion.md). Core
formulas are invariant across sectors; what varies is the Layer 1 trajectory, Layer 2 parameters,
lifetime `T`, and the data sources (`W-17`).

Analysis level today: **Level 1 only**. Every published result is a destination-cohort impact, not
an export claim, because registration data does not carry production origin (`C-01`).

## 4. Non-negotiables

Violating any of these invalidates the output, not just the presentation.

| id | Rule | Source |
|---|---|---|
| `W-16` | TI **never** nets against, offsets, or reduces Scope 3 Category 11. Separate additional disclosure only. | WP §5.3, GL §5.4 |
| `C-05` | A missing input produces an **unavailable** result — never zero, never an invented default. | product-contract publication gate; rebuild-spec §0 |
| `C-04` | A lifetime result is published only when all eight required input families are source-complete for the affected activity; otherwise status `inputs_incomplete`. | product-contract |
| `G-08` | Never S2 alone. S1, S2, S3 always reported together. | GL §4.7 |
| `W-07` | No headline without decomposition by operating country **and** product type. | WP §3.6 |
| `G-06` | `r_fleet,c ≠ r_power,c`. Derived from separate policy variables, independently sourced. | GL §3.4, App. E |
| `W-14` | Every input carries a tier (A firm-verified / B estimated / C proxy), declared per layer. | WP §5.1 |
| `C-09` | Tier-C share above the configured threshold (currently >50% of covered units) suppresses magnitudes: direction only. | Engine `directional_only`; `M-03` |
| `G-10` | Every published output carries the data-quality declaration. | GL §5.3 |
| `G-03` | Pro-rata NDC allocation is disclosed wherever used, with S1 as the conservative cross-check. | GL §2.3, App. F.1 |
| `C-03` | The five-level destination target hierarchy is followed and every fallback disclosed. A regional or economy-wide proxy is **never** relabelled a country-specific target. | product-contract |
| `C-07` | Builds run from hash-pinned snapshots, never a live API; the full published set recomputes byte-identically. | `data-pipeline/check_published.py` |
| `C-08` | Every anchored theory rule has a code token and a test; a rule with no code+test, or a token with no table row, fails the build. | [`theory/SYNC.md`](../theory/SYNC.md), `scripts/check_sync.py` |
| — | Findings are directions and associations, reported as ranges, not point estimates or causal claims. | `W-21`, `M-03` |

## 5. Deliverables

| id | Deliverable | Format | Acceptance condition | Milestone |
|---|---|---|---|---|
| `D-01` | Automotive EU27 2024 lifetime TI comparison, two cohorts | Published JSON in `data/published/`, web report, deck | `check_published.py` OK; readiness not `inputs_incomplete`; S1/S2/S3 + both decompositions + declaration present; withheld items listed with unit counts | **Delivered 2026-08-11** |
| `D-02` | Research database of referenced inputs | SQLite, generated | Every published figure joins to a source row (`source_id`) or a numbered assumption; rebuild is deterministic and hash-checked; missing values are NULL with a reason | PH2 |
| `D-03` | Generated HTML dashboard | HTML, generated from `D-02` | No hand-typed number anywhere; regenerates from the database; contradicts nothing in `data/published/` | PH2 |
| `D-04` | Closure of the withheld automotive outputs: rolling portfolio (`W-09`), PHEV, FCEV | Published JSON + web + declaration | Multi-year cohorts pinned; UF and H₂ intensity sourced with tier; portfolio no longer a repeated single cohort | PH3 |
| `D-05` | Level 2 origin decision: attribution matrix, or a documented statement that TI stays destination-cohort | Published JSON field + method note | `V_p,c,v` exact/estimated split recorded per model, or `origin_mapping_status` stated with the reason it cannot be closed | PH3 |
| `D-06` | Second sector as an active cohort pilot (power, then shipping) | Published JSON + web, per sector method | All eight `C-06` acceptance gates evidenced; no hidden allocation; no cross-sector unit addition | PH4 |
| `D-07` | Methodological challenges response | Paper (M6 synthesis) | Each of `M-01`…`M-08` has a stated rule, a bounded residual error, or a disclosed limitation — never silence | PH5 |

Language: English for all published artefacts. Working notes in `docs/` are bilingual as-is; new
governance documents are English.

Licence: GNU GPL v3, code and methodology (`W-20`, `C-10`).

## 6. Explicit exclusions

Out of scope. An artefact that crosses one of these lines is withdrawn, not caveated.

| Excluded | Source |
|---|---|
| Manufacturing and end-of-life emissions (use phase only; LCA supplements separately where material) | `W-13`, App. F.6 |
| Any netting, offsetting or credit interpretation | `W-16` |
| Avoided-emissions / Scope 4 claims, and additionality claims | `M-07`, `W-21` §9.2 |
| Non-passenger road segments — two/three-wheelers, LCV, heavy vehicles — until a segment extension exists | `M-04` |
| A single cross-sector score adding gCO₂/km, kgCO₂e/MWh, gCO₂e/t-nm and tCO₂e/t | `C-06` |
| Production or export origin inferred from destination registrations | `C-01` |
| Rolling portfolio computed by repeating one observed cohort | rebuild-spec §0 finding 1 |
| Magnitudes (as opposed to direction) while the tier-C share exceeds the threshold | `C-09` |
| Regional or global average grid intensity in place of a country value | `G-13`, App. E |
| A second correction applied to an already-corrected certification value | `G-12`, App. C.1 |

## 7. What the truth source does not settle

Named blockers. Each would change a method, so none may be resolved by analyst discretion.

| id | Open question | Who resolves |
|---|---|---|
| `B-01` | CA/AU S2 treatment: keep economy-wide pro-rata with a note, or use the current-policy projection as S2 with a tier downgrade. Both are listed as choices in [`data-pipeline/sectoral-sources.md`](../data-pipeline/sectoral-sources.md) §4 and neither is chosen. | Methodology owner (PH5, `M-01`) |
| `B-02` | The FLAG-market rule for unquantifiable benchmarks exists only as an engine default (`NOTES.md` D3, `flag_market_rule="exclude"`). `M-01` says it "cannot be left to analyst discretion" — it is not yet a methodology-level rule. | Methodology owner (PH5) |
| `B-03` | EU `r_power` S2 is pinned to 0 because the 2030 pro-rata target is already met. Is 0 the correct encoding, or should S2 fall back to the observed S1 trend with a disclosure? | Methodology owner (PH3/PH5) |
| `B-04` | `W-20` publishes at `transitionarc.climatearc.org`; the project actually deploys per [`docs/deploy.md`](../docs/deploy.md). Which is the canonical publication address? | Project owner |
| `B-05` | Whether the sector-split correction factor (`M-01`) is method work (PH5) or data work (PH3) — it changes the benchmark for every live market. | Research director + methodology owner |
| `B-06` | Level 2 feasibility: whether any public source supports a model→factory→destination mapping for these cohorts at all, or whether `D-05` resolves as a documented impossibility. | PH3 stage owner |

---

Current state, per-objective judgement and gate verdicts live in [`tracker.md`](tracker.md) — never
in this document.
