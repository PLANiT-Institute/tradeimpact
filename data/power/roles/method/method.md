# roles — who did what on each project, in which phase, with what share

## What this dataset is

The attribution table of the power case study. Attribution rule (project lead, 2026-09-05, refined
2026-09-07): **the trade impact is attributed to each role separately, the role and the share are
data columns, and the five phases are never pooled.**

Roles carry **three levels**, all of them in `method/roles.csv`:

| level | column | what it is |
|---|---|---|
| phase | `phase` | when in the project's life the company acted |
| tier 1 | `role_tier1` | the group the unit is **attributed** at |
| tier 2 | `role_tier2` | the scope the source actually states |

| phase | role_tier1 | role_tier2 |
|---|---|---|
| development | `developer` | `sponsor_award`, `project_development` |
| construction | `epc_contractor` | `epc_lead`, `epc_consortium_member`, `epc_civil_works`, `epc_port_works`, `epc_balance_of_plant`, `epc_unspecified` |
| construction | `equipment_supplier` | `boiler_supply`, `steam_turbine_supply`, `gas_turbine_supply`, `generator_supply`, `equipment_unspecified` |
| investment | `equity_owner` | `equity_direct`, `equity_parent`, `equity_unspecified` |
| construction | `owners_engineer` | `construction_supervision`, `technical_advisory` |
| construction | `commissioning_contractor` | `commissioning_service` |
| operation | `om_contractor` | `om_contract`, `maintenance_support`, `operator_of_record` |
| finance | `lender` | `project_loan`, `buyers_credit`, `loan_unspecified` |
| finance | `eca_cover` | `insurance_cover`, `guarantee`, `cover_unspecified` |

**Attribution is at tier 1.** A company holds one `epc_contractor` role on a unit even where its
own release names two scopes — Sumitomo's civil works and its port works at Matarbari — so the
unit's figure is never counted twice against the same company and role. The scopes stay visible:
`role_tier2` carries the most specific one on file and `role_tier2_all` every scope that source
states, pipe-separated. A `*_unspecified` key means the source names the tier-1 role without
saying which scope, which is what a keyword read of a wiki sentence can support; a specific key
always outranks it when both are on file.

A utility that both owns and runs a plant carries two rows, one in investment and one in
operation; the report's role matrix (Companies → Role matrix) is that table read across phases.
Equity is **investment**, not operation: the two are different responsibilities and are asked
about separately.

**A share is never assumed.** Where the source states no percentage the `share` column is blank
and the share-weighted figure is blank beside a full figure that still stands.

## The four sources, in the order a row wins

1. **`raw/project_roles.csv`** — the hand register, any role, one source link per row. Empty so
   far; a row here replaces every machine reading of the same company × plant × tier-1 role.
