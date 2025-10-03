# Feature Specification: Architecture Refactoring

## Overview

Refactor Digital Spiral from a monolithic structure with mixed concerns into a clean, layered architecture that supports multi-tenant Jira integration, AI-powered automation, and scalable data synchronization.

## Current State Analysis

### Existing Components

1. **mockjira/** - Mock Jira server with in-memory storage
   - `store.py`: In-memory data structures (User, Project, Issue, etc.)
   - `routers/`: FastAPI routers (platform, agile, service_management, webhooks)
   - `auth.py`: Token-based authentication
   - `fixtures/`: Seed data generators

2. **orchestrator/** - AI orchestration and business logic
   - `app.py`: Main FastAPI app with credit system, webhooks
   - `db.py`: SQLAlchemy models (Tenant, CreditEventRecord, ApplyActionRecord)
   - `pulse_*.py`: Work Pulse feature (metrics, dashboards)
   - `ai_assistant_api.py`: AI chat interface
   - `sql_tools.py`: SQL query execution

3. **mcp_jira/** - Model Context Protocol bridge
   - `server.py`: MCP tool registry
   - `tools.py`: Jira operation tools
   - `http_server.py`: HTTP bridge for MCP

4. **clients/python/** - Jira API client
   - `jira_cloud_adapter.py`: HTTP client for Jira Cloud

### Problems with Current Architecture

1. **Mixed concerns**: Business logic, data access, and API routing are intertwined
2. **In-memory storage**: mockjira uses in-memory store, not suitable for production
3. **Single-tenant**: No proper multi-tenant isolation
4. **No sync layer**: No systematic data synchronization from Jira
5. **Scattered models**: Data models spread across multiple files
6. **No domain layer**: Business logic mixed with infrastructure
7. **Limited observability**: Basic logging, no metrics or tracing
8. **No rate limiting**: No protection against API abuse
9. **Weak error handling**: Inconsistent error responses
10. **No caching**: Every request hits Jira API

## Target Architecture

### Layered Architecture

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

### New Directory Structure

```
digital-spiral/
├── src/
│   ├── domain/                    # Domain layer (pure business logic)
│   │   ├── entities/              # Core entities
│   │   │   ├── jira_instance.py
│   │   │   ├── project.py
│   │   │   ├── issue.py
│   │   │   ├── user.py
│   │   │   ├── comment.py
│   │   │   ├── changelog.py
│   │   │   └── sprint.py
│   │   ├── value_objects/         # Immutable value objects
│   │   │   ├── issue_key.py
│   │   │   ├── status.py
│   │   │   ├── priority.py
│   │   │   └── custom_field.py
│   │   ├── services/              # Domain services
│   │   │   ├── issue_service.py
│   │   │   ├── transition_service.py
│   │   │   └── sync_service.py
│   │   └── events/                # Domain events
│   │       ├── issue_created.py
│   │       ├── issue_updated.py
│   │       └── comment_added.py
│   │
│   ├── application/               # Application layer (use cases)
│   │   ├── use_cases/             # Business use cases
│   │   │   ├── sync/
│   │   │   │   ├── backfill_instance.py
│   │   │   │   ├── sync_issue.py
│   │   │   │   └── reconcile_data.py
│   │   │   ├── issues/
│   │   │   │   ├── create_issue.py
│   │   │   │   ├── update_issue.py
│   │   │   │   ├── transition_issue.py
│   │   │   │   └── search_issues.py
│   │   │   ├── ai/
│   │   │   │   ├── classify_intent.py
│   │   │   │   ├── generate_response.py
│   │   │   │   └── detect_pii.py
│   │   │   └── analytics/
│   │   │       ├── calculate_metrics.py
│   │   │       └── generate_dashboard.py
│   │   ├── dtos/                  # Data Transfer Objects
│   │   │   ├── issue_dto.py
│   │   │   ├── search_dto.py
│   │   │   └── metrics_dto.py
│   │   └── services/              # Application services
│   │       ├── auth_service.py
│   │       ├── tenant_service.py
│   │       └── rate_limit_service.py
│   │
│   ├── infrastructure/            # Infrastructure layer
│   │   ├── database/              # Database implementation
│   │   │   ├── models/            # SQLAlchemy models
│   │   │   │   ├── base.py
│   │   │   │   ├── jira_instance.py
│   │   │   │   ├── project.py
│   │   │   │   ├── issue.py
│   │   │   │   ├── user.py
│   │   │   │   ├── comment.py
│   │   │   │   ├── changelog.py
│   │   │   │   ├── custom_field.py
│   │   │   │   ├── sync_watermark.py
│   │   │   │   └── audit_log.py
│   │   │   ├── repositories/      # Repository implementations
│   │   │   │   ├── issue_repository.py
│   │   │   │   ├── project_repository.py
│   │   │   │   └── user_repository.py
│   │   │   ├── migrations/        # Alembic migrations
│   │   │   └── views/             # SQL views and materialized views
│   │   │       ├── issue_metrics_view.sql
│   │   │       └── lead_time_view.sql
│   │   ├── cache/                 # Redis caching
│   │   │   ├── redis_client.py
│   │   │   └── cache_service.py
│   │   ├── queue/                 # Background jobs
│   │   │   ├── celery_app.py
│   │   │   └── tasks/
│   │   │       ├── sync_tasks.py
│   │   │       └── metrics_tasks.py
│   │   ├── external/              # External API clients
│   │   │   ├── jira_client.py
│   │   │   ├── ai_client.py
│   │   │   └── webhook_client.py
│   │   ├── observability/         # Logging, metrics, tracing
│   │   │   ├── logger.py
│   │   │   ├── metrics.py
│   │   │   └── tracer.py
│   │   └── config/                # Configuration
│   │       ├── settings.py
│   │       └── secrets.py
│   │
│   └── interfaces/                # API layer (interfaces)
│       ├── rest/                  # REST API
│       │   ├── api.py             # FastAPI app
│       │   ├── routers/
│       │   │   ├── instances.py
│       │   │   ├── issues.py
│       │   │   ├── projects.py
│       │   │   ├── webhooks.py
│       │   │   ├── ai_assistant.py
│       │   │   └── pulse.py
│       │   ├── middleware/
│       │   │   ├── auth.py
│       │   │   ├── rate_limit.py
│       │   │   └── logging.py
│       │   └── schemas/           # Pydantic request/response models
│       │       ├── issue_schema.py
│       │       └── search_schema.py
│       ├── mcp/                   # MCP interface
│       │   ├── server.py
│       │   ├── tools/
│       │   │   ├── jira_tools.py
│       │   │   ├── sql_tools.py
│       │   │   └── ai_tools.py
│       │   └── http_bridge.py
│       └── sql/                   # SQL interface (read-only views)
│           ├── views.py
│           └── query_builder.py
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── contract/                  # Contract tests
│   └── e2e/                       # End-to-end tests
│
├── schemas/                       # OpenAPI schemas
│   ├── jira-platform.v3.json
│   ├── jira-software.v3.json
│   └── jsm.v3.json
│
├── migrations/                    # Database migrations
│   └── versions/
│
└── docker/                        # Docker configuration
    ├── Dockerfile
    ├── docker-compose.yml
    └── docker-compose.dev.yml
```

## Requirements

### Functional Requirements

#### FR1: Multi-Tenant Jira Instance Management
- **FR1.1**: Add/remove Jira Cloud instances per tenant
- **FR1.2**: Store encrypted credentials (OAuth tokens, API keys)
- **FR1.3**: Test connectivity before activation
- **FR1.4**: Support multiple instances per tenant
- **FR1.5**: Tenant isolation enforced at database level (RLS)

#### FR2: Data Synchronization
- **FR2.1**: Initial backfill of all projects, issues, users, sprints
- **FR2.2**: Incremental sync via webhooks (issue.updated, comment.created, etc.)
- **FR2.3**: Polling fallback with watermarks for instances without webhooks
- **FR2.4**: Reconciliation jobs to detect drift
- **FR2.5**: Idempotent sync operations (handle duplicates)
- **FR2.6**: Rate limiting per instance (respect Jira API limits)

#### FR3: Unified Data Model
- **FR3.1**: Core tables: instances, projects, users, issues, comments, changelogs
- **FR3.2**: Custom fields stored in `raw_jsonb` with metadata table
- **FR3.3**: Materialized views for common aggregations
- **FR3.4**: Support for issue links, parent-child relationships, epics
- **FR3.5**: Sprint tracking with historical data

#### FR4: REST API
- **FR4.1**: CRUD operations for issues, comments, transitions
- **FR4.2**: JQL-like search across all instances
- **FR4.3**: Webhook registration and management
- **FR4.4**: AI assistant chat interface
- **FR4.5**: Work Pulse dashboard and metrics

#### FR5: MCP Interface
- **FR5.1**: Tools for read operations (search, get_issue, get_transitions)
- **FR5.2**: Tools for write operations (create, update, transition, comment)
- **FR5.3**: SQL query tool (read-only views)
- **FR5.4**: Authorization per tool and tenant

#### FR6: AI Integration
- **FR6.1**: Intent classification for support tickets
- **FR6.2**: Automated response generation
- **FR6.3**: PII detection and redaction
- **FR6.4**: Credit tracking per AI operation
- **FR6.5**: Multiple AI provider support (OpenAI, Anthropic, Google)

### Non-Functional Requirements

#### NFR1: Performance
- API response time: p95 < 200ms, p99 < 500ms
- Sync latency: < 5 minutes for webhook processing
- Support 1000+ concurrent users
- Handle 10,000+ issues per instance

#### NFR2: Scalability
- Horizontal scaling of API servers
- Background job workers scale independently
- Database connection pooling
- Redis cluster for caching

#### NFR3: Reliability
- 99.9% uptime SLA
- Automatic retry with exponential backoff
- Circuit breakers for external services
- Graceful degradation on failures

#### NFR4: Security
- OAuth 2.0 / API token authentication
- Secrets encrypted at rest (Vault/KMS)
- PII detection and hashing
- Audit log for all write operations
- Row-level security (RLS) for multi-tenancy

#### NFR5: Observability
- Structured JSON logging
- Prometheus metrics export
- OpenTelemetry distributed tracing
- Health check endpoints

## Success Criteria

1. **Clean separation of concerns**: Domain, application, infrastructure layers are independent
2. **Multi-tenant support**: Multiple Jira instances per tenant with isolation
3. **Reliable sync**: 99.9% sync success rate with automatic retry
4. **Performance**: API response times meet NFR1 targets
5. **Test coverage**: >80% for business logic, 95%+ contract test parity
6. **Zero data loss**: All Jira changes captured in audit log
7. **Backward compatibility**: Existing APIs continue to work during migration

## Out of Scope

- Real-time collaboration features
- Mobile app development
- On-premise Jira Server support (Cloud only)
- Custom workflow engine
- Advanced reporting beyond Work Pulse

## Migration Strategy

1. **Phase 1**: Create new domain and infrastructure layers (parallel to existing code)
2. **Phase 2**: Migrate orchestrator to use new layers
3. **Phase 3**: Migrate MCP server to use new layers
4. **Phase 4**: Deprecate mockjira in-memory store, use PostgreSQL
5. **Phase 5**: Remove old code, cleanup

## Dependencies

- PostgreSQL 14+ with JSONB support
- Redis 6+ for caching and rate limiting
- Celery/RQ for background jobs
- Alembic for database migrations
- OpenTelemetry for observability

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data migration complexity | High | Incremental migration with rollback plan |
| Performance degradation | Medium | Load testing before production deployment |
| Breaking changes to existing APIs | High | Versioned APIs with deprecation notices |
| Jira API rate limits | Medium | Aggressive caching and rate limiting |
| Multi-tenant data leakage | Critical | RLS policies + application-level checks |

