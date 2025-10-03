# Tests - Digital Spiral

This directory contains all tests for the Digital Spiral project.

## Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── mcp/jira/           # MCP Jira tool tests
│   └── services/           # Service layer tests
├── integration/            # Integration tests (database, external services)
│   └── mcp/jira/           # MCP server integration tests
├── e2e/                    # End-to-end tests (full system)
├── conftest.py             # Shared fixtures
└── README.md               # This file
```

## Running Tests

### All Tests
```bash
make test
# or
pytest tests/ -v
```

### Unit Tests Only
```bash
make test-unit
# or
pytest tests/unit/ -v
```

### Integration Tests Only
```bash
make test-integration
# or
pytest tests/integration/ -v
```

### With Coverage
```bash
make test-coverage
# or
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

## Test Coverage

Current test files:
- ✅ `test_audit_log_service.py` - AuditLogService tests
- ✅ `test_idempotency_service.py` - IdempotencyService tests
- ✅ `test_metrics_service.py` - MetricsCollector tests
- ✅ `test_rate_limiter.py` - RateLimiter tests
- ✅ `test_tools.py` - MCP Jira tools tests
- ✅ `test_server.py` - MCP server integration tests

## Legacy Tests

### Webhook Tests
- Webhook tests patch `httpx.AsyncClient` and rely on deterministic jitter.
- Adjust jitter/poison probabilities via `POST /rest/api/3/_mock/webhooks/settings`.
- Signature helpers live under `tests/utils/webhook_sig.py` and implement the
  `sha256(secret + body)` verifier used by new test cases.
- Set `WEBHOOK_SIGNATURE_COMPAT=1` before starting the app to surface the
  optional `X-MockJira-Legacy-Signature` header when validating older clients.

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
