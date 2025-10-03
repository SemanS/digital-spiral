# Digital Spiral - Project Constitution

## Core Principles

### 1. Architecture Philosophy
- **Multi-tenant first**: Every entity has `instance_id` or `tenant_id` for isolation
- **API-first design**: OpenAPI specifications drive implementation
- **Domain-driven design**: Clear separation between domain, application, and infrastructure layers
- **Event sourcing**: All state changes captured in audit log and changelog
- **Idempotency**: All write operations are idempotent with deduplication

### 2. Data Management
- **Single source of truth**: PostgreSQL with JSONB for flexibility
- **Schema evolution**: Alembic migrations for all schema changes
- **Raw payload preservation**: Always store original API responses in `raw_jsonb`
- **Materialized views**: Pre-computed aggregations for performance
- **Row-level security (RLS)**: Postgres policies enforce tenant isolation

### 3. Technology Stack

#### Core Technologies
- **Python 3.11+**: Modern Python with type hints
- **FastAPI**: High-performance async API framework
- **Pydantic v2**: Data validation and serialization
- **SQLAlchemy 2.0**: ORM with async support
- **PostgreSQL 14+**: Primary database with JSONB, RLS, and GIN indexes
- **Redis**: Caching, distributed locks, rate limiting, pub/sub
- **Celery/RQ**: Background job processing with retry logic

#### API & Integration
- **OpenAPI 3.0**: Contract-first API design
- **MCP (Model Context Protocol)**: AI agent integration
- **Webhooks**: Event-driven architecture with retry/backoff
- **httpx**: Modern HTTP client with connection pooling

#### Testing & Quality
- **pytest**: Unit and integration testing
- **schemathesis**: Contract testing against OpenAPI specs
- **openapi-core**: Response validation
- **hypothesis**: Property-based testing
- **Contract tests**: 95%+ parity threshold

### 4. Code Quality Standards

#### Type Safety
- All functions have type hints
- Pydantic models for all DTOs
- SQLAlchemy models for all database entities
- No `Any` types without justification

#### Error Handling
- Custom exception hierarchy
- Structured error responses (RFC 7807)
- Comprehensive logging with context
- Circuit breakers for external services

#### Testing Requirements
- Unit tests for all business logic (80%+ coverage)
- Integration tests for API endpoints
- Contract tests against OpenAPI schemas
- E2E tests for critical workflows

### 5. Security & Compliance

#### Authentication & Authorization
- OAuth 2.0 / API tokens for Jira integration
- JWT tokens for internal services
- Secrets stored in Vault/KMS (never in code)
- Token rotation support

#### Data Protection
- PII detection and redaction
- Email hashing for privacy
- Encryption at rest (database level)
- Encryption in transit (TLS 1.3)
- Audit log for all sensitive operations

#### Multi-tenancy
- Tenant isolation via RLS policies
- Per-tenant rate limiting
- Per-tenant configuration
- Tenant-scoped API keys

### 6. Performance & Scalability

#### Caching Strategy
- Redis for hot data (TTL-based)
- Materialized views for aggregations
- HTTP caching headers (ETag, Last-Modified)
- Query result caching with invalidation

#### Rate Limiting
- Token bucket algorithm per instance
- Distributed rate limiting via Redis
- Graceful degradation on limit exceeded
- Retry-After headers

#### Database Optimization
- GIN indexes on JSONB columns
- Partial indexes for common queries
- Connection pooling (pgbouncer)
- Query timeout enforcement

### 7. Observability

#### Logging
- Structured JSON logs
- Request ID propagation
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Sensitive data redaction

#### Metrics
- Prometheus metrics export
- Request latency histograms
- Error rate counters
- Business metrics (tickets processed, AI calls, etc.)

#### Tracing
- OpenTelemetry integration
- Distributed tracing across services
- Span annotations for key operations

### 8. Development Workflow

#### Version Control
- Git with feature branches
- Conventional commits (feat, fix, docs, refactor, test, chore)
- Pull request reviews required
- CI/CD pipeline validation

#### Documentation
- OpenAPI specs for all APIs
- README per module
- Architecture Decision Records (ADRs)
- Inline docstrings (Google style)

#### Deployment
- Docker containers
- Docker Compose for local development
- Health checks (/health, /healthz)
- Graceful shutdown support
- Zero-downtime deployments

### 9. Jira Integration Specifics

#### API Coverage
- Jira Platform REST API v3
- Jira Software (Agile) API
- Jira Service Management API
- Webhook support (v2)

#### Data Sync Strategy
- Initial backfill via JQL pagination
- Incremental updates via webhooks
- Polling fallback with watermarks
- Reconciliation jobs for drift detection

#### Custom Fields
- Store in `raw_jsonb` column
- Extract common fields to dedicated columns
- Metadata in `custom_fields` table
- Type-safe access via Pydantic models

### 10. AI Integration

#### MCP Tools
- Read operations: `jql_search`, `get_issue`, `get_transitions`
- Write operations: `create_issue`, `transition_issue`, `add_comment`
- SQL access: `sql_query` (read-only views)
- Authorization per tool

#### AI Providers
- OpenAI GPT-4
- Anthropic Claude
- Google Gemini
- Provider abstraction layer

#### Safety & Validation
- Input validation before AI calls
- Output validation after AI responses
- Cost tracking per tenant
- Rate limiting per tenant

## Non-Negotiables

1. **No direct database access from API layer** - Always use service layer
2. **No secrets in code or logs** - Use environment variables or Vault
3. **All write operations are audited** - Audit log is mandatory
4. **Multi-tenant isolation is enforced** - RLS policies or application-level checks
5. **OpenAPI specs are source of truth** - Code generation from specs
6. **Contract tests must pass** - 95%+ parity threshold
7. **Type hints are mandatory** - No untyped code
8. **Error handling is comprehensive** - No bare `except:` blocks
9. **Tests are required for new features** - No PR without tests
10. **Documentation is updated with code** - No stale docs

## Success Metrics

- **API Response Time**: p95 < 200ms, p99 < 500ms
- **Test Coverage**: >80% for business logic
- **Contract Test Parity**: >95% with Jira Cloud APIs
- **Uptime**: 99.9% availability
- **Error Rate**: <0.1% of requests
- **Sync Latency**: <5 minutes for webhook processing
- **AI Response Time**: <3 seconds for intent classification

## References

- [Jira Cloud REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)

