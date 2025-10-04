# Digital Spiral - Auggie Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-04

---

## 🎯 Project Overview

**Digital Spiral** is a multi-tenant Jira analytics platform with AI-powered insights using the Model Context Protocol (MCP).

**Current Features**:
- Feature 001: Architecture Refactoring (Clean Architecture)
- Feature 002: Admin UI (React + TypeScript)
- Feature 003: MCP SQL Enhancement (SQL Query Tools)
- **Feature 004: LLM + SQL Analytics System** (In Progress)

---

## 🏗️ Active Technologies

### Backend
- **Python 3.11+** - Type hints mandatory, async/await patterns
- **FastAPI** - REST API framework with SSE support
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **PostgreSQL 14+** - JSONB, window functions, materialized views, RLS, pgvector
- **Redis 6+** - Caching, job queues, rate limiting
- **Celery** - Background job orchestration
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation and serialization

### AI/ML
- **OpenAI GPT-4** - LLM for NL → AnalyticsSpec translation
- **Anthropic Claude** - Alternative LLM provider
- **pgvector** - Vector similarity search for semantic search

### Frontend
- **React 18+** - UI framework
- **TypeScript** - Type-safe JavaScript
- **TanStack Query** - Data fetching and caching
- **Vega-Lite** - Chart rendering

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Local development
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization

---

## 📁 Project Structure

```
digital-spiral/
├── .specify/                           # Spec-Kit methodology files
│   ├── features/                       # Feature specifications
│   │   ├── 001-architecture-refactoring/
│   │   ├── 002-admin-ui/
│   │   ├── 003-mcp-sql-enhancement/
│   │   └── 004-llm-sql-analytics/      # Current feature
│   │       ├── constitution.md         # Project principles
│   │       ├── spec.md                 # Requirements & user stories
│   │       ├── plan.md                 # Implementation plan
│   │       ├── tasks.md                # Task breakdown
│   │       ├── AUGGIE_GUIDE.md         # Auggie implementation guide
│   │       └── README.md               # Feature overview
│   ├── memory/
│   │   └── constitution.md             # Global project constitution
│   ├── scripts/                        # Automation scripts
│   └── templates/                      # Document templates
├── src/
│   ├── application/                    # Application layer (use cases)
│   │   └── services/
│   │       └── analytics/              # Analytics services (NEW)
│   │           ├── metrics_catalog_service.py
│   │           ├── nl_to_spec_translator.py
│   │           ├── query_builder.py
│   │           ├── query_executor.py
│   │           ├── cache_service.py
│   │           ├── job_manager_service.py
│   │           ├── semantic_search_service.py
│   │           └── schemas.py
│   ├── domain/                         # Domain layer (entities)
│   ├── infrastructure/                 # Infrastructure layer
│   │   ├── database/
│   │   │   └── models/                 # SQLAlchemy models
│   │   │       ├── sprint.py           # NEW
│   │   │       ├── sprint_issue.py     # NEW
│   │   │       ├── metrics_catalog.py  # NEW
│   │   │       ├── analytics_job.py    # NEW
│   │   │       └── analytics_cache.py  # NEW
│   │   └── queue/                      # Celery tasks (NEW)
│   │       ├── celery_config.py
│   │       └── analytics_tasks.py
│   └── interfaces/                     # Interface layer (API, MCP)
│       ├── api/
│       │   └── analytics/              # Analytics API (NEW)
│       │       ├── analytics_router.py
│       │       └── job_router.py
│       └── mcp/
│           ├── jira/                   # Jira MCP server
│           └── sql/                    # SQL MCP server
├── migrations/                         # Alembic migrations
│   └── versions/
│       ├── 006_add_analytics_tables.py # NEW
│       ├── 007_add_materialized_views.py # NEW
│       └── 008_add_pgvector.py         # NEW
├── scripts/                            # Utility scripts
│   ├── metrics_catalog.json            # NEW - Metrics definitions
│   ├── seed_metrics_catalog.py         # NEW - Seeder script
│   └── refresh_materialized_views.py   # NEW - MV refresh
├── tests/
│   ├── unit/                           # Unit tests (90%+ coverage)
│   ├── integration/                    # Integration tests
│   ├── contract/                       # Contract tests
│   └── e2e/                            # End-to-end tests
├── admin-ui/                           # React frontend
├── orchestrator/                       # Pulse service (legacy)
├── pyproject.toml                      # Python dependencies
├── docker-compose.yml                  # Local development
└── AUGGIE.md                           # This file
```

---

## 🚀 Slash Commands

### Available Commands

