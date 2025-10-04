# Implementation Plan: LLM + SQL Analytics System

## Overview

12-week implementation plan for building an AI-powered analytics system with natural language querying, metrics catalog, job orchestration, and semantic search.

## Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  Chat Interface | Metrics Catalog | Results Viewer | Charts │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator (FastAPI)                     │
│  Analytics API | Job Manager | Cache Manager | Auth         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────┬──────────────────┬──────────────────────┐
│   LLM Provider   │  Query Builder   │   Job Orchestrator   │
│  (OpenAI/Claude) │  (Spec → SQL)    │   (Celery)           │
└──────────────────┴──────────────────┴──────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL + Redis                        │
│  Metrics Catalog | Materialized Views | Cache | Job Queue   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend**:
- Python 3.11+, FastAPI, SQLAlchemy 2.0 (async)
- PostgreSQL 14+ (JSONB, window functions, materialized views)
- Redis 6+ (cache, job queue)
- Celery (job orchestration)
- OpenAI GPT-4 / Anthropic Claude (LLM)
- pgvector (semantic search)

**Frontend**:
- React 18+, TypeScript, Tailwind CSS
- TanStack Query (data fetching)
- Recharts / Vega-Lite (charts)
- Monaco Editor (SQL viewer)

**Infrastructure**:
- Docker, docker-compose
- Prometheus, Grafana (monitoring)
- OpenTelemetry (tracing)
- GitHub Actions (CI/CD)

## Database Schema

### New Tables

#### 1. sprints
```sql
CREATE TABLE sprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    instance_id UUID NOT NULL REFERENCES jira_instances(id),
    sprint_id VARCHAR(50) NOT NULL,
    board_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(20) NOT NULL, -- future, active, closed
    goal TEXT,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    complete_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(instance_id, sprint_id)
);
CREATE INDEX idx_sprints_tenant_instance ON sprints(tenant_id, instance_id);
CREATE INDEX idx_sprints_state ON sprints(state);
CREATE INDEX idx_sprints_dates ON sprints(start_date, end_date);
```

#### 2. sprint_issues
```sql
CREATE TABLE sprint_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sprint_id UUID NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL,
    removed_at TIMESTAMPTZ,
    story_points FLOAT,
    completed BOOLEAN DEFAULT FALSE,
    UNIQUE(sprint_id, issue_id)
);
CREATE INDEX idx_sprint_issues_sprint ON sprint_issues(sprint_id);
CREATE INDEX idx_sprint_issues_issue ON sprint_issues(issue_id);
```

#### 3. metrics_catalog
```sql
CREATE TABLE metrics_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL, -- throughput, lead_time, quality, capacity, composite
    sql_template TEXT NOT NULL,
    dependencies JSONB DEFAULT '[]', -- ["spillover_ratio", "scope_churn_ratio"]
    weights JSONB DEFAULT '{}', -- {"spillover": 0.25, "churn": 0.20}
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    deprecated BOOLEAN DEFAULT FALSE,
    tested BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_metrics_catalog_category ON metrics_catalog(category);
CREATE INDEX idx_metrics_catalog_deprecated ON metrics_catalog(deprecated);
```

#### 4. analytics_jobs
```sql
CREATE TABLE analytics_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(100) NOT NULL,
    spec JSONB NOT NULL,
    spec_hash VARCHAR(64) NOT NULL, -- SHA256 of spec
    status VARCHAR(20) NOT NULL, -- queued, running, completed, failed, cancelled
    progress FLOAT DEFAULT 0.0, -- 0.0 to 1.0
    result JSONB,
    error TEXT,
    query_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
CREATE INDEX idx_analytics_jobs_tenant_user ON analytics_jobs(tenant_id, user_id);
CREATE INDEX idx_analytics_jobs_status ON analytics_jobs(status);
CREATE INDEX idx_analytics_jobs_spec_hash ON analytics_jobs(spec_hash);
CREATE INDEX idx_analytics_jobs_created ON analytics_jobs(created_at DESC);
```

#### 5. analytics_cache
```sql
CREATE TABLE analytics_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spec_hash VARCHAR(64) NOT NULL UNIQUE,
    spec JSONB NOT NULL,
    result JSONB NOT NULL,
    query_time_ms INTEGER NOT NULL,
    ttl INTEGER NOT NULL DEFAULT 300, -- seconds
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_analytics_cache_expires ON analytics_cache(expires_at);
```

