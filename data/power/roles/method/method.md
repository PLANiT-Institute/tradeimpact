# roles — who did what on each project, in which phase, with what share

## What this dataset is

The attribution table of the power case study. Attribution rule (project lead, 2026-09-05, refined
2026-09-07): **the trade impact is attributed to each role separately, the role and the share are
data columns, and the five phases are never pooled.**

| phase | role | what it means |
|---|---|---|
| development | `developer` | originated or developed the project (won the award, sponsored it) |
| construction | `epc_contractor`, `equipment_supplier` | built it, or supplied boiler / turbine / generator |
| investment | `equity_owner` | holds equity in the project company |
| operation | `om_contractor` | operates and maintains the plant |
| finance | `lender`, `eca_cover` | lent to it, or insured / guaranteed the debt |

A utility that both owns and runs a plant carries two rows, one in investment and one in
operation; the report's role matrix (Companies → Role matrix) is that table read across phases.
Equity is **investment**, not operation: the two are different responsibilities and are asked
about separately.

## The four sources, in the order a row wins

1. **`raw/project_roles.csv`** — the hand register, any role, one source link per row. Empty so
   far; a row here replaces every machine reading of the same company × plant × role.
2. **`raw/company_ir_roles.csv`** — read by hand from a company disclosure or project page that is
   **on disk**: `roles/method/company_ir_sources.csv` lists the pages,
   `script/power/roles/fetch_company_ir.py` saves each one under `raw/company_ir/` and records its
   URL, size and SHA-256 in `raw/company_ir/index.csv`. Every register row cites the
   `source_key` of the page that states the **role** and, separately, of the page that states the
   **share**, with the sentence quoted in `role_quote` / `share_quote`;
   `extract_company_ir_roles.py` rejects a row whose key is not in the index or whose URL does not
   match it. Tier A. The unit ids here also bring their units into scope in
   `projects/extract_gem_tracker.py` — which is how projects the tracker's owner field misses
   (Vung Ang 2, Jawa 9 and 10) enter the result set at all.
3. **`processed/gem_tracker_roles.csv`** — the tracker's own fields: `Owner(s)` and `Parent(s)`
   give `equity_owner` with the share it prints in brackets, `Operator(s)` gives `om_contractor`.
   Tier B, no transcription (`extract_gem_roles.py`).
4. **`processed/gem_wiki_roles.csv`** — construction, finance and ownership roles read by keyword
   from the GEM wiki pages. `fetch_gem_wiki.py` writes **one readable text file per page** under
   `raw/gem_wiki/` (a header with the page title, URL, API call and fetch date, then the wikitext
   as returned) plus `raw/gem_wiki/index.csv` with each page's SHA-256;
   `extract_wiki_roles.py` splits each page into sentences and reads a role wherever a sentence
   names an in-scope company together with the role's words. Sentences about intentions, protests,
   scandals, memoranda or quotations are skipped, and the developer role is read only from an
   explicit development statement. Every row carries the sentence and the page link. Tier C.

Both `index.csv` files are hash-recorded in [`../../registry/raw_files.csv`](../../registry/raw_files.csv)
and loaded into the database (`gem_wiki_index`, `company_ir_index`), so a reader can verify any
single page without a 400-row registry.

## The company register's fields

| field | note |
|---|---|
| company_id | key in `companies/method/companies.csv` |
| gem_unit_id / gem_location_id | at least one; a location row applies to every unit there |
| plant_name, country | for the reader |
| role | one of the seven above; the phase comes from `method/roles.csv` |
| share | fraction 0 < share ≤ 1, or blank when the page states none |
| from_year, to_year | when the role held, where the page says |
| role_as_stated | the company's own wording, verbatim |
| role_source_key / role_source_url / role_quote | the page that states the role, and its sentence |
| share_source_key / share_source_url / share_quote | the page that states the share, and its sentence |
| accessed_date, note | ISO date; the note carries what the page does *not* say |

## Reading rule for a sponsor's own wording

A company's history list saying it was *awarded* a project states a **development** role, not an
EPC contract and not an equity share: those need their own source. "Acquired equity and O&M
rights" states investment **and** operation. "Construction & Operation Project" states operation.
The verbatim wording stays in `role_as_stated` so the mapping can be checked.

## Status (2026-09-07)

26 register rows for 4 companies from 4 pages: KEPCO's own overseas history list (12 development
rows, Ilijan operation, Egbin investment and operation), the Vung Ang 2 shareholding from
BankTrack's project page (KEPCO 40 %, Mitsubishi 40 %, Chugoku 20 %; Mitsubishi's later 15 % sale
to Shikoku is not yet on file, so no Shikoku row), KEPCO's 15 % in Jawa 9 and 10 and Doosan's
construction of them from the GEM wiki station page, and Doosan's own release for Song Hau 1 as
sole main EPC contractor. Next: J-POWER, JERA, Marubeni, Sumitomo, Mitsui and the Korean gencos —
their project lists are image or script driven, so each row needs the project page or release that
states the fact.
