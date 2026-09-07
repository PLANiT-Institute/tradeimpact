# Trade impact of the power trade — method, rules and status

The power case study applies the Trade Impact (TI) framework to the overseas power projects of
Korean and Japanese companies: the generating units they own, built, supplied or financed in
other countries, measured year by year against the grid they feed. The mathematics is in
[`methodology/TI_Power_Technical_Guideline_v1.0.md`](../../../methodology/TI_Power_Technical_Guideline_v1.0.md);
this note is the operational record of how the pipeline under `script/power/` implements it and
which decisions were taken. Every dataset has its own `method/method.md` beside its raw and
processed files; this document links them and does not repeat them.

## Unit of analysis

One **generating unit** (or project phase) in one **destination country**, as recorded in the
Global Energy Monitor tracker ([`projects`](../projects/method/method.md)), with a **role** held
by a company ([`roles`](../roles/method/method.md)). The result set therefore has two grains:

- `ti_power_by_unit.csv` — unit × scenario: what the unit adds to or avoids from its
  destination's inventory over its life, with latitude and longitude, so the map is unit by unit.
- `ti_power_by_role.csv` — company × tier-1 role × unit × scenario: the same unit result
  attributed to each company that held a role on it, with the tier-2 scope the source states;
  `ti_power_company.csv` sums it per company × tier-1 role.

## Decisions (project lead, 2026-09-05)

1. **Attribution is per role, never pooled, in five separate phases.** A unit's trade impact is
   attributed separately to each role, and the five phases are kept apart:
   **development** (developer), **construction** (EPC contractor, equipment supplier),
   **investment** (equity owner), **operation** (O&M contractor) and **finance** (lender, ECA
   cover). Equity is investment, not operation: a utility that both owns and runs a plant carries
   two rows, one in each phase (project lead, 2026-09-07). Roles carry three levels: the phase,
   the **tier-1 role** the unit is attributed at, and the **tier-2 scope** as the source states it
   (`epc_lead`, `epc_civil_works`, `boiler_supply`, `equity_direct`, `buyers_credit`, … or a
   `*_unspecified` key where the source names the group only). Attribution happens at tier 1, so a
   contractor whose release names two scopes on one unit carries that unit once with both scopes
   named beside it in `role_tier2_all` (project lead, 2026-09-07). The register carries the role,
   the phase and the share as data columns; the model reports each role row twice, the unit's full
   figure and the share-weighted figure, and never adds rows of different roles into one company
   total, so the weighting can be revisited later without re-collecting. A blank share yields a
   blank weighted figure, not an assumed one. The report's Companies → Role matrix is this table
   read across the phases.
2. **Emission factor: national first, IPCC otherwise.** A unit's CO2 per unit of fuel is the
   destination country's own fuel-specific factor where one is on file
   ([`emission_factors`](../emission_factors/method/method.md), tier A) and the IPCC 2006 default
   otherwise (tier C, with the IPCC bounds carried for the sensitivity). Heat rate and capacity
   factor: the tracker's unit-level estimate where published (tier B), the technology default
   otherwise (tier C). Every choice is a column on the result row.
3. **Roles come from four sources, in order of standing** ([`roles`](../roles/method/method.md)):
   the hand register; the companies' own disclosures and project pages, each row citing the page
   on disk that states the role and, separately, the page that states the share, with the sentence
   quoted (tier A); the tracker's own `Owner`, `Parent` and `Operator` fields (tier B); and the GEM
   wiki sentences read by keyword (tier C, and always a `*_unspecified` scope — a narrative
   sentence supports the group, not the scope). A sourced reading always replaces a machine one for
   the same company × plant × tier-1 role, and the origins that agree with it are listed in
   `also_stated_by` rather than repeated as rows. The register's unit ids also bring units into scope: the tracker's
   owner field names only the project company on Vung Ang 2 and only PLN and Barito on Jawa 9 and
   10, so without the register the Korean and Japanese sponsors of those four 660–1,000 MW coal
   units would be missing from the result set entirely.
4. **Global Energy Monitor is the project registry**, and it is a hand download (its form asks
   for a name and email). The role register, the national emission factors and the committed
   targets are hand-gathered too. Each is marked below and in its dataset's method note, and the
   runner stops with `[hand]` naming the file when one is missing.
