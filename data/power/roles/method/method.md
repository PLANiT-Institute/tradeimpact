# roles — who did what on each project, in which phase, with what share

## What this dataset is

The attribution table of the power case study. The tracker says who owns a unit; it does not say
who built it, who supplied the boiler and turbine, who operates it, or who financed it. This
register records, per company × unit (or plant) × role, the phase the role belongs to and the
share the company carried, each with the page it was read from.

Attribution rule (project lead, 2026-09-05): **the trade impact is attributed to each role
separately, and the share and the role are data columns, so the weighting can be changed later
without re-collecting anything.** The model therefore reports, per role row, the unit's full
trade impact and the share-weighted figure side by side, and never adds rows of different roles
into one company total.

## Raw file — HAND-GATHERED

`raw/project_roles.csv` — header-only until filled (reported as pending, not fatal: the pipeline
runs on the tracker's equity rows meanwhile). One row per company × unit × role.

| field | note |
|---|---|
| company_id | key in `companies/method/companies.csv`; unknown ids are rejected |
| gem_unit_id | the tracker's unit / phase id; leave blank when the role is plant-wide |
| gem_location_id | the tracker's location id; a plant-wide row applies to every unit at the location |
| plant_name, country | for the reader; the join is on the ids |
| role | one of `method/roles.csv`: developer, equity_owner, epc_contractor, equipment_supplier, om_contractor, lender, eca_cover |
| phase | must equal the role's phase in `roles.csv`: development, construction, operation, finance |
| share | fraction 0 < share ≤ 1, or blank when the source does not state it |
| share_basis | must equal the role's basis in `roles.csv` (equity_share, contract_share, scope_share, debt_share, cover_share, none) |
| from_year, to_year | years the role held (equity can be sold; an EPC ends at commissioning); blank = whole life |
| source_url | the page the row was read from: the GEM wiki page, the company's release, the lender's project page. Required. |
| source_note | what the page says, in English, briefly |
| accessed_date | ISO date |

Every distinct source also needs a row in [`../../registry/sources.csv`](../../registry/sources.csv)
with `how_obtained = read by hand`. Where a fact is known only from a press report rather than a
company or lender document, say so in `source_note`; the tier of a share read from a press report
is C, from the company's own release A.

## Equity rows read from the tracker

The tracker writes ownership with shares — `Marubeni Corp [50.0%]; Korea Electric Power Corp
[50.0%]` in `Owner(s)` and `Parent(s)` — so the **equity_owner** role needs no hand transcription:
`script/power/roles/extract_gem_ownership.py` writes `processed/gem_ownership.csv`, one row per
company × unit with the level it was read at (owner or parent), the entity as written, the share
as a fraction (blank where the tracker states none) and the unit's wiki page as source. Tier B: a
third-party compilation of company disclosures. The attribution step merges it with the hand
register; where the register has an equity_owner row for the same company and unit, the register
wins. Construction, equipment, O&M and finance roles are not in the tracker and remain hand rows.

## Processed output

`processed/project_roles.csv` — the validated register joined to the company's country, name and
type, by `script/power/roles/extract_roles.py`. Validation failures stop the extractor and name
the row.

## Rules

- One company can hold several roles on one unit (Doosan as EPC lead and boiler supplier; a
  trading house as developer then equity owner). Each is its own row.
- A consortium EPC is one row per member with the member's `contract_share`; where the split is
  unpublished, shares are left blank and the full figure is what the model reports for the row.
- Roles are never inferred from `companies.type`; an EPC group that also took equity has an
  `equity_owner` row only if a source says so.
