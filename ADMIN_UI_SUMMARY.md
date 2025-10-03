# 🎉 Admin UI - Complete Spec-Driven Development Setup

## Overview

Vytvoril som **kompletný, production-ready Spec-Driven Development plán** pre Admin UI na správu Jira inštancií. Všetko je pripravené na implementáciu s Auggie.

---

## 📦 Čo bolo vytvorené

### 1. **Spec-Kit Dokumentácia** (6 súborov)

```
.specify/features/002-admin-ui/
├── constitution.md          # Princípy, tech stack, štandardy (250+ riadkov)
├── spec.md                  # Požiadavky, user stories, architektúra (300+ riadkov)
├── plan.md                  # Implementačný plán, tech stack (300+ riadkov)
├── tasks.md                 # 40+ taskov s acceptance criteria (300+ riadkov)
├── README.md                # Prehľad projektu, getting started (300+ riadkov)
└── AUGGIE_GUIDE.md          # Návod pre Auggie s promptami (300+ riadkov)
```

### 2. **Auggie Commands** (3 súbory)

```
.augment/commands/
├── admin-ui-setup.md        # Kompletný setup (všetky fázy)
├── admin-ui-phase1.md       # Phase 1 only (project setup)
└── admin-ui-add-instance.md # Add instance wizard
```

### 3. **Quick Start Guides** (2 súbory)

```
ADMIN_UI_QUICK_START.md      # 5-minútový quick start
ADMIN_UI_SUMMARY.md          # Tento súbor (kompletný súhrn)
```

### 4. **Konfigurácia**

- ✅ Aktualizovaný `.env.example` (Google OAuth credentials)

---

## 🏗️ Architektúra

### **Tech Stack**

#### Frontend
- **Next.js 15**: App Router, Server Components, Server Actions
- **React 18**: Hooks, Suspense, Error Boundaries
- **TypeScript 5.3+**: Strict mode, type-safe development
- **Tailwind CSS 3.4+**: Utility-first styling
- **shadcn/ui**: High-quality component library

#### Forms & Validation
- **React Hook Form 7.x**: Performant form management
- **Zod 3.x**: Schema validation
- **@hookform/resolvers**: RHF + Zod integration

#### Data Fetching
- **TanStack Query v5**: Server state management, caching
- **axios**: HTTP client with interceptors

#### Authentication
- **NextAuth v5**: Authentication for Next.js
- **Google OAuth 2.0**: Primary authentication provider
- **JWT**: Session management

### **Features**

✅ **Instance Management**
- List view s search, filters, pagination
- Add wizard (Details → Auth → Validate → Save)
- Detail view s tabs (Overview, Sync, History, Settings)
- Edit a delete functionality

✅ **Connection Testing**
- Test connection pred uložením
- Real-time feedback (user info, rate limits, errors)
- Rate limiting (max 3 tests/min)

✅ **Sync Management**
- Backfill (full historical sync)
- Incremental sync (recent changes only)
- Real-time status monitoring
- Progress tracking s ETA

✅ **Security**
- Google OAuth 2.0 authentication
- Role-based access control (admin required)
- API tokens encrypted before storage
- HTTPS only in production

✅ **UX**
- Responsive design (mobile-first)
- WCAG 2.1 AA compliant
- Loading states (skeleton loaders)
- Error handling (detailed messages)
- Optimistic updates

---

## 📋 Implementačný plán

### **8 fáz, 5 týždňov, 40+ taskov**

| Fáza | Trvanie | Tasky | Popis |
|------|---------|-------|-------|
| **Phase 1** | Week 1 | 1.1-1.7 | Project Setup & Authentication |
| **Phase 2** | Week 1-2 | 2.1-2.5 | API Client & Types |
| **Phase 3** | Week 2 | 3.1-3.4 | Instances List Page |
| **Phase 4** | Week 2-3 | 4.1-4.5 | Add Instance Wizard |
| **Phase 5** | Week 3 | 5.1-5.4 | Instance Detail Page |
| **Phase 6** | Week 3-4 | 6.1-6.3 | Backfill & Sync |
| **Phase 7** | Week 4 | 7.1-7.2 | Edit & Delete |
| **Phase 8** | Week 4-5 | 8.1-8.3 | Testing |

