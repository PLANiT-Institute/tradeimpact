# Source catalogue

Every source the process may use, and what we actually hold. `SRC-nn` is the governance handle
used by the phase and stage documents; `source_id` is the pipeline's own key inside the data.

Locators, the literal query and what is fetched from each source live with the dataset that uses
it, in [`../stages/st02-06-datasets.md`](../stages/st02-06-datasets.md) — one home per fact. Raw
file names and SHA-256 hashes live in each `data/auto/<dataset>/method/method.md`.

**Access route** — `api` reachable programmatically · `download` portal or file download ·
`document` PDF or statute needing hand extraction · `paywalled` out of scope under `C-08` and
`X-02` · `unresolved` no route found yet.

**Data level** is a hard constraint, not metadata: a national aggregate cannot serve a stage that
needs per-model values.

## Held and in use

| id | Source | Dataset | Access | Data level | Licence / terms |
|---|---|---|---|---|---|
| `SRC-01` | EEA CO2 monitoring of new passenger cars, 2024 final — Toyota EU27 | `sales`, `vehicle_technology` | api (snapshot pinned) | Country × commercial name × powertrain; no production origin | EEA re-use policy; acknowledge EEA, check item-specific terms |
| `SRC-02` | Same, Hyundai EU27 | `sales`, `vehicle_technology` | api (snapshot pinned) | As above | As above |
| `SRC-04` | Kia IR retail sales by model and market, 2026 year to date | `sales` | document (hand-gathered workbook) | Model × market, market being an IR **region** in most columns | Company IR disclosure; redistribution not cleared |
| `SRC-05` | Hyundai IR global plant sales, 2025 | `sales` | document (hand-gathered workbook) | Model × plant, with a domestic/export split — production side | Company IR disclosure; redistribution not cleared |
| `SRC-20` | Archived EU27 destination inputs snapshot | `vehicle_usage`, `country_emissions`, `emission_targets` | held file | Per EU27 country: VKT, operating life, stock, fleet intensity base, grid intensity, S1/S2/S3 rates, each with tier and derivation | Derived work product of the prior build; underlying sources individually licensed |
| `SRC-24` | Archived source register and published lifetime results | ST07, ST11 | held files | 26 registered sources; one published EU27 2024 cohort result set | Prior work product; used as a register seed and a regression baseline |

## Needed, not yet held

| id | Source | Dataset | Access | Data level | Consequence if it stays missing |
|---|---|---|---|---|---|
| `SRC-03` | EEA CO2 monitoring — Kia and Honda brands | `sales`, `vehicle_technology` | api | As `SRC-01` | Two of the four target exporters have no EU27 result |
| `SRC-06` | United States volumes by model and powertrain | `sales` | unresolved (Experian, WardsAuto `paywalled`) | Model level needed; company IR gives less | No US result; the market leaves the headline |
| `SRC-07` | Australia volumes by model and powertrain | `sales` | unresolved (VFACTS `paywalled`; FCAI summaries aggregate) | Model level needed; FCAI is one level too coarse | No Australian result |
| `SRC-08` | National GHG inventories, CRF 1.A.3.b.i passenger cars | `country_emissions` | download | Country × year | No base-year benchmark outside the archived EU27 values |
| `SRC-09` | EPA Inventory of US GHG Emissions and Sinks | `country_emissions` | download + hand extraction | National, per sector | No US benchmark base |
| `SRC-10` | DCCEEW National Greenhouse Accounts | `country_emissions` | download + hand extraction | National, per sector | No Australian benchmark base |
| `SRC-11` | Ember electricity data | `country_emissions` | download | Country × year | No grid intensity outside the archived EU27 values; regional averages are not acceptable (guideline §7.4) |
| `SRC-12` | EEA electricity CO2 intensity series | `country_emissions` | download | Country × year | Loses the cross-check on `SRC-11` |
| `SRC-13` | UNFCCC NDC Registry | `emission_targets` | document | Economy-wide; **no transport or power sub-target in any priority market** (challenges Ch1) | No S2 benchmark at all; `A-01` pro-rata becomes universal |
| `SRC-14` | Regulation (EU) 2019/631 as amended | `emission_targets` | document | Regional sector target, outranks the NDC | EU markets drop a hierarchy level |
| `SRC-15` | IEA World Energy Outlook 2024 | `emission_targets` | document (PDF held in Drive) | Regional or national, sector level | No S1 or S3 rates |
| `SRC-16` | IEA Global EV Outlook 2024 | `emission_targets` | document (PDF held in Drive) | Regional, EV penetration | Methods A and C lose their new-entrant intensity |
| `SRC-17` | ICCT lab-to-road 2018; real-world CO2 in Europe January 2024 | `vehicle_technology` | document (PDFs held in Drive) | Per powertrain, Europe-derived | No real-world correction; certified values would overstate product performance |
| `SRC-18` | ICCT EU vehicle market statistics pocketbook 2024 | `vehicle_usage` | document (PDF held in Drive) | Country, market structure | Loses a stock cross-check |
| `SRC-19` | Transport and Environment PHEV report 2023 | `vehicle_technology` | document (PDF held in Drive) | Per market where studied | PHEV results withheld with their unit counts (`A-06`) |
| `SRC-21` | FHWA highway statistics; BTS vehicle survival tables | `vehicle_usage` | download | National, per vehicle | No US distance or lifetime |
| `SRC-22` | ABS Survey of Motor Vehicle Use (last edition 2020); BITRE | `vehicle_usage` | download | National, per vehicle, stale vintage | Australian distance is proxied at best |
| `SRC-23` | EPA certification data | `vehicle_technology` | download | Per model | No US technology parameters |
| `SRC-25` | GHG Protocol Scope 3 standard and Chapter 11 technical guidance | ST12 | document (PDFs held in Drive) | Framework, not data | `C-06`'s comparative overview has no primary anchor |

## Standing gaps and what they cost

| Gap | Consequence | Blocks |
|---|---|---|
| No country-level transport or power sub-target in any priority NDC | Pro-rata allocation is universal, which overstates the transport benchmark decline and understates ICE lock-in (`A-01`) | PH2 objective 2 |
| The United States has no active NDC | No S2 benchmark for the market; the decision rule is unmade (`B-04`) | PH1 objective 3 |
| No real-world PHEV utility factor held | PHEV rows withheld with unit counts | PH1 objective 4 |
| No 2022 or 2023 registration snapshots | Rolling portfolio TI — the whitepaper's primary disclosure metric — cannot be computed | PH1 objective 5 |
| Kia and Hyundai IR tables carry no powertrain | Their rows cannot enter a TI result until the ST06 join resolves them | PH1 objective 2 |
| Kia IR reports regions, Hyundai IR reports plant-side sales | Neither can produce a country-level TI as it stands; both are reported separately | PH1 objective 5 |
| Redistribution of the IR workbooks not cleared | The open dataset (`C-02`) may not be able to include them | PH3 objective 4 |

Anything used in place of a source is a numbered row in [`assumptions.md`](assumptions.md).
