# 🚀 Quick Start: Architecture Refactoring

## ⚡ Začnite za 5 minút

### 1. Prečítajte si dokumentáciu

```bash
# Otvorte v editore
code .specify/features/001-architecture-refactoring/
```

**Povinné čítanie** (v tomto poradí):
1. ✅ `README.md` - Prehľad projektu (5 min)
2. ✅ `AUGGIE_GUIDE.md` - Návod pre Auggie (10 min)
3. ✅ `constitution.md` - Princípy a štandardy (15 min)
4. ✅ `spec.md` - Požiadavky a architektúra (20 min)
5. ✅ `plan.md` - Implementačný plán (30 min)
6. ✅ `tasks.md` - Konkrétne úlohy (20 min)

**Celkový čas**: ~1.5 hodiny

---

## 🎯 Prvý task: Directory Structure

### Krok 1: Požiadajte Auggie

Skopírujte tento prompt do Auggie:

```
Auggie, implementuj Task 1.1: Create New Directory Structure

Požiadavky z .specify/features/001-architecture-refactoring/tasks.md:

1. Vytvor src/domain/ s podadresármi:
   - entities/
   - value_objects/
   - services/
   - events/

2. Vytvor src/application/ s podadresármi:
   - use_cases/sync/
   - use_cases/issues/
   - use_cases/ai/
   - use_cases/analytics/
   - dtos/
   - services/
   - interfaces/

3. Vytvor src/infrastructure/ s podadresármi:
   - database/models/
   - database/repositories/
   - database/migrations/
   - database/views/
   - cache/
   - queue/tasks/
   - external/
   - observability/
   - config/

4. Vytvor src/interfaces/ s podadresármi:
   - rest/routers/
   - rest/middleware/
   - rest/schemas/
   - mcp/tools/
   - sql/

5. Pridaj __init__.py do všetkých packages

6. Aktualizuj .gitignore (už je hotové)

Acceptance criteria:
- [ ] All directories created
- [ ] All __init__.py files added
- [ ] .gitignore updated
- [ ] Directory structure matches plan.md
```

### Krok 2: Overenie

```
Auggie, over či Task 1.1 spĺňa všetky acceptance criteria.
Vypíš zoznam vytvorených adresárov a súborov.
```

---

## 🗄️ Druhý task: PostgreSQL Setup

### Krok 1: Požiadajte Auggie

```
Auggie, implementuj Task 1.2: Set Up PostgreSQL with Docker Compose

Požiadavky z tasks.md:

1. Vytvor docker/docker-compose.dev.yml s:
   - PostgreSQL 14+ service
   - Redis 6+ service
   - Environment variables
   - Health checks
   - Volume mounts

2. PostgreSQL konfigurácia:
   - Extensions: uuid-ossp, pg_trgm
   - JSONB support
   - Port: 5432
   - Database: digital_spiral_dev
   - User: postgres
   - Password: postgres (dev only)

3. Redis konfigurácia:
   - Port: 6379
   - Persistence: AOF

4. Vytvor .env.example s connection strings

5. Dokumentuj v README.md

Acceptance criteria:
- [ ] docker-compose.dev.yml created
- [ ] PostgreSQL service configured
- [ ] Redis service configured
- [ ] Health checks working
- [ ] .env.example created
- [ ] Documentation updated
```

### Krok 2: Spustenie

```bash
# Spustite služby
docker compose -f docker/docker-compose.dev.yml up -d

# Overte že bežia
docker compose -f docker/docker-compose.dev.yml ps

# Overte PostgreSQL
docker compose -f docker/docker-compose.dev.yml exec postgres psql -U postgres -d digital_spiral_dev -c "SELECT version();"

# Overte Redis
docker compose -f docker/docker-compose.dev.yml exec redis redis-cli ping
```

---

## 🔧 Tretí task: Alembic Migrations

### Krok 1: Požiadajte Auggie

