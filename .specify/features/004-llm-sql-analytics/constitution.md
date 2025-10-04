# LLM + SQL Analytics System - Project Constitution

## Core Principles

### 1. Architecture Philosophy
- **Deterministic over Flexible**: LLM generates structured specs, not raw SQL
- **Security First**: Whitelisted metrics catalog, no arbitrary SQL execution
- **Multi-tenant Native**: All queries isolated by tenant_id/instance_id
- **Performance by Design**: Materialized views, pre-computed metrics, caching
- **Scalable from Day 1**: Job orchestration for large datasets, per-instance sharding

### 2. Technology Stack

#### Backend Core
- **Python 3.11+**: Type hints mandatory, async/await patterns
- **FastAPI**: REST API + SSE for real-time updates
- **SQLAlchemy 2.0**: Async ORM with PostgreSQL
- **PostgreSQL 14+**: JSONB, window functions, materialized views, RLS
- **Redis 6+**: Caching, job queues, rate limiting
- **Celery**: Background job orchestration

#### Analytics Engine
- **AnalyticsSpec DSL**: JSON-based query specification language
- **Metrics Catalog**: Versioned, tested metric definitions
- **Query Builder**: Spec → SQL translation with validation
- **Job Orchestrator**: Celery for long-running queries
- **Chart Renderer**: Vega-Lite for visualization specs

#### AI Integration
- **OpenAI GPT-4**: NL → AnalyticsSpec translation
- **Anthropic Claude**: Alternative provider
- **pgvector**: Semantic search over issue text
- **Prompt Engineering**: Few-shot examples, chain-of-thought

### 3. Code Quality Standards

#### Python
- Type hints mandatory (mypy strict mode)
- No `Any` types without explicit justification
- Pydantic v2 for all DTOs and validation
- Async/await for all I/O operations
- Error handling with custom exception hierarchy

#### SQL
- Parameterized queries only (no string interpolation)
- Window functions for z-scores and percentiles
- Materialized views for expensive aggregations
- GIN indexes for JSONB columns
- Partial indexes for filtered queries

#### Testing
- **pytest**: Unit tests with 90%+ coverage
- **pytest-asyncio**: Async test support
- **Contract tests**: Metrics catalog validation
- **E2E tests**: NL → AnalyticsSpec → SQL → Results
- **Load tests**: Multi-tenant, parallel queries

### 4. Security

#### Query Execution
- **Whitelisted Metrics**: Only pre-defined metrics allowed
- **Parameterized Queries**: No SQL injection possible
- **RLS Enforcement**: Row-level security on all tables
- **Rate Limiting**: Per-tenant, per-user limits
- **Audit Logging**: All queries logged with user context

#### Data Protection
- **Tenant Isolation**: RLS policies on all tables
- **API Token Encryption**: Fernet symmetric encryption
- **Secrets Management**: Environment variables, never in code
- **HTTPS Only**: TLS 1.3 in production
- **CORS**: Strict origin whitelist

#### Input Validation
- **Pydantic Schemas**: All inputs validated
- **Whitelist Validation**: Metrics, dimensions, filters
- **Limit Enforcement**: Max rows, max dimensions, timeout
- **Injection Prevention**: Parameterized queries only

### 5. Performance

#### Database Optimization
- **Materialized Views**: Pre-computed metrics (sprint_stats, issue_stats)
- **Indexes**: 80+ indexes on hot paths
- **Partitioning**: Time-based partitioning for large tables
- **Connection Pooling**: SQLAlchemy async pool
- **Query Timeout**: 30s default, 5min for jobs

#### Caching Strategy
- **Redis Cache**: Query results (TTL: 5min)
- **Cache Key**: Hash of AnalyticsSpec
- **Invalidation**: On data updates (webhooks)
- **Warm Cache**: Pre-compute popular queries

#### Job Orchestration
- **Celery Workers**: 4 workers per instance
- **Priority Queues**: High (interactive), Low (batch)
- **Retry Logic**: Exponential backoff, max 3 retries
- **Idempotency**: Job IDs for duplicate prevention
- **Monitoring**: Flower dashboard

### 6. Metrics Catalog

#### Structure
```python
{
  "name": "sprint_problematic_score",
  "description": "Composite score for sprint health",
  "type": "derived",
  "sql_template": "...",
  "dependencies": ["spillover_ratio", "scope_churn_ratio", ...],
  "weights": {"spillover": 0.25, "churn": 0.20, ...},
  "version": "1.0.0",
  "tested": true
}
```

#### Core Metrics
- **Throughput**: created, closed, velocity
- **Lead Time**: p50, p90, avg (in days)
- **Sprint Health**: spillover_ratio, scope_churn_ratio, accuracy_abs
- **Quality**: reopened_count, bug_count, escaped_defects
- **Capacity**: blocked_hours, wip, stuck_count
- **Composite**: sprint_problematic_score (z-score weighted)

