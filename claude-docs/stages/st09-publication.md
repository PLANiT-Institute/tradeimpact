# ST09 — Publication

## Main goal

Put a verified result in front of a reader with everything the framework requires attached to it,
and nothing it forbids.

## Activity

Publish the result through the web application, the MCP server, the deck, and any written report.
Attach the data-quality declaration, the S1/S2/S3 band, both decompositions, the sensitivity ranges,
the target-hierarchy level and its fallback disclosure, and the withheld list with unit counts.
Derive every status string from the dataset. Route anything client-facing through `consultant` and
anything travelling externally through `provenance-auditor` for licence and trace clearance.

## Phases served

| Phase | Objective | How this stage evidences it |
|---|---|---|
| PH1 | 4 | The published web report, the deck, and the declaration rendered from the engine payload |
| PH3 | all | Republication of the closed outputs, with the reissue routed through `consultant` |
| PH4 | 3, 4, 5 | The new sector's report and the cross-sector view |

## Inputs

Consumes: ST05 outputs, ST06 gate verdicts, ST07/ST08 record and dashboard, the presentation rules,
the licence terms in [`../toolbox/data/register.md`](../toolbox/data/register.md).

## Outputs

Produces: the `web/` pages, the MCP tool responses, the deck, and written reports. Client-facing
drafts land in [`../engagement/`](../engagement/README.md) and are never sent from here.

## Methodology

[`../toolbox/methods/presentation-rules.md`](../toolbox/methods/presentation-rules.md).
Governing text: Whitepaper §5.2 (`W-15`), §7 (`W-18`, `W-19`), §5.3 (`W-16`), Guideline §5
(`G-08`…`G-10`), `C-03`, `C-04`, `C-09`.

## Owner agents

Owner `web-app-engineer` (web), `mcp-server-engineer` (MCP), `visualizer` (figures and deck),
`result-reporter` and `doc-writer` (written report), `log-reporter` (the work record).
Review chain: `reviewer` → `auditor` → `provenance-auditor`; `consultant` for anything a client
reads, and only as a draft.

## When to stop

- Nothing published rests on an unverified figure.
- The declaration, both decompositions, the scenario band and the withheld list are present on
  every surface that shows a headline.
- No S2-alone number anywhere (`G-08`); no netting or offset language anywhere (`W-16`); no
  avoided-emissions framing (`M-07`).
- Every state string derived from the dataset — checked by scanning the rendered output, not the
  source.
- Licence and attribution terms satisfied for every source shown.

## When to repeat

- Any figure changes, including a refresh that changes only a citation.
- A method or assumption changes such that a published caveat is no longer accurate.
- A reader-facing framing changes — route through `consultant` first.

## Backward moves

- A rendered page contradicting its own dataset → back to ST08/ST09 to derive the label from data.
  This has happened three times in this project's history; treat a hand-written status sentence as a
  defect on sight.
- A number already in a client's hands that later moves → `consultant` matter, logged in
  `../log/decisions.md`. Never let a published number change silently.
- A figure without a register row or an assumption id → back to ST02; it does not exist.

## Process

[`../process/st09-publication.md`](../process/st09-publication.md)
