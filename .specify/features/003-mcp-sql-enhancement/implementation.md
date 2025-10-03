# Implementation Guide - MCP & SQL Enhancement

## 🚀 Getting Started

### Prerequisites

1. **Environment Setup**
```bash
# Install dependencies
pip install -r requirements.txt
cd admin-ui && npm install

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration
```

2. **Database Setup**
```bash
# Start PostgreSQL + Redis
docker compose -f docker/docker-compose.dev.yml up -d postgres redis

# Run migrations
alembic upgrade head

# Verify RLS is enabled
psql $DATABASE_URL -c "\d+ work_items"
```

3. **Verify Extensions**
```bash
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm', 'btree_gin');"
```

## 📝 Implementation Order

### Week 1-2: Foundation

#### Day 1-3: Database Models
```bash
# Create models
touch src/infrastructure/database/models/source_instance.py
touch src/infrastructure/database/models/audit_log.py
touch src/infrastructure/database/models/idempotency_key.py

# Create migrations
alembic revision --autogenerate -m "Add source_instances model"
alembic revision --autogenerate -m "Enhance work_items for multi-source"
alembic revision --autogenerate -m "Add audit_log model"
alembic revision --autogenerate -m "Add idempotency_keys model"

# Apply migrations
alembic upgrade head

# Run tests
pytest tests/unit/database/models/
```

#### Day 4-5: Indexes & Performance
```bash
# Create index migrations
alembic revision -m "Add work_items indexes"
alembic revision -m "Add JSONB GIN indexes"
alembic revision -m "Add trigram index for full-text search"

# Apply migrations
alembic upgrade head

# Run EXPLAIN ANALYZE tests
pytest tests/performance/test_query_plans.py -v
```

#### Day 6-7: RLS Implementation
```bash
# Create RLS migration
alembic revision -m "Enable RLS on all tenant tables"

# Edit migration file with policies
# See: src/infrastructure/database/rls/policies.sql

# Apply migration
alembic upgrade head

# Test RLS isolation
pytest tests/integration/database/test_rls.py -v
```

### Week 3-4: MCP Jira

#### Day 8-10: Schemas & Server
```bash
# Create MCP Jira structure
mkdir -p src/interfaces/mcp/jira
touch src/interfaces/mcp/jira/__init__.py
touch src/interfaces/mcp/jira/schemas.py
touch src/interfaces/mcp/jira/errors.py
touch src/interfaces/mcp/jira/server.py
touch src/interfaces/mcp/jira/router.py
touch src/interfaces/mcp/jira/tools.py

# Implement schemas
# See: clarifications.md for detailed schemas

# Run schema tests
pytest tests/unit/mcp/jira/test_schemas.py -v
```

#### Day 11-14: Tool Implementations
```bash
# Implement tools one by one
# 1. jira.search
# 2. jira.get_issue
# 3. jira.create_issue
# 4. jira.update_issue
# 5. jira.transition_issue
# 6. jira.add_comment
# 7. jira.link_issues
# 8. jira.list_transitions

# Test each tool
pytest tests/unit/mcp/jira/test_search.py -v
pytest tests/unit/mcp/jira/test_get_issue.py -v
# ... etc
```

#### Day 15-16: Audit & Idempotency
```bash
# Create services
mkdir -p src/application/services
touch src/application/services/audit_log_service.py
touch src/application/services/idempotency_service.py
touch src/application/services/rate_limiter.py

# Implement services
# See: plan.md for implementation details

# Run service tests
pytest tests/unit/services/ -v
```

### Week 5-6: MCP SQL

#### Day 17-19: Query Templates
```bash
# Create MCP SQL structure
mkdir -p src/interfaces/mcp/sql
touch src/interfaces/mcp/sql/__init__.py
touch src/interfaces/mcp/sql/templates.py
touch src/interfaces/mcp/sql/schemas.py
touch src/interfaces/mcp/sql/server.py
touch src/interfaces/mcp/sql/router.py

# Implement all 6 templates
# See: clarifications.md for SQL templates

# Test templates
pytest tests/unit/mcp/sql/ -v
```

