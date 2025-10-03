# Digital Spiral - Source Code Structure

This directory contains the refactored Digital Spiral codebase following Clean Architecture principles.

## Architecture Layers

### 1. Domain Layer (`domain/`)

**Purpose**: Pure business logic without external dependencies

**Subdirectories**:
- `entities/` - Core business entities (Issue, Project, User, Comment, etc.)
- `value_objects/` - Immutable value objects (IssueKey, Status, Priority)
- `services/` - Domain services for complex business logic
- `events/` - Domain events representing state changes

**Key Principles**:
- No framework dependencies
- No database or HTTP dependencies
- Pure Python with type hints
- Fully testable in isolation

### 2. Application Layer (`application/`)

**Purpose**: Orchestrate domain logic and implement use cases

**Subdirectories**:
- `use_cases/` - Business workflows (CreateIssue, SyncInstance, etc.)
- `dtos/` - Data Transfer Objects for API boundaries
- `services/` - Application services (auth, rate limiting, etc.)
- `interfaces/` - Abstract interfaces for infrastructure layer

**Key Principles**:
- Depends only on domain layer
- Defines interfaces for infrastructure
- No direct database or HTTP calls
- Coordinates domain objects

### 3. Infrastructure Layer (`infrastructure/`)

**Purpose**: Implement technical details and external integrations

**Subdirectories**:
- `database/` - SQLAlchemy models, repositories, migrations
  - `models/` - SQLAlchemy ORM models
  - `repositories/` - Repository implementations
- `cache/` - Redis client and caching logic
- `queue/` - Celery tasks and job scheduling
- `external/` - External API clients (Jira, AI providers)
- `observability/` - Logging, metrics, tracing
- `config/` - Configuration management

**Key Principles**:
- Implements application interfaces
- Handles all I/O operations
- Framework-specific code lives here
- Swappable implementations

### 4. Interface Layer (`interfaces/`)

**Purpose**: Expose application via different protocols

**Subdirectories**:
- `rest/` - FastAPI routers and schemas
- `mcp/` - Model Context Protocol tools
- `sql/` - Read-only SQL views for analytics

**Key Principles**:
- Thin layer, delegates to application
- Protocol-specific code only
- Input validation and serialization
- Error handling and responses

## Dependency Flow

```
interfaces/ → application/ → domain/
     ↓            ↓
infrastructure/  ←
```

**Rules**:
- Domain layer has NO dependencies
- Application layer depends ONLY on domain
- Infrastructure implements application interfaces
- Interfaces depend on application and infrastructure

## Testing Strategy

- **Domain**: Unit tests with 95%+ coverage
- **Application**: Unit tests for use cases
- **Infrastructure**: Integration tests with real dependencies
- **Interfaces**: Contract tests against OpenAPI specs

## Getting Started

See the main [README.md](../README.md) for setup instructions.

