# 🚀 LLM + SQL Analytics - Quick Start Guide

## 📋 Prehľad

Tento guide ti ukáže, ako rýchlo začať s implementáciou **Feature 004: LLM + SQL Analytics System** podľa GitHub Spec-Kit metodológie.

**Timeline**: 12 týždňov  
**Metodológia**: [GitHub Spec-Kit](https://github.com/github/spec-kit)

---

## 📚 Krok 1: Prečítaj Dokumentáciu (30 min)

### Povinné Dokumenty
1. **[constitution.md](specs/004-llm-sql-analytics/constitution.md)** (15 min)
   - Princípy projektu
   - Tech stack
   - Code quality štandardy
   - Security requirements

2. **[spec.md](specs/004-llm-sql-analytics/spec.md)** (10 min)
   - User stories
   - Technical requirements
   - API endpoints
   - Success metrics

3. **[plan.md](specs/004-llm-sql-analytics/plan.md)** (5 min)
   - Implementation phases
   - Database schema
   - File structure

### Voliteľné Dokumenty
- **[README.md](specs/004-llm-sql-analytics/README.md)** - Prehľad projektu
- **[LLM_SQL_ANALYTICS_SUMMARY.md](LLM_SQL_ANALYTICS_SUMMARY.md)** - Kompletný súhrn

---

## 🛠️ Krok 2: Setup Prostredia (15 min)

### Prerequisites
```bash
# Python 3.11+
python --version

# PostgreSQL 14+ with pgvector
psql --version

# Redis 6+
redis-cli --version

# OpenAI API key
export OPENAI_API_KEY="sk-..."
```

### Install Dependencies
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd admin-ui && npm install
```

### Database Setup
```bash
# Create database
createdb digital_spiral

# Run migrations
alembic upgrade head

# Verify
psql digital_spiral -c "\dt"
```

---

## 🏗️ Krok 3: Phase 1 - Foundation (Week 1-2)

### Week 1: Database Schema & Models

#### Task 1.1: Create Migration for New Tables
```bash
# Create migration file
alembic revision -m "add_analytics_tables"

# Edit migration file: migrations/versions/006_add_analytics_tables.py
```

**Tables to Create**:
- `sprints` - Sprint metadata
- `sprint_issues` - Many-to-many: sprint ↔ issues
- `metrics_catalog` - Metric definitions
- `analytics_jobs` - Job tracking
- `analytics_cache` - Query result cache

**Acceptance Criteria**:
- ✅ All tables created with correct columns
- ✅ Foreign keys and indexes added
- ✅ RLS policies applied
- ✅ Migration runs without errors

**SQL Example** (sprints table):
```sql
CREATE TABLE sprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    instance_id UUID NOT NULL REFERENCES jira_instances(id),
    sprint_id VARCHAR(50) NOT NULL,
    board_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(20) NOT NULL,
    goal TEXT,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    complete_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(instance_id, sprint_id)
);
```

#### Task 1.2: Create SQLAlchemy Models
```bash
# Create model files
touch src/infrastructure/database/models/sprint.py
touch src/infrastructure/database/models/sprint_issue.py
touch src/infrastructure/database/models/metrics_catalog.py
touch src/infrastructure/database/models/analytics_job.py
touch src/infrastructure/database/models/analytics_cache.py
```

**Acceptance Criteria**:
- ✅ Models inherit from Base, UUIDMixin, TimestampMixin, TenantMixin
- ✅ All relationships defined
- ✅ Type hints for all columns
- ✅ Docstrings for all models

**Example** (Sprint model):
```python
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base, UUIDMixin, TimestampMixin, TenantMixin

