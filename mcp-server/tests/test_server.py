from __future__ import annotations

import asyncio

from mcp import Client

from tradeimpact_mcp.server import mcp


def test_mcp_discovers_read_only_export_impact_contract() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == {
                "list_sectors",
                "get_sector_requirements",
                "list_companies",
                "list_product_cohorts",
                "get_product_cohort",
                "get_destination_pathway",
                "get_impact_readiness",
                "trace_source",
            }
            for tool in tools.tools:
                assert tool.annotations is not None
                assert tool.annotations.read_only_hint is True
                assert tool.annotations.destructive_hint is False

            resources = await client.list_resources()
            assert {str(resource.uri) for resource in resources.resources} == {
                "ti://methodology/sectors"
            }
            templates = await client.list_resource_templates()
            assert {template.uri_template for template in templates.resource_templates} == {
                "ti://methodology/sectors/{sector_id}",
                "ti://cohorts/{cohort_id}",
                "ti://destinations/{geography}/{sector_id}",
            }
            prompts = await client.list_prompts()
            assert {prompt.name for prompt in prompts.prompts} == {
                "exported_product_impact_audit"
            }

    asyncio.run(run())


def test_mcp_queries_observed_cohort_and_destination() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            cohorts = await client.call_tool(
                "list_product_cohorts",
                {"company_id": "toyota", "sector_id": "automotive", "year": 2024},
            )
            assert cohorts.structured_content is not None
            assert cohorts.structured_content["status"] == "available"
            summary = cohorts.structured_content["cohorts"][0]
            assert summary["cohort_id"] == "toyota-eu27-passenger-cars-2024"
            assert summary["record_count"] == 660
            assert summary["destination_count"] == 27

            france_bev = await client.call_tool(
                "get_product_cohort",
                {
                    "cohort_id": "toyota-eu27-passenger-cars-2024",
                    "destination_geography": "FR",
                    "product_type": "BEV",
                },
            )
            assert france_bev.structured_content is not None
            cohort = france_bev.structured_content["cohort"]
            assert cohort["selection"]["selected_units"] > 0
            assert cohort["records"]
            assert all(
                row["destination_geography"] == "FR" and row["product_type"] == "BEV"
                for row in cohort["records"]
            )

    asyncio.run(run())


def test_mcp_preserves_target_hierarchy_and_lifetime_gate() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            pathways = await client.call_tool(
                "get_destination_pathway",
                {"geography": "FR", "sector_id": "automotive"},
            )
            assert pathways.structured_content is not None
            assert pathways.structured_content["status"] == "available"
            rows = pathways.structured_content["pathways"]
            assert [row["comparison_role"] for row in rows] == [
                "sector_proxy",
                "fallback_context",
            ]
            assert rows[0]["calculation_status"] == "proxy_requires_disclosure"
            assert rows[1]["calculation_status"] == "not_directly_usable"

            readiness = await client.call_tool(
                "get_impact_readiness",
                {"cohort_id": "toyota-eu27-passenger-cars-2024"},
            )
            assert readiness.structured_content is not None
            assert readiness.structured_content["status"] == "inputs_incomplete"
            gate = readiness.structured_content["readiness"]
            assert gate["publication_decision"] == "withhold_lifetime_ti"
            assert len(gate["missing_required_inputs"]) == 9

            source = await client.call_tool(
                "trace_source", {"source_id": "unfccc-eu-ndc-2025"}
            )
            assert source.structured_content is not None
            assert source.structured_content["status"] == "available"
            assert source.structured_content["source"]["publisher"].startswith(
                "European Union"
            )

    asyncio.run(run())
