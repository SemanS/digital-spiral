# Feature 004: LLM + SQL Analytics System

## 🎯 Overview

AI-powered analytics system that allows users to query Jira data using natural language. The system translates natural language queries into structured AnalyticsSpec (DSL), executes them against a metrics catalog, and returns results with chart recommendations.

**Status**: 📋 Specification Phase  
**Timeline**: 12 weeks  
**Team**: Backend (2), Frontend (1), QA (1)

---

## 📚 Documentation

### Core Documents
1. **[constitution.md](constitution.md)** - Project principles, tech stack, standards
2. **[spec.md](spec.md)** - Requirements, user stories, technical specs
3. **[plan.md](plan.md)** - Implementation plan, phases, architecture
4. **[tasks.md](tasks.md)** - Detailed tasks with acceptance criteria (coming soon)
5. **[AUGGIE_GUIDE.md](AUGGIE_GUIDE.md)** - Guide for AI assistant (coming soon)

### Quick Links
- [GitHub Spec Kit](https://github.com/github/spec-kit) - Methodology
- [SPEC_KIT_MASTER_GUIDE.md](../../SPEC_KIT_MASTER_GUIDE.md) - How to use Spec-Kit

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ with pgvector extension
- Redis 6+
- OpenAI API key or Anthropic API key

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup database
alembic upgrade head

# 3. Seed metrics catalog
python scripts/seed_metrics_catalog.py

# 4. Start Celery worker
celery -A src.infrastructure.queue.celery_config worker --loglevel=info

# 5. Start orchestrator
uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000

# 6. Start admin UI
cd admin-ui && npm run dev
```

### Example Usage

```bash
# Natural language query
curl -X POST http://localhost:8000/analytics/run \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo" \
  -d '{
    "query": "Show me the most problematic sprints in the last 6 months"
  }'

# Response
{
  "success": true,
  "data": {
    "results": [
      {
        "sprint_name": "Sprint 42",
        "project_key": "PROJ1",
        "sprint_problematic_score": 2.34,
        "spillover_ratio": 0.45,
        "scope_churn_ratio": 0.32
      }
    ],
    "total": 10,
    "query_time_ms": 234
  },
  "chart": {
    "type": "bar",
    "x": "sprint_name",
    "y": "sprint_problematic_score"
  }
}
```

---

## 🏗️ Architecture

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

### Key Features

#### 1. Natural Language Querying
- **Input**: "Show me the most problematic sprints"
- **LLM**: Translates to AnalyticsSpec
- **Validation**: Checks against metrics catalog
- **Execution**: Runs SQL query
- **Output**: Results + chart recommendation

#### 2. Metrics Catalog
- **Pre-defined Metrics**: 25+ metrics (throughput, lead time, quality, etc.)
- **Versioned**: Semantic versioning (1.0.0)
- **Tested**: Contract tests for all metrics
- **Documented**: Auto-generated docs

#### 3. Job Orchestration
- **Sync Execution**: <30s queries run immediately
- **Async Execution**: >30s queries run as Celery jobs
- **Progress Tracking**: Real-time status updates via SSE
- **Idempotency**: Same spec = same job ID

#### 4. Semantic Search
- **pgvector**: Vector embeddings for issues
- **Similarity Search**: Find issues by meaning, not keywords
- **Multi-language**: English, Slovak, Czech

#### 5. Chart Rendering
- **Auto-recommendation**: Based on data shape
- **10+ Chart Types**: Bar, line, scatter, heatmap, box plot, etc.
- **Vega-Lite**: Interactive, responsive charts

---

## 📊 Implementation Phases

### Phase 1: Foundation (Week 1-2)
- ✅ Database schema (sprints, metrics_catalog, analytics_jobs)
- ✅ SQLAlchemy models
- ✅ Materialized views
- ✅ Metrics catalog seeder

### Phase 2: Query Builder (Week 3-4)
- ✅ AnalyticsSpec DSL (Pydantic schema)
- ✅ Query builder (Spec → SQL)
- ✅ Query executor
- ✅ Caching layer (Redis)

### Phase 3: LLM Integration (Week 5-6)
- ✅ LLM provider abstraction (OpenAI, Claude)
- ✅ NL → AnalyticsSpec translator
- ✅ Semantic search (pgvector)

### Phase 4: Job Orchestration (Week 7-8)
- ✅ Celery setup
- ✅ Job manager service
- ✅ Job API (start, status, result, cancel)
- ✅ SSE for real-time updates

### Phase 5: Analytics API (Week 9-10)
- ✅ Core API endpoints
- ✅ Chart rendering
- ✅ Export (CSV, Excel, JSON)

### Phase 6: Frontend (Week 11-12)
- ✅ Chat interface
- ✅ Results viewer
- ✅ Metrics catalog browser
- ✅ E2E tests

---

## 🧪 Testing

### Unit Tests (90%+ coverage)
```bash
pytest tests/unit/application/services/analytics/
```

### Integration Tests
```bash
pytest tests/integration/analytics/
```

### Contract Tests
```bash
pytest tests/contract/test_metrics_catalog_contract.py
```

### E2E Tests
```bash
pytest tests/e2e/analytics/test_nl_to_results.py
```

### Load Tests
```bash
locust -f tests/load/analytics_load_test.py
```

---

## 📈 Success Metrics

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

## 🔒 Security

### Query Execution
- **Whitelisted Metrics**: Only pre-defined metrics allowed
- **Parameterized Queries**: No SQL injection possible
- **RLS Enforcement**: Row-level security on all tables
- **Rate Limiting**: Per-tenant, per-user limits
- **Audit Logging**: All queries logged with user context

### Data Protection
- **Tenant Isolation**: RLS policies on all tables
- **API Token Encryption**: Fernet symmetric encryption
- **Secrets Management**: Environment variables, never in code
- **HTTPS Only**: TLS 1.3 in production

---

## 📚 API Documentation

### Core Endpoints

#### Execute Query (Sync)
```bash
POST /analytics/run
Content-Type: application/json
X-Tenant-ID: demo

{
  "query": "Show me the most problematic sprints"
}
```

#### Start Job (Async)
```bash
POST /analytics/jobs
Content-Type: application/json
X-Tenant-ID: demo

{
  "spec": {...}
}
```

#### Get Job Status
```bash
GET /analytics/jobs/{job_id}
X-Tenant-ID: demo
```

#### Get Job Result
```bash
GET /analytics/jobs/{job_id}/result
X-Tenant-ID: demo
```

#### List Metrics
```bash
GET /analytics/metrics
X-Tenant-ID: demo
```

#### Semantic Search
```bash
POST /analytics/semantic-search
Content-Type: application/json
X-Tenant-ID: demo

{
  "query": "rollback discussions",
  "project_keys": ["PROJ1"],
  "top_k": 10
}
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## 📞 Support

- **Documentation**: [specs/004-llm-sql-analytics/](.)
- **Issues**: [GitHub Issues](https://github.com/SemanS/digital-spiral/issues)
- **Email**: slavomir.seman@hotovo.com

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Owner**: Digital Spiral Team