---

## 🚀 Ako začať

### **Krok 1: Prečítajte dokumentáciu** (1.5 hodiny)

```bash
code .specify/features/002-admin-ui/
```

1. `README.md` - Prehľad (5 min)
2. `AUGGIE_GUIDE.md` - Návod (10 min)
3. `constitution.md` - Princípy (15 min)
4. `spec.md` - Požiadavky (20 min)
5. `plan.md` - Implementácia (30 min)
6. `tasks.md` - Úlohy (20 min)

### **Krok 2: Začnite s prvým taskom**

#### Možnosť A: Manuálne (task po tasku)

```
Auggie, implementuj Task 1.1: Initialize Next.js Project

Požiadavky z .specify/features/002-admin-ui/tasks.md:
- Vytvor Next.js 15 projekt v admin-ui/
- Nainštaluj dependencies
- Konfiguruj ESLint a Prettier
- Nastav Git hooks

Acceptance criteria sú v tasks.md, Task 1.1.
Dodržuj constitution.md štandardy.
```

#### Možnosť B: Použite Auggie command (celá fáza)

```
Auggie, použij command: .augment/commands/admin-ui-phase1.md

Implementuj Phase 1 (Week 1) s všetkými 7 taskami.
Po dokončení daj mi kompletný report.
```

#### Možnosť C: Kompletný setup (všetky fázy)

```
Auggie, použij command: .augment/commands/admin-ui-setup.md

Implementuj kompletný Admin UI s všetkými 8 fázami.
Po každej fáze daj mi report a čakaj na potvrdenie.
```

### **Krok 3: Iterujte cez tasky**

Pre každý task:
1. Implementácia
2. Testy (80%+ coverage)
3. Overenie acceptance criteria
4. Refactoring
5. Dokumentácia

---

## 🎯 User Stories

### US1: Admin can view all Jira instances
- List view s table
- Search, filters, pagination
- Status badges (idle, syncing, error)

### US2: Admin can add a new Jira instance
- Multi-step wizard (4 kroky)
- Form validation s Zod
- Test connection pred uložením
- Save s backend API

### US3: Admin can test Jira connection
- "Test Connection" button
- Real-time feedback
- User info, rate limits, errors

### US4: Admin can view instance details
- Detail page s tabs
- Overview, Sync, History, Settings
- Read-only configuration

### US5: Admin can trigger backfill
- "Start Backfill" button
- Confirmation dialog
- Progress tracking s ETA
- Cancel option

### US6: Admin can trigger incremental sync
- "Resync" button
- Faster than backfill
- Updates watermark

### US7: Admin can edit instance configuration
- Edit form (same as add wizard)
- Pre-filled values
- Test connection pred save

### US8: Admin can delete instance
- "Delete" button
- Confirmation dialog (type name)
- Soft delete (restore within 30 days)

---

## 🔧 Backend API Endpoints

### Instances
- `GET /api/instances` - List instances
- `POST /api/instances` - Create instance
- `GET /api/instances/:id` - Get instance details
- `PUT /api/instances/:id` - Update instance
- `DELETE /api/instances/:id` - Delete instance

### Connection & Sync
- `POST /api/instances/:id/test` - Test connection
- `POST /api/instances/:id/backfill` - Start backfill
- `POST /api/instances/:id/resync` - Start resync
- `GET /api/instances/:id/status` - Get sync status

### MCP Tools
- `jira:test_connection(baseUrl, email, apiToken)` → {success, user, rateLimit}
- `jira:add_instance(config)` → {instanceId}
- `jira:start_backfill(instanceId)` → {jobId}
- `jira:get_sync_status(instanceId)` → {status, progress, watermark}

---

## 📊 Success Metrics

Po dokončení budete mať:

