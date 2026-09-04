# Stages ST12–ST15 — methodology, tool, publication, new sectors

The output half of the engagement. None of these is live as of 2026-09-04, and none is started
early: the tool is built when there is a result to package, and a sector is onboarded when the
five-step process has worked once. Each stage's own process document is written at its stage
entry, not now — an unused procedure written months in advance is a procedure nobody follows.

---

## ST12 — Methodology maintenance

**Main goal.** Keep the whitepaper, the sector guidelines and the challenges document correct,
mutually consistent, and ahead of the code — the method is written down before it is implemented.

**Activity.** Revise `methodology/` in response to case-study evidence, peer review and Technical
Advisory Group input; convert each open challenge into either a stated rule with a bounded
residual error or a documented limitation; move an equation, its implementation and its test
together whenever any of the three changes; and date every rule change with its reason.

**Phases served.** PH2/1–6 (this stage is that phase's engine); PH1/3–4 (the rules ST08 and ST09
obey); PH4/1 (drafting the power and shipping guidelines); PH5/1–2.

**Consumes.** `methodology/TI_Whitepaper_v1.5.md`, `TI_Automotive_Technical_Guideline_v1.8.md`,
`TI_Methodological_Challenges_v1.md`; case-study evidence from ST08–ST10 and adequacy findings
from ST11; `SRC-25` (GHG Protocol Scope 3 standard and Chapter 11 technical guidance) and the
PCAF and Scope 4 literature in
[`../toolbox/references-and-archive.md`](../toolbox/references-and-archive.md); peer-review and TAG
feedback (`C-07`, `B-06`).

**Produces.** Revised `methodology/` documents with a version bump and change note; a resolution
record per challenge (rule, derivation, residual error — or a stated limitation); the `C-06`
comparative overview against Scope 3 Category 11, Scope 4 and PCAF.

**Owners.** `climate-risk-modeller` (owner), `doc-writer` and `writing-support-team` (drafting),
`math-reviewer` (derivations), `auditor` (whether the resolution answers the challenge),
`consultant` (anything the funder or the TAG sees).

**Stop when.** Each targeted challenge is closed with a rule or carried as a bounded limitation;
no equation lacks an implementation and a test; the comparative overview exists.

**Repeat when.** Peer-review or TAG feedback; a case-study finding that breaks a premise; a new
sector.

**Backward move.** A rule change invalidates every result computed under the old rule: ST08–ST10
re-run and their figures revert to `[compute]`.

---

## ST13 — Open-source tool and dashboard

**Main goal.** A model and a prototype dashboard that someone outside the team can run and read
(`D-06`, `D-08`), plus the Climate Arc integration specification (`D-05`).

**Activity.** Package the `script/auto/` pipeline for release under GPL v3 with tests and a
reproducible build; build the dashboard to present result, decomposition, scenario spread,
crossover, sensitivity and the data-quality declaration, reading only published outputs; and
specify the data contract Transition Arc would consume. Neither the tool nor the dashboard exists
yet, and `B-08` (rebuild from `data/auto/output/` or resurrect the archived web application) is
open — see [`../toolbox/references-and-archive.md`](../toolbox/references-and-archive.md) for what
the archive already provides.

**Phases served.** PH3/1–4; PH5/3.

**Consumes.** `ti_by_model.csv`, `ti_annual.csv`, `ti_withheld.csv` and the
`ti_country` / `ti_powertrain` / `ti_company` tables
(ST09, ST10); the licence verdicts from ST07; the verification verdicts from ST11.

**Produces.** The released repository and dashboard, and `D-05` as a specification document.

**Owners.** `developer` and `frontend-developer` (build), `visualizer` (figures and pages),
`web-app-engineer` if the archived application is resurrected, `provenance-auditor` (licence
clearance), `reviewer` and `tester` (gates), `consultant` (anything sent to Climate Arc).

**Stop when.** A clean clone reproduces the published outputs byte-identically; every figure
resolves to a `source_id` or an assumption id; the interface shows S1/S2/S3 together (`N-05`) and
a decomposition beside every headline (`N-06`); no source is redistributed without a licence
verdict.

**Repeat when.** A result set is refreshed; a licence changes; `B-08` resolves differently.

**Backward move.** A figure that cannot be traced is removed from the interface and returned to
its producing stage — never annotated into acceptability.

---

## ST14 — Publication and reporting

**Main goal.** Get the findings out in the two forms the charter requires: peer-reviewable papers
and openly published case studies, datasets, synthesis and policy brief.

**Activity.** Draft the case-study and methodology papers with their data-quality declarations;
publish the open dataset; write the synthesis (`D-07`) and the policy brief (`D-09`); prepare the
training and sharing materials (`C-10`). Interpretation language is checked every time:
associations and directions, never causal or predictive claims (`N-09`), and no netting language
anywhere near Scope 3 (`N-01`).

**Phases served.** PH1/7; PH2/7; PH4/2–3; PH5/1–4.

**Consumes.** Verified outputs from ST10 via ST11; the methodology set (ST12); the catalogue and
assumptions (ST07).

**Produces.** `D-01`, `D-02`, `D-03`, `D-04`, `D-07`, `D-09`, `D-10` — each with the guideline
§5.3 declaration and a retrievable locator recorded in the tracker.

**Owners.** `result-reporter` (analysis write-ups), `log-reporter` (the work record per unit),
`visualizer` (figures), `writing-support-team` and `doc-writer` (drafting), `consultant` (every
Climate Arc-facing draft — drafts only, never sent without the project lead's approval),
`provenance-auditor` (clearance before anything travels).

**Stop when.** No `[compute]` figure appears anywhere; every number traces; every claim states its
range and its tier; the funder-facing version is approved by the project lead.

**Repeat when.** A refreshed result changes a published figure — in which case the affected report
is rebuilt and, if it already reached Climate Arc, routed through `consultant` rather than
corrected silently.

**Backward move.** A reviewer objection that lands on the method returns to ST12, not to the
prose.

---

## ST15 — Sector onboarding

**Main goal.** Bring power generation and shipbuilding into the same five-step process without
re-inventing it, and without letting a sector-specific boundary problem hide inside a shared
pipeline.

**Activity.** Draft the sector Technical Guideline (Layer 1 anchor, Layer 2 parameters, lifetime
T, data sources), identify the sector's datasets in the same `raw` → `processed` shape, and run
ST01 through ST11 for that sector. Power substitutes the grid-intensity trajectory for the fleet
benchmark; shipping substitutes the IMO GHG Strategy Carbon Intensity Indicator trajectory for the
national NDC, which is a conceptual change rather than a parameter swap (challenges Challenges 5
and 6).

**Phases served.** PH4/1–4; PH3/2 (`D-08` needs three sectors); PH5/1–2.

**Consumes.** The sector firm selection from ST01; the archived power and shipping source snapshots
(`SRC-24`: JERA, KOEN, MOL) as prior work; challenges Challenges 5 and 6.

**Produces.** A sector Technical Guideline per sector, and the sector's dataset directories,
processed tables and results through ST10.

**Owners.** `climate-risk-modeller` (sector method), `energy-finance-team` (power sector),
`data-collector`, `developer`, `math-reviewer`, `auditor`.

**Stop when.** The sector's guideline exists, its results pass ST11, and its structural challenge
is either resolved with a stated rule or carried as a bounded limitation.

**Repeat when.** A third sector is added — which `C-11` bounds at three, so this is a change-control
question rather than a scheduling one.

**Backward move.** If a sector's operating-country boundary cannot be defined defensibly, the work
returns to PH2: the boundary is a whitepaper premise, not a sector detail.
