# 🤖 LLM + SQL Analytics System - Complete Summary

## 📋 Overview

**Feature 004: LLM + SQL Analytics System** je AI-powered analytický systém, ktorý umožňuje používateľom dotazovať sa na Jira dáta pomocou prirodzeného jazyka. Systém prekladá natural language dotazy do štruktúrovaného AnalyticsSpec (DSL), vykonáva ich proti katalógu metrík a vracia výsledky s odporúčaniami pre grafy.

**Status**: 📋 Specification Phase  
**Timeline**: 12 týždňov (3 mesiace)  
**Team**: Backend (2), Frontend (1), QA (1)

---

## 🎯 Kľúčové Vlastnosti

### 1. Natural Language Querying
- **Vstup**: "Ukáž mi najproblematickejšie sprinty za posledných 6 mesiacov"
- **LLM**: Preloží do AnalyticsSpec (OpenAI GPT-4 / Anthropic Claude)
- **Validácia**: Overí proti katalógu metrík
- **Exekúcia**: Spustí SQL dotaz
- **Výstup**: Výsledky + odporúčanie grafu

### 2. Metrics Catalog
- **25+ Predefinovaných Metrík**: throughput, lead time, sprint health, quality, capacity
- **Verzované**: Semantic versioning (1.0.0)
- **Testované**: Contract tests pre všetky metriky
- **Dokumentované**: Auto-generovaná dokumentácia

### 3. Job Orchestration
- **Sync Execution**: <30s dotazy sa vykonajú okamžite
- **Async Execution**: >30s dotazy sa vykonajú ako Celery joby
- **Progress Tracking**: Real-time status updates cez SSE
- **Idempotency**: Rovnaký spec = rovnaký job ID

### 4. Semantic Search
- **pgvector**: Vector embeddings pre issues
- **Similarity Search**: Nájdi issues podľa významu, nie len kľúčových slov
- **Multi-language**: Angličtina, Slovenčina, Čeština

### 5. Chart Rendering
- **Auto-recommendation**: Na základe tvaru dát
- **10+ Typov Grafov**: Bar, line, scatter, heatmap, box plot, atď.
- **Vega-Lite**: Interaktívne, responzívne grafy

---

## 🏗️ Architektúra

### High-Level Komponenty

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

### Tech Stack

**Backend**:
- Python 3.11+, FastAPI, SQLAlchemy 2.0 (async)
- PostgreSQL 14+ (JSONB, window functions, materialized views, pgvector)
- Redis 6+ (cache, job queue)
- Celery (job orchestration)
- OpenAI GPT-4 / Anthropic Claude (LLM)

**Frontend**:
- React 18+, TypeScript, Tailwind CSS
- TanStack Query (data fetching)
- Recharts / Vega-Lite (charts)
- Monaco Editor (SQL viewer)

---

## 📊 Implementačné Fázy

### Phase 1: Foundation (Week 1-2)
**Cieľ**: Database schema, models, materialized views, metrics catalog

**Tasks**:
- ✅ Create migration for new tables (sprints, sprint_issues, metrics_catalog, analytics_jobs, analytics_cache)
- ✅ Create SQLAlchemy models
- ✅ Create materialized views (mv_sprint_stats_enriched, mv_issue_comment_stats)
- ✅ Seed metrics catalog (25+ metrics)
- ✅ Write unit tests (90%+ coverage)

**Deliverables**:
- Migration: `006_add_analytics_tables.py`
- Models: `Sprint`, `SprintIssue`, `MetricsCatalog`, `AnalyticsJob`, `AnalyticsCache`
- Seeder: `seed_metrics_catalog.py`

### Phase 2: Query Builder (Week 3-4)
**Cieľ**: AnalyticsSpec DSL, query builder, query executor, caching

**Tasks**:
- ✅ Define AnalyticsSpec Pydantic schema
- ✅ Build validator for AnalyticsSpec
- ✅ Create query builder (Spec → SQL)
- ✅ Build query executor
- ✅ Add caching layer (Redis)
- ✅ Write integration tests

**Deliverables**:
- Schema: `AnalyticsSpec` (Pydantic)
- Builder: `QueryBuilder`
- Executor: `QueryExecutor`
- Cache: `AnalyticsCacheService`

