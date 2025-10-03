# Auggie Guide: Architecture Refactoring

## 🎯 Ako použiť Spec-Driven Development s Auggie

Tento guide vám ukáže, ako použiť Auggie na implementáciu architektúrneho refactoringu Digital Spiral pomocou Spec-Driven Development.

## 📋 Prehľad dokumentov

Vytvorili sme kompletný set dokumentov pre refactoring:

1. **[constitution.md](./constitution.md)** - Princípy projektu, technologický stack, štandardy
2. **[spec.md](./spec.md)** - Detailná špecifikácia, požiadavky, cieľová architektúra
3. **[plan.md](./plan.md)** - Implementačný plán, technické detaily, fázy
4. **[tasks.md](./tasks.md)** - Rozdelenie na konkrétne úlohy (40+ taskov)
5. **[README.md](./README.md)** - Prehľad projektu, getting started, dokumentácia

## 🚀 Workflow s Auggie

### Krok 1: Prečítajte si dokumenty

```
Auggie, prečítaj si tieto dokumenty:
- .specify/features/001-architecture-refactoring/constitution.md
- .specify/features/001-architecture-refactoring/spec.md
- .specify/features/001-architecture-refactoring/plan.md
- .specify/features/001-architecture-refactoring/tasks.md
```

### Krok 2: Implementujte konkrétny task

Vyberte si task z `tasks.md` a požiadajte Auggie o implementáciu:

```
Auggie, implementuj Task 1.1: Create New Directory Structure

Požiadavky:
- Vytvor src/domain/ s podadresármi: entities/, value_objects/, services/, events/
- Vytvor src/application/ s podadresármi: use_cases/, dtos/, services/
- Vytvor src/infrastructure/ s podadresármi: database/, cache/, queue/, external/, observability/, config/
- Vytvor src/interfaces/ s podadresármi: rest/, mcp/, sql/
- Pridaj __init__.py do všetkých packages
- Aktualizuj .gitignore

Acceptance criteria sú v tasks.md, Task 1.1.
```

### Krok 3: Overenie implementácie

Po implementácii požiadajte Auggie o overenie:

```
Auggie, over či Task 1.1 spĺňa všetky acceptance criteria:
- [ ] Create src/domain/ with subdirectories
- [ ] Create src/application/ with subdirectories
- [ ] Create src/infrastructure/ with subdirectories
- [ ] Create src/interfaces/ with subdirectories
- [ ] Add __init__.py files
- [ ] Update .gitignore

Ak niečo chýba, doplň to.
```

### Krok 4: Testy

```
Auggie, napíš testy pre Task 1.4: Create Base SQLAlchemy Models

Požiadavky:
- Unit testy pre Tenant model
- Unit testy pre JiraInstance model
- Test relationships medzi modelmi
- Test TimestampMixin
- Test UUIDMixin
- Použij pytest a in-memory SQLite
- Dosiahni 80%+ coverage

Acceptance criteria sú v tasks.md, Task 1.4.
```

## 📝 Príklady konkrétnych promptov

### Príklad 1: Vytvorenie domain entity

```
Auggie, vytvor domain entity pre Issue podľa constitution.md a spec.md:

Požiadavky:
- Súbor: src/domain/entities/issue.py
- Pure Python class (bez framework dependencies)
- Dataclass s type hints
- Polia: id, key, project_id, summary, description, status, priority, assignee_id, reporter_id, created_at, updated_at
- Validačné metódy: is_valid_issue_key(), can_transition_to(new_status)
- Business logic: calculate_age_days(), is_overdue()
- Žiadne database dependencies
- Žiadne FastAPI dependencies

Acceptance criteria:
- [ ] Pure Python class
- [ ] All fields with type hints
- [ ] Validation methods
- [ ] Business logic methods
- [ ] Unit tests (80%+ coverage)
```

### Príklad 2: Vytvorenie repository

```
Auggie, vytvor IssueRepository podľa plan.md, Task 2.2:

Požiadavky:
- Súbor: src/infrastructure/database/repositories/issue_repository.py
- Implementuj IssueRepository interface z src/application/interfaces/repository.py
- Metódy: get_by_id(), get_by_key(), get_all(), create(), update(), delete(), search()
- search() s filtrami: status, assignee, project, created_after, created_before
- Pagination support (limit, offset)
- Sorting support
- SQLAlchemy session management
- Type hints

Acceptance criteria:
- [ ] All CRUD operations
- [ ] search() with filters
- [ ] Pagination and sorting
- [ ] Unit tests with in-memory SQLite (80%+ coverage)
```

### Príklad 3: Vytvorenie use case

