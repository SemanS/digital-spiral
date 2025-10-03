# Implementation Plan: Architecture Refactoring

## Technology Stack

### Core Technologies
- **Python 3.11+**: Modern Python with type hints and async support
- **FastAPI 0.111+**: High-performance async web framework
- **Pydantic v2.7+**: Data validation and serialization
- **SQLAlchemy 2.0+**: ORM with async support and type hints
- **Alembic**: Database migration tool
- **PostgreSQL 14+**: Primary database with JSONB, RLS, GIN indexes
- **Redis 6+**: Caching, distributed locks, rate limiting, pub/sub
- **Celery**: Background job processing with retry logic
- **httpx 0.27+**: Modern async HTTP client

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **OpenTelemetry**: Distributed tracing
- **MinIO/S3**: Object storage for backups

### Testing
- **pytest 8.2+**: Test framework
- **pytest-asyncio**: Async test support
- **schemathesis 3.x**: Contract testing
- **openapi-core 0.19.x**: OpenAPI validation
- **hypothesis**: Property-based testing
- **faker**: Test data generation

## Architecture Layers

### 1. Domain Layer (`src/domain/`)

**Purpose**: Pure business logic, no external dependencies

**Components**:
- **Entities**: Core business objects (Issue, Project, User, etc.)
- **Value Objects**: Immutable objects (IssueKey, Status, Priority)
- **Domain Services**: Business logic that doesn't fit in entities
- **Domain Events**: Events that represent state changes

**Key Principles**:
- No framework dependencies
- No database dependencies
- Pure Python with type hints
- Testable in isolation

### 2. Application Layer (`src/application/`)

**Purpose**: Orchestrate domain logic, implement use cases

**Components**:
- **Use Cases**: Business workflows (CreateIssue, SyncInstance, etc.)
- **DTOs**: Data Transfer Objects for API boundaries
- **Application Services**: Cross-cutting concerns (auth, rate limiting)
- **Interfaces**: Abstract interfaces for infrastructure

**Key Principles**:
- Depends on domain layer only
- Defines interfaces for infrastructure
- No direct database or HTTP calls
- Coordinates domain objects

### 3. Infrastructure Layer (`src/infrastructure/`)

**Purpose**: Implement technical details, external integrations

**Components**:
- **Database**: SQLAlchemy models, repositories, migrations
- **Cache**: Redis client and caching logic
- **Queue**: Celery tasks and job scheduling
- **External APIs**: Jira client, AI providers
- **Observability**: Logging, metrics, tracing

**Key Principles**:
- Implements application interfaces
- Handles all I/O operations
- Framework-specific code lives here
- Swappable implementations

### 4. Interface Layer (`src/interfaces/`)

**Purpose**: Expose application via different protocols

**Components**:
- **REST API**: FastAPI routers and schemas
- **MCP Server**: Model Context Protocol tools
- **SQL Interface**: Read-only views for analytics
- **Middleware**: Auth, rate limiting, logging

**Key Principles**:
- Thin layer, delegates to application
- Protocol-specific code only
- Input validation and serialization
- Error handling and responses

## Database Schema

### Core Tables

