# 🚀 Quick Start: Feature 004 - LLM + SQL Analytics System

## 📋 Pre Auggie (AI Assistant)

Tento guide ti ukáže, ako **okamžite začať** s implementáciou Feature 004 pomocou jediného príkazu.

---

## ⚡ Rýchly Štart (1 príkaz)

```bash
/implement
```

**To je všetko!** Auggie automaticky:
1. ✅ Načíta všetky dokumenty (constitution, spec, plan, tasks)
2. ✅ Validuje prerequisites
3. ✅ Parsuje 30+ taskov z tasks.md
4. ✅ Implementuje tasky v správnom poradí
5. ✅ Dodržiava dependencies medzi taskami
6. ✅ Poskytuje progress updates

---

## 📚 Čo Auggie Potrebuje Vedieť

### 1. Dokumentácia (Už Pripravená)

Všetky dokumenty sú v `.specify/features/004-llm-sql-analytics/`:

| Dokument | Účel | Čas čítania |
|----------|------|-------------|
| `constitution.md` | Princípy projektu, tech stack, štandardy | 15 min |
| `spec.md` | User stories, requirements, API endpoints | 10 min |
| `plan.md` | 6 fáz implementácie, database schema | 10 min |
| `tasks.md` | 30+ taskov s acceptance criteria | 5 min |
| `AUGGIE_GUIDE.md` | Detailný guide pre Auggie | 10 min |

**Celkový čas**: 50 minút čítania

### 2. Štruktúra Projektu

```
digital-spiral/
├── .specify/
│   └── features/
│       └── 004-llm-sql-analytics/      # ← Všetko tu
│           ├── constitution.md         # Princípy
│           ├── spec.md                 # Requirements
│           ├── plan.md                 # Implementačný plán
│           ├── tasks.md                # Tasky (30+)
│           ├── AUGGIE_GUIDE.md         # Guide pre Auggie
│           └── README.md               # Prehľad
├── AUGGIE.md                           # Hlavný guide pre Auggie
├── QUICKSTART_FEATURE_004.md           # Tento súbor
└── src/                                # Zdrojový kód
```

### 3. Tech Stack (z constitution.md)

- **Python 3.11+** - Type hints mandatory
- **FastAPI** - REST API
- **PostgreSQL 14+** - JSONB, pgvector, RLS
- **Redis 6+** - Caching, job queues
- **Celery** - Background jobs
- **OpenAI/Claude** - LLM providers
- **React 18+** - Frontend

---

## 🎯 Implementačný Proces

### Fáza 1: Foundation (Week 1-2)

**Tasky**:
- Task 1.1: Create Migration for Analytics Tables (4h)
- Task 1.2: Create SQLAlchemy Models (6h)
- Task 1.3: Create Materialized Views (8h)
- Task 1.4: Write Unit Tests (6h)
- Task 2.1: Define Core Metrics (8h)
- Task 2.2: Create Metrics Catalog Seeder (4h)
- Task 2.3: Build Metrics Catalog Service (6h)
- Task 2.4: Write Contract Tests (4h)

**Celkový čas**: ~46 hodín

**Acceptance Criteria**:
- [ ] All migrations run successfully
- [ ] All models created and tested (90%+ coverage)
- [ ] Materialized views created and indexed
- [ ] Metrics catalog seeded (25+ metrics)
- [ ] Contract tests pass

### Fáza 2: Query Builder (Week 3-4)

**Tasky**:
- Task 3.1: Define AnalyticsSpec Pydantic Schema (6h)
- Task 3.2: Build AnalyticsSpec Validator (6h)
- Task 3.3: Create Query Builder (10h)
- Task 3.4: Write Unit Tests (6h)
- Task 4.1: Build Query Executor (8h)
- Task 4.2: Add Caching Layer (6h)
- Task 4.3: Write Integration Tests (6h)

**Celkový čas**: ~48 hodín

### Fáza 3-6: Pokračovanie

Detaily v `tasks.md` - celkovo 30+ taskov.

---

## 🤖 Použitie s Auggie

### Automatický Prístup (Odporúčané)

```
/implement
```

Auggie automaticky:
1. Načíta všetky dokumenty
2. Validuje prerequisites
3. Implementuje všetky tasky v poradí
4. Poskytuje progress updates

### Manuálny Prístup (Task po Tasku)

