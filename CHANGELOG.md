# Changelog

## Unreleased

### Added - MCP & SQL Enhancement (003-mcp-sql-enhancement)

#### MCP Servers
- Added MCP Jira Server (port 8055) with 8 tools for AI assistant integration
- Added MCP SQL Server (port 8056) with 6 whitelisted query templates
- Added Server-Sent Events (SSE) support for real-time communication
- Added metrics endpoints for performance tracking

#### Database
- Added `AuditLog` model for tracking all write operations
- Added `IdempotencyKey` model for safe retries with 24h TTL
- Added migration for audit_logs and idempotency_keys tables

#### Services
- Added `AuditLogService` for automatic audit logging
- Added `IdempotencyService` for duplicate prevention
- Added `RateLimiter` with Redis and in-memory backends
- Added `MetricsCollector` for performance tracking with percentiles

#### Testing
- Added 50+ unit tests with ~85% coverage
- Added integration tests for MCP servers
- Added pytest configuration and fixtures

#### Documentation
- Added comprehensive documentation (7 files)
- Added demo script and examples
- Added health check and coverage scripts

#### Infrastructure
- Added Docker Compose services for Redis, MCP Jira, and MCP SQL
- Added Makefile commands for development
- Added `sse-starlette` dependency

### Changed
- Updated `requirements.txt` with new dependencies
- Updated `docker-compose.yml` with new services
- Updated `pytest.ini` with new markers
- Webhook deliveries now sign payloads with `sha256(secret + body)` and expose
  deterministic `X-MockJira-Signature-Version` headers.
- Dual signature mode can be toggled via `WEBHOOK_SIGNATURE_COMPAT` to keep the
  legacy HMAC digest during migration.

### Security
- Added SQL injection protection via whitelisted query templates
- Added JQL validation to prevent forbidden keywords
- Added parameter validation with Pydantic
- Added rate limiting to prevent abuse

### Previous Changes
- Delivery metadata now persists the canonical wire body (base64) and headers
  for replay verification.
- New `/_mock/webhooks/logs` endpoint exposing structured delivery attempts and
  a FastAPI admin info payload advertising the active signature version.
- Expanded test coverage for webhooks, JQL order/filter behaviour, custom
  fields, issue links and changelog history.