```bash
/constitution   # Create or update project principles
/specify        # Define what you want to build
/clarify        # Clarify underspecified areas
/plan           # Create technical implementation plan
/tasks          # Generate actionable task list
/analyze        # Cross-artifact consistency check
/implement      # Execute all tasks
```

### Usage Example

```
/implement
```

This will:
1. Validate prerequisites (constitution, spec, plan, tasks)
2. Parse task breakdown from tasks.md
3. Execute tasks in order, respecting dependencies
4. Follow TDD approach
5. Provide progress updates

---

## 📋 Current Feature: LLM + SQL Analytics System

### Quick Start

```bash
# Read documentation (40 min)
cat .specify/features/004-llm-sql-analytics/constitution.md
cat .specify/features/004-llm-sql-analytics/spec.md
cat .specify/features/004-llm-sql-analytics/plan.md
cat .specify/features/004-llm-sql-analytics/tasks.md

# Implement feature
/implement
```

### Implementation Phases

1. **Phase 1: Foundation (Week 1-2)**
   - Database schema & models
   - Metrics catalog (25+ metrics)
   - Materialized views

2. **Phase 2: Query Builder (Week 3-4)**
   - AnalyticsSpec DSL
   - Query builder (Spec → SQL)
   - Query executor & caching

3. **Phase 3: LLM Integration (Week 5-6)**
   - NL → AnalyticsSpec translator
   - Semantic search (pgvector)

4. **Phase 4: Job Orchestration (Week 7-8)**
   - Celery setup
   - Job manager service
   - Job API & SSE

5. **Phase 5: Analytics API (Week 9-10)**
   - Core endpoints
   - Chart rendering
   - Export functionality

6. **Phase 6: Frontend (Week 11-12)**
   - Chat interface
   - Results viewer
   - Metrics catalog UI

### Key Principles (from constitution.md)

1. **Deterministic over Flexible** - Whitelisted metrics, no raw SQL from LLM
2. **Security First** - RLS, parameterized queries, rate limiting
3. **Multi-tenant Native** - Tenant isolation at all layers
4. **Performance** - Materialized views, caching, async jobs
5. **Type Safety** - Type hints mandatory, mypy strict mode

---

## 🧪 Testing Commands

### Unit Tests
```bash
pytest tests/unit/ -v --cov=src/
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Contract Tests
```bash
pytest tests/contract/ -v
```

### E2E Tests
```bash
pytest tests/e2e/ -v
```

### All Tests
```bash
pytest tests/ -v --cov=src/ --cov-report=html
```

### Type Checking
```bash
mypy src/
```

### Linting
```bash
ruff check src/
```

### Formatting
```bash
ruff format src/
```

---

## 🔧 Development Commands

### Database Migrations
```bash
# Create migration
alembic revision -m "description"

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current version
alembic current
```

### Celery Worker
```bash
# Start worker
celery -A src.infrastructure.queue.celery_config worker --loglevel=info

# Start beat (scheduler)
celery -A src.infrastructure.queue.celery_config beat --loglevel=info

# Monitor tasks
celery -A src.infrastructure.queue.celery_config flower
```

### FastAPI Server
```bash
# Development
uvicorn src.interfaces.api.main:app --reload --port 8000

# Production
uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up -d --build
```

---

## 📝 Code Style

### Python
- **Type hints mandatory** - All functions, methods, variables
- **Async/await** - All I/O operations
- **Pydantic v2** - All DTOs and validation
- **Docstrings** - Google style for all public APIs
- **Line length** - 120 characters max
- **Imports** - isort with black profile

### TypeScript
- **Strict mode** - tsconfig.json strict: true
- **No any** - Use unknown or proper types
- **Functional components** - React hooks only
- **Named exports** - No default exports

---

## 🔍 Recent Changes

### Feature 004: LLM + SQL Analytics System (In Progress)
**Added**:
- AnalyticsSpec DSL for query specification
- Metrics catalog with 25+ metrics
- NL → AnalyticsSpec translation with LLM
- Semantic search with pgvector
- Job orchestration with Celery
- Materialized views for performance

### Feature 003: MCP SQL Enhancement (Completed)
**Added**:
- SQL query templates for common analytics
- MCP SQL server with 6 tools
- Query result caching

### Feature 002: Admin UI (Completed)
**Added**:
- React + TypeScript admin interface
- Jira instance management
- User management
- Dashboard with metrics

---

## 📞 Support

- **Documentation**: `.specify/features/004-llm-sql-analytics/`
- **GitHub Issues**: https://github.com/SemanS/digital-spiral/issues
- **Email**: slavomir.seman@hotovo.com

---

<!-- MANUAL ADDITIONS START -->
<!-- Add any manual notes or overrides here -->
<!-- MANUAL ADDITIONS END -->

