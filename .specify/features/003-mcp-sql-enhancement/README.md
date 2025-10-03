# Feature 003: MCP & SQL Enhancement

## 📋 Overview

Rozšírenie existujúceho MCP a SQL systému pre plnohodnotné multi-source manažérske rozhodovanie. Umožní kombinovať informácie z viacerých Jira inštancií, GitHub, Asana, Linear a ďalších PM nástrojov cez jednotné MCP a SQL rozhranie.

## 🎯 Goals

1. **Multi-Instance Support** - Podpora viacerých Jira inštancií pre jedného tenanta
2. **Multi-Source Support** - Podpora GitHub, Asana, Linear okrem Jira
3. **Enhanced MCP** - 8 Jira tools + 6 SQL query templates
4. **Row-Level Security** - Kompletná tenant izolácia na DB úrovni
5. **Performance** - < 100ms SQL queries, < 500ms MCP calls (p95)
6. **Security** - Audit log, idempotency, rate limiting, encryption

## 📁 Structure

```
.specify/features/003-mcp-sql-enhancement/
├── README.md                  # This file
├── constitution.md            # Quality requirements & principles
├── spec.md                    # Detailed specification
├── clarifications.md          # Schemas, SQL templates, RLS policies
├── plan.md                    # Technical architecture & implementation
├── tasks.md                   # Task breakdown (100+ tasks)
├── implementation.md          # Implementation guide & deployment
└── mcp-config.json           # MCP server configuration
```

## 🚀 Quick Start

### 1. Review Documentation

Read in this order:
1. `constitution.md` - Understand quality requirements
2. `spec.md` - Understand what we're building
3. `clarifications.md` - Understand detailed schemas
4. `plan.md` - Understand technical architecture
5. `tasks.md` - Understand task breakdown
6. `implementation.md` - Start implementing

### 2. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt
cd admin-ui && npm install

# Setup database
docker compose -f docker/docker-compose.dev.yml up -d postgres redis
alembic upgrade head

# Verify setup
pytest tests/unit/ -v
```

### 3. Start Implementation

Follow the implementation order in `implementation.md`:
- Week 1-2: Foundation (DB models, indexes, RLS)
- Week 3-4: MCP Jira (8 tools)
- Week 5-6: MCP SQL (6 templates)
- Week 7-8: Multi-Source (adapters)
- Week 9-10: Admin API & UI
- Week 11-12: Observability & QA

## 🏗️ Architecture

### High-Level Components

```
Admin UI (Next.js)
    ↓
Orchestrator (FastAPI)
    ↓
┌─────────────┬─────────────┬─────────────┐
│  MCP Jira   │  MCP SQL    │  Adapters   │
│  (SSE)      │  (SSE)      │  (Multi)    │
└─────────────┴─────────────┴─────────────┘
    ↓               ↓               ↓
PostgreSQL      PostgreSQL      External APIs
(RLS)           (RLS)           (Jira/GitHub)
```

### Key Technologies

- **Backend:** Python 3.10+, FastAPI, SQLAlchemy 2.0
- **Database:** PostgreSQL 14+ (RLS, JSONB, GIN indexes)
- **Cache:** Redis 6+ (rate limiting, idempotency)
- **Frontend:** Next.js 14+, React, TypeScript
- **Observability:** Prometheus, structured logs, OpenTelemetry

## 📊 Key Features

### MCP Jira Tools (8)

1. `jira.search` - Multi-instance JQL search
2. `jira.get_issue` - Get issue details
3. `jira.create_issue` - Create with idempotency
4. `jira.update_issue` - Update with audit log
5. `jira.transition_issue` - Change status
6. `jira.add_comment` - Add comment (ADF)
7. `jira.link_issues` - Link issues
8. `jira.list_transitions` - Get available transitions

### SQL Query Templates (6)

1. `search_issues_by_project` - Fast project search
2. `get_project_metrics` - Aggregated metrics
3. `search_issues_by_text` - Full-text search (trigram)
4. `get_issue_history` - Change history
5. `get_user_workload` - User workload analysis
6. `lead_time_metrics` - Lead time analytics

### Multi-Source Support

- **Jira** - Cloud & Server
- **GitHub** - Issues & Pull Requests
- **Asana** - Tasks
- **Linear** - Issues (future)
- **ClickUp** - Tasks (future)

## 🔒 Security Features

### Row-Level Security (RLS)
- All tables have RLS enabled
- Tenant isolation at DB level
- Session context: `SET app.current_tenant_id`

### Audit Log
- All write operations logged
- Immutable, append-only
- Includes: who, what, when, changes

### Idempotency
- Write operations support idempotency keys
- 24-hour deduplication window
- Redis-based storage

### Rate Limiting
- 100 rpm per instance (default)
- Token bucket algorithm
- Redis-based

### Encryption
- Credentials encrypted at rest (Fernet)
- TLS 1.3+ in transit
- Secure key management

## 📈 Performance Targets

### Response Times (p95)
- MCP tool calls: < 500ms
- SQL queries: < 100ms
- API endpoints: < 200ms

### Throughput
- 100 rpm per Jira instance
- 1000 req/s API capacity
- 10k issues/min sync

### Database
- Indexed queries: < 50ms
- Full-text search: < 100ms
- Aggregations: < 200ms

## 🧪 Testing

### Coverage Targets
- Unit tests: 80%+
- Integration tests: Key flows
- E2E tests: Happy paths

### Test Commands
```bash
# Unit tests
pytest tests/unit/ -v --cov=src --cov-report=html

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v --slow

