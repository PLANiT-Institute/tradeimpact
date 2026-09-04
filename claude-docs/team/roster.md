# Team roster

Which agent owns which stage, and which review chain it sits in. No project-specific agent has
been created: every capability the stages need is covered by a user-level pack agent, and a new
agent that overlaps an existing one splits the knowledge across two definitions and rots both.

**Roster refreshed 2026-09-04** against the pack update that added four Tier 4 roles. Three of them
close gaps this project named itself:

- `ir-disclosure-analyst` — this roster had rejected the role on 2026-09-03 as covered by
  `data-collector` + `source-reconciliation-analyst`. Every stall in PH1 since was sales data on the
  wrong basis: the Hyundai IR file is plant-side (US-built cars only), the Kia file reports regions
  for Europe and a half year for the US, neither splits powertrains, and the Australian cohort does
  not exist in any release. The rejection is withdrawn. It owns the **reporting-basis map** across
  the four exporters and the **build-vs-buy verdict** on a licensed dataset (S&P Global Mobility,
  MarkLines, JATO, Dataforce) that would give sales by market × model × powertrain directly and
  remove the hand-gathered IR workbooks from the critical path. Financial IR is out of scope — the
  framework never touches company financials.
- `transport-emissions-reviewer` — needed **before publication, not full time**. The open items from
  the independent review are all methodology calls a transport-emissions specialist should settle:
  the segment ratio (decisive for the US sign), the S2 grid rule where a target is already met,
  real-world factors for hybrids and for EPA-cycle values, lifetime construction, and the
  P10/P50/P90 crossover the proposal promised (`C-05`, `B-07`). It gates ST14.
- `esg-disclosure-analyst` — needed **at the white-paper and peer-review stage**, after the case
  study is defensible. The grant's stated targets are investors, GHG Protocol and PCAF; positioning
  TI against Scope 3 Category 11 and avoided-emissions guidance (`C-06`, `N-01`, `X-05`) and writing
  `D-09` so a standard-setter can act on it is where this role earns its place.
- `policy-analyst` — the NDC anchors that decide S2 (`B-04`: the US has no NDC in force) are target
  anatomy — base year, gas basket, sector boundary, conditionality, version — and the decision rule
  for a market with no target is a policy call, not a modelling one. It owns that register and the
  storyline for `D-09`.

## Owners by stage

| Stage | Owner | Supporting | Review chain |
|---|---|---|---|
| ST01 targets | `consultant` (firm scope), `climate-risk-modeller` (market criteria) | `research-director`, `policy-analyst` (which markets have a target in force) | `auditor` |
| ST02 `sales` | `ir-disclosure-analyst` (reporting basis, crosswalk, build-vs-buy), then `data-collector` | `developer`, `source-reconciliation-analyst` | `tester` → `auditor` |
| ST03 `country_emissions` | `data-collector` | `developer`, `source-reconciliation-analyst` | `tester` → `auditor` |
| ST04 `emission_targets` | `policy-analyst` (target anatomy and the no-target rule), `climate-risk-modeller` (pathway construction) | `data-collector`, `developer` | `math-reviewer` → `auditor` |
| ST05 `vehicle_usage` | `data-collector` | `developer`, `data-scientist` | `math-reviewer` → `auditor` |
| ST06 `vehicle_technology` | `data-collector` | `developer`, `data-scientist`, `ir-disclosure-analyst` (nameplate ↔ certification crosswalk) | `math-reviewer` → `auditor` |
| ST07 provenance | `provenance-auditor` | `source-reconciliation-analyst`, `data-collector` | `auditor` |
| ST08 benchmark | `climate-risk-modeller` | `developer` | `math-reviewer` → `auditor` |
| ST09 impact | `data-scientist` | `developer`, `climate-risk-modeller` | `math-reviewer` → `tester` → `auditor` |
| ST10 aggregation | `data-scientist` | `developer` | `math-reviewer` → `auditor` |
| ST11 verification | `auditor` | `math-reviewer`, `tester`, `provenance-auditor`, `reviewer`, `transport-emissions-reviewer` (methodology register) | — (this stage *is* the chain) |
| ST12 methodology | `climate-risk-modeller` | `doc-writer`, `writing-support-team`, `esg-disclosure-analyst` (the `C-06` comparative overview against Scope 3 Cat. 11, Scope 4 and PCAF) | `transport-emissions-reviewer` → `math-reviewer` → `auditor` |
| ST13 tool and dashboard | `developer` | `frontend-developer`, `visualizer`, `web-app-engineer` | `reviewer` → `tester` → `provenance-auditor` |
| ST14 publication | `result-reporter` (analysis), `log-reporter` (work record) | `visualizer`, `writing-support-team`, `doc-writer`, `policy-analyst` (`D-09` storyline), `esg-disclosure-analyst` (`D-09` standard-setter text) | `transport-emissions-reviewer` (gate) → `provenance-auditor` → `consultant` |
| ST15 sector onboarding | `climate-risk-modeller` | `energy-finance-team`, `data-collector`, `developer` | `math-reviewer` → `auditor` |

## Standing roles

| Role | Agent | Boundary |
|---|---|---|
| Governance | `research-director` | Owns `claude-docs/`. Designs and judges; never produces a figure and never talks to the client |
| Client-facing | `consultant` | The **only** Climate Arc-facing role. Drafts only; never sends, never accepts scope. Every request outside the charter goes to change control |
| Process and dashboards | `report-manager` | Owns `claude-docs/dashboard/`. Regenerates it after every tracking pass |
| Reporting | `log-reporter`, `result-reporter` | One writes what was done and what failed; the other writes what was found, as an article. Never merged |

## Parallelism

- **Independent now, launch concurrently:** ST03, ST04 and ST05 (three different source families,
  no shared inputs) and ST02 with ST06 (which share the EEA snapshots but write different tables).
- **Gated, never parallelised across the gate:** ST08 waits on ST03, ST04 and ST05; ST09 waits on
  ST08 plus ST02 and ST06; ST10 waits on ST09; ST13 and ST14 wait on ST11's verdicts.
- **Sequenced by design, not by capacity:** PH4's sector onboarding waits until the five-step
  process has worked once in PH1. Two sectors debugged at once is two sectors with no baseline.

## Unowned work

None at current scope. Two capabilities will need an owner before their phase opens, and are named
here so they are decisions rather than surprises:

| Capability | Needed by | Candidate |
|---|---|---|
| Uncertainty propagation to a P10/P50/P90 band (`C-05`, `B-07`) | PH2 objective 3 | `transport-emissions-reviewer` specifies the propagation design (distributions, correlation, seed); `data-scientist` with `math-reviewer` implement it; `consultant` if the wording is renegotiated |
| Transition Arc integration specification (`D-05`) | PH3 objective 3 | `developer` drafting, `consultant` owning the interface with Climate Arc |
| Licensed sales dataset — licence, budget, lead time (if `ir-disclosure-analyst` returns **buy**) | PH1 US/AU cohorts | project lead decides; `consultant` raises it with Climate Arc if it touches the data-sharing terms; `provenance-auditor` on the republication grain |
