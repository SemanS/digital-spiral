# 🚀 Admin UI Quick Start

## ⚡ Začnite za 5 minút

### 1. Prečítajte si dokumentáciu

```bash
# Otvorte v editore
code .specify/features/002-admin-ui/
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

## 🎯 Prvý task: Initialize Next.js Project

### Krok 1: Požiadajte Auggie

Skopírujte tento prompt do Auggie:

```
Auggie, implementuj Task 1.1: Initialize Next.js Project

Požiadavky z .specify/features/002-admin-ui/tasks.md:

1. Vytvor Next.js 15 projekt v admin-ui/ adresári:
   npx create-next-app@latest admin-ui --typescript --tailwind --app --src-dir --import-alias "@/*"

2. Nainštaluj core dependencies:
   npm install next-auth@beta @auth/core
   npm install @tanstack/react-query @tanstack/react-query-devtools
   npm install react-hook-form @hookform/resolvers zod
   npm install axios
   npm install lucide-react class-variance-authority clsx tailwind-merge
   npm install date-fns

3. Nainštaluj dev dependencies:
   npm install -D @types/node @types/react @types/react-dom
   npm install -D eslint-config-prettier prettier
   npm install -D vitest @testing-library/react @testing-library/jest-dom
   npm install -D @playwright/test

4. Konfiguruj ESLint a Prettier:
   - Vytvor .eslintrc.json s Next.js config
   - Vytvor .prettierrc s pravidlami
   - Pridaj scripts do package.json (lint, format)

5. Nastav Git hooks s Husky:
   - npx husky-init
   - Pridaj pre-commit hook (lint-staged)

Acceptance criteria:
- [ ] Next.js projekt vytvorený v admin-ui/
- [ ] Všetky dependencies nainštalované
- [ ] ESLint a Prettier nakonfigurované
- [ ] Git hooks nastavené
- [ ] npm run dev spúšťa dev server
- [ ] TypeScript strict mode enabled

Dodržuj constitution.md štandardy.
```

### Krok 2: Overenie

```
Auggie, over či Task 1.1 spĺňa všetky acceptance criteria.
Vypíš zoznam vytvorených súborov a konfigurácie.
```

---

## 🔐 Druhý task: Configure NextAuth v5

### Krok 1: Požiadajte Auggie

```
Auggie, implementuj Task 1.4: Configure NextAuth v5 with Google OAuth

Požiadavky z tasks.md:

1. Vytvor lib/auth/config.ts:
   - Import NextAuth, Google provider
   - Konfiguruj Google provider (clientId, clientSecret)
   - Nastav JWT session strategy
   - Pridaj session callback (include user role)
   - Export authOptions

2. Vytvor app/api/auth/[...nextauth]/route.ts:
   - Import NextAuth, authOptions
   - Export GET a POST handlers

3. Vytvor lib/auth/types.ts:
   - Define Session interface (user, expires)
   - Define User interface (id, name, email, image, role)

4. Vytvor .env.local s:
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   NEXT_PUBLIC_API_URL=http://localhost:8000
   API_URL=http://localhost:8000

Acceptance criteria:
- [ ] NextAuth nakonfigurovaný s Google provider
- [ ] JWT session strategy enabled
- [ ] Session callback includes user role
- [ ] /api/auth/signin funguje
- [ ] Google OAuth flow úspešne dokončený
- [ ] Session persistuje po refresh

Dodržuj constitution.md štandardy (TypeScript strict mode, no any).
```

### Krok 2: Získanie Google OAuth credentials

1. Choďte na [Google Cloud Console](https://console.cloud.google.com/)
2. Vytvorte nový projekt alebo vyberte existujúci
3. Povoľte Google+ API
4. Vytvorte OAuth 2.0 credentials
5. Pridajte authorized redirect URI: `http://localhost:3000/api/auth/callback/google`
6. Skopírujte Client ID a Client Secret do `.env.local`

### Krok 3: Test

```bash
# Spustite dev server
cd admin-ui
npm run dev

# Otvorte browser
open http://localhost:3000/api/auth/signin

# Prihláste sa cez Google
# Over že session funguje
```

---

## 🎨 Tretí task: Create Layout Components

### Krok 1: Požiadajte Auggie

```
Auggie, implementuj Task 1.6: Create Layout Components

Požiadavky z tasks.md:

1. Vytvor components/layout/Header.tsx:
   - Logo (Digital Spiral)
   - Navigation links (Dashboard, Instances, Settings, Logs)
   - User menu (dropdown):
     - User name + email
     - Sign out button
   - Responsive (mobile hamburger menu)

2. Vytvor components/layout/Sidebar.tsx:
   - Navigation links (Dashboard, Instances, Settings, Logs)
   - Active link highlighting
   - Icons (lucide-react)
   - Collapsible on mobile

3. Vytvor components/layout/Footer.tsx:
   - Copyright © 2024 Digital Spiral
   - Links (Privacy, Terms)

4. Vytvor app/(dashboard)/layout.tsx:
   - Use Header, Sidebar, Footer
   - Responsive layout (mobile-first)
   - Grid layout (sidebar + main content)

5. Style s Tailwind CSS

Acceptance criteria:
- [ ] Header component vytvorený s logo, nav, user menu
- [ ] Sidebar component vytvorený s navigation links
- [ ] Footer component vytvorený
- [ ] Dashboard layout používa všetky komponenty
- [ ] Layout je responsive (mobile, tablet, desktop)
- [ ] Active link highlighted v sidebar

Dodržuj constitution.md štandardy (TypeScript, Tailwind, shadcn/ui).
```

### Krok 2: Test

```bash
# Spustite dev server
npm run dev

# Otvorte browser
open http://localhost:3000/admin

# Over:
# - Header zobrazuje logo a navigation
# - Sidebar zobrazuje links
# - Footer zobrazuje copyright
# - Layout je responsive (resize browser)
```