#### Day 20-21: Performance & Security
```bash
# Run EXPLAIN ANALYZE on all templates
pytest tests/performance/test_sql_templates.py -v

# Run SQL injection tests
pytest tests/security/test_sql_injection.py -v

# Verify query performance
# All queries should be < 100ms (p95)
```

### Week 7-8: Multi-Source Support

#### Day 22-24: Adapters
```bash
# Create adapter structure
mkdir -p src/infrastructure/external/adapters
touch src/infrastructure/external/adapters/__init__.py
touch src/infrastructure/external/adapters/base.py
touch src/infrastructure/external/adapters/jira_adapter.py
touch src/infrastructure/external/adapters/github_adapter.py
touch src/infrastructure/external/adapters/asana_adapter.py

# Implement adapters
# See: plan.md for adapter implementations

# Test adapters
pytest tests/unit/adapters/ -v
```

#### Day 25-26: Normalization
```bash
# Create domain services
mkdir -p src/domain/services
touch src/domain/services/status_normalizer.py
touch src/domain/services/field_mapper.py

# Implement normalization logic
# See: spec.md for status mapping

# Test normalization
pytest tests/unit/domain/ -v
```

#### Day 27-28: Factory & Integration
```bash
# Create adapter factory
touch src/application/services/source_adapter_factory.py

# Implement factory
# See: plan.md for factory implementation

# Integration tests
pytest tests/integration/adapters/ -v
```

### Week 9-10: Admin API & UI

#### Day 29-32: REST Endpoints
```bash
# Create REST structure
mkdir -p src/interfaces/rest/admin
touch src/interfaces/rest/admin/__init__.py
touch src/interfaces/rest/admin/instances.py
touch src/interfaces/rest/admin/sync.py

# Implement all 8 endpoints
# See: tasks.md for endpoint list

# Test endpoints
pytest tests/integration/rest/ -v
```

#### Day 33-36: Admin UI
```bash
# Create Next.js pages
cd admin-ui
mkdir -p src/app/instances
touch src/app/instances/page.tsx
touch src/app/instances/new/page.tsx
touch src/app/instances/[id]/page.tsx

# Implement UI components
# See: tasks.md for UI requirements

# Test UI
npm run test
npm run build
```

### Week 11-12: Observability & QA

#### Day 37-39: Metrics & Logging
```bash
# Create observability structure
mkdir -p src/infrastructure/observability
touch src/infrastructure/observability/__init__.py
touch src/infrastructure/observability/metrics.py
touch src/infrastructure/observability/logging.py
touch src/infrastructure/observability/tracing.py

# Implement observability
# See: plan.md for metrics/logging

# Add /metrics endpoint
touch src/interfaces/rest/metrics.py

# Test metrics
curl http://localhost:7010/metrics
```

#### Day 40-42: E2E Tests
```bash
# Create E2E test structure
mkdir -p tests/e2e
touch tests/e2e/__init__.py
touch tests/e2e/test_jira_instance_flow.py
touch tests/e2e/test_multi_instance_queries.py
touch tests/e2e/test_cross_source_aggregation.py

# Run E2E tests
pytest tests/e2e/ -v --slow
```

## 🧪 Testing Strategy

### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v --cov=src --cov-report=html

# Coverage target: 80%+
# Check coverage report
open htmlcov/index.html
```

### Integration Tests
```bash
# Start test containers
docker compose -f docker/docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Stop test containers
docker compose -f docker/docker-compose.test.yml down
```

### E2E Tests
```bash
# Start all services
docker compose -f docker/docker-compose.dev.yml up -d

# Run E2E tests
pytest tests/e2e/ -v --slow