2. **`raw/company_ir_roles.csv`** — read by hand from a company disclosure or project page that is
   **on disk**: `roles/method/company_ir_sources.csv` lists the pages,
   `script/power/roles/fetch_company_ir.py` saves each one under `raw/company_ir/` and records its
   URL, size and SHA-256 in `raw/company_ir/index.csv`. Every register row cites the
   `source_key` of the page that states the **role** and, separately, of the page that states the
   **share**, with the sentence quoted in `role_quote` / `share_quote`;
   `extract_company_ir_roles.py` rejects a row whose key is not in the index or whose URL does not
   match it, **and checks the quote against the page**: every substantial fragment of
   `role_quote` and `share_quote` has to appear in the saved file's own text, so a sentence cannot
   be paraphrased into the register or invented (that check caught 14 paraphrased quotes on its
   first run and they were replaced with the pages' own words). Rows are keyed to **units, never
   to a station**: a company page states a role on a named project — "Nghi Son II", "Matarbari
   Phase I", "Mong Duong 2", "Tanjung Jati B units 3 and 4" — and a station usually carries phases
   that project never touched. Tier A. The unit ids here also bring their units into scope in
   `projects/extract_gem_tracker.py` — which is how projects the tracker's owner field misses
   (Vung Ang 2, Jawa 9 and 10) enter the result set at all.
3. **`processed/gem_tracker_roles.csv`** — the tracker's own fields: `Owner(s)` gives
   `equity_direct` and `Parent(s)` gives `equity_parent`, each with the share printed in brackets;
   `Operator(s)` gives `operator_of_record`. Tier B, no transcription (`extract_gem_roles.py`).
4. **`processed/gem_wiki_roles.csv`** — construction, finance and ownership roles read by keyword
   from the GEM wiki pages. `fetch_gem_wiki.py` writes **one readable text file per page** under
   `raw/gem_wiki/` (a header with the page title, URL, API call and fetch date, then the wikitext
   as returned) plus `raw/gem_wiki/index.csv` with each page's SHA-256;
   `extract_wiki_roles.py` splits each page into sentences and reads a role wherever a sentence
   names an in-scope company together with the role's words. Sentences about intentions, protests,
   scandals, memoranda or quotations are skipped, and the developer role is read only from an
   explicit development statement. A sentence supports the tier-1 role only, so every row here
   carries a `*_unspecified` tier-2 key. Every row carries the sentence and the page link. Tier C.

Both `index.csv` files are hash-recorded in [`../../registry/raw_files.csv`](../../registry/raw_files.csv)
and loaded into the database (`gem_wiki_index`, `company_ir_index`), so a reader can verify any
single page without a 400-row registry.

## The company register's fields

| field | note |
|---|---|
| company_id | key in `companies/method/companies.csv` |
| gem_unit_id | required, one row per unit the cited project covers; a station-level key would attribute units the source says nothing about |
| plant_name, country | for the reader |
| role_tier2 | one of the tier-2 keys above; `role_tier1` and `phase` come from `method/roles.csv` |
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

165 register rows for 23 companies, citing 39 of the 45 pages on disk. By company: KEPCO 35,
Toshiba 17, Doosan 15, Sumitomo 14, IHI 14, KOMIPO 9, Mitsui 8, MHI 8, Marubeni 5, KOSPO 5,
Chugoku 4, POSCO International 4, Daewoo E&C 4, KEXIM 4, JBIC 3, Hyundai E&C 3, Mitsubishi
Corporation 2, Kansai 2, NEXI 2, Hyundai Engineering 2, J-POWER 2, Samsung C&T 2, JERA 1.

The projects the register now covers: Vung Ang 2, Nghi Son 1 and 2, Van Phong 1, Mong Duong 2,
Vinh Tan 4 and its extension, Song Hau 1, Jawa 9 and 10, Cirebon 1 and 2, Tanjung Jati B units
1-4 and 5-6, Jimah East, Safi, Jorf Lasfar 5-6, Matarbari Phase I, Egbin, Ilijan, Al Qatrana,
Rabigh, Shuweihat S3, Pulau Indah, Naga (Cebu), Niles and Trumbull.

Facts the desk research could **not** source on a company page, recorded here so nobody fills
them in from memory: Doosan has no page of its own naming Vung Ang 2 at all, and the EPC scope
split between Doosan and Samsung C&T is stated nowhere; Sumitomo's and United Tractors'
percentages in Tanjung Jati B units 5-6; the boiler and turbine suppliers for those units;
Marubeni's percentage in Cirebon 2; KOMIPO's percentage in Cirebon 1 (it publishes the USD 70
million invested instead); KEPCO's current percentage in Nghi Son 2 after Tohoku entered; the
Cirebon 1 EPC contractor; and any equipment supplier for Nghi Son 1. Two corrections came out of
the same research: Tohoku Electric's 10 % is in Nghi Son **2**, not Nghi Son 1, and Doosan's Jawa
9-10 consortium partner is Indonesia's Hutama Karya, not a Korean contractor.

Vintage conflict left open: the Vung Ang 2 project company's own page states Mitsubishi 40 %,
KEPCO 40 %, Chugoku 20 % at the One Energy Asia holding level, while the BankTrack page already
on file records a later 15 % Mitsubishi-to-Shikoku sale. The project company's page is undated,
so neither is demonstrably the newer statement; both stay on file and the register carries the
BankTrack shares with that note.

`raw/project_roles.csv`, the free-form hand register, is still header-only: every role now on
file came from a page.

## Fetching notes

Three Korean utility sites refuse Python's TLS handshake or serve an incomplete certificate chain
(`kospo.co.kr`, `komipo.co.kr`). `fetch_company_ir.py` falls back to the system `curl`, which
still verifies the certificate against the operating system's trust store, and records which
transport was used in `fetched_with`. Verification is never turned off.
