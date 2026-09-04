# Charter — Trade as a Climate Amplifier

Extracted only from the governing document. Nothing here is inferred; where the proposal is
silent, that silence is recorded as a blocker rather than filled in.

**Governing document (truth source).** `TI_Proposal_v3.docx`, Climate Arc grant proposal,
Google Drive `12_Finance/Grant/Climate Arc/2026/Trade/Proposal/Copy of TI_Proposal_v3.docx`.
No countersigned grant agreement has been located; the proposal is therefore treated as
governing (see `B-05`).

**Methodology truth source** (subordinate to the proposal, and itself a deliverable):
[`../methodology/TI_Whitepaper_v1.6.md`](../methodology/TI_Whitepaper_v1.6.md),
[`../methodology/TI_Automotive_Technical_Guideline_v1.9.md`](../methodology/TI_Automotive_Technical_Guideline_v1.9.md),
[`../methodology/TI_Methodological_Challenges_v1.md`](../methodology/TI_Methodological_Challenges_v1.md).

Grantee: PLANiT, South Korea. Duration: "12 Months". Primary contact: Sanghyun Hong, Co-founder.

---

## 1. Research purpose

The question the engagement exists to answer, in the proposal's own words:

> "no standardised methodology exists that tells a firm, an investor, or a standard-setter
> whether a given export portfolio is accelerating or entrenching decarbonisation in the
> markets it serves."

The project answers it by measuring "a firm's export volume against the importing country's
own emissions baseline and NDC trajectory, producing both a time-series impact signal and a
Crossover Point that identifies when a product transitions from climate contribution to
lock-in liability."

### The core formula, as stated in the proposal

```
TI = Σ [ (Layer 1 Baseline(t) − Layer 2 Product Emissions(t)) × Volume(t) ]   over product lifetime T
```

Layer 1 is the displacement/enabling/trajectory reference — "the importing country's own
dynamic emissions baseline, projected along its NDC trajectory for the full product
lifetime". Sign convention, quoted: "A positive TI score indicates net displacement of
emissions relative to the importing country's baseline. A negative TI score indicates
lock-in: the exported product is more carbon-intensive than what the importing market is on
track to deploy."

> **Sign convention superseded, 2026-09-04.** The quotation above is the contract's wording and
> stays as written. The framework has since reversed the ordering: whitepaper v1.6 §3.3 defines
> TI_gap as `E_prod − E_ref`, so in every current output a **positive** figure is emissions
> **added** — the lock-in the contract describes as negative — and a **negative** figure is the
> displacement it describes as positive. The magnitudes are unchanged; only the sign is. The
> reason is that TI is reported in tonnes of CO₂e and a positive number of tonnes should mean
> tonnes emitted. Any deliverable that quotes the contract's wording must say which convention
> its figures use.

The operational equation set that implements this formula is the whitepaper's §3.1–§3.8 and
the automotive guideline's §2–§4; it is not restated here (one home per fact). See
[`toolbox/references-and-archive.md`](toolbox/references-and-archive.md).

---

## 2. Deliverables

Dates are the proposal's own milestone labels. They cannot be converted to calendar dates
because the proposal states no start date — blocker `B-01`.

| id | Deliverable (proposal wording) | Format | Milestone | Acceptance condition |
|---|---|---|---|---|
| `D-01` | Methodology white paper | "Working paper (open-access)" | Month 7 | Submitted for open-access peer review to "the Journal of Cleaner Production or equivalent journal" (success criterion a) |
| `D-02` | Automotive case study | Working paper + open dataset + open-source model | Month 7 | Results documented and publicly available; the dashboard validated against it (criterion b) |
| `D-03` | Power generation case study | as `D-02` | Month 7 | as `D-02` |
| `D-04` | Shipbuilding case study | Open-source GitHub repository | Month 10 | as `D-02`; serves as cross-validation (`X-08`) |
| `D-05` | "Climate Arc integration specification" | Specification document | Month 10 | Specifies TI as an additional analytical layer on Transition Arc (`C-09`) |
| `D-06` | "Build open-source TI model" | Open-source GitHub repository | Month 10 | Runs the three case studies end to end from registered sources; GPL v3 (`C-01`) |
| `D-07` | "Final synthesis report" | Report | Month 12 | Published openly (`C-02`) |
| `D-08` | "open-source tool public release" — the prototype dashboard | "Open-source tool (potentially linked to Transition Arc)" | Month 12 | "the prototype dashboard is fully functional and validated against the three case study sectors, with results documented and made publicly available" (criterion b) |
| `D-09` | Policy brief | Publicly available document | Month 12 | "maps the TI Framework's implications for GHG Protocol and PCAF standard-setting and made publicly available for uptake by relevant bodies" (criterion c) |
| `D-10` | "open dataset" | Open data | Month 7 | Published without restriction; every row carries a `source_id` (`N-03`) |

