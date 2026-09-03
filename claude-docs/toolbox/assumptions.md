# Numbered assumptions

Every fallback, default and analyst decision standing in place of a source. A figure with no
catalogue row and no assumption id here does not exist (`N-03`).

Each row states **what it costs the analysis** — the direction of the bias, not merely its
existence, because an undirected caveat cannot be acted on. Values themselves live in the data,
the script or the source document; this file is the governance index and does not duplicate them.

## Benchmark and policy assumptions

| id | Assumption | Cited | Cost to the analysis |
|---|---|---|---|
| `A-01` | Pro-rata allocation from the economy-wide NDC is used wherever no transport sub-target exists — which the June 2026 scan found to be every priority market | Guideline §2.3 Method B; challenges Challenge 1 | Assumes every sector decarbonises at the economy-wide rate. Transport decarbonises more slowly, so this **overstates** `r_fleet` and **understates** ICE lock-in liability — a directional bias favouring the firms the framework exists to scrutinise. Disclosed per row via `target_level`; S1 reported as the conservative cross-check |
| `A-02` | The benchmark declines exponentially rather than along an S-curve | Guideline §2.2 caveat; challenges cross-cutting B | In fast-transition markets the near-term benchmark decline is understated, which again understates ICE lock-in. Flagged in the data-quality declaration for those markets |
| `A-03` | `r_power` is derived from the power-sector pathway independently of `r_fleet`; where no power sub-target exists, pro-rata from the economy-wide target | Guideline §3.4, Appendix E; `N-07` | Where both come from the same economy-wide target, the independence is procedural rather than substantive. The identity `r_fleet = r_power` is never encoded, but a shared origin is disclosed |
| `A-09` | A market with no active NDC gets no S2 benchmark and is reported separately rather than assigned a substitute | Challenges Challenge 1; blocker `B-04` | Removes the United States from the S2 headline entirely. The alternative — an IEA sector trajectory as an S2 proxy — is a live decision, not a settled rule, so results are not comparable across the two treatments until `B-04` closes |
| `A-11` | The derived annual rate is extrapolated unchanged beyond the target year for the remainder of the vehicle lifetime | Guideline §6.2 step 5 | A 2035 target driving a 25-year benchmark is an extrapolation, not a commitment. Recorded per row; the further past the target year, the weaker the reference |

## Usage and lifetime assumptions

| id | Assumption | Cited | Cost to the analysis |
|---|---|---|---|
| `A-04` | Vehicle lifetime T is taken from the market's mean fleet age, with the mandatory T ± 3 year sensitivity | Guideline §6.4, §5.2 | A modelling bracket rather than an observed survival curve. Markets with atypical scrappage sit outside it, and the lifetime sets the whole summation horizon |
| `A-07` | The archived EU27 destination snapshot is reused with its tiers and derivations intact, rather than re-collected | `SRC-20`; prior work product of the archived pipeline | Inherits that build's sourcing decisions, including its vintages. Cheap and traceable, but a correction upstream in the original sources will not reach us until the snapshot is refreshed |
| `A-08` | Where no matching national traffic series exists, distance per vehicle is a proxied (Tier C) value | `vehicle_usage/method/method.md`; `SRC-20` derivations | More than half of the EU27 units currently rest on a proxied distance. Distance multiplies every emission term in both layers, so first-pass results are **directions with a stated coverage ratio, never magnitudes** (`N-04`) |

## Product-parameter assumptions

| id | Assumption | Cited | Cost to the analysis |
|---|---|---|---|
| `A-05` | Certified values are corrected to real world exactly once, at ST06 processing time, using ICCT factors derived from European monitoring | Guideline §7.2, Appendix C.1, Appendix F.4; `SRC-17` | Applicability to Korean- and Japanese-market specifications sold outside Europe is unverified. Until `SRC-17` is registered no correction is applied at all, which leaves certified values in place and **understates** combustion emissions |
| `A-06` | A PHEV row without a sourced utility factor is withheld rather than given a default | Guideline §7.3; challenges Challenge 4; `SRC-19` | Removes PHEV units from the result and reports them as withheld. The alternative — a regulatory utility factor — systematically overstates electric driving share and would convert a modest liability into an apparent contribution |
| `A-10` | Hyundai plant-side rows are used only where destination sales are absent, and never as destination volumes | `sales/method/method.md`; `X-04` | Production-side volumes carry no destination, so they cannot enter a destination TI. Using them would attribute a market's climate direction to a market that never received the vehicles |
| `A-12` | Non-plug-in hybrids are computed in the combustion channel | Guideline §3.3 | Correct per the guideline, and it means a class many readers assume is low-emission can be the largest single liability in a result. It is never labelled zero-emission |

## Reporting assumptions

| id | Assumption | Cited | Cost to the analysis |
|---|---|---|---|
| `A-13` | Where the Tier-C share of covered units is high enough to put the sign in doubt, magnitudes are suppressed and only direction is published | `N-04`; challenges Challenge 3 | The threshold is a project default, not a derived rule. Challenge 3 requires a propagation procedure and a justified threshold; until PH2 delivers one, the line is defensible but arbitrary — and it is active on the first-pass EU27 result |

## Retirement rule

An assumption is retired when its source arrives — in the same change that adopts the source, not
later. A retired assumption is deleted from this file and its retirement recorded in
[`../log/README.md`](../log/README.md). Two rows describing the same quantity, one live and one
superseded, is the failure this rule prevents.