- ✅ **Modern UI** - Next.js 15 + TypeScript + Tailwind
- ✅ **Secure Auth** - Google OAuth 2.0 + NextAuth v5
- ✅ **Type-safe** - TypeScript strict mode, Zod validation
- ✅ **Well-tested** - 80%+ coverage, unit + component + E2E tests
- ✅ **Accessible** - WCAG 2.1 AA compliant
- ✅ **Performant** - Lighthouse score > 90
- ✅ **Production-ready** - Vercel deployment, Docker support

---

## 📚 Všetky dokumenty

### Spec-Kit Feature
1. **[constitution.md](.specify/features/002-admin-ui/constitution.md)** - Princípy projektu
2. **[spec.md](.specify/features/002-admin-ui/spec.md)** - Špecifikácia
3. **[plan.md](.specify/features/002-admin-ui/plan.md)** - Implementačný plán
4. **[tasks.md](.specify/features/002-admin-ui/tasks.md)** - 40+ taskov
5. **[README.md](.specify/features/002-admin-ui/README.md)** - Prehľad
6. **[AUGGIE_GUIDE.md](.specify/features/002-admin-ui/AUGGIE_GUIDE.md)** - Návod pre Auggie

### Auggie Commands
7. **[admin-ui-setup.md](.augment/commands/admin-ui-setup.md)** - Kompletný setup
8. **[admin-ui-phase1.md](.augment/commands/admin-ui-phase1.md)** - Phase 1 only
9. **[admin-ui-add-instance.md](.augment/commands/admin-ui-add-instance.md)** - Add instance wizard

### Quick Start
10. **[ADMIN_UI_QUICK_START.md](ADMIN_UI_QUICK_START.md)** - Quick start guide
11. **[ADMIN_UI_SUMMARY.md](ADMIN_UI_SUMMARY.md)** - Tento súbor

---

## 🎓 Príklady promptov pre Auggie

### Implementácia tasku
```
Auggie, implementuj Task 1.1 podľa tasks.md
```

### Celá fáza
```
Auggie, použij command: .augment/commands/admin-ui-phase1.md
```

### Kompletný setup
```
Auggie, použij command: .augment/commands/admin-ui-setup.md
```

### Progress tracking
```
Auggie, ukáž mi progress Phase 1 (Task 1.1 - 1.7)
```

### Overenie
```
Auggie, over či Task 1.1 spĺňa všetky acceptance criteria
```

---

## ✨ Výsledok

Máte teraz **kompletný, production-ready Spec-Driven Development plán** pre Admin UI:

✅ **Constitution** - Princípy, tech stack, štandardy  
✅ **Specification** - User stories, požiadavky, architektúra  
✅ **Implementation Plan** - Technické detaily, fázy  
✅ **Tasks** - 40+ konkrétnych taskov s acceptance criteria  
✅ **Documentation** - README, Auggie guide, quick start  
✅ **Auggie Commands** - Ready-to-use commands pre rýchlu implementáciu  

**Môžete začať implementovať hneď teraz! 🚀**

---

## 🔗 Integrácia s existujúcim projektom

Admin UI sa integruje s:

1. **Backend API** (FastAPI):
   - `src/interfaces/rest/instances.py` - Instances router
   - `src/application/use_cases/instances/` - Business logic
   - `src/domain/entities/instance.py` - Domain model

2. **MCP Server** (jira-adapter):
   - `mcp_jira/tools.py` - MCP tools
   - `jira:test_connection`, `jira:add_instance`, `jira:start_backfill`

3. **Database** (PostgreSQL):
   - `jira_instances` table
   - `sync_watermarks` table
   - `audit_log` table

4. **Authentication**:
   - Google OAuth 2.0 (NextAuth v5)
   - Backend API token (JWT)

---

## 🎯 Ďalší krok

**Otvorte `ADMIN_UI_QUICK_START.md` a začnite s Task 1.1!**

```
Auggie, začnime s Task 1.1: Initialize Next.js Project
```

Alebo použite Auggie command:

```
Auggie, použij command: .augment/commands/admin-ui-phase1.md
```

---

**Happy coding! 🚀**

