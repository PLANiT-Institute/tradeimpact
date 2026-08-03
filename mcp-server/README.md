# Trade Impact MCP

Read-only MCP interface for the evidence-first, multi-sector Trade Impact dataset. It exposes
company activity snapshots, direct and contextual market benchmarks, sector pathways,
coverage, and source traceability. Missing data remains missing; the server does not estimate it.

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

For a local HTTP endpoint, bind to loopback by default:

```bash
tradeimpact-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Set `TRADEIMPACT_DATA_DIR` when the published JSON files are not in this repository's
`data/published` directory. A public remote deployment requires authentication, rate limits,
source-licence enforcement, and a separately reviewed network configuration.

The recommended client query sequence and the questions the server is designed to answer are in
[`../docs/MCP.md`](../docs/MCP.md).

## Public contract

- Tools perform exact queries and comparisons.
- Resources expose reusable sector and market context.
- Prompts provide source-first audit workflows.
- Direct arithmetic fails closed unless sector, metric, geography, and unit match.
- Every company metric must include activity-weighted coverage and source identifiers.
