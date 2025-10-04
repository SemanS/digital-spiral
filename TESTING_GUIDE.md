# 🧪 Testing Guide: Digital Spiral System

## ✅ System Status

Všetky Docker services bežia:
- ✅ PostgreSQL: localhost:5432
- ✅ Redis: localhost:6379
- ✅ Mock Jira: http://localhost:9000

---

## 🚀 Spustenie Systému

### 1. Spusti Orchestrator (FastAPI)

```bash
# V prvom terminále
cd /Users/hotovo/Projects/digital-spiral
python -m uvicorn orchestrator.app:app --reload --port 8000
```

**Alebo**:

```bash
# Použiť existujúci orchestrator
python orchestrator/app.py
```

### 2. Spusti Admin UI (voliteľné)

```bash
# V druhom terminále
cd admin-ui
npm run dev
```

---

## 🧪 Testovanie API

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Očakávaný výstup**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T..."
}
```

### Test 2: Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**Očakávaný výstup**: Prometheus metrics

### Test 3: Mock Jira

```bash
curl http://localhost:9000/_mock/health
```

**Očakávaný výstup**:
```json
{
  "status": "ok"
}
```

### Test 4: Jira Projects

```bash
curl http://localhost:9000/rest/api/3/project
```

**Očakávaný výstup**: Zoznam projektov

---

## 📊 Feature 004: LLM + SQL Analytics (Po Implementácii)

### Test 5: Metrics Catalog

```bash
curl http://localhost:8000/analytics/metrics
```

**Očakávaný výstup**:
```json
{
  "metrics": [
    {
      "name": "sprint_problematic_score",
      "display_name": "Sprint Problematic Score",
      "category": "composite",
      "version": "1.0.0"
    },
    ...
  ]
}
```

### Test 6: Natural Language Query

```bash
curl -X POST http://localhost:8000/analytics/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Ukáž mi najproblematickejšie sprinty",
    "tenant_id": "tenant-1"
  }'
```

**Očakávaný výstup**:
```json
{
  "job_id": "job-123",
  "status": "queued",
  "query": "Ukáž mi najproblematickejšie sprinty"
}
```

### Test 7: Job Status

```bash
curl http://localhost:8000/analytics/jobs/job-123
```

**Očakávaný výstup**:
```json
{
  "job_id": "job-123",
  "status": "completed",
  "progress": 1.0,
  "result": {
    "data": [...],
    "chart": {...}
  }
}
```

### Test 8: Semantic Search

```bash
curl -X POST http://localhost:8000/analytics/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Nájdi sprinty s diskusiami o rollbackoch",
    "tenant_id": "tenant-1",
    "limit": 10
  }'
```

**Očakávaný výstup**:
```json
{
  "results": [
    {
      "issue_id": "PROJ-123",
      "score": 0.95,
      "summary": "Sprint 42 - Rollback issues"
    },
    ...
  ]
}
```

---

## 🔍 Debugging

### Check Logs

```bash
# Orchestrator logs
tail -f logs/orchestrator.log

# Docker logs
docker logs digital-spiral-postgres
docker logs digital-spiral-redis
docker logs mock-jira
```

### Check Database

```bash
# Connect to PostgreSQL
docker exec -it digital-spiral-postgres psql -U ds -d ds_orchestrator

# List tables
\dt

# Check metrics catalog
SELECT * FROM metrics_catalog LIMIT 10;

# Check analytics jobs
SELECT * FROM analytics_jobs ORDER BY created_at DESC LIMIT 10;
```

### Check Redis

```bash
# Connect to Redis
docker exec -it digital-spiral-redis redis-cli

# Check keys
KEYS *

# Check cache
GET analytics:cache:*
```

---

## 📚 Dokumentácia pre Auggie

### Prečítaj Dokumentáciu (45 min)

```bash
# Hlavný guide
cat AUGGIE.md

# Feature 004 dokumentácia
cat .specify/features/004-llm-sql-analytics/constitution.md
cat .specify/features/004-llm-sql-analytics/spec.md
cat .specify/features/004-llm-sql-analytics/plan.md
cat .specify/features/004-llm-sql-analytics/tasks.md
cat .specify/features/004-llm-sql-analytics/AUGGIE_GUIDE.md
```

### Implementuj Feature 004

```bash
# Spusti implementáciu
/implement
```

Auggie automaticky:
1. ✅ Načíta všetky dokumenty
2. ✅ Validuje prerequisites
3. ✅ Implementuje 29 taskov v správnom poradí
4. ✅ Poskytuje progress updates

---

## 🎯 Success Criteria

### Functional
- [ ] Natural language queries work (NL → AnalyticsSpec → SQL → Results)
- [ ] Metrics catalog has 25+ metrics
- [ ] Semantic search works (pgvector)
- [ ] Job orchestration works (Celery)
- [ ] Charts render correctly (Vega-Lite)

### Performance
- [ ] Interactive queries <30s (90% of queries)
- [ ] Async jobs <5min (99% of queries)
- [ ] Cache hit rate >80%
- [ ] Query performance <1s for 10k sprints

### Quality
- [ ] 90%+ test coverage
- [ ] No mypy errors
- [ ] No ruff errors
- [ ] All contract tests pass
- [ ] All E2E tests pass

---

## 🚀 Next Steps

### 1. Spusti Orchestrator

```bash
python -m uvicorn orchestrator.app:app --reload --port 8000
```

### 2. Otvor API Docs

```
http://localhost:8000/docs
```

### 3. Testuj Endpoints

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### 4. Implementuj Feature 004 s Auggie

```bash
# Prečítaj dokumentáciu
cat AUGGIE.md

# Spusti implementáciu
/implement
```

---

## 📞 Support

- **Dokumentácia**: `.specify/features/004-llm-sql-analytics/`
- **GitHub Issues**: https://github.com/SemanS/digital-spiral/issues
- **Email**: slavomir.seman@hotovo.com

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Status**: ✅ **READY FOR TESTING**

