# Deployment Guide - MCP & SQL Enhancement

**Feature:** 003-mcp-sql-enhancement  
**Version:** 1.0.0  
**Date:** 2025-10-03

---

## 📋 Pre-Deployment Checklist

### Code Review
- [ ] All code reviewed and approved
- [ ] No merge conflicts with main
- [ ] All tests passing
- [ ] Coverage meets threshold (80%+)
- [ ] Documentation complete

### Infrastructure
- [ ] PostgreSQL database available
- [ ] Redis instance available (optional for dev)
- [ ] Environment variables configured
- [ ] Secrets management in place

### Security
- [ ] Authentication strategy decided
- [ ] Rate limits configured appropriately
- [ ] SQL injection protection verified
- [ ] Tenant isolation tested

---

## 🚀 Deployment Steps

### 1. Database Migration

```bash
# Backup database first
pg_dump -h localhost -U ds -d ds_orchestrator > backup_$(date +%Y%m%d).sql

# Run migration
alembic upgrade head

# Verify migration
alembic current
# Should show: 5e27bebd242f (head)
```

**Migration creates:**
- `audit_logs` table
- `idempotency_keys` table
- All necessary indexes

### 2. Environment Configuration

Create `.env` file or set environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# Redis (optional, falls back to in-memory)
REDIS_URL=redis://host:6379/0

# MCP Servers
MCP_JIRA_PORT=8055
MCP_SQL_PORT=8056

# Rate Limiting (optional)
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import sse_starlette; print('SSE installed')"
```

### 4. Start Services

#### Option A: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f mcp-jira
docker-compose logs -f mcp-sql
```

#### Option B: Manual Start

```bash
# Terminal 1 - MCP Jira
uvicorn src.interfaces.mcp.jira.server:app --host 0.0.0.0 --port 8055

# Terminal 2 - MCP SQL
uvicorn src.interfaces.mcp.sql.server:app --host 0.0.0.0 --port 8056
```

#### Option C: Production with Gunicorn

```bash
# MCP Jira
gunicorn src.interfaces.mcp.jira.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8055

# MCP SQL
gunicorn src.interfaces.mcp.sql.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8056
```

### 5. Verify Deployment

```bash
# Run health check
./scripts/health_check.sh

# Or manually
curl http://localhost:8055/health
curl http://localhost:8056/health

# Check tools/templates
curl http://localhost:8055/tools
curl http://localhost:8056/templates

# Check metrics
curl http://localhost:8055/metrics
curl http://localhost:8056/metrics
```

---

## 🔧 Configuration

### Rate Limiting

Default: 100 requests per 60 seconds per instance

To customize:
```python
# In server.py
rate_limiter = RateLimiter(
    redis_client=redis_client,
    default_limit=200,  # Custom limit
    default_window=60,  # Custom window
)
```

### Idempotency TTL

Default: 24 hours

To customize:
```python
# In server.py
idempotency_service = IdempotencyService(
    session=session,
    ttl_hours=48,  # Custom TTL
)
```

### Metrics Collection

Metrics are collected automatically. To export to Prometheus:

```python
# TODO: Add Prometheus exporter
# from prometheus_client import make_asgi_app
# metrics_app = make_asgi_app()
# app.mount("/prometheus", metrics_app)
```

---

## 🔒 Security Hardening

### 1. Authentication

**Current:** Header-based (X-Tenant-ID, X-User-ID)

**Recommended for Production:**

```python
# Add JWT authentication
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/tools/invoke")
async def invoke_tool(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify JWT token
    token = credentials.credentials
    # ... verify token
```

### 2. HTTPS/TLS

Use reverse proxy (nginx, Caddy) for TLS termination:

```nginx
server {
    listen 443 ssl;
    server_name mcp-jira.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Rate Limiting

Configure rate limits based on your needs:

```python
# Per instance
rate_limiter.check(instance_id, limit=100, window=60)

# Per user
rate_limiter.check(user_id, limit=1000, window=3600)
```

### 4. CORS

If needed, configure CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Monitoring

### Health Checks

Set up monitoring for:
- `GET /health` - Overall health
- Database connectivity
- Redis connectivity (if used)

### Metrics

Monitor these key metrics:
- `mcp.jira.tool.invocations` - Tool usage
- `mcp.jira.tool.duration` - Performance
- `mcp.jira.tool.errors` - Error rate
- `mcp.sql.query.executions` - Query usage
- `mcp.sql.query.duration` - Query performance

### Logging

Configure structured logging:

```python
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Log as JSON
logger.info(json.dumps({
    "event": "tool_invocation",
    "tool": "jira.search",
    "duration_ms": 45.2,
    "tenant_id": "...",
}))
```

---

## 🔄 Rollback Plan

If issues occur:

### 1. Stop Services

```bash
docker-compose down
# or
kill <pid>
```

### 2. Rollback Migration

```bash
alembic downgrade -1
```

### 3. Restore Database

```bash
psql -h localhost -U ds -d ds_orchestrator < backup_YYYYMMDD.sql
```

### 4. Revert Code

```bash
git checkout main
```

---

## 📈 Performance Tuning

### Database

```sql
-- Add indexes if needed
CREATE INDEX CONCURRENTLY idx_audit_logs_custom 
ON audit_logs (tenant_id, created_at DESC) 
WHERE action = 'create';

-- Analyze tables
ANALYZE audit_logs;
ANALYZE idempotency_keys;
```

### Connection Pooling

```python
# In database configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
```

### Caching

Consider adding caching for:
- Frequently accessed issues
- Project metadata
- User information

---

## 🧪 Post-Deployment Testing

### 1. Smoke Tests

```bash
# Run demo script
python examples/mcp_demo.py

# Check all endpoints
curl http://localhost:8055/
curl http://localhost:8055/health
curl http://localhost:8055/tools
curl http://localhost:8055/metrics
```

### 2. Load Testing

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Test MCP Jira
hey -n 1000 -c 10 http://localhost:8055/health

# Test MCP SQL
hey -n 1000 -c 10 http://localhost:8056/health
```

### 3. Integration Testing

Test with real AI assistant (Claude Desktop):

```json
// Add to Claude Desktop config
{
  "mcpServers": {
    "jira": {
      "url": "http://localhost:8055/sse",
      "headers": {
        "X-Tenant-ID": "your-tenant-id"
      }
    }
  }
}
```

---

## 📞 Support

### Troubleshooting

**Issue:** Services won't start
- Check logs: `docker-compose logs`
- Verify ports available: `lsof -i :8055`
- Check environment variables

**Issue:** Database connection errors
- Verify DATABASE_URL
- Check PostgreSQL is running
- Verify migrations: `alembic current`

**Issue:** Rate limiting not working
- Check Redis connection
- Falls back to in-memory if Redis unavailable
- Check logs for rate limiter initialization

### Getting Help

1. Check documentation in `src/interfaces/mcp/README.md`
2. Review logs for error messages
3. Run health check: `./scripts/health_check.sh`
4. Check metrics: `curl http://localhost:8055/metrics`

---

## ✅ Deployment Verification

After deployment, verify:

- [ ] All services healthy
- [ ] Database migration successful
- [ ] All 8 MCP tools available
- [ ] All 6 SQL templates available
- [ ] Metrics being collected
- [ ] Audit logs being created
- [ ] Rate limiting working
- [ ] Idempotency working
- [ ] Documentation accessible
- [ ] Demo script runs successfully

---

**Deployment Complete!** 🎉

The MCP & SQL Enhancement feature is now live and ready for use.