---

## 📦 Štvrtý task: Create API Client

### Krok 1: Požiadajte Auggie

```
Auggie, implementuj Task 2.1: Create API Client with Axios

Požiadavky z tasks.md:

1. Vytvor lib/api/client.ts:
   - Import axios
   - Vytvor axios instance s base URL (process.env.NEXT_PUBLIC_API_URL)
   - Pridaj request interceptor:
     - Add Authorization header (Bearer token)
     - Add Content-Type: application/json
   - Pridaj response interceptor:
     - Handle errors (401, 403, 404, 500)
     - Transform error response
   - Pridaj retry logic s exponential backoff (3 retries)

2. Vytvor lib/api/errors.ts:
   - Define ApiError class (extends Error)
   - Define NetworkError class
   - Define ValidationError class
   - Add error codes (UNAUTHORIZED, FORBIDDEN, NOT_FOUND, SERVER_ERROR)

3. Testuj s sample request:
   - GET /health
   - Handle success
   - Handle error

Acceptance criteria:
- [ ] Axios client vytvorený s base URL
- [ ] Request interceptor adds auth token
- [ ] Response interceptor handles errors
- [ ] Retry logic funguje (3 retries s exponential backoff)
- [ ] Custom error types defined
- [ ] Sample request funguje

Dodržuj constitution.md štandardy (TypeScript strict mode).
```

### Krok 2: Test

```bash
# Spustite backend API (FastAPI)
cd ..
uvicorn src.interfaces.rest.main:app --reload --port 8000

# V novom terminali, test API client
cd admin-ui
npm run test lib/api/client.test.ts
```

---

## 🧙 Piaty task: Add Instance Wizard

### Krok 1: Použite Auggie command

```
Auggie, použij command: .augment/commands/admin-ui-add-instance.md

Implementuj kompletný wizard na pridanie Jira inštancie s:
- Multi-step wizard (Details → Auth → Validate → Save)
- Form validation s Zod
- Test connection s MCP tool
- Save s backend API
- Responsive design
- Testy

Dodržuj všetky požiadavky z command file.
```

### Krok 2: Test E2E flow

```bash
# Spustite dev server
npm run dev

# Otvorte browser
open http://localhost:3000/admin/instances/new

# Prejdite celým wizardom:
# 1. Details: Zadajte name, base URL, project filter
# 2. Auth: Vyberte API token, zadajte email, API token
# 3. Validate: Kliknite "Test Connection", over výsledok
# 4. Save: Kliknite "Save", over redirect na /admin/instances
```

---

## 📊 Progress Tracking

### Checklist Phase 1 (Week 1)

- [ ] Task 1.1: Initialize Next.js Project ✅
- [ ] Task 1.2: Install shadcn/ui ✅
- [ ] Task 1.3: Configure Environment Variables ✅
- [ ] Task 1.4: Configure NextAuth v5 ✅
- [ ] Task 1.5: Create Auth Middleware ✅
- [ ] Task 1.6: Create Layout Components ✅
- [ ] Task 1.7: Set Up TanStack Query ✅

### Checklist Phase 2 (Week 1-2)

- [ ] Task 2.1: Create API Client ✅
- [ ] Task 2.2: Define TypeScript Types
- [ ] Task 2.3: Create Zod Schemas
- [ ] Task 2.4: Create API Functions
- [ ] Task 2.5: Create Custom Hooks

### Ako sledovať progress

```
Auggie, ukáž mi progress Phase 1:

Pre každý task (1.1 - 1.7):
- Over či existujú súbory
- Over či existujú testy
- Over či testy prechádzajú
- Vytvor markdown report s progress

Format:
- ✅ Task 1.1: Initialize Project (DONE)
- 🚧 Task 1.2: Install shadcn/ui (IN PROGRESS)
- ❌ Task 1.3: Environment Variables (NOT STARTED)
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

Po dokončení Phase 1 (Task 1.1 - 1.7):

1. **Phase 2: API Client & Types** (Task 2.1 - 2.5)
   - API client s axios
   - TypeScript types a DTOs
   - Zod schemas
   - API functions
   - Custom hooks

2. **Phase 3: Instances List** (Task 3.1 - 3.4)
   - List page
   - Table component
   - Search a filters
   - Pagination

3. **Phase 4: Add Wizard** (Task 4.1 - 4.5)
   - Wizard layout
   - Step 1: Details
   - Step 2: Auth
   - Step 3: Validate
   - Step 4: Save

4. **Phase 5-8**: Detail page, Backfill, Edit/Delete, Testing

---

## 📚 Dokumentácia

Všetka dokumentácia je v:
```
.specify/features/002-admin-ui/
├── README.md                # Prehľad projektu
├── AUGGIE_GUIDE.md          # Návod pre Auggie
├── constitution.md          # Princípy a štandardy
├── spec.md                  # Požiadavky a architektúra
├── plan.md                  # Implementačný plán
└── tasks.md                 # 40+ taskov s acceptance criteria
```

Auggie commands:
```
.augment/commands/
├── admin-ui-setup.md        # Kompletný setup
├── admin-ui-phase1.md       # Phase 1 only
└── admin-ui-add-instance.md # Add instance wizard
```

---

## 🤝 Podpora

Pre otázky alebo problémy:
- GitHub Issues: [digital-spiral/issues](https://github.com/SemanS/digital-spiral/issues)
- Email: slavomir.seman@hotovo.com

---

**Začnite teraz! 🚀**

```
Auggie, začnime s Task 1.1: Initialize Next.js Project
```

Alebo použite Auggie command:

```
Auggie, použij command: .augment/commands/admin-ui-phase1.md
```

