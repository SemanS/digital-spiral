# Architecture Refactoring - Digital Spiral

## 📋 Overview

This feature implements a complete architectural refactoring of Digital Spiral from a monolithic structure into a clean, layered architecture that supports:

- **Multi-tenant Jira integration** with proper isolation
- **Scalable data synchronization** (backfill, webhooks, polling)
- **AI-powered automation** with multiple providers
- **Production-ready infrastructure** (PostgreSQL, Redis, Celery)
- **Comprehensive observability** (logging, metrics, tracing)

## 🎯 Goals

1. **Clean Architecture**: Separate domain, application, infrastructure, and interface layers
2. **Multi-Tenancy**: Support multiple Jira instances per tenant with RLS
3. **Reliable Sync**: 99.9% sync success rate with automatic retry
4. **Performance**: API response times p95 < 200ms, p99 < 500ms
5. **Scalability**: Horizontal scaling of API servers and workers
6. **Security**: OAuth 2.0, encrypted secrets, PII detection, audit logging
7. **Observability**: Structured logging, Prometheus metrics, OpenTelemetry tracing

## 📁 New Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (Interfaces)                    │
│  • REST API (FastAPI)  • MCP Server  • SQL Interface         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   Application Layer                          │
│  • Use Cases  • DTOs  • API Handlers  • MCP Tools           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Domain Layer (Core)                       │
│  • Entities  • Value Objects  • Domain Services              │
│  • Business Rules  • Domain Events                           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  • Repositories  • External APIs  • Database  • Cache        │
│  • Message Queue  • Event Bus  • Observability              │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Directory Structure

```
src/
├── domain/                    # Pure business logic
│   ├── entities/              # Core entities (Issue, Project, User)
│   ├── value_objects/         # Immutable values (IssueKey, Status)
│   ├── services/              # Domain services
│   └── events/                # Domain events
│
├── application/               # Use cases and orchestration
│   ├── use_cases/             # Business workflows
│   │   ├── sync/              # Data synchronization
│   │   ├── issues/            # Issue operations
│   │   ├── ai/                # AI-powered features
│   │   └── analytics/         # Metrics and dashboards
│   ├── dtos/                  # Data Transfer Objects
│   └── services/              # Application services
│
├── infrastructure/            # Technical implementation
│   ├── database/              # SQLAlchemy models, repositories
│   ├── cache/                 # Redis caching
│   ├── queue/                 # Celery tasks
│   ├── external/              # Jira client, AI providers
│   ├── observability/         # Logging, metrics, tracing
│   └── config/                # Configuration
│
└── interfaces/                # API layer
    ├── rest/                  # FastAPI routers
    ├── mcp/                   # MCP server
    └── sql/                   # SQL interface
```

## 🗄️ Database Schema

### Core Tables

- **tenants**: Multi-tenant isolation
- **jira_instances**: Jira Cloud instances per tenant
- **projects**: Jira projects
- **users**: Jira users (with email hashing)
- **issues**: Core issue table with JSONB for custom fields
- **issue_links**: Issue relationships (blocks, relates to, etc.)
- **comments**: Issue comments with ADF support
- **changelogs**: Issue history tracking
- **custom_fields**: Custom field metadata
- **sync_watermarks**: Incremental sync tracking
- **audit_log**: All write operations

### Key Features

- **JSONB columns** for flexible custom fields
- **GIN indexes** for fast JSONB queries
- **Row-Level Security (RLS)** for tenant isolation
- **Materialized views** for pre-computed metrics
- **Foreign key constraints** with cascade rules

## 🔄 Data Synchronization

### Backfill (Initial Sync)
1. Fetch all projects from Jira
2. Fetch all users from Jira
3. Fetch all issues using JQL pagination (100 per page)
4. Fetch comments and changelogs for each issue
5. Store in database with upsert logic
6. Update sync watermarks

### Incremental Sync (Webhooks)
1. Receive webhook from Jira (issue.updated, comment.created, etc.)
2. Fetch updated issue from Jira API
3. Upsert issue in database
4. Invalidate cache
5. Update sync watermark

### Polling Fallback
1. Query issues with `updated >= last_watermark` using JQL
2. Fetch updated issues in batches
3. Upsert in database
4. Update watermark

### Reconciliation
1. Sample random issues from database
2. Fetch same issues from Jira
3. Compare timestamps
4. Trigger re-sync for drifted issues

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1-2)
- Create directory structure
- Set up PostgreSQL and Redis
- Configure Alembic migrations
- Create base models and entities
- Set up observability