```sql
-- Multi-tenant isolation
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Jira instances per tenant
CREATE TABLE jira_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    kind VARCHAR(50) NOT NULL, -- 'cloud', 'server', 'datacenter'
    base_url VARCHAR(500) NOT NULL,
    auth_method VARCHAR(50) NOT NULL, -- 'oauth', 'api_token', 'pat'
    email VARCHAR(255),
    api_token_encrypted TEXT,
    display_name VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, base_url, email)
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES jira_instances(id) ON DELETE CASCADE,
    jira_id VARCHAR(50) NOT NULL,
    key VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    project_type VARCHAR(50),
    lead_account_id VARCHAR(255),
    raw_jsonb JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(instance_id, jira_id)
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES jira_instances(id) ON DELETE CASCADE,
    account_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    email_hash VARCHAR(64), -- SHA256 hash for privacy
    time_zone VARCHAR(50),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    raw_jsonb JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(instance_id, account_id)
);

-- Issues (core table)
CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES jira_instances(id) ON DELETE CASCADE,
    jira_id VARCHAR(50) NOT NULL,
    key VARCHAR(50) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Core fields
    issue_type VARCHAR(50),
    status VARCHAR(100) NOT NULL,
    priority VARCHAR(50),
    summary TEXT NOT NULL,
    description_adf JSONB,
    
    -- People
    assignee_id UUID REFERENCES users(id),
    reporter_id UUID REFERENCES users(id),
    creator_id UUID REFERENCES users(id),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    due_date DATE,
    
    -- Hierarchy
    parent_issue_id UUID REFERENCES issues(id),
    epic_key VARCHAR(50),
    
    -- Agile
    sprint_ids INTEGER[],
    story_points NUMERIC(10, 2),
    
    -- Labels and components
    labels TEXT[],
    components TEXT[],
    
    -- Custom fields (raw)
    raw_jsonb JSONB NOT NULL,
    
    -- Sync metadata
    jira_updated_at TIMESTAMPTZ NOT NULL,
    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(instance_id, jira_id),
    UNIQUE(instance_id, key)
);

-- Issue links
CREATE TABLE issue_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES jira_instances(id) ON DELETE CASCADE,
    inward_issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    outward_issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    link_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Comments
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES jira_instances(id) ON DELETE CASCADE,
    jira_id VARCHAR(50) NOT NULL,
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id),
    body_adf JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(instance_id, jira_id)
);

-- Changelogs (history)
CREATE TABLE changelogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES jira_instances(id) ON DELETE CASCADE,
    jira_id VARCHAR(50) NOT NULL,
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL,
    field VARCHAR(100) NOT NULL,
    field_type VARCHAR(50),
    from_value TEXT,
    to_value TEXT,
    from_string TEXT,
    to_string TEXT,
    raw_jsonb JSONB,
    UNIQUE(instance_id, jira_id)
);

-- Custom field metadata
CREATE TABLE custom_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES jira_instances(id) ON DELETE CASCADE,
    field_key VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    field_type VARCHAR(50),
    schema_raw JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(instance_id, field_key)
);

-- Sync watermarks (for incremental sync)
CREATE TABLE sync_watermarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES jira_instances(id) ON DELETE CASCADE,
    entity VARCHAR(50) NOT NULL, -- 'issues', 'comments', 'changelogs'
    last_cursor VARCHAR(255),
    last_updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(instance_id, entity)
);

-- Audit log (all write operations)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID REFERENCES jira_instances(id) ON DELETE SET NULL,
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    actor VARCHAR(255) NOT NULL, -- user ID or 'system'
    action VARCHAR(100) NOT NULL, -- 'create_issue', 'transition', 'add_comment'
    target VARCHAR(255), -- issue key, comment ID, etc.
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_issues_instance_id ON issues(instance_id);
CREATE INDEX idx_issues_project_id ON issues(project_id);
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_issues_assignee_id ON issues(assignee_id);
CREATE INDEX idx_issues_created_at ON issues(created_at);
CREATE INDEX idx_issues_updated_at ON issues(updated_at);
CREATE INDEX idx_issues_key ON issues(key);
CREATE INDEX idx_issues_jira_updated_at ON issues(jira_updated_at);

-- GIN indexes for JSONB and arrays
CREATE INDEX idx_issues_raw_jsonb ON issues USING GIN(raw_jsonb);
CREATE INDEX idx_issues_labels ON issues USING GIN(labels);
CREATE INDEX idx_issues_sprint_ids ON issues USING GIN(sprint_ids);

CREATE INDEX idx_comments_issue_id ON comments(issue_id);
CREATE INDEX idx_comments_created_at ON comments(created_at);

CREATE INDEX idx_changelogs_issue_id ON changelogs(issue_id);
CREATE INDEX idx_changelogs_created_at ON changelogs(created_at);
CREATE INDEX idx_changelogs_field ON changelogs(field);

CREATE INDEX idx_audit_log_instance_id ON audit_log(instance_id);
CREATE INDEX idx_audit_log_tenant_id ON audit_log(tenant_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- Row-Level Security (RLS) policies
ALTER TABLE jira_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE changelogs ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (tenant isolation)
CREATE POLICY tenant_isolation_policy ON issues
    USING (instance_id IN (
        SELECT id FROM jira_instances WHERE tenant_id = current_setting('app.current_tenant_id')::UUID
    ));
```