---

## 3. Obligations

| id | Obligation (from the proposal) |
|---|---|
| `C-01` | Codebase released on GitHub under GNU GPL v3, which "not only permits but requires that any derivative work also remain open". |
| `C-02` | "All outputs from this project — the methodology white paper, empirical case studies, prototype dashboard, and underlying datasets — will be published openly and without restriction." |
| `C-03` | The white paper "will be submitted for open-access peer-reviewed publication". |
| `C-04` | "three-tier data quality system (A: firm-verified; B: segment-estimated; C: proxy-based) … Each score carries its data quality tier so users understand the evidence base." |
| `C-05` | "The three-scenario architecture (low/central/high NDC ambition) … Crossover Points are presented as P10/P50/P90 ranges … Sensitivity analysis on NDC scenarios will be published alongside all results." |
| `C-06` | Attribution "grounded in the PCAF financed emissions analogy … documented and defended explicitly in the white paper. A comparative overview of the TI Framework's relationship to Scope 3 Cat. 11, Scope 4, and PCAF will be included in the methodology paper". |
| `C-07` | "a small Technical Advisory Group — comprising two to three financial sector representatives and one manufacturing sector specialist — to provide feedback at the methodology design and pilot stages." |
| `C-08` | "publicly available data only, no primary data collection." |
| `C-09` | "The TI Framework is conceived as an additional analytical layer within the Climate Arc ecosystem"; PLANiT "will draw on Climate Arc's experience in platform development, distribution, and operation". |
| `C-10` | "We will conduct training and sharing sessions to support researchers, analysts, and institutions seeking to apply or extend the TI Framework." |
| `C-11` | Scope bound: "three sectors, six firms, publicly available data only"; "The four-phase structure with defined deliverables per phase provides a clear sequencing framework to maintain focus." |
| `C-12` | Team: the lead researcher plus "a researcher who has 5 years of experience in industrial decarbonisation with a background in economics or finance related fields"; research direction set by the co-founders. |
| `C-13` | Duration 12 months; grantee PLANiT (South Korea). |
| `C-14` | Success assessed on (a) methodological rigour, (b) practical utility, (c) policy relevance — as quoted in `D-01`, `D-08`, `D-09`. |

---

## 4. Explicit exclusions

An out-of-scope output delivered anyway creates an expectation nobody priced.

| id | Out of scope |
|---|---|
| `X-01` | More than three sectors or six firms; "The deliverable is a replicable, open-source methodology — not an exhaustive firm database." |
| `X-02` | Primary data collection, and paywalled or proprietary data (`C-08`). Where a needed source is paywalled, the answer is a documented fallback or an unavailable result — never a purchase and never a guess. |
| `X-03` | Manufacturing and end-of-life emissions (whitepaper §4.4). |
| `X-04` | Production-country emissions inside the Layer 1/Layer 2 boundary; production country is relevant only to Level 2 attribution (whitepaper §4.2). |
| `X-05` | Avoided-emissions / Scope 4 claims and additionality tests. TI is a policy-trajectory counterfactual, not a market-displacement one (challenges, cross-cutting issue A). |
| `X-06` | Driving adoption: "The research does not attempt to drive adoption — it attempts to make adoption possible." |
| `X-07` | Vehicle segments beyond passenger cars — light-commercial, two/three-wheelers, heavy vehicles (challenges, Challenge 4). |
| `X-08` | Treating shipbuilding as a primary validation vehicle: "The automotive and power generation case studies are the primary validation vehicle; the shipbuilding case study serves as cross-validation." |

