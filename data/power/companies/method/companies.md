# companies — the Korean and Japanese power companies in scope

## What this table is

`companies.csv` is the scoping list for the power case study: every Korean and Japanese company
whose overseas power projects the study attributes a trade impact to. It is authored in the
repository (a method table, not a fetched dataset) and is the join key for two things:

- matching Global Energy Monitor owner and parent strings (`gem_owner_pattern`, a case-
  insensitive regular expression applied to the tracker's Owner and Parent fields), which is how
  a project enters `projects/processed/projects_gem.csv` when no role row names it yet;
- the `company_id` in the hand-gathered role register `roles/raw/project_roles.csv`.

## Fields

| field | note |
|---|---|
| company_id | lowercase key used everywhere else |
| name_en | English name as the company writes it |
| country | HQ, ISO 3166-1 alpha-2 (`KR`, `JP`) |
| type | `utility`, `genco`, `trading_house`, `developer`, `epc_contractor`, `equipment_supplier`, `eca` |
| gem_owner_pattern | regex for the tracker's Owner / Parent text; `(?! &)` excludes a longer name |
| in_scope | `yes` to attribute; a `no` row is kept as a documented exclusion |
| note | representative overseas projects, from public knowledge; not a data row and not cited |

## Rules

- `type` describes the company, not its role in a project: a trading house can be an equity
  owner in one project and an EPC lead in another. The role, the phase and the share are
  recorded per project in the role register, never inferred from `type`.
- A company is added here before any role row names it; the roles extractor rejects an unknown
  `company_id`.
- The `note` column is orientation for the person filling the role register. Every project it
  mentions still needs a sourced role row before it counts.

## Status (2026-09-05)

First pass authored from the project lead's scoping conversation: KEPCO and its six generation
subsidiaries, three Korean developers, eight Korean EPC or equipment groups and the two Korean
export credit agencies; seven Japanese trading houses, ten Japanese utilities, five Japanese
equipment or EPC groups and the two Japanese export credit agencies. Regex patterns are first
guesses against GEM naming and are corrected when the tracker is on disk.
