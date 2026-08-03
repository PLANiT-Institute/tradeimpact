# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only MCP adapter over the shared Trade Impact query service."""

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
def get_company_snapshot(
    company_id: str,
    year: int,
    geography: str | None = None,
) -> dict[str, Any]:
    """Return source-backed company metrics for one reporting-year snapshot, if available."""
    return service.get_company_snapshot(company_id, year, geography)


@mcp.tool(annotations=READ_ONLY)
def get_market_context(geography: str, sector_id: str) -> dict[str, Any]:
    """Return a sector pathway as context without pretending it is a direct company target."""
    return service.get_market_context(geography, sector_id)


@mcp.tool(annotations=READ_ONLY)
def get_market_benchmarks(
    sector_id: str,
    geography: str,
    metric_id: str | None = None,
) -> dict[str, Any]:
    """Return direct and contextual policy or regulatory benchmarks for an exact scope."""
    return service.get_market_benchmarks(sector_id, geography, metric_id)


@mcp.tool(annotations=READ_ONLY)
def assess_company_alignment(
    company_id: str,
    sector_id: str,
    geography: str,
    observation_year: int,
    metric_id: str,
    target_year: int,
) -> dict[str, Any]:
    """Compare one company metric with a compatible benchmark and expose coverage and sources."""
    return service.assess_company_alignment(
        company_id,
        sector_id,
        geography,
        observation_year,
        metric_id,
        target_year,
    )


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


@mcp.resource("ti://markets/{geography}/{sector_id}")
def market_context_resource(geography: str, sector_id: str) -> str:
    """Market pathway context for one geography and sector."""
    return json.dumps(
        service.get_market_context(geography, sector_id), ensure_ascii=False, sort_keys=True
    )


@mcp.prompt()
def company_market_audit(
    company_id: str,
    sector_id: str,
    geography: str,
    year: int,
) -> str:
    """Guide a source-first audit without filling data gaps with estimates."""
    return (
        f"Audit {company_id} in {geography} for {year} in the {sector_id} sector. "
        "First inspect sector requirements, then retrieve the company snapshot, market "
        "benchmarks, market context, coverage, and every cited source. Calculate a margin only "
        "when metric definition, unit, geography, and policy scope match. Report missing or "
        "unmatched activity explicitly and do not estimate it."
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
