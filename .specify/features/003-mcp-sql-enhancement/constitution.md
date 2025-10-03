# Constitution - MCP & SQL Enhancement

## 🎯 Cieľ

Multi-tenant „Digital Spiral" adapter pre Jira a ďalšie PM zdroje (GitHub, Asana, Linear), s rozšíreným MCP a SQL systémom, bezpečným write-path a RLS izoláciou.

## 📋 Požiadavky Kvality

### Testing & Coverage
- **80%+ unit coverage** v domain/repositories/use-cases
- **Integration tests** pre sync flows
- **E2E tests** pre MCP tool chains
- **Contract tests** pre external APIs (Jira, GitHub, etc.)

### Database & Performance
- **PostgreSQL 14+** s Row-Level Security (RLS)
- **Všetky tabuľky tenant-scoped** - žiadne cross-tenant leaky
- **JSONB + GIN indexy** na raw/custom fields
- **EXPLAIN ANALYZE** pri ťažkých dotazoch (> 100ms)
- **Materialized views** pre agregované metriky
- **Partial indexes** pre bežné filtre

### Security
- **Žiadne tajomstvá v gite** - všetko cez environment variables alebo secrets manager
- **RLS politiky** na všetkých tenant tabuľkách
- **Audit log** pre všetky write operácie
- **Idempotencia** pri webhookoch a MCP write operáciách
- **Rate limiting** per inštancia (100 rpm default)
- **SQL injection protection** - iba whitelisted/parameterizované queries

### Caching & Performance
- **Redis caching** s TTL a invalidáciou
- **Cache invalidation** po write operáciách
- **Connection pooling** (pool_size=5, max_overflow=10)
- **Query timeout** (30s statement_timeout)

### Observability
- **Štruktúrované logy** (JSON format) s tenant_id/user_id/instance_id
- **Prometheus /metrics** endpoint
- **Tracing context** (traceparent propagation)
- **Health checks** (/health, /ready)
- **Error tracking** s context

### Development Workflow
- **Spec-driven cyklus**: /clarify → /plan → /tasks → /implement
- **Žiadne skoky mimo plánu** - vždy najprv spec, potom kód
- **Code review** pred merge
- **Automated CI/CD** - testy musia prejsť

## 🏗️ Architectural Principles

### Multi-Source Support
- **Extensible adapter pattern** pre rôzne PM systémy
- **Unified WorkItem model** - superset naprieč Jira/GitHub/Asana/Linear
- **Source-specific fields** v JSONB custom_fields
- **Consistent API** naprieč všetkými zdrojmi

### MCP Design
- **Tool-based architecture** - každá operácia je samostatný tool
- **Strict parameter validation** - Pydantic/Zod schémy
- **Error handling** - štandardizované error kódy
- **Idempotency keys** pre write operácie
- **Audit trail** - kto, kedy, čo zmenil

### SQL Safety
- **Whitelisted queries only** - žiadny raw SQL od AI
- **Parameterized queries** - SQL injection protection
- **Query templates** s validáciou parametrov
- **Performance monitoring** - slow query log
- **Query complexity limits** - max joins, max rows

### API Design
- **RESTful endpoints** pre admin operácie
- **SSE transport** pre MCP tools
- **Versioned APIs** (/v1/, /v2/)
- **Consistent error responses**
- **OpenAPI/Swagger docs**

## 🔒 Security Requirements

### Authentication & Authorization
- **Multi-tenant isolation** - RLS + application-level checks
- **API token encryption** - Fernet encryption at rest
- **OAuth2 support** pre Jira/GitHub
- **Role-based access control** (RBAC)
- **Session management** - secure, httpOnly cookies

### Data Protection
- **Encryption at rest** - sensitive credentials
- **Encryption in transit** - TLS 1.3+
- **PII handling** - GDPR compliance
- **Data retention policies**
- **Secure deletion** - soft delete + hard delete after retention

### Audit & Compliance
- **Audit log** - immutable, append-only
- **Change tracking** - who, what, when, why
- **Compliance reports** - GDPR, SOC2
- **Data export** - tenant data portability

## 📊 Performance Targets

### Response Times
- **MCP tool calls**: < 500ms (p95)
- **SQL queries**: < 100ms (p95)
- **API endpoints**: < 200ms (p95)
- **Sync operations**: < 5s per 100 issues

### Throughput
- **100 rpm** per Jira instance (rate limit)
- **1000 req/s** API capacity
- **10k issues/min** sync throughput

### Availability
- **99.9% uptime** (SLA)
- **Zero downtime deployments**
- **Graceful degradation** - fallback to cached data

## 🧪 Testing Strategy

### Unit Tests
- **Domain logic** - 100% coverage
- **Repositories** - 90%+ coverage
- **Use cases** - 90%+ coverage
- **Validators** - 100% coverage

### Integration Tests
- **Database operations** - testcontainers PostgreSQL
- **Cache operations** - testcontainers Redis
- **External APIs** - mocked responses
- **Sync flows** - end-to-end

### E2E Tests
- **Happy paths** - complete user journeys
- **Error scenarios** - network failures, timeouts
- **Multi-tenant isolation** - no data leakage
- **Performance tests** - load testing

## 📝 Documentation Requirements

### Code Documentation
- **Docstrings** - všetky public funkcie/classes
- **Type hints** - 100% coverage
- **README** - setup, usage, examples
- **Architecture docs** - ADRs (Architecture Decision Records)

### API Documentation
- **OpenAPI/Swagger** - auto-generated
- **Examples** - request/response samples
- **Error codes** - complete reference
- **Rate limits** - documented per endpoint

### Operational Documentation
- **Deployment guide** - step-by-step
- **Monitoring guide** - metrics, alerts
- **Troubleshooting** - common issues
- **Runbooks** - incident response

## 🚀 Deployment Requirements

### Infrastructure
- **Docker containers** - reproducible builds
- **Kubernetes ready** - health checks, graceful shutdown
- **Database migrations** - Alembic, zero-downtime
- **Configuration management** - environment-based

### CI/CD
- **Automated tests** - run on every PR
- **Code quality checks** - linting, formatting
- **Security scanning** - dependency vulnerabilities
- **Automated deployments** - staging → production

### Monitoring
- **Application metrics** - Prometheus
- **Log aggregation** - structured JSON logs
- **Distributed tracing** - OpenTelemetry
- **Alerting** - PagerDuty/Slack integration

## ✅ Definition of Done

### Feature Complete
- [ ] All MCP tools implemented and tested
- [ ] All SQL templates implemented and tested
- [ ] RLS policies enabled and verified
- [ ] Admin UI functional and tested
- [ ] Documentation complete

### Quality Gates
- [ ] 80%+ test coverage
- [ ] All tests passing
- [ ] No critical security vulnerabilities
- [ ] Performance targets met
- [ ] Code review approved

### Production Ready
- [ ] Deployed to staging
- [ ] E2E tests passing in staging
- [ ] Monitoring and alerts configured
- [ ] Runbooks updated
- [ ] Stakeholder sign-off

---

**Version:** 1.0.0  
**Created:** 2025-10-03  
**Status:** Draft