### Materialized Views

#### 1. mv_sprint_stats_enriched
```sql
CREATE MATERIALIZED VIEW mv_sprint_stats_enriched AS
WITH sprint_metrics AS (
    SELECT
        s.id AS sprint_id,
        s.tenant_id,
        s.instance_id,
        s.name AS sprint_name,
        p.project_key,
        s.state,
        s.start_date,
        s.end_date,
        -- Planned vs Completed
        SUM(si.story_points) FILTER (WHERE si.added_at <= s.start_date) AS planned_sp,
        SUM(si.story_points) FILTER (WHERE si.completed = TRUE) AS completed_sp,
        SUM(si.story_points) FILTER (WHERE si.added_at > s.start_date) AS added_after_start_sp,
        SUM(si.story_points) FILTER (WHERE si.removed_at IS NOT NULL) AS removed_sp,
        -- Quality
        COUNT(*) FILTER (WHERE i.issue_type = 'Bug') AS bug_count,
        COUNT(*) FILTER (WHERE EXISTS (
            SELECT 1 FROM changelogs cl
            WHERE cl.issue_id = i.id AND cl.items @> '[{"field":"status","toString":"Reopened"}]'
        )) AS reopened_count
    FROM sprints s
    LEFT JOIN sprint_issues si ON s.id = si.sprint_id
    LEFT JOIN issues i ON si.issue_id = i.id
    LEFT JOIN projects p ON i.project_id = p.id
    GROUP BY s.id, s.tenant_id, s.instance_id, s.name, p.project_key, s.state, s.start_date, s.end_date
),
z_scores AS (
    SELECT
        *,
        -- Calculate z-scores for composite metric
        (spillover_ratio - AVG(spillover_ratio) OVER ()) / NULLIF(STDDEV(spillover_ratio) OVER (), 0) AS z_spillover,
        (scope_churn_ratio - AVG(scope_churn_ratio) OVER ()) / NULLIF(STDDEV(scope_churn_ratio) OVER (), 0) AS z_churn,
        (reopened_count - AVG(reopened_count) OVER ()) / NULLIF(STDDEV(reopened_count) OVER (), 0) AS z_reopened,
        (bug_count - AVG(bug_count) OVER ()) / NULLIF(STDDEV(bug_count) OVER (), 0) AS z_bugs,
        (accuracy_abs - AVG(accuracy_abs) OVER ()) / NULLIF(STDDEV(accuracy_abs) OVER (), 0) AS z_accuracy
    FROM (
        SELECT
            *,
            removed_sp / NULLIF(planned_sp, 0) AS spillover_ratio,
            added_after_start_sp / NULLIF(planned_sp, 0) AS scope_churn_ratio,
            ABS(completed_sp - planned_sp) / NULLIF(planned_sp, 0) AS accuracy_abs
        FROM sprint_metrics
    ) sub
)
SELECT
    *,
    -- Composite score (default weights)
    (0.25 * COALESCE(z_spillover, 0) +
     0.20 * COALESCE(z_churn, 0) +
     0.20 * COALESCE(z_reopened, 0) +
     0.15 * 0 + -- blocked_hours (TODO)
     0.10 * COALESCE(z_bugs, 0) +
     0.10 * COALESCE(z_accuracy, 0)) AS sprint_problematic_score,
    NOW() AS refreshed_at
FROM z_scores;

CREATE UNIQUE INDEX idx_mv_sprint_stats_enriched_sprint ON mv_sprint_stats_enriched(sprint_id);
CREATE INDEX idx_mv_sprint_stats_enriched_tenant ON mv_sprint_stats_enriched(tenant_id);
CREATE INDEX idx_mv_sprint_stats_enriched_score ON mv_sprint_stats_enriched(sprint_problematic_score DESC);
```