# Stop services
docker compose -f docker/docker-compose.dev.yml down
```

### Performance Tests
```bash
# Run EXPLAIN ANALYZE tests
pytest tests/performance/ -v

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:7010
```

## 🚀 Deployment

### Local Development
```bash
# Start all services
docker compose -f docker/docker-compose.dev.yml up -d

# Start MCP Jira server
python -m src.interfaces.mcp.jira.server --port 8055

# Start MCP SQL server
python -m src.interfaces.mcp.sql.server --port 8056

# Start orchestrator
python -m orchestrator.app

# Start admin UI
cd admin-ui && npm run dev
```

### Production
```bash
# Build Docker images
docker build -t digital-spiral:latest .

# Run migrations
docker run --rm digital-spiral:latest alembic upgrade head

# Start services
docker compose -f docker/docker-compose.prod.yml up -d

# Verify health
curl http://localhost:7010/health
curl http://localhost:8055/health
curl http://localhost:8056/health
```

## 🔧 Configuration

### MCP Configuration

Create `~/.config/auggie/mcp.json`:
```json
{
  "mcpServers": {
    "jira-mcp": {
      "transport": "sse",
      "url": "http://localhost:8055/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    },
    "sql-mcp": {
      "transport": "sse",
      "url": "http://localhost:8056/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5433/digital_spiral
POSTGRES_USER=digital_spiral
POSTGRES_PASSWORD=dev_password
POSTGRES_DB=digital_spiral

# Redis
REDIS_URL=redis://localhost:6379/0

# Jira (for testing)
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Observability
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
TRACING_ENABLED=true
```

## 📊 Monitoring

### Prometheus Metrics

```bash
# View metrics
curl http://localhost:7010/metrics

# Key metrics:
# - mcp_tool_calls_total{tool="jira.search",status="success"}
# - mcp_tool_duration_seconds{tool="jira.search"}
# - sql_query_total{template="search_issues_by_project",status="success"}
# - sql_query_duration_seconds{template="search_issues_by_project"}
```

### Logs

```bash
# View structured logs
docker compose logs -f orchestrator

# Filter by tenant
docker compose logs orchestrator | jq 'select(.tenant_id == "demo")'

# Filter by error level
docker compose logs orchestrator | jq 'select(.level == "error")'
```

### Tracing

```bash
# View traces in Jaeger
open http://localhost:16686

# Search for traces by operation
# - mcp.jira.search
# - mcp.sql.query_template
```

## 🐛 Troubleshooting

### Common Issues

#### 1. RLS Not Working
```bash
# Check if RLS is enabled
psql $DATABASE_URL -c "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';"

# Check policies
psql $DATABASE_URL -c "\d+ work_items"

# Verify session context
psql $DATABASE_URL -c "SHOW app.current_tenant_id;"
```

#### 2. Rate Limiting Issues
```bash
# Check Redis connection
redis-cli ping

# Check rate limit keys
redis-cli keys "rate_limit:*"

# Reset rate limit for instance
redis-cli del "rate_limit:INSTANCE_ID"
```

#### 3. Slow Queries
```bash
# Check query plans
psql $DATABASE_URL -c "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM work_items WHERE tenant_id = 'demo' AND project_key = 'PROJ';"

# Check indexes
psql $DATABASE_URL -c "\di+ work_items*"

# Check table statistics
psql $DATABASE_URL -c "SELECT * FROM pg_stat_user_tables WHERE relname = 'work_items';"
```

## 📚 Resources

### Documentation
- [MCP Protocol Spec](https://spec.modelcontextprotocol.io/)
- [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/docs)

### Tools
- [Alembic](https://alembic.sqlalchemy.org/)
- [Pytest](https://docs.pytest.org/)
- [Prometheus](https://prometheus.io/docs/)
- [Redis](https://redis.io/docs/)

---

**Version:** 1.0.0  
**Created:** 2025-10-03  
**Status:** Draft