```
Auggie, implementuj Task 1.3: Set Up Alembic for Database Migrations

Požiadavky z tasks.md:

1. Nainštaluj Alembic:
   pip install alembic

2. Inicializuj Alembic:
   alembic init migrations

3. Konfiguruj alembic.ini:
   - Database URL from environment variable
   - Script location: migrations

4. Konfiguruj migrations/env.py:
   - Import SQLAlchemy metadata
   - Support for async operations
   - Auto-generate migrations

5. Vytvor initial migration:
   alembic revision --autogenerate -m "Initial schema"

6. Dokumentuj v README.md:
   - Migration commands
   - How to create new migrations
   - How to upgrade/downgrade

Acceptance criteria:
- [ ] Alembic installed
- [ ] alembic.ini configured
- [ ] migrations/env.py configured
- [ ] Initial migration created
- [ ] Test: alembic upgrade head
- [ ] Test: alembic downgrade -1
- [ ] Documentation updated
```

### Krok 2: Test migrácie

```bash
# Upgrade
alembic upgrade head

# Check
docker compose -f docker/docker-compose.dev.yml exec postgres psql -U postgres -d digital_spiral_dev -c "\dt"

# Downgrade
alembic downgrade -1

# Upgrade again
alembic upgrade head
```

---

## 📦 Štvrtý task: Base Models

### Krok 1: Požiadajte Auggie

```
Auggie, implementuj Task 1.4: Create Base SQLAlchemy Models

Požiadavky z tasks.md:

1. Vytvor src/infrastructure/database/models/base.py:
   - Base class (declarative_base)
   - TimestampMixin (created_at, updated_at)
   - UUIDMixin (id as UUID primary key)

2. Vytvor src/infrastructure/database/models/tenant.py:
   - Tenant model
   - Fields: id, name, created_at, updated_at
   - Relationships: jira_instances

3. Vytvor src/infrastructure/database/models/jira_instance.py:
   - JiraInstance model
   - Fields: id, tenant_id, kind, base_url, auth_method, email, api_token_encrypted, display_name, active, created_at, updated_at
   - Relationships: tenant, projects, users, issues
   - Unique constraint: (tenant_id, base_url, email)

4. Vytvor src/infrastructure/database/session.py:
   - Database session factory
   - Connection pool configuration
   - Session context manager

5. Napíš unit testy:
   - Test Tenant model creation
   - Test JiraInstance model creation
   - Test relationships
   - Test TimestampMixin
   - Test UUIDMixin
   - Use in-memory SQLite

Acceptance criteria:
- [ ] Base models created
- [ ] Tenant model created
- [ ] JiraInstance model created
- [ ] Session factory created
- [ ] Unit tests written (80%+ coverage)
- [ ] All tests passing
```

### Krok 2: Spustenie testov

```bash
# Spustite testy
pytest tests/unit/infrastructure/database/models/ -v

# Coverage report
pytest tests/unit/infrastructure/database/models/ --cov=src/infrastructure/database/models --cov-report=html
```

---

## 🎨 Piaty task: Domain Entities

### Krok 1: Požiadajte Auggie

```
Auggie, implementuj Task 1.5: Create Domain Entities

Požiadavky z tasks.md:

1. Vytvor src/domain/entities/issue.py:
   - Pure Python dataclass (no framework dependencies)
   - Fields: id, key, project_id, summary, description, status, priority, assignee_id, reporter_id, created_at, updated_at
   - Type hints for all fields
   - Validation methods: is_valid_issue_key(), can_transition_to(new_status)
   - Business logic: calculate_age_days(), is_overdue()

2. Vytvor src/domain/entities/project.py:
   - Pure Python dataclass
   - Fields: id, key, name, project_type, lead_account_id
   - Validation methods

3. Vytvor src/domain/entities/user.py:
   - Pure Python dataclass
   - Fields: id, account_id, display_name, email_hash, time_zone, active
   - Validation methods

4. Vytvor src/domain/entities/comment.py:
   - Pure Python dataclass
   - Fields: id, issue_id, author_id, body, created_at, updated_at

5. Vytvor src/domain/entities/changelog.py:
   - Pure Python dataclass
   - Fields: id, issue_id, author_id, created_at, field, from_value, to_value

6. Napíš unit testy pre každú entitu:
   - Test creation
   - Test validation
   - Test business logic
   - 80%+ coverage

Acceptance criteria:
- [ ] All entities created as pure Python classes
- [ ] No framework dependencies
- [ ] All fields with type hints
- [ ] Validation methods implemented
- [ ] Business logic methods implemented
- [ ] Unit tests written (80%+ coverage)
- [ ] All tests passing
```