5. **Sign convention** as in the automotive sector and whitepaper v1.6: TI = product emissions −
   benchmark emissions; **positive is tonnes added** (a lock-in liability), negative tonnes
   avoided. Zero-stack units (nuclear, hydro, wind, solar, geothermal) are negative by
   construction; biogenic CO2 (bioenergy) is computed and flagged, not added to the fossil total.

## Benchmark and scenarios

Layer 1 is the destination's grid carbon intensity ([`grid`](../grid/method/method.md), Ember via
Our World in Data, all countries): observed values for past years, and two pathways after the
latest observation ([`targets`](../targets/method/method.md)) — **S1** the log-linear trend of the
observed series since 2015 excluding 2020–2021, **S2** the destination government's own
committed target read onto grid intensity and applied pro rata from the latest observation,
floored at S1 where already met or where the trend is steeper. The S2 anchor is machine-read from
Climate Watch's structured NDC content (latest submission; the unconditional figure, the base
year, the furthest stated target year), with hand rows on top where the registry text is not the
furthest stated pathway (EU members, Taiwan, US territories). No third scenario. A destination whose
target is stated against a business-as-usual projection, as GDP intensity, or as a fixed level
without base-year emissions has no S2; its units are reported under S1 and the sentence that was
read is listed in the exclusions.

## Sign and horizon

Each unit's flow runs from its commissioning year to its retirement year (published) or to the
end of its default lifetime, over the years the grid path covers; years before the first grid
observation are dropped and counted in `years_dropped`, never filled. Two totals are published:
`ti_lifetime_tco2` over the whole flow and `ti_remaining_tco2` from the analysis year (the first
year after the latest grid observation) forward — the part that is still a choice.

## Hand-gathered inputs

| file | what | link exists? | status |
|---|---|---|---|
| `projects/raw/gem_global_integrated_power_2026_08_v3.xlsx` | Global Integrated Power Tracker, August 2026 v3 | landing page and licence yes; the file only through GEM's download form | on disk 2026-09-05 (downloaded by the project lead) |
| `roles/raw/gem_wiki_pages.json` | wikitext of the 420 GEM wiki pages of the plants in scope | yes, the wiki's API | fetched; construction, equipment, finance and ownership roles read from the sentences (`roles/processed/gem_wiki_roles.csv`, tier C) |
| `roles/raw/project_roles.csv` | hand rows that confirm or replace a wiki-read role, one source link per row | each row cites its page | header-only; equity rows come from the tracker's owner shares (`roles/processed/gem_ownership.csv`, tier B), other roles from the wiki pages |
| `emission_factors/raw/national_emission_factors.csv` | destination's own implied factor per fuel (UNFCCC CRT 1.A(a)) | each row cites its table | header-only; IPCC defaults apply meanwhile |
| `targets/raw/climatewatch_ndc_content.json` | every country's NDC target text, type and year per submission (Climate Watch, WRI) | yes, public API | fetched; S2 anchors machine-read from it |
| `targets/raw/ndc_anchors_power.csv` | hand rows that replace a parsed anchor (EU members → EU 2040; Taiwan; Guam and Puerto Rico under the US; any `needs_review` destination) | each row cites its document | 30 rows; fixed-level and trajectory targets (CN, ID, MX, ZA, MY, CL, AR, SA, QA) still need a hand level |
| `projects/method/technology_defaults.csv` | lifetime, capacity factor, efficiency by technology | each row cites its document; `verified = no` | authored, to verify |
| `emission_factors/method/ipcc_2006_table_2_2.csv` | IPCC Table 2.2 transcription | verified against the PDF text by the extractor on every run | done |

## Layer 2 stays tier C for now (project lead, 2026-09-06)

The tracker publishes no unit-level heat rate or capacity factor and the destinations' own
fuel-specific factors are not filed, so every fossil unit runs on technology defaults and IPCC
default factors: Layer 2 is tier C throughout. The project lead accepted this on 2026-09-06 as the
basis for the first results; it is declared on every result row (`cf_source`, `heat_rate_source`,
`ef_basis`, `tier`), the bands are carried in the sensitivity table, and national factors
(`emission_factors/raw/national_emission_factors.csv`) lift a destination to tier A when filed.

