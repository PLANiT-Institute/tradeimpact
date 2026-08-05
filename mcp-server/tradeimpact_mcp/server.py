# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only MCP adapter for exported-product lifetime and destination-NDC analysis."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from ti_framework.alignment import TradeImpactService


def _published_dir() -> Path:
    configured = os.environ.get("TRADEIMPACT_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    repository_candidate = Path(__file__).resolve().parents[2] / "data" / "published"
    if repository_candidate.is_dir():
        return repository_candidate
    raise RuntimeError(
        "Set TRADEIMPACT_DATA_DIR to the directory containing the published JSON dataset."
    )


service = TradeImpactService(_published_dir())
mcp = MCPServer("Trade Impact Evidence")
READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


@mcp.tool(annotations=READ_ONLY)
def list_sectors() -> dict[str, Any]:
    """List supported and planned sectors, their boundaries, metrics, and data requirements."""
    return service.list_sectors()


@mcp.tool(annotations=READ_ONLY)
def get_sector_requirements(sector_id: str) -> dict[str, Any]:
    """Explain the activity data, direct metrics, context, and boundary risks for one sector."""
    return service.get_sector_requirements(sector_id)


@mcp.tool(annotations=READ_ONLY)
def list_companies(sector_id: str | None = None) -> dict[str, Any]:
    """List candidate companies, optionally filtered by canonical sector id."""
    return service.list_companies(sector_id)


@mcp.tool(annotations=READ_ONLY)
def list_product_cohorts(
    company_id: str | None = None,
    sector_id: str | None = None,
    year: int | None = None,
) -> dict[str, Any]:
    """List observed sales/deployment cohorts and their destination and product coverage."""
    return service.list_product_cohorts(company_id, sector_id, year)


@mcp.tool(annotations=READ_ONLY)
def get_product_cohort(
    cohort_id: str,
    destination_geography: str | None = None,
    product_type: str | None = None,
    product_name: str | None = None,
) -> dict[str, Any]:
    """Get observed destination × product rows for a cohort, with optional exact filters."""
    return service.get_product_cohort(
        cohort_id,
        destination_geography,
        product_type,
        product_name,
    )


@mcp.tool(annotations=READ_ONLY)
def get_destination_pathway(geography: str, sector_id: str) -> dict[str, Any]:
    """Return destination-sector, regional-proxy, and economy-wide NDC levels separately."""
    return service.get_destination_pathway(geography, sector_id)


@mcp.tool(annotations=READ_ONLY)
def get_impact_readiness(cohort_id: str) -> dict[str, Any]:
    """Show whether lifetime TI is publishable and which sourced inputs are still missing."""
    return service.get_impact_readiness(cohort_id)


@mcp.tool(annotations=READ_ONLY)
def trace_source(source_id: str) -> dict[str, Any]:
    """Return the publisher, URL, evidence class, date, licence, and notes for one source."""
    return service.trace_source(source_id)


@mcp.resource("ti://methodology/sectors")
def sector_catalog_resource() -> str:
    """Machine-readable sector registry."""
    return json.dumps(service.list_sectors(), ensure_ascii=False, sort_keys=True)


@mcp.resource("ti://methodology/sectors/{sector_id}")
def sector_resource(sector_id: str) -> str:
    """Machine-readable methodology boundary for one sector."""
    return json.dumps(
        service.get_sector_requirements(sector_id), ensure_ascii=False, sort_keys=True
    )


@mcp.resource("ti://destinations/{geography}/{sector_id}")
def destination_pathway_resource(geography: str, sector_id: str) -> str:
    """Target hierarchy for one product-use destination and sector."""
    return json.dumps(
        service.get_destination_pathway(geography, sector_id),
        ensure_ascii=False,
        sort_keys=True,
    )


@mcp.resource("ti://cohorts/{cohort_id}")
def product_cohort_resource(cohort_id: str) -> str:
    """Observed destination × product records for one company cohort."""
    return json.dumps(
        service.get_product_cohort(cohort_id), ensure_ascii=False, sort_keys=True
    )


@mcp.prompt()
def exported_product_impact_audit(
    company_id: str,
    sector_id: str,
    year: int,
) -> str:
    """Guide a source-first cohort and destination-NDC audit."""
    return (
        f"Audit {company_id}'s {year} sold-product cohort in the {sector_id} sector. "
        "First inspect sector requirements and list matching cohorts. Then retrieve destination "
        "and product records, inspect each destination's target hierarchy, and check impact "
        "readiness. Separate observed inputs, sourced scenario inputs, and derived results. "
        "Do not publish lifetime impact when the readiness gate is incomplete; list missing "
        "inputs and trace every source instead."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Trade Impact MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
