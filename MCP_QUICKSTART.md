# MCP Servers - Quick Start Guide

This guide will help you get the MCP (Model Context Protocol) servers up and running quickly.

## Prerequisites

1. **Python 3.10+** installed
2. **PostgreSQL** database running
3. **Redis** (optional, for production rate limiting)
4. **Environment variables** configured

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
# Apply all migrations including audit_log and idempotency_keys
alembic upgrade head
```

### 3. Set Environment Variables

Create a `.env` file or export these variables:

```bash
# Database
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/digital_spiral"

# Redis (optional, for rate limiting)
export REDIS_URL="redis://localhost:6379/0"

# Server Configuration
export MCP_JIRA_PORT=8055
export MCP_SQL_PORT=8056
```

## Running the Servers

### Option 1: Run Individually

**Terminal 1 - MCP Jira Server:**
```bash
python -m src.interfaces.mcp.jira.server
# or
uvicorn src.interfaces.mcp.jira.server:app --host 0.0.0.0 --port 8055 --reload
```

**Terminal 2 - MCP SQL Server:**
```bash
python -m src.interfaces.mcp.sql.server
# or
uvicorn src.interfaces.mcp.sql.server:app --host 0.0.0.0 --port 8056 --reload
```

### Option 2: Run with Docker Compose

```bash
docker-compose up mcp-jira mcp-sql
```

## Testing the Servers

### 1. Health Check

```bash
# MCP Jira
curl http://localhost:8055/health

# MCP SQL
curl http://localhost:8056/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-03T10:30:00Z"
}
```

### 2. List Available Tools/Templates

**MCP Jira:**
```bash
curl http://localhost:8055/tools
```

Response:
```json
{
  "tools": ["jira.search", "jira.get_issue"],
  "count": 2
}
```

**MCP SQL:**
```bash
curl http://localhost:8056/templates
```

Response:
```json
{
  "templates": [
    "search_issues_by_project",
    "get_project_metrics",
    "search_issues_by_text",
    "get_issue_history",
    "get_user_workload",
    "lead_time_metrics"
  ],
  "count": 6
}
```

### 3. Test SSE Connection

**Using curl:**
```bash
curl -N -H "X-Tenant-ID: your-tenant-uuid" http://localhost:8055/sse
```

You should see:
```
event: connected
data: {"server":"mcp-jira","version":"1.0.0","tenant_id":"...","timestamp":"..."}

event: heartbeat
data: {"timestamp":"..."}
```

### 4. Invoke a Tool

**Search Jira Issues:**
```bash
curl -X POST http://localhost:8055/tools/invoke \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-tenant-uuid" \
  -H "X-User-ID: user@example.com" \
  -d '{
    "name": "jira.search",
    "arguments": {
      "query": "project = PROJ AND status = Open",
      "limit": 10
    }
  }'
```

**Execute SQL Query:**
```bash
curl -X POST http://localhost:8056/query \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-tenant-uuid" \
  -d '{
    "template_name": "search_issues_by_project",
    "params": {
      "project_key": "PROJ",
      "status": "Open",
      "limit": 50
    }
  }'
```

## Common Issues

### Issue 1: "Missing tenant ID" Error

**Problem:** Authentication header not provided

**Solution:**
```bash
# Always include X-Tenant-ID header
curl -H "X-Tenant-ID: your-tenant-uuid" http://localhost:8055/tools
```

### Issue 2: Database Connection Error

**Problem:** Cannot connect to PostgreSQL

**Solution:**
1. Check DATABASE_URL is correct
2. Ensure PostgreSQL is running
3. Verify migrations are applied: `alembic upgrade head`

### Issue 3: Rate Limit Error

**Problem:** "Rate limit exceeded" error

**Solution:**
1. Wait for the retry_after period
2. Or reset rate limit (development only):
   ```python
   from src.application.services.rate_limiter import RateLimiter
   # Reset for specific instance
   await rate_limiter.reset(instance_id)
   ```

### Issue 4: Redis Connection Error

**Problem:** Cannot connect to Redis

**Solution:**
1. For development, the servers will fall back to in-memory rate limiting
2. For production, ensure Redis is running and REDIS_URL is correct

## Development Tips

### 1. Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
uvicorn src.interfaces.mcp.jira.server:app --log-level debug --reload
```

### 2. Test with Different Tenants

```bash
# Tenant 1
curl -H "X-Tenant-ID: tenant-1-uuid" http://localhost:8055/tools/invoke ...

# Tenant 2
curl -H "X-Tenant-ID: tenant-2-uuid" http://localhost:8055/tools/invoke ...
```

### 3. Monitor Rate Limits

```python
from src.application.services.rate_limiter import RateLimiter

# Get remaining requests
remaining = await rate_limiter.get_remaining(instance_id)
print(f"Remaining requests: {remaining}")
```

### 4. View Audit Logs

```sql
-- View recent audit logs
SELECT * FROM audit_logs 
WHERE tenant_id = 'your-tenant-uuid'
ORDER BY created_at DESC 
LIMIT 10;
```

### 5. Check Idempotency Keys

```sql
-- View active idempotency keys
SELECT * FROM idempotency_keys 
WHERE tenant_id = 'your-tenant-uuid'
AND expires_at > NOW()
ORDER BY created_at DESC;
```

## Next Steps

1. **Implement Additional Tools:**
   - Add `jira.create_issue`, `jira.update_issue`, etc.
   - See `src/interfaces/mcp/jira/tools.py`

2. **Add Tests:**
   - Unit tests: `tests/unit/mcp/`
   - Integration tests: `tests/integration/mcp/`

3. **Configure Production:**
   - Set up proper authentication (JWT/OAuth2)
   - Configure Redis for rate limiting
   - Add monitoring and metrics
   - Set up logging

4. **Integrate with AI Assistant:**
   - Configure MCP client
   - Test with Claude Desktop or other MCP clients
   - See `.specify/features/003-mcp-sql-enhancement/mcp-config.json`

## Resources

- **MCP Documentation:** `src/interfaces/mcp/README.md`
- **Feature Spec:** `.specify/features/003-mcp-sql-enhancement/spec.md`
- **Implementation Summary:** `IMPLEMENTATION_SUMMARY.md`
- **MCP Protocol:** https://modelcontextprotocol.io/

## Support

For issues or questions:
1. Check the logs: `tail -f logs/mcp-jira.log`
2. Review error responses for `request_id` and trace
3. Check database for audit logs
4. Verify environment variables are set correctly

---

**Last Updated:** 2025-10-03  
**Version:** 1.0.0

