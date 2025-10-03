# Digital Spiral Constitution

**Version:** 1.0  
**Last Updated:** 2025-01-03  
**Status:** Active

## 🎯 Mission Statement

Digital Spiral is an intelligent automation platform for support teams built on top of Jira Cloud. We deliver production-ready SaaS solutions that automate support workflows through AI-powered orchestration, maintaining the highest standards of reliability, type safety, and developer experience.

## 🏗️ Core Architectural Principles

### 1. API-First Design with OpenAPI Specifications

**Principle:** Every service MUST expose a well-documented, OpenAPI 3.0+ compliant REST API.

**Implementation Standards:**
- All FastAPI applications MUST generate OpenAPI specifications automatically
- API documentation MUST be accessible via `/docs` (Swagger UI) and `/redoc` endpoints
- OpenAPI schemas MUST be versioned and stored in the `schemas/` directory
- Breaking changes MUST increment major version numbers
- All endpoints MUST include comprehensive examples and descriptions

**Example Structure:**
```python
from fastapi import FastAPI

app = FastAPI(
    title="Digital Spiral Service",
    version="1.0.0",
    description="Comprehensive service description",
    openapi_tags=[
        {"name": "core", "description": "Core operations"},
        {"name": "admin", "description": "Administrative operations"}
    ]
)
```

### 2. Contract Testing with Schemathesis

**Principle:** All APIs MUST be validated against their OpenAPI specifications using automated contract testing.

**Implementation Standards:**
- Schemathesis MUST be used for property-based API testing
- Contract tests MUST run in CI/CD pipeline on every pull request
- All endpoints MUST pass contract validation before deployment
- Test coverage MUST include both positive and negative test cases
- Custom test strategies MUST be documented in `tests/contract/`

**Required Test Structure:**
```python
import schemathesis as st
from hypothesis import settings, HealthCheck

SCHEMA = st.from_path("schemas/service-api.v1.json")
CONTRACT_SETTINGS = settings(suppress_health_check=[HealthCheck.function_scoped_fixture])

@SCHEMA.parametrize()
@CONTRACT_SETTINGS
def test_api_contract(case):
    response = case.call()
    case.validate_response(response)
```

### 3. Mock-First Development Approach

**Principle:** Development MUST begin with comprehensive mocks that implement full API contracts.

**Implementation Standards:**
- Mock services MUST implement complete API surfaces, not just stubs
- Mocks MUST maintain state and support realistic workflows
- Mock data MUST be generated using configurable seed profiles
- All external dependencies MUST have corresponding mock implementations
- Mock services MUST support webhook simulation and administrative controls

**Mock Service Requirements:**
- In-memory persistence with realistic data relationships
- Configurable seed data generation via JSON profiles
- Administrative endpoints for reset, export, and health checks
- Request/response logging for debugging and analysis
- Webhook simulation with retry logic and failure scenarios

### 4. Python 3.11+ with FastAPI

**Principle:** All backend services MUST use Python 3.11+ with FastAPI framework.

**Implementation Standards:**
- Minimum Python version: 3.11 (for enhanced type hints and performance)
- FastAPI version: 0.111+ (for latest OpenAPI and performance features)
- Async/await MUST be used for all I/O operations
- Dependency injection MUST be used for service configuration
- Middleware MUST be implemented for cross-cutting concerns (logging, metrics, auth)

**Required Dependencies:**
```toml
[project]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.29",
    "pydantic>=2.7",
    "httpx>=0.27",
]
```

### 5. Type Safety with Pydantic

**Principle:** All data models MUST use Pydantic v2+ for validation and serialization.

**Implementation Standards:**
- All API request/response models MUST inherit from `pydantic.BaseModel`
- Field validation MUST be comprehensive with appropriate constraints
- Custom validators MUST be used for complex business logic
- Alias support MUST be provided for backward compatibility
- Configuration MUST enable strict validation and populate by name

**Model Standards:**
```python
from pydantic import BaseModel, Field, ConfigDict, AliasChoices

class ServiceModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True
    )
    
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt"
    )
```

### 6. Comprehensive Test Coverage

**Principle:** All code MUST maintain minimum 90% test coverage with comprehensive test suites.

