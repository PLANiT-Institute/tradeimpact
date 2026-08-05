# Evidence and logic audit

Audit date: 2026-08-05 · Public contract: `export-impact-v1`

## Conclusion

The project's whitepaper and lifetime engine match the intended research question: sold-product
use-phase emissions are evaluated over time against the operating country's NDC-derived sector
path. The previous public `alignment-v2` presentation did not. It reduced Toyota to a current WLTP
average and EU regulatory target distance, and introduced a fixed-1,000km load unrelated to
vehicle lifetime or destination use. That metric and the corresponding visual narrative have been
removed.

The corrected Toyota–Hyundai comparison now publishes what the evidence supports and withholds
what it does not:

| Claim | Evidence status | Publication decision |
|---|---|---|
| 803,094 Toyota-brand EU27 first registrations in 2024 | EEA final regulatory dataset | publish |
| 429,936 Hyundai-brand EU27 first registrations in 2024 | EEA final regulatory dataset | publish |
| Destination × commercial name × powertrain composition | reproducible EEA aggregation; 1,286 rows | publish with mapping coverage |
| Production/export origin | not present in EEA registration data | do not infer |
| Certified WLTP tailpipe/electricity fields | EEA regulatory fields where reported | publish as product parameters, not lifetime GHG |
| EU collective 2035 NDC | official UNFCCC NDC submission | publish as economy-wide fallback context |
| EU 2030 domestic-transport path | Eurostat base plus Commission pathway | publish as regional sector proxy with boundary caveat |
| Country-specific passenger-car pathways | not collected for 27 destinations | mark missing |
| Actual annual or lifetime GHG and TI | use, survival, real-world, and country pathways incomplete | withhold |

## Toyota and Hyundai evidence chain

1. The [EEA passenger-car monitoring dataset](https://co2cars.apps.eea.europa.eu/) is queried for
   final 2024 `TOYOTA` and `HYUNDAI` brand records in the EU27 using separate exact queries.
2. The committed aggregate response and exact query are content-addressed. Builds do not depend
   on a live API.
3. Registration field `r` is aggregated by destination `MS`, commercial name `Cn`, and a disclosed
   powertrain classification based on fuel mode/type.
4. Certified tailpipe `Ewltp` and electricity-use `z` fields are registration weighted only over
   records where they are reported; mapped units remain explicit.
5. Toyota's 660 rows reconcile to 803,094 registrations; Hyundai's 626 rows reconcile to 429,936.
   Mapping coverage is retained separately for each company.
6. The data establishes operating destination, not manufacturing or export origin. Level 2
   production attribution remains missing.

## Target hierarchy audit

The [EU and Member States' 2025 NDC](https://unfccc.int/sites/default/files/2025-11/DK-2025-11-05%20EU%20NDC.pdf)
is a collective economy-wide commitment. Its 2035 range cannot be subtracted directly from a
vehicle intensity.

The European Commission 2040-target impact assessment reports a 2030 domestic-transport pathway.
Combined with the 2023 Eurostat domestic-transport inventory, it supports a transparent regional
sector-rate proxy. It still differs from the desired benchmark because it covers all domestic
transport, not passenger-car service intensity, and it is regional rather than country-specific.
The data contract labels it `sector_proxy` and `proxy_requires_disclosure`.

The calculation hierarchy therefore remains:

1. destination-country passenger-car or road-transport path — missing;
2. EU domestic-transport regional proxy — available with caveat;
3. EU collective economy-wide NDC — context only.

No proxy is relabelled as an observed country target.

## Logic audit

The engine correctly implements:

- a dynamic destination benchmark rather than a static product comparator;
- distinct product emissions trajectories for combustion, BEV, and PHEV channels;
- independent transport and power decarbonisation rates;
- lifetime summation over `t = 0…T−1`;
- mandatory decomposition by destination and powertrain;
- S1/S2/S3 scenarios and missing-input propagation.

The arithmetic is logically coherent, but a coherent formula does not make unsourced inputs
objective. The public readiness gate now prevents the validation fixture, proxy VKT, assumed
lifetime, or reconstructed history from becoming a company result.

## Remaining risks and controls

- **Brand boundary:** `TOYOTA` and `HYUNDAI` registration filters are not consolidated-group
  boundaries. Each brand boundary is explicit.
- **Origin boundary:** company-reported European production shares are broader aggregate context,
  not factory assignments for the EEA registration rows. National export comparisons remain
  unavailable.
- **Commercial-name quality:** EEA strings need normalization before model-family or factory
  mapping. Raw names are retained.
- **Hybrid interpretation:** HEV and PHEV are not labelled zero-emission. PHEV needs a real-world
  utility factor.
- **Energy transfer:** BEV use emissions move from road transport tailpipe to the power sector;
  zero certified tailpipe is not zero use-phase GHG.
- **Regional proxy:** the EU transport rate is broader than passenger cars. A final country result
  requires country-specific evidence or a prominently disclosed proxy decision.
- **Scope relationship:** TI is additional to Scope 3 Category 11 and is never netted against it.

## Next evidence priority

Collect country-specific vehicle use and survival first for the largest destination shares, then
country road-transport and grid pathways, followed by real-world product parameters. This order
turns the largest observed cohort coverage into calculation-ready coverage without inventing a
complete EU27 result.