---

## 5. Non-negotiables

These bind every stage. A result that breaches one is not published, whatever its milestone.

| id | Rule | Source |
|---|---|---|
| `N-01` | TI is additional to Scope 3 Category 11 and never nets, offsets or reduces it. | Whitepaper §5.3, guideline §5.4 |
| `N-02` | A missing input produces an **unavailable** result — never zero, never a silent default. Withheld units are counted and reported. | Repo `README.md`; whitepaper §5.2 |
| `N-03` | Every figure traces to a registered `source_id` or a numbered assumption in [`toolbox/assumptions.md`](toolbox/assumptions.md). A number with neither does not exist. | `C-04`, `C-02` |
| `N-04` | Results on proxied (Tier C) inputs are published as directions and ranges, never as point estimates; tiers are declared per layer. | `C-04`, `C-05`, whitepaper §5.1 |
| `N-05` | S1, S2 and S3 are always reported together. "Never report S2 alone." | Guideline §4.7 |
| `N-06` | Every headline carries its decomposition by operating country and by powertrain; the identity `TI_cohort = Σ_c TI_country = Σ_v TI_type` holds. | Whitepaper §3.6 |
| `N-07` | `r_fleet` and `r_power` are derived independently and never set equal. | Guideline §3.4, Appendix E |
| `N-08` | Raw data is immutable; `processed/` is written only by scripts under `script/auto/`; the same raw inputs produce byte-identical processed outputs. | Repo `script/auto/README.md` |
| `N-09` | Findings are stated as associations and directions, not causes or predictions; pro-rata, proxy and extrapolation use is disclosed, not smoothed. | Guideline §2.2, Appendix F; challenges Ch1 |

---

## 6. What the governing documents do not settle

| id | Open question | Who can resolve it |
|---|---|---|
| `B-01` | No project start date is stated, so "Month 7 / 10 / 12" cannot be converted to calendar dates. Every milestone in this set is therefore relative. | `consultant` → Climate Arc (grant agreement) |
| `B-02` | "AMOUNT REQUESTED" is blank in the proposal copy; the researcher hire in `C-12` has no confirmed budget. | Project lead |
| `B-03` | `C-11` bounds the work at six firms across three sectors. The current automotive direction names four exporters (Hyundai, Kia, Toyota, Honda), which consumes four of the six. Either the firm count is per sector or the automotive set must shrink. | Project lead, then `consultant` via change control |
| `B-04` | The importer set (EU27, United States, Australia) is a project-lead decision, not a proposal commitment. The United States has no active NDC as of the June 2026 scan, so it has no S2 benchmark at all (challenges Ch1). The decision rule — exclude from the headline, or substitute an IEA sector trajectory as the S2 proxy — is unmade. | Project lead + `climate-risk-modeller`; recorded in [`log/README.md`](log/README.md) |
| `B-05` | No countersigned grant agreement located. If one exists and differs from the proposal, this charter is wrong and Pass 3 must re-run. | `consultant` |
| `B-06` | The Technical Advisory Group (`C-07`) is not convened, and the proposal ties its feedback to "the methodology design and pilot stages" — both of which are now live. | Project lead |
| `B-07` | `C-05` promises Crossover Points as **P10/P50/P90 ranges**. The methodology delivers three deterministic scenarios plus parameter-by-parameter sensitivity, and the challenges document (Challenge 3) records that no uncertainty-propagation method exists yet. Either a propagation procedure is built or the commitment is renegotiated. | `climate-risk-modeller` + `math-reviewer`; `consultant` if renegotiated |
| `B-08` | Whether the Month 12 dashboard (`D-08`) is rebuilt from `data/auto/output/` or resurrected from the archived web application. | Project lead |

---

## 7. Where the rest of the governance set lives

[`README.md`](README.md) indexes it. [`tracker.md`](tracker.md) holds all status; nothing in
this charter is updated to reflect progress.
