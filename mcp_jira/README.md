# MCP Jira Integration

## Purpose
The `mcp_jira` package exposes the mock Jira capabilities through the Model Context Protocol so that Codex-style agents can turn user prompts into actionable Jira operations. This aligns with the Codex vision of natural language instructions being executed as code against real services.

## Tool Registry Highlights
- `jira.create_issue`, `jira.get_issue`, `jira.search`
- `jira.list_transitions`, `jira.transition_issue`, `jira.add_comment`
- `jsm.create_request`, `agile.list_sprints`

Each tool accepts a JSON payload and returns JSON responses mirroring Jira Cloud.

## Connecting MCP to Jira
1. **Configure environment variables** for the session that will load the MCP server:
   - `JIRA_BASE_URL` – defaults to `http://localhost:9000` when using the included mock server.
   - `JIRA_TOKEN` – defaults to `mock-token`; replace with a real API token when targeting Jira Cloud.
   - `JIRA_TIMEOUT` – optional per-request timeout in seconds (default `10`).
2. **Start the mock Jira server** (or ensure your Jira Cloud instance is reachable).
3. **Load the MCP server facade** in your orchestrator:
   ```python
   from mcp_jira.server import list_tools, invoke_tool

   available = list_tools()
   result = invoke_tool("jira.create_issue", {
       "project_key": "SUP",
       "issue_type_id": "10003",
       "summary": "Ticket from MCP agent"
   })
   print(result["key"])
   ```
4. **Handle authentication**: the server automatically adds the bearer token from `JIRA_TOKEN` to outgoing requests. For OAuth flows, see `mcp_jira.oauth` for helper routines.

## Best Practices
- Validate tool inputs before invocation to keep responses deterministic for Codex-powered workflows.
- Respect rate limiting feedback from the mock server to mirror production Jira behavior.
- Log tool invocations to provide traceability between natural language prompts and executed API actions.