## Raw data is left in a form a reader can open (project lead, 2026-09-07)

Every raw input is stored so that a person can open it and check the figure it produced, with the
explanation beside it. Where an API answers one large document, it is written out flat: the GEM
wiki pages are **one readable text file per plant** under `roles/raw/gem_wiki/` (provenance header,
then the wikitext as returned) and Climate Watch's NDC content is a **CSV, one row per country ×
indicator × submission**, with the submission order in a second CSV. Company pages are saved as
served under `roles/raw/company_ir/`. Each such directory carries an `index.csv` with every file's
URL, byte count and SHA-256; that index is hash-recorded in `registry/raw_files.csv` and loaded
into the database, so the chain from a published figure to the page it came from is one join. Each
dataset's `method/method.md` says what its raw files are and how they were obtained.

## Scope: which destinations, and whether home counts

`registry/scope.csv` holds two settings read by the pipeline: `destinations` (`all` or a list of
alpha-2 codes) and `exclude_home_country` (`yes` by default: a company's units in its own country
are left out at extraction, so the result is the export impact; `no` keeps them). The automotive
sector has the same table (`data/auto/registry/scope.csv`: `markets`, `exclude_home_market`,
default `no` because a domestic sale is still a sale into that fleet) and its report has the same
switch as a filter. Changing a setting and re-running the pipeline is the whole procedure.

## Sensitivity

`ti_power_sensitivity.csv` varies, one at a time, the operating lifetime and the capacity factor
over the technology-default bands and the fuel emission factor over the IPCC 95 % bounds, for
every unit whose input is a default, under both scenarios; each dimension carries a central row
identical to the published result. Units with a published retirement year are not varied on
lifetime.

## Database and report

`build_database.py` loads every CSV of the sector into `database/tradeimpact_power.sqlite` (with
per-value tiers from `registry/value_tiers.csv`, a tables manifest, a column dictionary and the
world geometry as `map_geometry`); `report/build_report.py` writes `report/ti_power_report.html`,
an interactive page that reads that database in the browser: eight story tabs (companies and
projects, the unit × company map, coverage and roles, destination benchmarks with the NDC sentence
read, other inputs, annual impact, total impact by company and role, sources) with a filter bar
(scenario, home country, company, destination, fuel, status). Serve with
`.venv/bin/python script/auto/serve_dashboard.py --root power --port 8766` and open
<http://127.0.0.1:8766/report/ti_power_report.html>.

## Run order

`script/power/run_all.py [--fetch]`: geography → grid → emission factors → projects → GEM ownership
→ wiki roles → hand roles → NDC anchors → rates → reference → unit impact → attribution →
sensitivity → database → report → ruff → pytest. Exit 3 with `[hand]` when a
hand-gathered file is missing; exit 1 on any other failure. Scripts and their inputs and outputs
are tabulated in [`script/power/README.md`](../../../script/power/README.md).

## Status (2026-09-07)

The pipeline runs end to end on the August 2026 tracker (v3). 711 overseas units in
71 countries are in scope — 553 carry an S1 result and 458 an S2 one, on the
43 of 71 destinations whose latest NDC states a level a pathway can be read from. Four of
those units (Vung Ang 2 Phase 2 Units 1 and 2, Banten Suralaya Units 9 and 10, the Jawa 9 and 10
project) are in scope only because the company register names them: the tracker's owner field
misses their Korean and Japanese sponsors.

Roles in the S1 result set by source: 47 rows from company disclosures and project pages,
439 from the tracker's own fields, 113 from wiki sentences, 0 from the hand register. Layer 2
is tier C throughout, accepted by the project lead as the basis for the first results.

Not yet done: the hand register (`roles/raw/project_roles.csv`) that would confirm the wiki-read
EPC, equipment and finance rows; company disclosures beyond KEPCO and Doosan (J-POWER, JERA,
Marubeni, Sumitomo, Mitsui and the Korean gencos); national emission factors; verifying the
technology defaults against their documents; hand levels for the fixed-level and trajectory NDCs
that still have no S2.