### Phase 3: LLM Integration (Week 5-6)
**Cieľ**: NL → AnalyticsSpec translation, semantic search

**Tasks**:
- ✅ Build LLM provider abstraction (OpenAI, Claude)
- ✅ Create prompt templates (few-shot examples)
- ✅ Build NL → AnalyticsSpec translator
- ✅ Install pgvector extension
- ✅ Build semantic search service
- ✅ Write E2E tests (NL → Spec → SQL → Results)

**Deliverables**:
- Provider: `LLMProvider`, `OpenAIProvider`, `ClaudeProvider`
- Translator: `NLToSpecTranslator`
- Service: `SemanticSearchService`

### Phase 4: Job Orchestration (Week 7-8)
**Cieľ**: Celery setup, job manager, job API, SSE

**Tasks**:
- ✅ Setup Celery with Redis backend
- ✅ Create job tasks (execute_analytics_job)
- ✅ Build job manager service
- ✅ Build job API endpoints (start, status, result, cancel)
- ✅ Add SSE endpoint for real-time updates
- ✅ Write integration tests

**Deliverables**:
- Celery config: `celery_config.py`
- Tasks: `analytics_tasks.py`
- Service: `JobManagerService`
- API: `POST /analytics/jobs`, `GET /analytics/jobs/{id}`

### Phase 5: Analytics API (Week 9-10)
**Cieľ**: Core API endpoints, chart rendering, export

**Tasks**:
- ✅ Build analytics API router
- ✅ Implement `POST /analytics/run` (sync execution)
- ✅ Implement `GET /analytics/metrics` (list catalog)
- ✅ Build chart recommendation engine
- ✅ Implement export endpoints (CSV, Excel, JSON)
- ✅ Write API tests

**Deliverables**:
- Router: `analytics_router.py`
- Endpoints: `/analytics/run`, `/analytics/metrics`, `/analytics/charts/render`
- Service: `ChartRecommendationService`

### Phase 6: Frontend (Week 11-12)
**Cieľ**: Chat interface, results viewer, metrics catalog UI

**Tasks**:
- ✅ Build chat interface component (React)
- ✅ Integrate LLM API (NL → AnalyticsSpec)
- ✅ Build results viewer (table + chart)
- ✅ Build metrics catalog browser
- ✅ Add query suggestions
- ✅ Write E2E tests (Playwright)

**Deliverables**:
- Components: `ChatInterface`, `ResultsViewer`, `ChartRenderer`, `MetricsCatalog`
- Hooks: `useAnalyticsQuery`, `useJobStatus`
- E2E tests: `analytics.spec.ts`

---

## 📚 Príklady Použitia

### 1. Natural Language Query

**Dotaz**: "Ukáž mi najproblematickejšie sprinty za posledných 6 mesiacov"

**Request**:
```bash
curl -X POST http://localhost:8000/analytics/run \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo" \
  -d '{
    "query": "Show me the most problematic sprints in the last 6 months"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "sprint_name": "Sprint 42",
        "project_key": "PROJ1",
        "sprint_problematic_score": 2.34,
        "spillover_ratio": 0.45,
        "scope_churn_ratio": 0.32,
        "reopened_count": 5,
        "bug_count": 8
      }
    ],
    "total": 10,
    "query_time_ms": 234
  },
  "chart": {
    "type": "bar",
    "x": "sprint_name",
    "y": "sprint_problematic_score",
    "series": "project_key"
  }
}
```

### 2. Semantic Search

**Dotaz**: "Nájdi sprinty s diskusiami o rollbackoch"

**Request**:
```bash
curl -X POST http://localhost:8000/analytics/semantic-search \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo" \
  -d '{
    "query": "rollback discussions",
    "project_keys": ["PROJ1"],
    "top_k": 10
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "issue_ids": ["PROJ1-123", "PROJ1-456", "PROJ1-789"],
    "scores": [0.95, 0.87, 0.82]
  }
}
```

### 3. Async Job

**Dotaz**: "Porovnaj lead time naprieč 10 Jira inštanciami za posledný rok"

