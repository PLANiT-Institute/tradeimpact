from __future__ import annotations

import asyncio

from mcp import Client

from tradeimpact_mcp.server import mcp


def test_mcp_discovers_read_only_tools_resources_and_prompt() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == {
                "list_sectors",
                "get_sector_requirements",
                "list_companies",
                "get_company_snapshot",
                "get_market_context",
                "get_market_benchmarks",
                "assess_company_alignment",
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
                "ti://markets/{geography}/{sector_id}",
            }
            prompts = await client.list_prompts()
            assert {prompt.name for prompt in prompts.prompts} == {"company_market_audit"}

    asyncio.run(run())


def test_mcp_calls_shared_service_for_available_and_missing_company_data() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            sectors = await client.call_tool("list_sectors", {})
            assert sectors.structured_content is not None
            assert len(sectors.structured_content["sectors"]) == 5

            snapshot = await client.call_tool(
                "get_company_snapshot",
                {"company_id": "toyota", "year": 2024, "geography": "EU27"},
            )
            assert snapshot.structured_content is not None
            assert snapshot.structured_content["status"] == "available"
            assert len(snapshot.structured_content["metrics"]) == 8
            normalized_load = next(
                row
                for row in snapshot.structured_content["metrics"]
                if row["metric_id"] == "normalized_tailpipe_co2_load"
            )
            assert normalized_load["value"] == 85_984.351
            assert normalized_load["unit"] == "tCO2/cohort-1000km"

            power_snapshot = await client.call_tool(
                "get_company_snapshot",
                {"company_id": "jera", "year": 2024, "geography": "JP"},
            )
            assert power_snapshot.structured_content is not None
            assert power_snapshot.structured_content["status"] == "available"
            assert len(power_snapshot.structured_content["metrics"]) == 2

            power_benchmarks = await client.call_tool(
                "get_market_benchmarks",
                {"sector_id": "power", "geography": "JP"},
            )
            assert power_benchmarks.structured_content is not None
            assert len(power_benchmarks.structured_content["benchmarks"]) == 3
            assert all(
                row["comparison_mode"] == "contextual"
                for row in power_benchmarks.structured_content["benchmarks"]
            )

            koen_snapshot = await client.call_tool(
                "get_company_snapshot",
                {"company_id": "koen", "year": 2024, "geography": "KR"},
            )
            assert koen_snapshot.structured_content is not None
            assert koen_snapshot.structured_content["status"] == "available"
            assert {
                row["metric_id"] for row in koen_snapshot.structured_content["metrics"]
            } == {"reported_generation", "scope1_emissions", "scope2_emissions"}

            korea_benchmarks = await client.call_tool(
                "get_market_benchmarks",
                {"sector_id": "power", "geography": "KR"},
            )
            assert korea_benchmarks.structured_content is not None
            assert len(korea_benchmarks.structured_content["benchmarks"]) == 3

            shipping_snapshot = await client.call_tool(
                "get_company_snapshot",
                {"company_id": "mitsui", "year": 2024, "geography": "GLOBAL"},
            )
            assert shipping_snapshot.structured_content is not None
            assert shipping_snapshot.structured_content["status"] == "available"
            assert shipping_snapshot.structured_content["metrics"][0]["value"] == 10.95

            shipping_benchmarks = await client.call_tool(
                "get_market_benchmarks",
                {"sector_id": "shipping", "geography": "GLOBAL"},
            )
            assert shipping_benchmarks.structured_content is not None
            assert len(shipping_benchmarks.structured_content["benchmarks"]) == 3
            assert all(
                row["comparison_mode"] == "contextual"
                for row in shipping_benchmarks.structured_content["benchmarks"]
            )

            missing = await client.call_tool(
                "get_company_snapshot",
                {"company_id": "hyundai", "year": 2024, "geography": "EU27"},
            )
            assert missing.structured_content is not None
            assert missing.structured_content["status"] == "not_available"
            assert missing.structured_content["metrics"] == []

            alignment = await client.call_tool(
                "assess_company_alignment",
                {
                    "company_id": "toyota",
                    "sector_id": "automotive",
                    "geography": "EU27",
                    "observation_year": 2024,
                    "metric_id": "new_vehicle_tailpipe_intensity",
                    "target_year": 2025,
                },
            )
            assert alignment.structured_content is not None
            assert alignment.structured_content["status"] == "available"
            assert alignment.structured_content["meets_target"] is False
            assert alignment.structured_content["alignment_margin"] < 0

            context = await client.call_tool(
                "get_market_context",
                {"geography": "KR", "sector_id": "power"},
            )
            assert context.structured_content is not None
            assert context.structured_content["status"] == "context_only"
            assert context.structured_content["pathway_rates"]["s2"] == 0.065024

    asyncio.run(run())