```
Auggie, implementuj Task 1.1: Create Migration for Analytics Tables

Požiadavky:
- Vytvor migration file: migrations/versions/006_add_analytics_tables.py
- Vytvor 5 tabuliek: sprints, sprint_issues, metrics_catalog, analytics_jobs, analytics_cache
- Pridaj foreign keys a indexes
- Pridaj RLS policies

Acceptance criteria:
- [ ] Migration file created
- [ ] All 5 tables created
- [ ] Foreign keys added
- [ ] RLS policies applied
- [ ] Migration runs without errors

Dodržuj constitution.md štandardy:
- Type hints mandatory
- Parameterized queries only
- RLS on all tables
```

---

## 📊 Progress Tracking

Po každom tasku Auggie poskytne report:

```
✅ Task 1.1: Create Migration for Analytics Tables (DONE)
   Files Created:
   - migrations/versions/006_add_analytics_tables.py
   
   Tests:
   - Migration runs successfully
   - Migration can be rolled back
   
   Acceptance Criteria:
   - [5/5] ✅
   
   Next Task: Task 1.2
```

---

## 🧪 Testing Commands

```bash
# Unit tests
pytest tests/unit/ -v --cov=src/

# Integration tests
pytest tests/integration/ -v

# Contract tests
pytest tests/contract/ -v

# E2E tests
pytest tests/e2e/ -v

# All tests
pytest tests/ -v --cov=src/ --cov-report=html

# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
ruff format src/
```

---

## 🔍 Validation Commands

```bash
# Check migrations
alembic current
alembic upgrade head

# Check database
psql digital_spiral -c "\dt"
psql digital_spiral -c "\dm"

# Check metrics catalog
psql digital_spiral -c "SELECT COUNT(*) FROM metrics_catalog;"

# Check Celery
celery -A src.infrastructure.queue.celery_config inspect active

# Check Redis
redis-cli ping
```

---

## 📚 Dokumentácia

### Pre Auggie
1. **[AUGGIE.md](AUGGIE.md)** - Hlavný guide pre Auggie
2. **[.specify/features/004-llm-sql-analytics/AUGGIE_GUIDE.md](.specify/features/004-llm-sql-analytics/AUGGIE_GUIDE.md)** - Detailný guide pre Feature 004

### Pre Developera
1. **[.specify/features/004-llm-sql-analytics/constitution.md](.specify/features/004-llm-sql-analytics/constitution.md)** - Princípy projektu
2. **[.specify/features/004-llm-sql-analytics/spec.md](.specify/features/004-llm-sql-analytics/spec.md)** - Requirements
3. **[.specify/features/004-llm-sql-analytics/plan.md](.specify/features/004-llm-sql-analytics/plan.md)** - Implementačný plán
4. **[.specify/features/004-llm-sql-analytics/tasks.md](.specify/features/004-llm-sql-analytics/tasks.md)** - Tasky

### Metodológia
- **[GitHub Spec-Kit](https://github.com/github/spec-kit)** - Oficiálna metodológia
- **[.specify/README.md](.specify/README.md)** - Prehľad Spec-Driven Development

---

## 🚨 Troubleshooting

### Issue: `/implement` nefunguje
**Solution**: 
```bash
# Skontroluj, či sú skripty executable
chmod +x .specify/scripts/bash/*.sh

# Skontroluj, či existujú všetky dokumenty
ls -la .specify/features/004-llm-sql-analytics/
```

### Issue: Auggie nevie, čo má robiť
**Solution**:
```bash
# Daj Auggie prečítať hlavný guide
cat AUGGIE.md

# Daj Auggie prečítať feature guide
cat .specify/features/004-llm-sql-analytics/AUGGIE_GUIDE.md
```

### Issue: Tasky zlyhávajú
**Solution**:
```bash
# Skontroluj acceptance criteria v tasks.md
cat .specify/features/004-llm-sql-analytics/tasks.md

# Skontroluj constitution.md pre štandardy
cat .specify/features/004-llm-sql-analytics/constitution.md
```

---

## 🎯 Success Criteria

Po dokončení Feature 004:

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

## 📞 Support

- **Dokumentácia**: `.specify/features/004-llm-sql-analytics/`
- **GitHub Issues**: https://github.com/SemanS/digital-spiral/issues
- **Email**: slavomir.seman@hotovo.com

---

## 🎉 Next Steps

Po úspešnom dokončení Feature 004:

1. **Run all tests**: `pytest tests/ -v --cov`
2. **Check types**: `mypy src/`
3. **Lint code**: `ruff check src/`
4. **Create PR**: `gh pr create`
5. **Deploy**: `docker-compose up -d --build`

---

**Happy coding! 🚀**

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Methodology**: [GitHub Spec-Kit](https://github.com/github/spec-kit)