**Implementation Standards:**
- Unit tests MUST cover all business logic with 95%+ coverage
- Integration tests MUST validate service interactions
- Contract tests MUST validate API compliance
- End-to-end tests MUST cover critical user workflows
- Performance tests MUST validate response times and throughput

**Test Structure:**
```
tests/
├── unit/           # Unit tests (95%+ coverage)
├── contract/       # Schemathesis contract tests
├── e2e/           # End-to-end workflow tests
├── smoke/         # Basic health and connectivity tests
└── utils/         # Test utilities and fixtures
```

### 7. Docker-Based Deployment

**Principle:** All services MUST be containerized using Docker with multi-stage builds.

**Implementation Standards:**
- Base images MUST use official Python slim images (python:3.11-slim)
- Multi-stage builds MUST be used to minimize image size
- Health checks MUST be implemented for all services
- Non-root users MUST be used for security
- Environment-specific configuration MUST use environment variables

**Dockerfile Standards:**
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8. Real-Time Webhook Support

**Principle:** All services MUST support real-time event processing via webhooks.

**Implementation Standards:**
- Webhook endpoints MUST implement signature verification
- Event processing MUST be idempotent with deduplication
- Retry logic MUST be implemented with exponential backoff
- Dead letter queues MUST handle failed events
- Webhook registration MUST be automated and self-healing

**Webhook Implementation:**
```python
@app.post("/webhooks/jira")
async def jira_webhook(request: Request):
    body = await request.body()
    verify_signature(request.headers, body)
    
    payload = await request.json()
    event_id = payload.get("id")
    
    # Idempotency check
    if await is_duplicate_event(event_id):
        return {"status": "duplicate", "processed": False}
    
    await process_webhook_event(payload)
    return {"status": "success", "processed": True}
```

### 9. ADF (Atlassian Document Format) Compliance

**Principle:** All content generation MUST comply with Atlassian Document Format specifications.

**Implementation Standards:**
- ADF documents MUST be validated against official schemas
- Content MUST support rich formatting (bold, italic, links, lists)
- Code blocks MUST use appropriate language highlighting
- Tables and media MUST be properly structured
- ADF generation MUST be testable and reproducible

**ADF Standards:**
```python
def create_adf_comment(content: str, mentions: List[str] = None) -> Dict[str, Any]:
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": content}
                ]
            }
        ]
    }
```

## 🔧 Development Standards

### Package Management
- Use appropriate package managers (pip, npm, etc.) instead of manual file editing
- Lock file versions for reproducible builds
- Regular dependency updates with security scanning

### Code Quality
- Black code formatting with line length 88
- Ruff linting with strict configuration
- Type hints required for all public APIs
- Docstrings required for all public functions and classes

### Git Workflow
- Feature branches with descriptive names
- Pull requests required for all changes
- Automated CI/CD validation before merge
- Semantic versioning for all releases

### Security
- Environment variables for all secrets
- Input validation on all endpoints
- Rate limiting on public APIs
- Regular security dependency updates

## 📊 Monitoring and Observability

### Metrics
- Prometheus metrics for all services
- Custom business metrics for key workflows
- Performance monitoring with response time tracking
- Error rate monitoring with alerting

### Logging
- Structured JSON logging
- Request ID tracking across services
- Appropriate log levels (DEBUG, INFO, WARN, ERROR)
- Log aggregation and searchability

### Health Checks
- Liveness and readiness probes
- Dependency health validation
- Graceful degradation strategies
- Circuit breaker patterns for external services

## 🎯 Success Criteria

A Digital Spiral service is considered compliant when it:

1. ✅ Exposes OpenAPI 3.0+ specification at `/docs`
2. ✅ Passes all Schemathesis contract tests
3. ✅ Maintains 90%+ test coverage
4. ✅ Uses Pydantic v2+ for all data models
5. ✅ Implements comprehensive webhook support
6. ✅ Generates valid ADF content
7. ✅ Runs in Docker with health checks
8. ✅ Follows Python 3.11+ standards
9. ✅ Implements proper monitoring and logging
10. ✅ Maintains security best practices

## 📝 Governance

This constitution is a living document that evolves with the project. Changes require:
- Technical review by core maintainers
- Impact assessment on existing services
- Migration plan for breaking changes
- Documentation updates and team communication

**Next Review Date:** 2025-04-03
