# Trade Impact MCP design

The MCP server is a read-only adapter over `ti_framework.alignment.TradeImpactService`. Web and
MCP clients therefore query the same published JSON and do not implement their own calculations.

## Intended questions

- What source-backed company activity is available for a sector, country, and year?
- Which official target is directly comparable, and which is context only?
- What is the distance to target, using the target's own eligibility and unit rules?
- Which broader sector or NDC pathway is relevant only as context?
- How much reported activity was mapped, and what remains unmatched?
- Which source and derivation produced a result?
- Why is a requested comparison unavailable or invalid?

## Tools

- `list_sectors`
- `get_sector_requirements`
- `list_companies`
- `get_company_snapshot`
- `get_market_context`
- `get_market_benchmarks`
- `assess_company_alignment`
- `trace_source`

## Resources and prompts

Resources expose reusable sector and market context under `ti://methodology/...` and
`ti://markets/...`. The `company_market_audit` prompt instructs clients to inspect requirements,
coverage, and sources before making a claim.

## Recommended client flow

1. Call `list_sectors` and `get_sector_requirements` to learn the sector denominator and boundary.
2. Call `list_companies` or request an exact company/year/geography snapshot.
3. Inspect coverage, scope, evidence class, derivation, and every `source_id` before interpreting a
   number.
4. Call `get_market_benchmarks` without assuming every returned record is directly comparable.
5. Use `assess_company_alignment` only for an exact metric and year. Respect `context_only`,
   `not_comparable`, and `not_available` as valid results rather than filling the gap.
6. Call `trace_source` for each cited record and expose the source links in the consuming product.

Typical user questions are: “What activity is actually observed?”, “Which operating geography
does it belong to?”, “Does a target use the same denominator?”, “How much activity is unmatched?”,
“Is this adopted policy, an outlook, or company reporting?”, and “Why was no gap calculated?”

The Toyota pilot demonstrates a direct distance-to-pathway query. The JERA pilot demonstrates the
equally important fail-closed result: assured company data and official national targets can both
exist while arithmetic remains invalid because their boundaries differ. KOEN adds a data-quality
failure mode: the MCP returns reported generation and Scope 1/2 facts, but leaves intensity and a
company gap unavailable because the denominator basis and displayed row reconciliation cannot be
verified.

MOL adds a sector-boundary failure mode: the MCP returns an assured current fleet EEOI and IMO
2030 context, but refuses a gap because MOL's FY2019-anchored lifecycle-GHG Standard Method and
IMO's 2008 international-shipping average CO2 measure are not interchangeable. It also preserves
the source warning that fleet EEOI must not be treated as a customer-specific emissions value.

## Deployment stages

1. Local `stdio` server for development and review.
2. Loopback Streamable HTTP for web/MCP integration tests.
3. Remote read-only service after OAuth, rate limiting, observability, dataset licence controls,
   and denial-of-service limits are reviewed.

The implementation uses the stable MCP Python SDK 2.x contract and pins the next breaking major
version out. Raw licensed registry records must not be redistributed merely because an aggregated
metric is available through MCP.
