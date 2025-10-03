# 🎯 Digital Spiral - Spec-Kit Master Guide

## Overview

Digital Spiral používa **Spec-Kit** (GitHub's Spec-Driven Development toolkit) pre štruktúrovaný vývoj s AI agentmi (Auggie). Tento guide vám ukáže, ako používať Spec-Kit príkazy pre implementáciu features.

---

## 📦 Čo je Spec-Kit?

[Spec-Kit](https://github.com/github/spec-kit) je toolkit od GitHubu pre **Spec-Driven Development** - prístup, ktorý umožňuje organizáciám sústrediť sa na produktové scenáre namiesto písania nediferencovaného kódu pomocou AI.

### Core Workflow

```
/constitution → /specify → /plan → /tasks → /implement
```

1. **Constitution**: Definuje princípy projektu, tech stack, štandardy
2. **Specify**: Detailná špecifikácia požiadaviek, user stories
3. **Plan**: Implementačný plán, technické detaily, fázy
4. **Tasks**: Konkrétne úlohy s acceptance criteria
5. **Implement**: Implementácia s AI agentom (Auggie)

---

## 🚀 Features v Digital Spiral

### Feature 001: Architecture Refactoring (Backend)

**Cieľ**: Refactor Digital Spiral do clean architecture s multi-tenant Jira integráciou.

**Dokumentácia**:
```
.specify/features/001-architecture-refactoring/
├── constitution.md          # Princípy, tech stack, štandardy
├── spec.md                  # Požiadavky, architektúra
├── plan.md                  # Implementačný plán, DB schéma
├── tasks.md                 # 40+ taskov s acceptance criteria
├── README.md                # Prehľad projektu
└── AUGGIE_GUIDE.md          # Návod pre Auggie
```

**Quick Start**:
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Kompletný súhrn
- [QUICK_START_REFACTORING.md](QUICK_START_REFACTORING.md) - Krok za krokom

**Tech Stack**:
- Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0
- PostgreSQL 14+ (JSONB, RLS, GIN indexes)
- Redis 6+ (cache, rate limiting)
- Celery (background jobs)

**Fázy**:
1. Foundation (Week 1-2): Directory structure, DB, models, entities
2. Data Layer (Week 3-4): Repositories, RLS, caching
3. Sync Layer (Week 5-6): Jira client, backfill, webhooks
4. Application (Week 7-8): Use cases, AI, audit
5. REST API (Week 9-10): Routers, middleware, tests
6. MCP Interface (Week 11): Migration, tools
7. Migration & Cleanup (Week 12): Remove old code

---

### Feature 002: Admin UI (Frontend)

**Cieľ**: Build modern Admin UI pre správu Jira inštancií s Next.js 15.

**Dokumentácia**:
```
.specify/features/002-admin-ui/
├── constitution.md          # Princípy, tech stack, štandardy
├── spec.md                  # Požiadavky, user stories
├── plan.md                  # Implementačný plán
├── tasks.md                 # 40+ taskov s acceptance criteria
├── README.md                # Prehľad projektu
└── AUGGIE_GUIDE.md          # Návod pre Auggie
```

**Quick Start**:
- [ADMIN_UI_SUMMARY.md](ADMIN_UI_SUMMARY.md) - Kompletný súhrn
- [ADMIN_UI_QUICK_START.md](ADMIN_UI_QUICK_START.md) - Krok za krokom

**Tech Stack**:
- Next.js 15 (App Router), React 18, TypeScript 5.3+
- Tailwind CSS 3.4+, shadcn/ui
- React Hook Form 7.x, Zod 3.x
- TanStack Query v5, axios
- NextAuth v5, Google OAuth 2.0

**Fázy**:
1. Project Setup & Auth (Week 1): Next.js, NextAuth, layout
2. API Client & Types (Week 1-2): Axios, types, Zod, hooks
3. Instances List (Week 2): List page, table, search, pagination
4. Add Wizard (Week 2-3): Multi-step wizard, validation, test connection
5. Detail Page (Week 3): Tabs (Overview, Sync, History, Settings)
6. Backfill & Sync (Week 3-4): Progress tracking, real-time updates
7. Edit & Delete (Week 4): Edit form, delete confirmation
8. Testing (Week 4-5): Unit, component, E2E tests

---

## 🎯 Ako používať Spec-Kit s Auggie

### Možnosť 1: Manuálne (task po tasku)

```
Auggie, implementuj Task 1.1: [Task Name]

Požiadavky z .specify/features/[feature-id]/tasks.md:
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

Acceptance criteria:
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

Dodržuj constitution.md štandardy.
```

### Možnosť 2: Použite Auggie command (celá fáza)

```
Auggie, použij command: .augment/commands/[command-name].md

Implementuj Phase X s všetkými taskami.
Po dokončení daj mi kompletný report.
```

### Možnosť 3: Kompletný setup (všetky fázy)

```
Auggie, použij command: .augment/commands/[feature]-setup.md

Implementuj kompletný [Feature Name] s všetkými fázami.
Po každej fáze daj mi report a čakaj na potvrdenie.
```

---

## 📋 Auggie Commands

### Architecture Refactoring (Backend)

Zatiaľ nie sú vytvorené commands pre refactoring. Použite manuálny prístup s tasks.md.

### Admin UI (Frontend)

```
.augment/commands/
├── admin-ui-setup.md        # Kompletný setup (všetky fázy)
├── admin-ui-phase1.md       # Phase 1 only (project setup)
└── admin-ui-add-instance.md # Add instance wizard
```

**Príklady použitia**:

```bash
# Kompletný setup
Auggie, použij command: .augment/commands/admin-ui-setup.md

# Len Phase 1
Auggie, použij command: .augment/commands/admin-ui-phase1.md

# Add instance wizard
Auggie, použij command: .augment/commands/admin-ui-add-instance.md
```

---

## 🔄 Workflow pre každý task

### 1. Implementácia
```
Auggie, implementuj Task X.Y podľa tasks.md
```

### 2. Testy
```
Auggie, napíš testy pre Task X.Y (80%+ coverage)
```

### 3. Overenie
```
Auggie, over či Task X.Y spĺňa všetky acceptance criteria
```

### 4. Refactoring
```
Auggie, refactoruj Task X.Y podľa constitution.md štandardov
```

### 5. Dokumentácia
```
Auggie, aktualizuj README.md s informáciami o Task X.Y
```

---

## 📊 Progress Tracking

### Po každej fáze

```
Auggie, daj mi progress report pre Phase X:

Pre každý task (X.1 - X.Y):
- ✅ DONE / 🚧 IN PROGRESS / ❌ NOT STARTED
- Zoznam vytvorených súborov
- Test coverage %
- Acceptance criteria status

Format:
✅ Task X.1: [Task Name] (DONE)
   Files: [list of files]
   Tests: [test files]
   Coverage: [percentage]
   Acceptance: [X/Y] ✅

🚧 Task X.2: [Task Name] (IN PROGRESS)
   Files: [list of files]
   Tests: [test files]
   Coverage: [percentage]
   Acceptance: [X/Y] 🚧
```

---

## 🎓 Best Practices

### 1. Prečítajte dokumentáciu pred začatím
- Constitution (princípy, štandardy)
- Specification (požiadavky, user stories)
- Plan (implementačný plán, tech stack)
- Tasks (konkrétne úlohy, acceptance criteria)

### 2. Implementujte task po tasku
- Nepreskakujte tasky
- Overujte acceptance criteria po každom tasku
- Píšte testy (80%+ coverage)

### 3. Dodržujte constitution.md štandardy
- TypeScript strict mode (Admin UI)
- Type hints mandatory (Backend)
- No `any` types
- Zod validation (Admin UI)
- Error handling
- Logging, metrics, tracing

### 4. Testujte priebežne
- Unit tests po každom tasku
- Integration tests po každej fáze
- E2E tests na konci

### 5. Používajte Auggie commands
- Rýchlejšie než manuálne prompty
- Konzistentné s constitution.md
- Obsahujú všetky acceptance criteria

---

## 🔧 Troubleshooting

### Auggie generuje nesprávny kód

**Riešenie**:
- Poskytnite viac kontextu z constitution.md alebo spec.md
- Referencujte konkrétne príklady
- Rozdeľte task na menšie kroky

### Testy zlyhávajú

```
Auggie, testy pre Task X.Y zlyhali s chybou: [error message]
Oprav kód a testy podľa acceptance criteria.
```

### TypeScript/Python errors

```
Auggie, [TypeScript/Python] hlási chyby v Task X.Y: [error messages]
Oprav errors podľa constitution.md (strict mode, type hints).
```

### Acceptance criteria nie sú splnené

```
Auggie, Task X.Y nespĺňa acceptance criteria:
- [ ] [Criterion 1] - [reason]
- [ ] [Criterion 2] - [reason]

Oprav implementáciu.
```

---

## 📚 Všetky dokumenty

### Feature 001: Architecture Refactoring
1. [constitution.md](.specify/features/001-architecture-refactoring/constitution.md)
2. [spec.md](.specify/features/001-architecture-refactoring/spec.md)
3. [plan.md](.specify/features/001-architecture-refactoring/plan.md)
4. [tasks.md](.specify/features/001-architecture-refactoring/tasks.md)
5. [README.md](.specify/features/001-architecture-refactoring/README.md)
6. [AUGGIE_GUIDE.md](.specify/features/001-architecture-refactoring/AUGGIE_GUIDE.md)
7. [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)
8. [QUICK_START_REFACTORING.md](QUICK_START_REFACTORING.md)

### Feature 002: Admin UI
1. [constitution.md](.specify/features/002-admin-ui/constitution.md)
2. [spec.md](.specify/features/002-admin-ui/spec.md)
3. [plan.md](.specify/features/002-admin-ui/plan.md)
4. [tasks.md](.specify/features/002-admin-ui/tasks.md)
5. [README.md](.specify/features/002-admin-ui/README.md)
6. [AUGGIE_GUIDE.md](.specify/features/002-admin-ui/AUGGIE_GUIDE.md)
7. [ADMIN_UI_SUMMARY.md](ADMIN_UI_SUMMARY.md)
8. [ADMIN_UI_QUICK_START.md](ADMIN_UI_QUICK_START.md)

### Auggie Commands
1. [admin-ui-setup.md](.augment/commands/admin-ui-setup.md)
2. [admin-ui-phase1.md](.augment/commands/admin-ui-phase1.md)
3. [admin-ui-add-instance.md](.augment/commands/admin-ui-add-instance.md)

---

## 🎯 Ďalšie kroky

### Pre Architecture Refactoring (Backend)

```bash
# Prečítajte dokumentáciu
code .specify/features/001-architecture-refactoring/

# Začnite s Phase 1, Task 1.1
# Použite QUICK_START_REFACTORING.md
```

### Pre Admin UI (Frontend)

```bash
# Prečítajte dokumentáciu
code .specify/features/002-admin-ui/

# Začnite s Phase 1, Task 1.1
# Použite ADMIN_UI_QUICK_START.md

# Alebo použite Auggie command
Auggie, použij command: .augment/commands/admin-ui-phase1.md
```

---

## 🤝 Podpora

Pre otázky alebo problémy:
- GitHub Issues: [digital-spiral/issues](https://github.com/SemanS/digital-spiral/issues)
- Email: slavomir.seman@hotovo.com

---

**Happy coding with Spec-Kit! 🚀**