```
Auggie, vytvor CreateIssue use case podľa plan.md, Task 4.1:

Požiadavky:
- Súbor: src/application/use_cases/issues/create_issue.py
- Input: CreateIssueDTO (project_key, issue_type, summary, description, assignee, priority)
- Output: IssueDTO
- Validácia: required fields, valid project, valid assignee
- Authorization: tenant isolation check
- Volaj Jira API client na vytvorenie issue v Jira
- Ulož do database cez IssueRepository
- Invaliduj cache
- Zaloguj do audit_log
- Error handling: raise custom exceptions

Acceptance criteria:
- [ ] Input validation
- [ ] Authorization check
- [ ] Call Jira API
- [ ] Save to database
- [ ] Invalidate cache
- [ ] Audit logging
- [ ] Unit tests (80%+ coverage)
```

### Príklad 4: Vytvorenie API endpoint

```
Auggie, vytvor REST API endpoint pre vytvorenie issue podľa plan.md, Task 5.1:

Požiadavky:
- Súbor: src/interfaces/rest/routers/issues.py
- Endpoint: POST /api/v1/issues
- Request schema: CreateIssueRequest (Pydantic model)
- Response schema: IssueResponse (Pydantic model)
- Middleware: auth (JWT token), rate limiting, logging
- Volaj CreateIssue use case
- Error handling: 400 (validation), 401 (unauthorized), 403 (forbidden), 500 (internal)
- OpenAPI documentation

Acceptance criteria:
- [ ] POST endpoint
- [ ] Pydantic schemas
- [ ] Auth middleware
- [ ] Rate limiting
- [ ] Error handling
- [ ] OpenAPI docs
- [ ] Integration tests
```

### Príklad 5: Vytvorenie Celery task

```
Auggie, vytvor Celery task pre backfill podľa plan.md, Task 3.5:

Požiadavky:
- Súbor: src/infrastructure/queue/tasks/sync_tasks.py
- Task: backfill_instance_task(instance_id: str)
- Volaj BackfillInstance use case
- Retry logic: max 3 retries, exponential backoff
- Timeout: 5 minutes
- Logging: progress updates (e.g., "Synced 500/1000 issues")
- Error handling: log errors, raise exception for retry

Acceptance criteria:
- [ ] Celery task decorator
- [ ] Call use case
- [ ] Retry logic
- [ ] Timeout
- [ ] Progress logging
- [ ] Error handling
- [ ] Unit tests
```

## 🔍 Debugging s Auggie

Ak niečo nefunguje:

```
Auggie, debug problém s Task 2.2 (IssueRepository):

Chyba: sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: issues.key

Kontext:
- Snažím sa vytvoriť issue s kľúčom "DEV-123"
- Issue s týmto kľúčom už existuje v databáze
- Repository by malo použiť upsert logic

Požiadavky:
- Skontroluj IssueRepository.create() metódu
- Implementuj upsert logic (INSERT ... ON CONFLICT UPDATE)
- Pridaj test pre duplicate key scenario
- Aktualizuj dokumentáciu
```

## 📊 Progress Tracking s Auggie

```
Auggie, ukáž mi progress refactoringu:

Požiadavky:
- Prejdi všetky tasky v tasks.md
- Pre každý task over či existujú súbory
- Pre každý task over či existujú testy
- Vytvor markdown report s progress (✅ done, 🚧 in progress, ❌ not started)
- Odhadni koľko percent je hotových
```

## 🎓 Best Practices

### 1. Vždy odkazujte na dokumenty

```
Auggie, implementuj Task X.Y podľa:
- constitution.md (princípy a štandardy)
- spec.md (požiadavky)
- plan.md (technické detaily)
- tasks.md (acceptance criteria)
```

### 2. Implementujte po jednom tasku

Neimplementujte viacero taskov naraz. Každý task má svoje acceptance criteria.

### 3. Píšte testy najprv (TDD)

```
Auggie, najprv napíš testy pre Task X.Y, potom implementuj kód.
```

### 4. Overujte acceptance criteria

Po implementácii vždy overte všetky acceptance criteria z tasks.md.

### 5. Používajte type hints

Všetok kód musí mať type hints (podľa constitution.md).

### 6. Dokumentujte zmeny

```
Auggie, aktualizuj README.md s informáciami o Task X.Y.
```

## 🔄 Iteratívny vývoj

### Iterácia 1: Implementácia
```
Auggie, implementuj Task 1.1
```

### Iterácia 2: Testy
```
Auggie, napíš testy pre Task 1.1
```

### Iterácia 3: Review
```
Auggie, over či Task 1.1 spĺňa všetky acceptance criteria a constitution.md štandardy
```

### Iterácia 4: Refactoring
```
Auggie, refactoruj Task 1.1 podľa code review feedback
```

## 📚 Ďalšie zdroje

- [Spec-Kit Documentation](https://github.com/github/spec-kit)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## 🎯 Cieľ

Implementovať všetkých 40+ taskov z tasks.md s:
- ✅ 80%+ test coverage
- ✅ 95%+ contract test parity
- ✅ Všetky acceptance criteria splnené
- ✅ Všetky princípy z constitution.md dodržané
- ✅ API response times p95 < 200ms

---

**Úspešný refactoring! 🚀**