#### 2. mv_issue_comment_stats
```sql
CREATE MATERIALIZED VIEW mv_issue_comment_stats AS
SELECT
    i.id AS issue_id,
    i.tenant_id,
    i.instance_id,
    i.issue_key,
    COUNT(c.id) AS comment_count,
    MAX(c.jira_created_at) AS last_comment_at,
    NOW() AS refreshed_at
FROM issues i
LEFT JOIN comments c ON i.id = c.issue_id
GROUP BY i.id, i.tenant_id, i.instance_id, i.issue_key;

CREATE UNIQUE INDEX idx_mv_issue_comment_stats_issue ON mv_issue_comment_stats(issue_id);
CREATE INDEX idx_mv_issue_comment_stats_count ON mv_issue_comment_stats(comment_count DESC);
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

#### Week 1: Database Schema & Models
**Tasks**:
1. Create migration for new tables (sprints, sprint_issues, metrics_catalog, analytics_jobs, analytics_cache)
2. Create SQLAlchemy models for new tables
3. Create materialized views (mv_sprint_stats_enriched, mv_issue_comment_stats)
4. Add indexes and RLS policies
5. Write unit tests for models

**Deliverables**:
- ✅ Migration file: `006_add_analytics_tables.py`
- ✅ Models: `Sprint`, `SprintIssue`, `MetricsCatalog`, `AnalyticsJob`, `AnalyticsCache`
- ✅ Materialized views created
- ✅ 90%+ test coverage

#### Week 2: Metrics Catalog
**Tasks**:
1. Define core metrics (throughput, lead_time, sprint_health, quality, capacity)
2. Create metrics catalog seeder script
3. Build metrics catalog service (CRUD operations)
4. Write SQL templates for each metric
5. Add contract tests for metrics catalog

**Deliverables**:
- ✅ Metrics catalog JSON file: `metrics_catalog.json`
- ✅ Seeder script: `seed_metrics_catalog.py`
- ✅ Service: `MetricsCatalogService`
- ✅ Contract tests: `test_metrics_catalog_contract.py`

### Phase 2: Query Builder (Week 3-4)

#### Week 3: AnalyticsSpec DSL
**Tasks**:
1. Define AnalyticsSpec Pydantic schema
2. Build validator for AnalyticsSpec
3. Create query builder (Spec → SQL)
4. Add whitelist validation (metrics, dimensions, filters)
5. Write unit tests for query builder

**Deliverables**:
- ✅ Schema: `AnalyticsSpec` (Pydantic)
- ✅ Validator: `AnalyticsSpecValidator`
- ✅ Builder: `QueryBuilder`
- ✅ Tests: `test_query_builder.py`

#### Week 4: Query Execution
**Tasks**:
1. Build query executor (execute SQL, return results)
2. Add caching layer (Redis)
3. Add query timeout and limits
4. Add performance tracking (query_time_ms)
5. Write integration tests

**Deliverables**:
- ✅ Executor: `QueryExecutor`
- ✅ Cache: `AnalyticsCacheService`
- ✅ Tests: `test_query_executor.py`

### Phase 3: LLM Integration (Week 5-6)

#### Week 5: NL → AnalyticsSpec Translation
**Tasks**:
1. Build LLM provider abstraction (OpenAI, Claude)
2. Create prompt templates (few-shot examples)
3. Build NL → AnalyticsSpec translator
4. Add validation and error handling
5. Write E2E tests (NL → Spec → SQL → Results)

**Deliverables**:
- ✅ Provider: `LLMProvider` (abstract), `OpenAIProvider`, `ClaudeProvider`
- ✅ Translator: `NLToSpecTranslator`
- ✅ Prompts: `prompts/analytics_translation.txt`
- ✅ Tests: `test_nl_to_spec.py`

#### Week 6: Semantic Search
**Tasks**:
1. Install pgvector extension
2. Generate embeddings for issues (summary + description)
3. Build semantic search service
4. Add similarity search queries
5. Write integration tests

**Deliverables**:
- ✅ Migration: `007_add_pgvector.py`
- ✅ Service: `SemanticSearchService`
- ✅ Tests: `test_semantic_search.py`

### Phase 4: Job Orchestration (Week 7-8)

#### Week 7: Celery Setup
**Tasks**:
1. Setup Celery with Redis backend
2. Create job tasks (execute_analytics_job)
3. Build job manager service
4. Add job status tracking
5. Write integration tests

**Deliverables**:
- ✅ Celery config: `celery_config.py`
- ✅ Tasks: `analytics_tasks.py`
- ✅ Service: `JobManagerService`
- ✅ Tests: `test_job_manager.py`

#### Week 8: Job API
**Tasks**:
1. Build job API endpoints (start, status, result, cancel)
2. Add SSE endpoint for real-time updates
3. Add job history and cleanup
4. Add idempotency (same spec = same job)
5. Write E2E tests

**Deliverables**:
- ✅ API: `POST /analytics/jobs`, `GET /analytics/jobs/{id}`, `GET /analytics/jobs/{id}/result`
- ✅ SSE: `GET /analytics/jobs/{id}/stream`
- ✅ Tests: `test_job_api.py`

### Phase 5: Analytics API (Week 9-10)

#### Week 9: Core API Endpoints
**Tasks**:
1. Build analytics API router
2. Implement `POST /analytics/run` (sync execution)
3. Implement `GET /analytics/metrics` (list catalog)
4. Implement `GET /analytics/metrics/{name}` (get metric)
5. Add authentication and rate limiting
6. Write API tests

**Deliverables**:
- ✅ Router: `analytics_router.py`
- ✅ Endpoints: `/analytics/run`, `/analytics/metrics`
- ✅ Tests: `test_analytics_api.py`

#### Week 10: Chart Rendering & Export
**Tasks**:
1. Build chart recommendation engine
2. Implement `POST /analytics/charts/render` (Vega-Lite spec)
3. Implement export endpoints (CSV, Excel, JSON)
4. Add async export for large datasets
5. Write integration tests

**Deliverables**:
- ✅ Service: `ChartRecommendationService`
- ✅ Endpoint: `POST /analytics/charts/render`
- ✅ Export: `GET /analytics/export/{job_id}`
- ✅ Tests: `test_chart_rendering.py`

### Phase 6: Frontend (Week 11-12)

#### Week 11: Chat Interface & Results Viewer
**Tasks**:
1. Build chat interface component (React)
2. Integrate LLM API (NL → AnalyticsSpec)
3. Build results viewer (table + chart)
4. Add loading states and error handling
5. Write component tests

**Deliverables**:
- ✅ Components: `ChatInterface`, `ResultsViewer`, `ChartRenderer`
- ✅ Hooks: `useAnalyticsQuery`, `useJobStatus`
- ✅ Tests: `ChatInterface.test.tsx`

#### Week 12: Metrics Catalog UI & Polish
**Tasks**:
1. Build metrics catalog browser
2. Add query suggestions
3. Add export functionality
4. Polish UI/UX (loading, errors, empty states)
5. Write E2E tests (Playwright)

**Deliverables**:
- ✅ Components: `MetricsCatalog`, `QuerySuggestions`
- ✅ E2E tests: `analytics.spec.ts`
- ✅ Documentation: User guide, API docs

## File Structure

```
digital-spiral/
├── src/
│   ├── application/
│   │   └── services/
│   │       ├── analytics/
│   │       │   ├── __init__.py
│   │       │   ├── metrics_catalog_service.py
│   │       │   ├── query_builder.py
│   │       │   ├── query_executor.py
│   │       │   ├── nl_to_spec_translator.py
│   │       │   ├── semantic_search_service.py
│   │       │   ├── job_manager_service.py
│   │       │   ├── chart_recommendation_service.py
│   │       │   └── analytics_cache_service.py
│   │       └── llm/
│   │           ├── __init__.py
│   │           ├── base.py
│   │           ├── openai_provider.py
│   │           └── claude_provider.py
│   ├── domain/
│   │   └── entities/
│   │       ├── sprint.py
│   │       ├── sprint_issue.py
│   │       ├── metrics_catalog.py
│   │       ├── analytics_job.py
│   │       └── analytics_cache.py
│   ├── infrastructure/
│   │   ├── database/
│   │   │   └── models/
│   │   │       ├── sprint.py
│   │   │       ├── sprint_issue.py
│   │   │       ├── metrics_catalog.py
│   │   │       ├── analytics_job.py
│   │   │       └── analytics_cache.py
│   │   ├── external/
│   │   │   └── llm/
│   │   │       ├── openai_client.py
│   │   │       └── claude_client.py
│   │   └── queue/
│   │       ├── celery_config.py
│   │       └── analytics_tasks.py
│   └── interfaces/
│       ├── api/
│       │   └── analytics/
│       │       ├── __init__.py
│       │       ├── router.py
│       │       ├── schemas.py
│       │       └── dependencies.py
│       └── mcp/
│           └── analytics/
│               ├── server.py
│               └── tools.py
├── migrations/
│   └── versions/
│       ├── 006_add_analytics_tables.py
│       └── 007_add_pgvector.py
├── scripts/
│   ├── seed_metrics_catalog.py
│   └── refresh_materialized_views.py
├── tests/
│   ├── unit/
│   │   └── application/
│   │       └── services/
│   │           └── analytics/
│   │               ├── test_metrics_catalog_service.py
│   │               ├── test_query_builder.py
│   │               ├── test_query_executor.py
│   │               ├── test_nl_to_spec_translator.py
│   │               └── test_semantic_search_service.py
│   ├── integration/
│   │   └── analytics/
│   │       ├── test_analytics_api.py
│   │       ├── test_job_manager.py
│   │       └── test_semantic_search.py
│   ├── contract/
│   │   └── test_metrics_catalog_contract.py
│   └── e2e/
│       └── analytics/
│           └── test_nl_to_results.py
├── admin-ui/
│   └── src/
│       ├── components/
│       │   └── analytics/
│       │       ├── ChatInterface.tsx
│       │       ├── ResultsViewer.tsx
│       │       ├── ChartRenderer.tsx
│       │       ├── MetricsCatalog.tsx
│       │       └── QuerySuggestions.tsx
│       ├── hooks/
│       │   └── analytics/
│       │       ├── useAnalyticsQuery.ts
│       │       ├── useJobStatus.ts
│       │       └── useMetricsCatalog.ts
│       └── lib/
│           └── analytics/
│               ├── api-client.ts
│               └── types.ts
└── specs/
    └── 004-llm-sql-analytics/
        ├── constitution.md
        ├── spec.md
        ├── plan.md
        ├── tasks.md
        ├── README.md
        └── AUGGIE_GUIDE.md