### Krok 2: Spustenie testov

```bash
# Spustite testy
pytest tests/unit/domain/entities/ -v

# Coverage report
pytest tests/unit/domain/entities/ --cov=src/domain/entities --cov-report=html
```

---

## 📊 Progress Tracking

### Checklist Phase 1 (Week 1-2)

- [ ] Task 1.1: Directory structure ✅
- [ ] Task 1.2: PostgreSQL + Redis ✅
- [ ] Task 1.3: Alembic migrations ✅
- [ ] Task 1.4: Base SQLAlchemy models ✅
- [ ] Task 1.5: Domain entities ✅
- [ ] Task 1.6: Redis caching
- [ ] Task 1.7: Logging, metrics, tracing
- [ ] Task 1.8: Repository interfaces

### Ako sledovať progress

```
Auggie, ukáž mi progress Phase 1:

Pre každý task (1.1 - 1.8):
- Over či existujú súbory
- Over či existujú testy
- Over či testy prechádzajú
- Vytvor markdown report s progress

Format:
- ✅ Task 1.1: Directory structure (DONE)
- 🚧 Task 1.2: PostgreSQL setup (IN PROGRESS)
- ❌ Task 1.3: Alembic migrations (NOT STARTED)
```

---

## 🔄 Iteratívny workflow

### Pre každý task:

1. **Implementácia**
   ```
   Auggie, implementuj Task X.Y podľa tasks.md
   ```

2. **Testy**
   ```
   Auggie, napíš testy pre Task X.Y (80%+ coverage)
   ```

3. **Overenie**
   ```
   Auggie, over či Task X.Y spĺňa všetky acceptance criteria
   ```

4. **Refactoring**
   ```
   Auggie, refactoruj Task X.Y podľa constitution.md štandardov
   ```

5. **Dokumentácia**
   ```
   Auggie, aktualizuj README.md s informáciami o Task X.Y
   ```

---

## 🎯 Ďalšie kroky

Po dokončení Phase 1 (Task 1.1 - 1.8):

1. **Phase 2: Data Layer** (Task 2.1 - 2.8)
   - SQLAlchemy models
   - Repositories
   - Indexes
   - RLS policies
   - Materialized views
   - Caching

2. **Phase 3: Sync Layer** (Task 3.1 - 3.9)
   - Jira API client
   - Backfill
   - Incremental sync
   - Polling
   - Celery tasks

3. **Phase 4-7**: Application, REST API, MCP, Migration

---

## 📚 Dokumentácia

Všetka dokumentácia je v:
```
.specify/features/001-architecture-refactoring/
├── README.md                # Prehľad projektu
├── AUGGIE_GUIDE.md          # Návod pre Auggie
├── constitution.md          # Princípy a štandardy
├── spec.md                  # Požiadavky a architektúra
├── plan.md                  # Implementačný plán
└── tasks.md                 # 40+ taskov s acceptance criteria
```

---

## 🤝 Podpora

Pre otázky alebo problémy:
- GitHub Issues: [digital-spiral/issues](https://github.com/SemanS/digital-spiral/issues)
- Email: slavomir.seman@hotovo.com

---

**Začnite teraz! 🚀**

```
Auggie, začnime s Task 1.1: Create New Directory Structure
```

