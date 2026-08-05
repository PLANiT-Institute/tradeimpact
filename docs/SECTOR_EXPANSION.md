# Sector expansion plan

The shared Trade Impact object is `company × product/asset × destination × cohort`. Expansion
reuses provenance, coverage, target hierarchy, readiness, decomposition, web, and MCP contracts;
it does not reuse automotive physics or units.

| Order | Sector | Cohort/activity object | Destination boundary | Use-phase service | Primary policy path |
|---:|---|---|---|---|---|
| 1 | Automotive | vehicle registrations/sales by model and powertrain | registration/use country | vehicle-km | passenger-car or road transport + grid/hydrogen |
| 2 | Power equipment/generation | commissioned capacity or delivered MWh by technology | connected grid / consumption market | MWh or capacity service | power-sector pathway |
| 3 | Shipping | vessel deployment or voyage transport work by fuel | voyage/served market and IMO jurisdiction | tonne-nautical-mile | IMO plus applicable served-market path |
| 4 | Steel | product tonnes by grade and route | destination/use market defined by method | tonne of functional product | industry/steel pathway |
| 5 | Petrochemicals | tonnes by chemical/product route | destination/use market defined by method | product-specific functional unit | chemicals/industry pathway |

## Acceptance gates

A sector becomes an active cohort pilot only after it has:

1. a written destination and service boundary;
2. observed company cohort volume by product/technology and destination;
3. product use-phase emissions parameters;
4. destination use and lifetime/survival parameters;
5. an explicit destination target hierarchy;
6. S1/S2/S3 scenario inputs where the sector method requires them;
7. reproducible transformations, source IDs, and mapping coverage;
8. tests that missing required inputs block results.

It becomes supported after at least two companies and two destination geographies can be assessed
without hidden allocation.

## Current status

Automotive is the only active exported-product cohort pilot. Toyota EU27 has observed product and
destination resolution but is not yet lifetime-result ready. Existing JERA, KOEN, and MOL
snapshots remain useful source research, but they do not yet contain the complete product/asset ×
destination × cohort dimensions and are not presented as equivalent Trade Impact assessments.

## Cross-sector rule

Cross-sector views may compare data coverage, result availability, evidence quality, affected
activity share, and direction within each sector's own method. They must not add gCO2/km,
kgCO2e/MWh, gCO2e/tonne-nm, and tCO2e/t into one score without a separately reviewed
normalization method.
