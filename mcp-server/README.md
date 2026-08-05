# Trade Impact MCP

Read-only MCP interface for company sold-product cohorts, destination policy pathways,
calculation readiness, sector requirements, and source traceability. The server never fills a
missing lifetime or policy input with an undisclosed estimate.

## Local development

```bash
python -m pip install -e ./ti-framework
python -m pip install -e ./mcp-server
tradeimpact-mcp --transport stdio
```

Use the MCP Inspector:

```bash
mcp dev mcp-server/tradeimpact_mcp/server.py
```

Or bind Streamable HTTP to loopback:

```bash
tradeimpact-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Set `TRADEIMPACT_DATA_DIR` if `data/published` is elsewhere. Remote deployment requires
authentication, rate limits, observability, and source-licence review.

The query flow and complete tool/resource contract are documented in [`../docs/MCP.md`](../docs/MCP.md).