#### Versioning
- Semantic versioning (1.0.0)
- Backward compatibility for 2 versions
- Deprecation warnings in API responses
- Migration scripts for breaking changes

### 7. AnalyticsSpec DSL

#### Structure
```json
{
  "datasource": "warehouse",
  "measures": [
    {"name": "sprint_problematic_score", "agg": "avg"},
    {"name": "spillover_ratio", "agg": "avg"}
  ],
  "dimensions": ["project_key", "sprint_name"],
  "filters": [
    {"field": "instance_id", "op": "in", "value": ["inst1", "inst2"]},
    {"field": "sprint_state", "op": "=", "value": "closed"}
  ],
  "sort": [{"field": "sprint_problematic_score", "dir": "desc"}],
  "limit": 50,
  "chart": {"type": "bar", "x": "sprint_name", "y": "sprint_problematic_score"}
}
```

#### Validation Rules
- Max 10 measures
- Max 5 dimensions
- Max 20 filters
- Max 1000 rows (interactive), 100k (jobs)
- Timeout: 30s (interactive), 5min (jobs)

### 8. API Design

#### Endpoints
- `POST /analytics/run` - Execute AnalyticsSpec (sync)
- `POST /analytics/jobs` - Start async job
- `GET /analytics/jobs/{id}` - Job status
- `GET /analytics/jobs/{id}/result` - Job result
- `GET /analytics/metrics` - List metrics catalog
- `POST /analytics/semantic-search` - Semantic search
- `POST /analytics/charts/render` - Render chart

#### Response Format
```json
{
  "success": true,
  "data": {
    "results": [...],
    "total": 50,
    "query_time_ms": 123,
    "cached": false
  },
  "meta": {
    "spec_version": "1.0.0",
    "metrics_used": ["sprint_problematic_score"],
    "cache_ttl": 300
  }
}
```

### 9. Observability

#### Logging
- Structured JSON logs (ECS format)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Context: tenant_id, user_id, request_id, query_hash
- Sensitive data redaction (API tokens, emails)

#### Metrics
- Prometheus metrics: query_duration, cache_hit_rate, job_queue_length
- Custom metrics: metrics_catalog_size, spec_validation_errors
- Grafana dashboards: Analytics Overview, Job Performance

#### Tracing
- OpenTelemetry spans: NL → Spec → SQL → Results
- Distributed tracing across services
- Jaeger UI for trace visualization

### 10. Development Workflow

#### Git Workflow
- Feature branches: `feature/004-analytics-*`
- PR reviews: 2 approvals required
- CI/CD: GitHub Actions
- Semantic commits: `feat:`, `fix:`, `docs:`, `test:`

#### Testing Strategy
- Unit tests: 90%+ coverage
- Integration tests: DB, Redis, Celery
- Contract tests: Metrics catalog
- E2E tests: NL → Results
- Load tests: 100 concurrent users

#### Documentation
- OpenAPI/Swagger for REST API
- Metrics catalog documentation (auto-generated)
- Architecture Decision Records (ADRs)
- Runbooks for operations

---

## Non-Negotiables

1. **No Raw SQL from LLM**: Only AnalyticsSpec allowed
2. **Tenant Isolation**: RLS on all tables, no exceptions
3. **Type Safety**: Pydantic validation on all inputs
4. **Audit Logging**: All queries logged with context
5. **Performance**: <30s for interactive, <5min for jobs
6. **Testing**: 90%+ coverage, contract tests mandatory
7. **Security**: Parameterized queries, rate limiting, encryption
8. **Observability**: Structured logs, Prometheus metrics, tracing

---

## Success Criteria

### Functional
- ✅ LLM translates NL to AnalyticsSpec with 95%+ accuracy
- ✅ Query execution <30s for 90% of interactive queries
- ✅ Job orchestration handles 100+ concurrent jobs
- ✅ Semantic search returns relevant results (top-5 accuracy >80%)
- ✅ Chart rendering supports 10+ chart types

### Non-Functional
- ✅ 99.9% uptime (3 nines)
- ✅ <100ms p50 latency for cached queries
- ✅ <5s p99 latency for uncached queries
- ✅ Scales to 100 tenants, 1M issues, 10M events
- ✅ Zero SQL injection vulnerabilities

### Quality
- ✅ 90%+ test coverage
- ✅ Zero critical security issues (Snyk, Bandit)
- ✅ <5% error rate in production
- ✅ <1% cache miss rate for popular queries
- ✅ 100% metrics catalog tested

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Owner**: Digital Spiral Team