### Phase 2: Data Layer (Week 3-4)
- Implement all SQLAlchemy models
- Create repository pattern
- Add database indexes
- Implement RLS policies
- Create materialized views
- Add caching layer

### Phase 3: Sync Layer (Week 5-6)
- Create Jira API client
- Implement backfill use case
- Implement incremental sync
- Implement polling fallback
- Create Celery tasks
- Add rate limiting and retry logic

### Phase 4: Application Layer (Week 7-8)
- Create use cases for issue operations
- Implement AI use cases
- Create DTOs
- Implement application services
- Add audit logging

### Phase 5: REST API (Week 9-10)
- Create FastAPI routers
- Implement Pydantic schemas
- Add middleware (auth, rate limiting, logging)
- Write API tests
- Run contract tests

### Phase 6: MCP Interface (Week 11)
- Migrate MCP server to new architecture
- Implement MCP tools
- Add authorization

### Phase 7: Migration & Cleanup (Week 12)
- Migrate existing features
- Remove old code
- Update documentation
- Performance testing

## 🧪 Testing Strategy

### Unit Tests
- Domain entities (pure Python)
- Use cases (mocked repositories)
- Repositories (in-memory SQLite)
- Target: 80%+ coverage

### Integration Tests
- API endpoints (real Postgres)
- Celery tasks (real Redis)
- Jira client (mock server)

### Contract Tests
- Validate against OpenAPI schemas
- Use schemathesis
- Target: 95%+ parity

### E2E Tests
- Complete workflows
- Multi-tenant scenarios
- Docker Compose stack

## 📊 Success Metrics

- ✅ All tests passing (unit, integration, contract, e2e)
- ✅ API response times: p95 < 200ms, p99 < 500ms
- ✅ Sync latency: < 5 minutes
- ✅ Test coverage: >80%
- ✅ Contract test parity: >95%
- ✅ Zero data loss during migration
- ✅ Backward compatibility maintained

## 🔧 Technology Stack

- **Python 3.11+**: Modern Python with type hints
- **FastAPI 0.111+**: High-performance async web framework
- **Pydantic v2.7+**: Data validation
- **SQLAlchemy 2.0+**: ORM with async support
- **PostgreSQL 14+**: Primary database
- **Redis 6+**: Caching and rate limiting
- **Celery**: Background jobs
- **httpx**: HTTP client
- **OpenTelemetry**: Observability

## 📚 Documentation

- [Constitution](./constitution.md) - Project principles and standards
- [Specification](./spec.md) - Detailed requirements and architecture
- [Implementation Plan](./plan.md) - Technical implementation details
- [Tasks](./tasks.md) - Detailed task breakdown

## 🚦 Getting Started

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Start infrastructure
docker compose -f docker/docker-compose.dev.yml up -d

# Run migrations
alembic upgrade head

# Seed database
python scripts/seed_database.py
```

### Development Workflow

```bash
# Run tests
pytest tests/

# Run linter
ruff check src/

# Run type checker
mypy src/

# Start API server
uvicorn src.interfaces.rest.api:app --reload

# Start Celery worker
celery -A src.infrastructure.queue.celery_app worker --loglevel=info
```

## 🔐 Security

- **Authentication**: OAuth 2.0 / API tokens
- **Secrets**: Encrypted at rest (Vault/KMS)
- **PII**: Email hashing, redaction
- **Multi-tenancy**: RLS policies
- **Audit**: All write operations logged

## 📈 Observability

- **Logging**: Structured JSON logs with request ID
- **Metrics**: Prometheus metrics at `/metrics`
- **Tracing**: OpenTelemetry distributed tracing
- **Health**: `/health` and `/healthz` endpoints

## 🤝 Contributing

1. Review [Constitution](./constitution.md) for coding standards
2. Pick a task from [Tasks](./tasks.md)
3. Create feature branch: `git checkout -b feature/task-1.1`
4. Write tests first (TDD)
5. Implement feature
6. Run tests: `pytest tests/`
7. Create pull request

## 📞 Support

For questions or issues:
- GitHub Issues: [digital-spiral/issues](https://github.com/SemanS/digital-spiral/issues)
- Email: slavomir.seman@hotovo.com

## 📄 License

MIT License - see LICENSE file for details

---

**Built with ❤️ using Spec-Driven Development**

