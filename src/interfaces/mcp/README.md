# MCP (Model Context Protocol) Servers

This directory contains the MCP server implementations for Digital Spiral.

## Overview

MCP servers provide a standardized interface for AI assistants to interact with Jira and SQL data. They support both Server-Sent Events (SSE) for real-time communication and REST endpoints for traditional request/response patterns.

## Servers

### 1. MCP Jira Server (`jira/`)

**Port:** 8055  
**Purpose:** Provides tools for interacting with Jira instances

**Available Tools:**
- `jira.search` - Search issues using JQL
- `jira.get_issue` - Get single issue details
- `jira.create_issue` - Create new issue (with audit log)
- `jira.update_issue` - Update issue fields
- `jira.transition_issue` - Change issue status
- `jira.add_comment` - Add comment to issue
- `jira.link_issues` - Link two issues
- `jira.list_transitions` - Get available transitions

**Endpoints:**
- `GET /` - Server info
- `GET /health` - Health check
- `GET /sse` - SSE connection for real-time communication
- `POST /tools/invoke` - Invoke a tool (REST fallback)
- `GET /tools` - List available tools

**Features:**
- ✅ Rate limiting per instance
- ✅ Audit logging for all write operations
- ✅ Idempotency key support
- ✅ Request ID tracing
- ✅ Pydantic schema validation
- ✅ Structured error responses

### 2. MCP SQL Server (`sql/`)

**Port:** 8056  
**Purpose:** Provides whitelisted SQL query templates for analytics

**Available Templates:**
- `search_issues_by_project` - Search issues by project with filters
- `get_project_metrics` - Get project metrics over time
- `search_issues_by_text` - Full-text search using trigram similarity
- `get_issue_history` - Get issue transition history
- `get_user_workload` - Get user workload by project
- `lead_time_metrics` - Get lead time metrics

**Endpoints:**
- `GET /` - Server info
- `GET /health` - Health check
- `GET /sse` - SSE connection
- `POST /query` - Execute query template
- `GET /templates` - List available templates

**Features:**
- ✅ Whitelisted query templates (SQL injection protection)
- ✅ Parameter validation with Pydantic
- ✅ Tenant isolation
- ✅ Query performance tracking
- ✅ Optimized with database indexes

## Running the Servers

### Development

**MCP Jira Server:**
```bash
python -m src.interfaces.mcp.jira.server
# or
uvicorn src.interfaces.mcp.jira.server:app --host 0.0.0.0 --port 8055 --reload
```

**MCP SQL Server:**
```bash
python -m src.interfaces.mcp.sql.server
# or
uvicorn src.interfaces.mcp.sql.server:app --host 0.0.0.0 --port 8056 --reload
```

### Production

Use Docker Compose:
```yaml
services:
  mcp-jira:
    build: .
    command: uvicorn src.interfaces.mcp.jira.server:app --host 0.0.0.0 --port 8055
    ports:
      - "8055:8055"
    environment:
      - DATABASE_URL
      - REDIS_URL
  
  mcp-sql:
    build: .
    command: uvicorn src.interfaces.mcp.sql.server:app --host 0.0.0.0 --port 8056
    ports:
      - "8056:8056"
    environment:
      - DATABASE_URL
```

## Authentication

Both servers use header-based authentication:

**Required Headers:**
- `X-Tenant-ID` - Tenant UUID
- `X-User-ID` - User identifier (optional)

**Example:**
```bash
curl -H "X-Tenant-ID: 123e4567-e89b-12d3-a456-426614174000" \
     -H "X-User-ID: user@example.com" \
     http://localhost:8055/tools
```

## Usage Examples

### MCP Jira - Search Issues

**SSE (Recommended):**
```javascript
const eventSource = new EventSource('http://localhost:8055/sse', {
  headers: {
    'X-Tenant-ID': 'your-tenant-id'
  }
});

eventSource.addEventListener('connected', (e) => {
  console.log('Connected:', JSON.parse(e.data));
});

eventSource.addEventListener('heartbeat', (e) => {
  console.log('Heartbeat:', JSON.parse(e.data));
});
```

**REST:**
```bash
curl -X POST http://localhost:8055/tools/invoke \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-tenant-id" \
  -d '{
    "name": "jira.search",
    "arguments": {
      "query": "project = PROJ AND status = Open",
      "limit": 10
    }
  }'
```

