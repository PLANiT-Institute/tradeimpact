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
- `ti_power_by_role.csv` — company × role × unit × scenario: the same unit result attributed to
  each company that held a role on it; `ti_power_company.csv` sums it per company × role.

## Decisions (project lead, 2026-09-05)

1. **Attribution is per role, never pooled.** A unit's trade impact is attributed separately to
   each role — developer, equity owner, EPC contractor, equipment supplier, O&M contractor,
   lender, ECA cover — and the register carries the **role, the phase (development,
   construction, operation, finance) and the share** as data columns. The model reports each
   role row twice, the unit's full figure and the share-weighted figure, and never adds rows of
   different roles into one company total; so the weighting can be revisited later without
   re-collecting. A blank share yields a blank weighted figure, not an assumed one.
2. **Emission factor: national first, IPCC otherwise.** A unit's CO2 per unit of fuel is the
   destination country's own fuel-specific factor where one is on file
   ([`emission_factors`](../emission_factors/method/method.md), tier A) and the IPCC 2006 default
   otherwise (tier C, with the IPCC bounds carried for the sensitivity). Heat rate and capacity
   factor: the tracker's unit-level estimate where published (tier B), the technology default
   otherwise (tier C). Every choice is a column on the result row.
3. **Roles are distinguished by phase.** Building a plant (EPC, equipment) and running it (equity,
   O&M) are different responsibilities; the phase sits on every role row and the company table is
   keyed by role, so a reader can take construction-side and operation-side attributions apart.
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
floored at S1 where already met or where the trend is steeper. No third scenario. A destination
with no usable anchor is reported under S1 and listed in the exclusions for S2.

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
| `roles/raw/project_roles.csv` | company × unit × role × phase × share, one source link per row | each row cites its page | header-only; equity rows meanwhile read from the tracker's owner shares (`roles/processed/gem_ownership.csv`, tier B) |
| `emission_factors/raw/national_emission_factors.csv` | destination's own implied factor per fuel (UNFCCC CRT 1.A(a)) | each row cites its table | header-only; IPCC defaults apply meanwhile |
| `targets/raw/ndc_anchors_power.csv` | committed target per destination | each row cites the NDC registry entry | header-only; S2 excluded per destination meanwhile |
| `projects/method/technology_defaults.csv` | lifetime, capacity factor, efficiency by technology | each row cites its document; `verified = no` | authored, to verify |
| `emission_factors/method/ipcc_2006_table_2_2.csv` | IPCC Table 2.2 transcription | verified against the PDF text by the extractor on every run | done |

## Run order

`script/power/run_all.py [--fetch]`: geography → grid → emission factors → projects → roles →
targets → reference → unit impact → attribution → ruff → pytest. Exit 3 with `[hand]` when a
hand-gathered file is missing; exit 1 on any other failure. Scripts and their inputs and outputs
are tabulated in [`script/power/README.md`](../../../script/power/README.md).

## Status (2026-09-05)

The pipeline runs end to end on the August 2026 tracker (v3). 685 overseas units in 71 countries
match a company in scope; 539 carry an S1 result (cancelled and shelved units, units with no
start year or capacity, and units whose operating years end before the grid series begins are
listed in `ti_power_excluded.csv`). 848 company × unit equity rows were read from the tracker's
owner shares, 737 with a stated share. Under S1 every fossil unit is on technology defaults (the
tracker publishes no unit heat rate or capacity factor) and IPCC default factors, so Layer 2 is
tier C throughout until national factors are filed. S2 is excluded for every destination until
`targets/raw/ndc_anchors_power.csv` is filled. Not yet built: the sensitivity table (lifetime,
capacity factor, IPCC bounds), the database and the dashboard/report readers with the unit × company
map, and the hand role register for construction, equipment, O&M and finance.
