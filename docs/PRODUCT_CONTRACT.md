# Trade Impact exported-product contract

Version: `export-impact-v1` · Status: implementation contract

## Purpose

Trade Impact evaluates the climate direction embedded in a company's sold-product portfolio. For
each cohort, it asks whether a product's use-phase emissions in its destination market stay below
or rise above the sector pathway that the destination is committed to under its NDC.

The public unit of analysis is:

```text
company × cohort year × destination geography × product / technology
```

Production origin is an optional Level 2 dimension and must not be inferred from destination
registrations. Where it is collected, the full unit becomes `production origin × destination ×
product × cohort year`.

## Three evidence layers

1. **Observed activity** — units sold or deployed, destination, product/model, technology,
   certified or measured performance, coverage, and source.
2. **Sourced scenario inputs** — use, survival, lifetime, real-world correction, fuel/grid
   intensity, and destination policy pathways, each with sensitivity and provenance.
3. **Derived results** — annual product gap, cumulative cohort TI, and mandatory decomposition by
   destination and product type.

The layers cannot be silently collapsed. A project-derived result is not an official statistic
merely because one or more of its inputs are official.

## Calculation

For product type `v`, destination `c`, and years since sale `t`:

```text
TI_gap,v,c(t) = E_ref,c(t) − E_product,v,c(t)
TI_product,v,c = Σ[t=0…T−1] TI_gap,v,c(t)
TI_cohort,F,Y0 = Σc Σv V_c,v × TI_product,v,c
```

Positive TI is a contribution relative to the pathway. Negative TI is carbon lock-in. Headline
results must reconcile to both country and product decompositions. S1 current-policy, S2 national
commitment, and S3 1.5°C scenarios are reported together; the transport and power pathways are
derived independently.

## Destination target hierarchy

Use the most specific source-backed level available and disclose all fallbacks:

1. passenger-car, road-transport, or exact destination-sector pathway;
2. broader destination transport/sector pathway;
3. regional sector pathway that legally or analytically applies to the destination;
4. economy-wide NDC translated with a documented allocation method;
5. economy-wide NDC as context only when no defensible sector translation exists.

A regional or economy-wide proxy is never relabelled as a country-specific product target.

## Publication gate

A lifetime result is published only when the following are source-complete for the affected
activity:

- observed destination volume and product classification;
- product use-phase efficiency or emissions channel;
- destination annual use and survival/lifetime;
- real-world performance correction;
- destination sector benchmark base and S1/S2/S3 pathway;
- destination energy-system pathway for electricity, hydrogen, or other indirect energy;
- technology-specific parameters such as PHEV utility factor;
- mapping coverage and uncertainty/sensitivity bounds.

If a required input is missing, the result status is `inputs_incomplete`. The application may
publish the observed cohort, target hierarchy, and missing-input list, but not a lifetime value,
avoided-emissions claim, or firm score.

## Scope position

Trade Impact is additional to Scope 3 Category 11. It does not remove, offset, or net against a
company's absolute inventory. Manufacturing and end-of-life emissions are outside the primary
use-phase boundary and should be disclosed separately where material.

## Sector expansion

The common contract is company × product × destination × cohort. Physical models remain
sector-specific:

- automotive: vehicle-km, powertrain, fuel/grid/hydrogen, fleet pathway;
- power equipment and generation: MWh or service output, asset life, connected grid, power path;
- shipping: tonne-nautical-mile, vessel/fuel/voyage, IMO or served-market path;
- steel and petrochemicals: product tonnes, downstream use or production location as defined by
  the sector method, route/technology, and industry pathway.

No universal physical denominator is imposed across sectors.
