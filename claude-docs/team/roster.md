# Team roster

Which agent owns which stage, and which review chain it sits in. No project-specific agent has
been created: every capability the stages need is covered by an existing template agent, and a new
agent that overlaps an existing one splits the knowledge across two definitions and rots both.

Considered and rejected: an `ir-disclosure-analyst` for the Korean-language IR workbooks —
`data-collector` already owns retrieval and `source-reconciliation-analyst` already owns the basis
and label conflicts those workbooks create, which is the whole of the work.

## Owners by stage

| Stage | Owner | Supporting | Review chain |
|---|---|---|---|
| ST01 targets | `consultant` (firm scope), `climate-risk-modeller` (market criteria) | `research-director` | `auditor` |
| ST02 `sales` | `data-collector` | `developer`, `source-reconciliation-analyst` | `tester` → `auditor` |
| ST03 `country_emissions` | `data-collector` | `developer`, `source-reconciliation-analyst` | `tester` → `auditor` |
| ST04 `emission_targets` | `climate-risk-modeller` | `data-collector`, `developer` | `math-reviewer` → `auditor` |
| ST05 `vehicle_usage` | `data-collector` | `developer`, `data-scientist` | `math-reviewer` → `auditor` |
| ST06 `vehicle_technology` | `data-collector` | `developer`, `data-scientist` | `math-reviewer` → `auditor` |
| ST07 provenance | `provenance-auditor` | `source-reconciliation-analyst`, `data-collector` | `auditor` |
| ST08 benchmark | `climate-risk-modeller` | `developer` | `math-reviewer` → `auditor` |
| ST09 impact | `data-scientist` | `developer`, `climate-risk-modeller` | `math-reviewer` → `tester` → `auditor` |
| ST10 aggregation | `data-scientist` | `developer` | `math-reviewer` → `auditor` |
| ST11 verification | `auditor` | `math-reviewer`, `tester`, `provenance-auditor`, `reviewer` | — (this stage *is* the chain) |
| ST12 methodology | `climate-risk-modeller` | `doc-writer`, `writing-support-team` | `math-reviewer` → `auditor` |
| ST13 tool and dashboard | `developer` | `frontend-developer`, `visualizer`, `web-app-engineer` | `reviewer` → `tester` → `provenance-auditor` |
| ST14 publication | `result-reporter` (analysis), `log-reporter` (work record) | `visualizer`, `writing-support-team`, `doc-writer` | `provenance-auditor` → `consultant` |
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
| Uncertainty propagation to a P10/P50/P90 band (`C-05`, `B-07`) | PH2 objective 3 | `data-scientist` with `math-reviewer`; escalate if a Monte Carlo design is required |
| Transition Arc integration specification (`D-05`) | PH3 objective 3 | `developer` drafting, `consultant` owning the interface with Climate Arc |
