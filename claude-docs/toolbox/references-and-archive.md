# References, methodology documents and reusable prior work

Pointers only. Nothing here restates a method or a number; each entry says what the document is
and what it is used for.

## 1. Methodology truth source (in repository)

| Document | Governs |
|---|---|
[`methodology/TI_Whitepaper_v1.6.md`](../../methodology/TI_Whitepaper_v1.6.md) | The framework: Layer 1 and Layer 2 definitions, the equation set (§3.1–§3.8), boundary conditions (§4), the three-tier data hierarchy and the no-netting rule (§5), required outputs (§7), limitations (§9) |
[`methodology/TI_Automotive_Technical_Guideline_v1.9.md`](../../methodology/TI_Automotive_Technical_Guideline_v1.9.md) | Automotive implementation: Layer 1 Methods A/B/C (§2.3), Layer 2 by powertrain (§3.3–§3.5), scenario architecture (§4.7), reporting and the data-quality declaration (§5), method and parameter selection (§6–§7), Appendices A–G |
[`methodology/TI_Methodological_Challenges_v1.md`](../../methodology/TI_Methodological_Challenges_v1.md) | The open questions, each with a resolution criterion and the case study that tests it — the work programme for PH2 |

## 2. Dataset method files (in repository)

The home for each dataset's sources, fields, raw-file hashes and rules. Linked from
[`../stages/st02-06-datasets.md`](../stages/st02-06-datasets.md); consolidated column view in
[`data-schema.md`](data-schema.md).

- [`data/auto/sales/method/method.md`](../../data/auto/sales/method/method.md) (plus the
  `kia_labels.csv` and `hyundai_plant_codes.csv` mapping tables beside it)
- [`data/auto/country_emissions/method/method.md`](../../data/auto/country_emissions/method/method.md)
- [`data/auto/emission_targets/method/method.md`](../../data/auto/emission_targets/method/method.md)
- [`data/auto/vehicle_usage/method/method.md`](../../data/auto/vehicle_usage/method/method.md)
- [`data/auto/vehicle_technology/method/method.md`](../../data/auto/vehicle_technology/method/method.md)
- [`script/auto/README.md`](../../script/auto/README.md) — the script layout and coding conventions

## 3. Key reference documents (Google Drive)

Folder: `12_Finance/Grant/Climate Arc/2026/Trade/References/`. Held locally as PDFs; each is a
primary document and is read as one — a figure taken from a summary of these is not evidence.

| Document | Used for | Source id |
|---|---|---|
| `IEA_2024_WEO_Full_Report.pdf` (and the executive summary) | STEPS and NZE transport and electricity pathways — S1 and S3 rates | `SRC-15` |
| `IEA_2024_Global_EV_Outlook.pdf` | Scenario-consistent EV penetration for new-entrant intensity | `SRC-16` |
| `ICCT_2018_LabToRoad.pdf`, `ICCT_2024_realworld_CO2_Europe_Jan2024.pdf` | Real-world correction factors by powertrain | `SRC-17` |
| `ICCT_2024_EU_vehicle_market_statistics_pocketbook.pdf` | EU fleet and market structure cross-check | `SRC-18` |
| `TE_2023_PHEVs_2_report.pdf` | Real-world PHEV utility factors | `SRC-19` |
| `Ember_2024_Global_Electricity_Review.pdf` | Country grid carbon intensity | `SRC-11` |
| `GHGProtocol_2011_Corporate_Value_Chain_Scope3_Standard.pdf`, `GHGProtocol_2013_Scope3_Technical_Guidance.pdf`, `Chapter11.pdf`, `Scope 2 Guidance.pdf` | The Scope 3 Category 11 boundary TI sits beside, and the `C-06` comparative overview | `SRC-25` |
| `Seto_et_al_2016_carbon_lockin_AnnualReview.pdf`, `Tong_2019_committed_emissions_NSF_accepted.pdf` | The carbon lock-in and committed-emissions literature the framework's premise rests on | — |
| `TI_PeerReview_v1.5_v1.8.docx`, `TI_Methodological_Issues_Balanced_Assessment.docx` | Review feedback feeding PH2 | — |

Also in the Drive engagement folder: `Arc_Technical_Review/` (the technical specification prepared
for Climate Arc), `Arc_Trade_Data/Auto/` (the two IR workbooks as received), and `Proposal/` (the
governing document — see [`../charter.md`](../charter.md)).

## 4. Reusable prior work in `archive/`

The previous full application build. **Read-only prior work products**, not current deliverables:
phases may reuse its equations, source snapshots and published baselines, but nothing in it counts
toward a charter deliverable and nothing in it is maintained.

| Asset | Path | Reuse |
|---|---|---|
| Source register | `archive/data/published/sources.json` | 26 registered sources with publisher, licence, accessed date, query hash and snapshot hash — the seed for [`catalogue.md`](catalogue.md) (`SRC-24`) |
| Published EU27 2024 lifetime results | `archive/data/published/lifetime_results.json` | The regression baseline for the same boundary the new pipeline targets — ST11 check 3 |
| Destination inputs snapshot | `archive/data-pipeline/source-snapshots/destination_eu27_inputs.json` | Already copied into `data/auto/vehicle_usage/raw/` (`SRC-20`, `A-07`) |
| Other sector snapshots | same directory: `jera_japan_fy2024.json`, `koen_korea_2024.json`, `mol_global_fy2024.json` | Starting points for PH4 power and shipbuilding onboarding |
| Calculation engine | `archive/ti-framework/ti_framework/` with 101 test functions | Equation implementations and crossover closed forms to port rather than re-derive; conflict decisions in `archive/ti-framework/NOTES.md` |
| Theory-to-code contract | `archive/theory/SYNC.md` | The model for anchoring each equation to its implementation and its test; adopting an equivalent for `script/auto/` is a PH3 objective |
| Web application and MCP server | `archive/web/`, `archive/mcp-server/` | Candidate basis for the `D-08` dashboard if `B-08` resolves that way |

## 5. Citation rule

Author, title, publisher, date and a retrievable locator, for every citation. Preference order:
primary source → official statistical publication → institutional report → anything else, which is
context and never evidence. Full rule in [`../process/general.md`](../process/general.md) §3.