### MCP SQL - Query Issues

```bash
curl -X POST http://localhost:8056/query \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-tenant-id" \
  -d '{
    "template_name": "search_issues_by_project",
    "params": {
      "project_key": "PROJ",
      "status": "Open",
      "limit": 50
    }
  }'
```

## Error Handling

All errors follow a standard format:

```json
{
  "code": "validation_error",
  "message": "Invalid JQL query",
  "details": {
    "field": "query",
    "error": "Forbidden keyword: DROP"
  },
  "retry_after": null,
  "request_id": "req_abc123",
  "timestamp": "2025-10-03T10:30:00Z"
}
```

**Error Codes:**
- `validation_error` - Invalid parameters
- `rate_limited` - Rate limit exceeded (includes `retry_after`)
- `not_found` - Resource not found
- `unauthorized` - Authentication failed
- `upstream_4xx` - Jira API client error
- `upstream_5xx` - Jira API server error
- `timeout` - Request timeout
- `network_error` - Network error

## Rate Limiting

MCP Jira implements rate limiting per instance:

**Default Limits:**
- 100 requests per 60 seconds per instance

**Rate Limit Response:**
```json
{
  "code": "rate_limited",
  "message": "Rate limit exceeded for instance",
  "retry_after": 45,
  "request_id": "req_xyz789"
}
```

## Audit Logging

All write operations (create, update, delete) are automatically logged:

**Logged Information:**
- User ID
- Action type
- Resource type and ID
- Before/after values
- Request ID
- IP address
- Timestamp

**Example Audit Log:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "user_id": "user@example.com",
  "action": "create",
  "resource_type": "issue",
  "resource_id": "PROJ-123",
  "changes": {
    "before": null,
    "after": {"summary": "New issue", "status": "Open"}
  },
  "request_id": "req_abc123",
  "timestamp": "2025-10-03T10:30:00Z"
}
```

## Idempotency

Write operations support idempotency keys to prevent duplicate operations:

**Usage:**
```bash
curl -X POST http://localhost:8055/tools/invoke \
  -H "X-Tenant-ID: your-tenant-id" \
  -d '{
    "name": "jira.create_issue",
    "arguments": {
      "project_key": "PROJ",
      "summary": "New issue",
      "idempotency_key": "unique-key-123"
    }
  }'
```

**Behavior:**
- First request: Creates issue and stores result
- Retry with same key: Returns stored result (no duplicate)
- Keys expire after 24 hours

## Monitoring

Both servers expose metrics and health endpoints:

**Health Check:**
```bash
curl http://localhost:8055/health
# {"status": "healthy", "timestamp": "2025-10-03T10:30:00Z"}
```

**Metrics:** (TODO)
- Request count by tool/template
- Request duration histogram
- Error rate
- Rate limit hits

## Development

### Adding a New Jira Tool

1. Add schema to `jira/schemas.py`
2. Implement tool in `jira/tools.py` with `@register_tool` decorator
3. Add tests in `tests/unit/mcp/jira/`

### Adding a New SQL Template

1. Add schema to `sql/schemas.py`
2. Add template to `QUERY_TEMPLATES` in `sql/templates.py`
3. Add schema mapping to `TEMPLATE_SCHEMAS`
4. Add tests in `tests/unit/mcp/sql/`

## Testing

```bash
# Unit tests
pytest tests/unit/mcp/

# Integration tests
pytest tests/integration/mcp/

# E2E tests
pytest tests/e2e/test_mcp_flow.py
```

## Security

- ✅ SQL injection protection (whitelisted templates only)
- ✅ JQL validation (forbidden keywords)
- ✅ Parameter validation with Pydantic
- ✅ Tenant isolation (RLS)
- ✅ Rate limiting
- ⏳ Authentication (TODO: implement proper auth)
- ⏳ Authorization (TODO: implement RBAC)

## TODO

- [ ] Implement proper authentication (JWT/OAuth2)
- [ ] Add authorization/RBAC
- [ ] Add Prometheus metrics
- [ ] Add OpenTelemetry tracing
- [ ] Add request/response logging
- [ ] Add WebSocket support
- [ ] Add batch operations
- [ ] Add caching layer
- [ ] Add circuit breaker for upstream calls
- [ ] Add comprehensive tests

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SSE Starlette](https://github.com/sysid/sse-starlette)