class Sprint(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """Sprint SQLAlchemy model."""
    
    __tablename__ = "sprints"
    
    instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("jira_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    sprint_id: Mapped[str] = mapped_column(String(50), nullable=False)
    board_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    # ... more columns
```

#### Task 1.3: Create Materialized Views
```bash
# Add to migration file
```

**Views to Create**:
- `mv_sprint_stats_enriched` - Sprint stats with z-scores
- `mv_issue_comment_stats` - Issue comment aggregations

**Acceptance Criteria**:
- ✅ Views created with correct SQL
- ✅ Indexes added for performance
- ✅ Refresh schedule configured (every 15min)

#### Task 1.4: Write Unit Tests
```bash
# Create test files
touch tests/unit/infrastructure/database/models/test_sprint.py
touch tests/unit/infrastructure/database/models/test_metrics_catalog.py
```

**Acceptance Criteria**:
- ✅ 90%+ test coverage
- ✅ All model methods tested
- ✅ Relationship tests
- ✅ Validation tests

**Run Tests**:
```bash
pytest tests/unit/infrastructure/database/models/ -v --cov
```

### Week 2: Metrics Catalog

#### Task 2.1: Define Core Metrics
```bash
# Create metrics catalog JSON
touch scripts/metrics_catalog.json
```

**Metrics to Define** (25+ total):
- **Throughput**: created, closed, velocity, throughput_ratio
- **Lead Time**: p50, p90, avg, cycle_time
- **Sprint Health**: spillover_ratio, scope_churn_ratio, accuracy_abs
- **Quality**: reopened_count, bug_count, escaped_defects
- **Capacity**: blocked_hours, wip, stuck_count
- **Composite**: sprint_problematic_score

**Example** (spillover_ratio):
```json
{
  "name": "spillover_ratio",
  "display_name": "Spillover Ratio",
  "description": "Ratio of story points removed from sprint to planned story points",
  "category": "sprint_health",
  "sql_template": "removed_sp / NULLIF(planned_sp, 0)",
  "dependencies": ["removed_sp", "planned_sp"],
  "version": "1.0.0",
  "tested": true
}
```

#### Task 2.2: Create Seeder Script
```bash
# Create seeder
touch scripts/seed_metrics_catalog.py
```

**Acceptance Criteria**:
- ✅ Reads metrics from JSON file
- ✅ Inserts into metrics_catalog table
- ✅ Handles duplicates (upsert)
- ✅ Validates metric definitions

**Run Seeder**:
```bash
python scripts/seed_metrics_catalog.py
```

#### Task 2.3: Build Metrics Catalog Service
```bash
# Create service
touch src/application/services/analytics/metrics_catalog_service.py
```

**Methods**:
- `get_all_metrics()` - List all metrics
- `get_metric(name)` - Get single metric
- `create_metric(data)` - Create new metric (admin)
- `update_metric(name, data)` - Update metric (admin)
- `deprecate_metric(name)` - Deprecate metric (admin)

**Acceptance Criteria**:
- ✅ CRUD operations implemented
- ✅ Validation for metric definitions
- ✅ Versioning support
- ✅ Unit tests (90%+ coverage)

#### Task 2.4: Write Contract Tests
```bash
# Create contract tests
touch tests/contract/test_metrics_catalog_contract.py
```

**Tests**:
- ✅ All metrics have valid SQL templates
- ✅ All dependencies exist
- ✅ Weights sum to 1.0 (for composite metrics)
- ✅ No circular dependencies

**Run Tests**:
```bash
pytest tests/contract/test_metrics_catalog_contract.py -v
```

---

## 📊 Krok 4: Verify Phase 1 (5 min)

### Checklist
- [ ] All migrations run successfully
- [ ] All models created and tested
- [ ] Materialized views created
- [ ] Metrics catalog seeded (25+ metrics)
- [ ] Unit tests pass (90%+ coverage)
- [ ] Contract tests pass

### Verify Database
```bash
# Check tables
psql digital_spiral -c "\dt"

# Check materialized views
psql digital_spiral -c "\dm"

# Check metrics catalog
psql digital_spiral -c "SELECT COUNT(*) FROM metrics_catalog;"
```

### Run All Tests
```bash
pytest tests/unit/ tests/contract/ -v --cov
```

---

## 🎯 Krok 5: Pokračuj s Phase 2 (Week 3-4)

Po úspešnom dokončení Phase 1, pokračuj s **Phase 2: Query Builder**.

**Tasks**:
- Task 3.1: Define AnalyticsSpec Pydantic schema
- Task 3.2: Build validator for AnalyticsSpec
- Task 3.3: Create query builder (Spec → SQL)
- Task 3.4: Build query executor
- Task 3.5: Add caching layer (Redis)

**Dokumentácia**: [plan.md](specs/004-llm-sql-analytics/plan.md#phase-2-query-builder-week-3-4)

---

## 🤖 Použitie s Auggie (AI Assistant)

### Manuálny Prístup (Task po Tasku)
```
Auggie, implementuj Task 1.1: Create Migration for New Tables

Požiadavky:
- Vytvor migration file: migrations/versions/006_add_analytics_tables.py
- Vytvor tabuľky: sprints, sprint_issues, metrics_catalog, analytics_jobs, analytics_cache
- Pridaj foreign keys a indexes
- Pridaj RLS policies

Acceptance criteria:
- [ ] All tables created with correct columns
- [ ] Foreign keys and indexes added
- [ ] RLS policies applied
- [ ] Migration runs without errors

Dodržuj constitution.md štandardy:
- Type hints mandatory
- Parameterized queries only
- RLS on all tables
```

### Automatický Prístup (Celá Fáza)
```
Auggie, implementuj Phase 1: Foundation (Week 1-2)

Začni s Week 1:
- Task 1.1: Create migration for new tables
- Task 1.2: Create SQLAlchemy models
- Task 1.3: Create materialized views
- Task 1.4: Write unit tests (90%+ coverage)

Potom Week 2:
- Task 2.1: Define core metrics (25+)
- Task 2.2: Create seeder script
- Task 2.3: Build metrics catalog service
- Task 2.4: Write contract tests

Po každom tasku daj mi report:
- ✅ DONE / 🚧 IN PROGRESS / ❌ NOT STARTED
- Zoznam vytvorených súborov
- Test coverage %
- Acceptance criteria status

Dodržuj constitution.md štandardy.
```

---

## 📚 Ďalšie Zdroje

### Dokumentácia
- [GitHub Spec-Kit](https://github.com/github/spec-kit) - Metodológia
- [SPEC_KIT_MASTER_GUIDE.md](SPEC_KIT_MASTER_GUIDE.md) - Ako používať Spec-Kit
- [constitution.md](specs/004-llm-sql-analytics/constitution.md) - Princípy projektu

### Príklady
- [Feature 001: Architecture Refactoring](specs/001-architecture-refactoring/)
- [Feature 002: Admin UI](specs/002-admin-ui/)

---

## 🤝 Podpora

- **Dokumentácia**: [specs/004-llm-sql-analytics/](specs/004-llm-sql-analytics/)
- **Issues**: [GitHub Issues](https://github.com/SemanS/digital-spiral/issues)
- **Email**: slavomir.seman@hotovo.com

---

**Happy coding! 🚀**

