# Trade Impact MCP design

The MCP server is a read-only interface over the same content-addressed cohort, pathway,
readiness, and source data used by the web application.

## Questions it should answer

- Which sold-product cohorts are observed for this company, sector, and year?
- In which countries did the products enter use?
- Which products and technologies make up the cohort?
- Which emissions channel applies to each product type?
- What destination-sector target is available, and is it exact, regional, or an NDC fallback?
- Is lifetime TI publishable? If not, which inputs are missing?
- Which source and derivation support every field?

## Tools

- `list_sectors`
- `get_sector_requirements`
- `list_companies`
- `list_product_cohorts`
- `get_product_cohort`
- `get_destination_pathway`
- `get_impact_readiness`
- `trace_source`

`get_product_cohort` can filter by destination geography, product type, and commercial/product
name. It returns selected units and record count with the source-backed rows. It does not compute a
lifetime result.

## Resources and prompt

- `ti://methodology/sectors`
- `ti://methodology/sectors/{sector_id}`
- `ti://cohorts/{cohort_id}`
- `ti://destinations/{geography}/{sector_id}`
- `exported_product_impact_audit` prompt

## Recommended client flow

1. Inspect sector requirements.
2. List matching product cohorts.
3. Retrieve the cohort and decompose it by destination and product/technology.
4. Retrieve the target hierarchy for each material destination.
5. Check impact readiness before requesting or interpreting a lifetime value.
6. Trace every source and retain mapping coverage and proxy labels in the answer.

An `inputs_incomplete` response is a valid analytical result. Clients must not fill missing use,
lifetime, real-world, grid, fuel, or policy inputs with undisclosed defaults.

## Deployment

Start with local `stdio`, then loopback Streamable HTTP. Remote deployment requires OAuth, rate
limits, observability, dataset-licence controls, and denial-of-service review. Aggregated registry
evidence does not grant permission to redistribute licensed raw records.