```

## Testing Strategy

### Unit Tests (90%+ coverage)
- Metrics catalog service
- Query builder (Spec → SQL)
- Query executor
- NL → Spec translator
- Semantic search service
- Job manager service
- Chart recommendation service

### Integration Tests
- Analytics API endpoints
- Job orchestration (Celery)
- Semantic search (pgvector)
- Cache layer (Redis)
- Database queries (PostgreSQL)

### Contract Tests
- Metrics catalog schema validation
- AnalyticsSpec schema validation
- SQL template validation

### E2E Tests
- NL query → AnalyticsSpec → SQL → Results
- Job submission → Status polling → Result retrieval
- Semantic search → Filter → Results
- Chart rendering → Export

### Load Tests
- 100 concurrent users per tenant
- 1000 queries per minute
- Multi-instance queries (10 instances)
- Large result sets (100k rows)

## Deployment

### Docker Compose
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg14
    environment:
      POSTGRES_DB: digital_spiral
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  celery_worker:
    build: .
    command: celery -A src.infrastructure.queue.celery_config worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/digital_spiral
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis

  orchestrator:
    build: .
    command: uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/digital_spiral
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
      - celery_worker

  admin_ui:
    build: ./admin-ui
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - orchestrator
```

## Monitoring

### Prometheus Metrics
- `analytics_query_duration_seconds` - Query execution time
- `analytics_cache_hit_rate` - Cache hit rate
- `analytics_job_queue_length` - Job queue length
- `analytics_job_duration_seconds` - Job execution time
- `analytics_spec_validation_errors_total` - Validation errors

### Grafana Dashboards
- **Analytics Overview**: Query volume, cache hit rate, error rate
- **Job Performance**: Queue length, execution time, success rate
- **Metrics Catalog**: Metric usage, deprecation warnings

### Alerts
- Query timeout rate >5%
- Cache hit rate <80%
- Job queue length >100
- Error rate >5%

## Success Criteria

### Functional
- ✅ 95%+ accuracy for NL → AnalyticsSpec translation
- ✅ 90% of queries complete in <30s
- ✅ 99% of jobs complete in <5min
- ✅ 80%+ semantic search top-5 accuracy
- ✅ 10+ chart types supported

### Performance
- ✅ <100ms p50 latency (cached)
- ✅ <5s p99 latency (uncached)
- ✅ 80%+ cache hit rate
- ✅ 100 concurrent users per tenant
- ✅ Scales to 100 tenants, 1M issues

### Quality
- ✅ 90%+ test coverage
- ✅ Zero SQL injection vulnerabilities
- ✅ <5% error rate in production
- ✅ 99.9% uptime (3 nines)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-04
**Owner**: Digital Spiral Team