**Request**:
```bash
curl -X POST http://localhost:8000/analytics/jobs \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo" \
  -d '{
    "spec": {
      "datasource": "warehouse",
      "measures": [{"name": "lead_time_p50_days", "agg": "avg"}],
      "dimensions": ["instance_id", "project_key"],
      "filters": [
        {"field": "instance_id", "op": "in", "value": ["inst1", "inst2", ...]},
        {"field": "created_at", "op": ">=", "value": "2024-01-01"}
      ],
      "limit": 1000
    }
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued"
  }
}
```

**Check Status**:
```bash
curl http://localhost:8000/analytics/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-Tenant-ID: demo"
```

**Response**:
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "progress": 0.65,
    "created_at": "2025-10-04T10:00:00Z",
    "started_at": "2025-10-04T10:00:05Z"
  }
}
```

---

## 🔒 Bezpečnosť

### Query Execution
- ✅ **Whitelisted Metrics**: Len predefinované metriky
- ✅ **Parameterized Queries**: Žiadna SQL injection
- ✅ **RLS Enforcement**: Row-level security na všetkých tabuľkách
- ✅ **Rate Limiting**: Per-tenant, per-user limity
- ✅ **Audit Logging**: Všetky dotazy logované s kontextom

### Data Protection
- ✅ **Tenant Isolation**: RLS policies na všetkých tabuľkách
- ✅ **API Token Encryption**: Fernet symmetric encryption
- ✅ **Secrets Management**: Environment variables, nikdy v kóde
- ✅ **HTTPS Only**: TLS 1.3 v produkcii

---

## 📈 Success Metrics

### Functional
- ✅ 95%+ presnosť pre NL → AnalyticsSpec preklad
- ✅ 90% dotazov dokončených v <30s
- ✅ 99% jobov dokončených v <5min
- ✅ 80%+ semantic search top-5 presnosť
- ✅ 10+ typov grafov podporovaných

### Performance
- ✅ <100ms p50 latency (cached)
- ✅ <5s p99 latency (uncached)
- ✅ 80%+ cache hit rate
- ✅ 100 concurrent users per tenant
- ✅ Škáluje na 100 tenantov, 1M issues

### Quality
- ✅ 90%+ test coverage
- ✅ Zero SQL injection vulnerabilities
- ✅ <5% error rate v produkcii
- ✅ 99.9% uptime (3 nines)

---

## 📚 Dokumentácia

### Spec-Kit Documents
1. **[constitution.md](specs/004-llm-sql-analytics/constitution.md)** - Princípy, tech stack, štandardy
2. **[spec.md](specs/004-llm-sql-analytics/spec.md)** - Požiadavky, user stories, technical specs
3. **[plan.md](specs/004-llm-sql-analytics/plan.md)** - Implementačný plán, fázy, architektúra
4. **[README.md](specs/004-llm-sql-analytics/README.md)** - Prehľad projektu

### Quick Links
- [GitHub Spec Kit](https://github.com/github/spec-kit) - Metodológia
- [SPEC_KIT_MASTER_GUIDE.md](SPEC_KIT_MASTER_GUIDE.md) - Ako používať Spec-Kit

---

## 🚀 Ďalšie Kroky

### Pre Implementáciu

```bash
# 1. Prečítaj dokumentáciu
code specs/004-llm-sql-analytics/

# 2. Začni s Phase 1, Week 1
# Vytvor database schema a models

# 3. Postupuj podľa plánu
# Každá fáza má jasné deliverables a acceptance criteria
```

### Pre Auggie (AI Assistant)

```
Auggie, implementuj Feature 004: LLM + SQL Analytics System

Začni s Phase 1, Week 1:
- Vytvor migration pre nové tabuľky (sprints, sprint_issues, metrics_catalog, analytics_jobs, analytics_cache)
- Vytvor SQLAlchemy models
- Vytvor materialized views
- Napíš unit tests (90%+ coverage)

Dodržuj constitution.md štandardy:
- Type hints mandatory
- Pydantic v2 pre všetky DTOs
- Async/await pre všetky I/O operácie
- Parameterized queries only
- 90%+ test coverage
```

---

## 🤝 Podpora

- **Dokumentácia**: [specs/004-llm-sql-analytics/](specs/004-llm-sql-analytics/)
- **Issues**: [GitHub Issues](https://github.com/SemanS/digital-spiral/issues)
- **Email**: slavomir.seman@hotovo.com

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Owner**: Digital Spiral Team