### Materialized Views

```sql
-- Issue metrics view
CREATE MATERIALIZED VIEW issue_metrics AS
SELECT 
    i.instance_id,
    i.project_id,
    p.key AS project_key,
    COUNT(*) AS total_issues,
    COUNT(*) FILTER (WHERE i.status IN ('Open', 'To Do')) AS open_issues,
    COUNT(*) FILTER (WHERE i.status IN ('In Progress', 'In Review')) AS in_progress_issues,
    COUNT(*) FILTER (WHERE i.status IN ('Done', 'Closed')) AS closed_issues,
    COUNT(*) FILTER (WHERE i.assignee_id IS NULL) AS unassigned_issues,
    AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 86400) AS avg_lead_time_days
FROM issues i
JOIN projects p ON p.id = i.project_id
GROUP BY i.instance_id, i.project_id, p.key;

CREATE UNIQUE INDEX ON issue_metrics(instance_id, project_id);

-- Lead time view (from changelog)
CREATE MATERIALIZED VIEW lead_time_view AS
SELECT 
    i.id AS issue_id,
    i.key AS issue_key,
    i.instance_id,
    MIN(CASE WHEN c.field = 'status' AND c.to_string = 'In Progress' THEN c.created_at END) AS started_at,
    MIN(CASE WHEN c.field = 'status' AND c.to_string IN ('Done', 'Closed') THEN c.created_at END) AS completed_at,
    EXTRACT(EPOCH FROM (
        MIN(CASE WHEN c.field = 'status' AND c.to_string IN ('Done', 'Closed') THEN c.created_at END) -
        MIN(CASE WHEN c.field = 'status' AND c.to_string = 'In Progress' THEN c.created_at END)
    )) / 3600 AS lead_time_hours
FROM issues i
LEFT JOIN changelogs c ON c.issue_id = i.id
GROUP BY i.id, i.key, i.instance_id;

CREATE UNIQUE INDEX ON lead_time_view(issue_id);
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goal**: Set up new architecture skeleton

**Tasks**:
1. Create new directory structure (`src/domain`, `src/application`, `src/infrastructure`, `src/interfaces`)
2. Set up PostgreSQL database with Docker Compose
3. Create Alembic migration setup
4. Implement base SQLAlchemy models (Base, Tenant, JiraInstance)
5. Create domain entities (Issue, Project, User) as pure Python classes
6. Set up Redis for caching
7. Configure logging, metrics, tracing infrastructure
8. Create base repository interfaces

**Deliverables**:
- New directory structure
- Database schema migration (initial)
- Base models and entities
- Docker Compose with Postgres + Redis
- Configuration management

### Phase 2: Data Layer (Week 3-4)

**Goal**: Implement complete data persistence layer

**Tasks**:
1. Create all SQLAlchemy models (Issues, Projects, Users, Comments, Changelogs, etc.)
2. Implement repository pattern for each entity
3. Create database indexes (GIN, B-tree)
4. Implement Row-Level Security (RLS) policies
5. Create materialized views for metrics
6. Implement caching layer with Redis
7. Write unit tests for repositories
8. Create seed data for testing

**Deliverables**:
- Complete database schema
- Repository implementations
- RLS policies
- Materialized views
- Unit tests (80%+ coverage)

### Phase 3: Sync Layer (Week 5-6)

**Goal**: Implement data synchronization from Jira

**Tasks**:
1. Create Jira API client (httpx-based)
2. Implement backfill use case (initial sync)
3. Implement incremental sync use case (webhooks)
4. Implement polling fallback with watermarks
5. Create Celery tasks for background sync
6. Implement rate limiting per instance
7. Add retry logic with exponential backoff
8. Create reconciliation job
9. Write integration tests

**Deliverables**:
- Jira client with retry logic
- Backfill and incremental sync
- Celery tasks
- Rate limiting
- Integration tests

### Phase 4: Application Layer (Week 7-8)

**Goal**: Implement business use cases

**Tasks**:
1. Create use cases for issue operations (create, update, transition, search)
2. Implement AI use cases (intent classification, response generation, PII detection)
3. Create DTOs for API boundaries
4. Implement application services (auth, tenant management)
5. Add audit logging for all write operations
6. Write unit tests for use cases

**Deliverables**:
- Complete use case implementations
- DTOs
- Application services
- Audit logging
- Unit tests

### Phase 5: REST API (Week 9-10)

**Goal**: Expose functionality via REST API

**Tasks**:
1. Create FastAPI routers (instances, issues, projects, webhooks, AI, pulse)
2. Implement Pydantic schemas for request/response
3. Add middleware (auth, rate limiting, logging, error handling)
4. Implement OpenAPI documentation
5. Add health check endpoints
6. Write API integration tests
7. Run contract tests against OpenAPI schemas

**Deliverables**:
- Complete REST API
- OpenAPI documentation
- Middleware
- Integration tests
- Contract tests (95%+ parity)

### Phase 6: MCP Interface (Week 11)

**Goal**: Expose functionality via MCP

**Tasks**:
1. Migrate MCP server to use new application layer
2. Implement MCP tools (jql_search, get_issue, transition_issue, add_comment, etc.)
3. Add SQL query tool (read-only views)
4. Implement authorization per tool
5. Write MCP integration tests

**Deliverables**:
- MCP server using new architecture
- All MCP tools migrated
- Authorization
- Integration tests

### Phase 7: Migration & Cleanup (Week 12)

**Goal**: Migrate existing features and remove old code

**Tasks**:
1. Migrate orchestrator features to new architecture
2. Migrate Work Pulse to use new data layer
3. Migrate AI Assistant to use new application layer
4. Update all tests to use new architecture
5. Remove old mockjira in-memory store
6. Remove duplicate code
7. Update documentation
8. Performance testing and optimization

**Deliverables**:
- All features migrated
- Old code removed
- Documentation updated
- Performance benchmarks

## Testing Strategy

### Unit Tests
- Test domain entities in isolation
- Test use cases with mocked repositories
- Test repositories with in-memory database
- Target: 80%+ code coverage

### Integration Tests
- Test API endpoints end-to-end
- Test database operations with real Postgres
- Test Celery tasks with real Redis
- Test Jira client with mock server

### Contract Tests
- Validate API responses against OpenAPI schemas
- Use schemathesis for property-based testing
- Target: 95%+ parity with Jira Cloud APIs

### E2E Tests
- Test complete workflows (sync, create issue, AI assistant)
- Use Docker Compose for full stack
- Test multi-tenant scenarios

### Performance Tests
- Load testing with locust or k6
- Measure API response times (p95, p99)
- Test sync performance with large datasets
- Identify bottlenecks

## Deployment Strategy

### Local Development
- Docker Compose with all services
- Hot reload for FastAPI
- Database migrations on startup
- Seed data for testing

### Staging
- Kubernetes deployment
- PostgreSQL RDS
- Redis ElastiCache
- Celery workers as separate pods
- Prometheus + Grafana for monitoring

### Production
- Blue-green deployment
- Database migrations before deployment
- Health checks and readiness probes
- Auto-scaling based on CPU/memory
- Backup and disaster recovery

## Rollback Plan

1. Keep old code in parallel during migration
2. Feature flags for new vs old code paths
3. Database migrations are reversible
4. Automated rollback on health check failures
5. Data export before major changes

## Success Metrics

- All tests passing (unit, integration, contract, e2e)
- API response times: p95 < 200ms, p99 < 500ms
- Sync latency: < 5 minutes
- Test coverage: >80%
- Contract test parity: >95%
- Zero data loss during migration
- Backward compatibility maintained

## Next Steps

Run `/tasks` to generate detailed task breakdown for implementation.