# Performance tests
pytest tests/performance/ -v
```

## 📊 Monitoring

### Metrics (Prometheus)
- `mcp_tool_calls_total` - Tool call counter
- `mcp_tool_duration_seconds` - Tool duration histogram
- `sql_query_total` - Query counter
- `sql_query_duration_seconds` - Query duration histogram

### Logs (Structured JSON)
```json
{
  "timestamp": "2025-10-03T10:30:00Z",
  "level": "info",
  "message": "MCP tool executed",
  "tenant_id": "uuid",
  "tool": "jira.search",
  "duration_ms": 150,
  "status": "success"
}
```

### Tracing (OpenTelemetry)
- Distributed tracing across services
- Trace MCP calls, SQL queries, external APIs
- Jaeger UI for visualization

## 🚀 Deployment

### Local Development
```bash
# Start services
docker compose -f docker/docker-compose.dev.yml up -d

# Start MCP servers
python -m src.interfaces.mcp.jira.server --port 8055
python -m src.interfaces.mcp.sql.server --port 8056

# Start orchestrator
python -m orchestrator.app

# Start admin UI
cd admin-ui && npm run dev
```

### Production
```bash
# Build images
docker build -t digital-spiral:latest .

# Run migrations
docker run --rm digital-spiral:latest alembic upgrade head

# Start services
docker compose -f docker/docker-compose.prod.yml up -d
```

## 📚 Documentation

### Spec-Kit Documents
- `constitution.md` - Quality requirements
- `spec.md` - Feature specification
- `clarifications.md` - Detailed schemas
- `plan.md` - Technical plan
- `tasks.md` - Task breakdown
- `implementation.md` - Implementation guide

### External Resources
- [MCP Protocol](https://spec.modelcontextprotocol.io/)
- [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [FastAPI](https://fastapi.tiangolo.com/)

## 🤝 Contributing

### Development Workflow

1. **Clarify** - Review spec and clarifications
2. **Plan** - Review technical plan
3. **Task** - Pick task from tasks.md
4. **Implement** - Follow implementation guide
5. **Test** - Write and run tests
6. **Review** - Code review
7. **Deploy** - Merge and deploy

### Code Quality

- **Type hints** - 100% coverage
- **Docstrings** - All public functions
- **Tests** - 80%+ coverage
- **Linting** - Black, isort, flake8
- **Security** - Bandit, safety

## 📝 Status

- **Version:** 1.0.0
- **Status:** Draft
- **Created:** 2025-10-03
- **Estimated Effort:** 8-12 weeks
- **Total Tasks:** 100+

## 🎯 Success Criteria

### Functional
- [ ] All 8 MCP Jira tools working
- [ ] All 6 SQL templates working
- [ ] Multi-instance support
- [ ] Multi-source support (Jira + GitHub)
- [ ] Admin UI functional

### Non-Functional
- [ ] 80%+ test coverage
- [ ] < 100ms SQL queries (p95)
- [ ] < 500ms MCP calls (p95)
- [ ] RLS enabled and tested
- [ ] Audit log working
- [ ] Rate limiting working

### Production Ready
- [ ] Deployed to staging
- [ ] E2E tests passing
- [ ] Monitoring configured
- [ ] Documentation complete
- [ ] Stakeholder sign-off

## 🔗 Links

- **Project Root:** `/Users/hotovo/Projects/digital-spiral`
- **Feature Spec:** `.specify/features/003-mcp-sql-enhancement/`
- **GitHub Spec-Kit:** https://github.com/github/spec-kit

---

**Next Steps:**
1. Review all spec documents
2. Setup development environment
3. Start with Phase 1: Foundation (Week 1-2)
4. Follow implementation guide

**Questions?**
- Review `clarifications.md` for detailed schemas
- Check `implementation.md` for troubleshooting
- See `tasks.md` for task breakdown

