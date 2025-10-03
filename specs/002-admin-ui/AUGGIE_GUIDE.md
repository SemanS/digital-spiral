# Auggie Implementation Guide: Admin UI

## Overview

This guide provides step-by-step prompts for using Auggie to implement the Admin UI for Jira Instance Management. Each prompt corresponds to a task in `tasks.md`.

## Prerequisites

Before starting, ensure you have:
- ✅ Read `constitution.md` (project principles)
- ✅ Read `spec.md` (requirements)
- ✅ Read `plan.md` (implementation plan)
- ✅ Read `tasks.md` (detailed tasks)

## Workflow

For each task:
1. Copy the prompt below
2. Paste into Auggie
3. Review the generated code
4. Test the implementation
5. Verify acceptance criteria
6. Move to next task

---

## Phase 1: Project Setup & Authentication

### Task 1.1: Initialize Next.js Project

```
Auggie, implementuj Task 1.1: Initialize Next.js Project

Požiadavky z .specify/features/002-admin-ui/tasks.md:

1. Vytvor Next.js 15 projekt v admin-ui/ adresári:
   npx create-next-app@latest admin-ui --typescript --tailwind --app --src-dir --import-alias "@/*"

2. Nainštaluj core dependencies:
   - next-auth@beta @auth/core
   - @tanstack/react-query @tanstack/react-query-devtools
   - react-hook-form @hookform/resolvers zod
   - axios
   - lucide-react class-variance-authority clsx tailwind-merge
   - date-fns

3. Nainštaluj dev dependencies:
   - @types/node @types/react @types/react-dom
   - eslint-config-prettier prettier
   - vitest @testing-library/react @testing-library/jest-dom
   - @playwright/test

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

---

### Task 1.2: Install and Configure shadcn/ui

```
Auggie, implementuj Task 1.2: Install and Configure shadcn/ui

Požiadavky z tasks.md:

1. Inicializuj shadcn/ui:
   cd admin-ui
   npx shadcn-ui@latest init

2. Nainštaluj komponenty:
   npx shadcn-ui@latest add button
   npx shadcn-ui@latest add input
   npx shadcn-ui@latest add label
   npx shadcn-ui@latest add table
   npx shadcn-ui@latest add dialog
   npx shadcn-ui@latest add card
   npx shadcn-ui@latest add badge
   npx shadcn-ui@latest add toast
   npx shadcn-ui@latest add form
   npx shadcn-ui@latest add select
   npx shadcn-ui@latest add tabs
   npx shadcn-ui@latest add progress
   npx shadcn-ui@latest add alert
   npx shadcn-ui@latest add dropdown-menu

3. Over že komponenty sú v components/ui/

4. Vytvor test page s sample komponentom (Button)

Acceptance criteria:
- [ ] shadcn/ui inicializované
- [ ] Všetky komponenty nainštalované v components/ui/
- [ ] components.json nakonfigurovaný
- [ ] Sample komponent renderuje správne

Dodržuj constitution.md štandardy.
```

---

### Task 1.3: Configure Environment Variables

```
Auggie, implementuj Task 1.3: Configure Environment Variables

Požiadavky z tasks.md:

1. Vytvor .env.local s:
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   NEXT_PUBLIC_API_URL=http://localhost:8000
   API_URL=http://localhost:8000
   NODE_ENV=development

2. Vytvor .env.example (bez sensitive values)

3. Pridaj .env.local do .gitignore

4. Dokumentuj environment variables v README.md:
   - Popis každej premennej
   - Ako získať Google OAuth credentials
   - Ako vygenerovať NEXTAUTH_SECRET

Acceptance criteria:
- [ ] .env.local vytvorený so všetkými premennými
- [ ] .env.example vytvorený
- [ ] .env.local v .gitignore
- [ ] README dokumentuje environment variables

Dodržuj constitution.md štandardy.
```

---

### Task 1.4: Configure NextAuth v5 with Google OAuth

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

4. Testuj Google OAuth flow:
   - Spusti dev server
   - Naviguj na /api/auth/signin
   - Prihlás sa cez Google
   - Over že session funguje

Acceptance criteria:
- [ ] NextAuth nakonfigurovaný s Google provider
- [ ] JWT session strategy enabled
- [ ] Session callback includes user role
- [ ] /api/auth/signin funguje
- [ ] Google OAuth flow úspešne dokončený
- [ ] Session persistuje po refresh

Dodržuj constitution.md štandardy (TypeScript strict mode, no any).
```

---

### Task 1.5: Create Auth Middleware

```
Auggie, implementuj Task 1.5: Create Auth Middleware

Požiadavky z tasks.md:

1. Vytvor middleware.ts v root:
   - Import NextAuth, authOptions
   - Check authentication status
   - Check user role (admin required)
   - Redirect to /api/auth/signin if unauthenticated
   - Redirect to / if not admin
   - Allow access if admin

2. Konfiguruj matcher pre /admin/* routes

3. Testuj middleware:
   - Unauthenticated user → redirect to login
   - Non-admin user → redirect to home
   - Admin user → allow access

Acceptance criteria:
- [ ] Middleware chráni /admin routes
- [ ] Unauthenticated users redirected to login
- [ ] Non-admin users redirected to home
- [ ] Admin users can access /admin routes
- [ ] Middleware runs on all /admin/* routes

Dodržuj constitution.md štandardy.
```

---

### Task 1.6: Create Layout Components

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

---

### Task 1.7: Set Up TanStack Query

```
Auggie, implementuj Task 1.7: Set Up TanStack Query

Požiadavky z tasks.md:

1. Vytvor components/providers/QueryProvider.tsx:
   - Import QueryClient, QueryClientProvider
   - Konfiguruj QueryClient s defaults:
     - staleTime: 5 * 60 * 1000 (5 minutes)
     - cacheTime: 10 * 60 * 1000 (10 minutes)
     - retry: 3
     - refetchOnWindowFocus: false
   - Pridaj ReactQueryDevtools (dev only)
   - Export QueryProvider

2. Wrap app v QueryProvider v app/layout.tsx

3. Testuj s sample query:
   - Vytvor test page
   - Use useQuery hook
   - Fetch data z API
   - Display loading, error, success states

Acceptance criteria:
- [ ] QueryProvider vytvorený
- [ ] QueryClient nakonfigurovaný s defaults
- [ ] React Query DevTools visible v dev mode
- [ ] App wrapped v QueryProvider
- [ ] Sample query funguje

Dodržuj constitution.md štandardy.
```

---

## Phase 2: API Client & Types

### Task 2.1: Create API Client with Axios

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

---

### Task 2.2: Define TypeScript Types and DTOs

```
Auggie, implementuj Task 2.2: Define TypeScript Types and DTOs

Požiadavky z tasks.md:

1. Vytvor lib/api/types.ts:
   - Define Instance interface:
     - id: string
     - tenantId: string
     - name: string
     - baseUrl: string
     - authMethod: 'api_token' | 'oauth'
     - email: string
     - projectFilter?: string
     - status: 'idle' | 'syncing' | 'error'
     - lastSyncAt?: string
     - watermark?: string
     - createdAt: string
     - updatedAt: string
   
   - Define CreateInstanceRequest interface
   - Define UpdateInstanceRequest interface
   - Define TestConnectionResponse interface
   - Define SyncStatus interface
   - Define BackfillProgress interface
   - Define PaginatedResponse<T> interface

2. Export všetky types

Acceptance criteria:
- [ ] Všetky types defined v lib/api/types.ts
- [ ] Types match backend API schema
- [ ] Všetky fields majú correct types
- [ ] Optional fields marked s ?
- [ ] Types exported

Dodržuj constitution.md štandardy (TypeScript strict mode, no any).
```

---

### Task 2.3: Create Zod Validation Schemas

```
Auggie, implementuj Task 2.3: Create Zod Validation Schemas

Požiadavky z tasks.md:

1. Vytvor lib/schemas/instance.ts:
   - Import zod
   - Define instanceDetailsSchema:
     - name: string, min 1, max 100
     - baseUrl: string, url, must be Jira Cloud URL
     - projectFilter: string, optional
   
   - Define instanceAuthSchema:
     - authMethod: enum ['api_token', 'oauth']
     - email: string, email
     - apiToken: string, min 20
   
   - Define createInstanceSchema (combine details + auth)
   - Define updateInstanceSchema

2. Pridaj custom validators:
   - URL validator (must be valid Jira Cloud URL: *.atlassian.net)
   - Email validator
   - API token format validator

3. Pridaj error messages pre každé field

Acceptance criteria:
- [ ] Všetky schemas defined v lib/schemas/instance.ts
- [ ] Custom validators implemented
- [ ] Error messages defined pre každé field
- [ ] Schemas match TypeScript types
- [ ] Test schemas s valid a invalid data

Dodržuj constitution.md štandardy (Zod validácia povinná).
```

---

### Task 2.4: Create API Functions for Instances

```
Auggie, implementuj Task 2.4: Create API Functions for Instances

Požiadavky z tasks.md:

1. Vytvor lib/api/instances.ts:
   - Import axios client, types
   - Implement getInstances(params?): Promise<PaginatedResponse<Instance>>
   - Implement getInstance(id): Promise<Instance>
   - Implement createInstance(data): Promise<Instance>
   - Implement updateInstance(id, data): Promise<Instance>
   - Implement deleteInstance(id): Promise<void>
   - Implement testConnection(id): Promise<TestConnectionResponse>
   - Implement startBackfill(id): Promise<{ jobId: string }>
   - Implement startResync(id): Promise<{ jobId: string }>
   - Implement getSyncStatus(id): Promise<SyncStatus>

2. Pridaj JSDoc comments pre každú funkciu

3. Handle errors s custom error types

Acceptance criteria:
- [ ] Všetky API functions implemented
- [ ] Functions use axios client
- [ ] Functions return typed responses
- [ ] Errors handled s custom error types
- [ ] JSDoc comments added
- [ ] Test s mock server

Dodržuj constitution.md štandardy (TypeScript strict mode, error handling).
```

---

### Task 2.5: Create Custom Hooks for Data Fetching

```
Auggie, implementuj Task 2.5: Create Custom Hooks for Data Fetching

Požiadavky z tasks.md:

1. Vytvor lib/hooks/useInstances.ts:
   - Use useQuery to fetch instances
   - Add pagination, search, filters params
   - Return { data, isLoading, error, refetch }

2. Vytvor lib/hooks/useInstance.ts:
   - Use useQuery to fetch single instance
   - Return { data, isLoading, error, refetch }

3. Vytvor lib/hooks/useCreateInstance.ts:
   - Use useMutation to create instance
   - Invalidate instances query on success
   - Return { mutate, isLoading, error }

4. Vytvor lib/hooks/useUpdateInstance.ts:
   - Use useMutation to update instance
   - Invalidate instance query on success

5. Vytvor lib/hooks/useDeleteInstance.ts:
   - Use useMutation to delete instance
   - Invalidate instances query on success

6. Vytvor lib/hooks/useTestConnection.ts:
   - Use useMutation to test connection
   - Return { mutate, isLoading, error, data }

7. Vytvor lib/hooks/useSyncStatus.ts:
   - Use useQuery s polling (every 5 seconds)
   - Return { data, isLoading, error }

Acceptance criteria:
- [ ] Všetky hooks created
- [ ] Hooks use TanStack Query
- [ ] Mutations invalidate queries on success
- [ ] Polling funguje pre sync status
- [ ] Hooks handle loading a error states
- [ ] Test hooks s mock data

Dodržuj constitution.md štandardy (TypeScript, custom hooks).
```

---

## Phase 3: Instances List Page

### Task 3.1: Create Instances List Page

```
Auggie, implementuj Task 3.1: Create Instances List Page

Požiadavky z tasks.md:

1. Vytvor app/(dashboard)/admin/instances/page.tsx:
   - Use useInstances() hook
   - Display loading state (skeleton loader)
   - Display error state (error message + retry button)
   - Display empty state (no instances message + add button)
   - Display InstancesTable component

2. Pridaj page title a breadcrumbs

3. Pridaj "Add Instance" button (top right):
   - Navigate to /admin/instances/new

Acceptance criteria:
- [ ] Page created at /admin/instances
- [ ] Loading state shows skeleton
- [ ] Error state shows message + retry button
- [ ] Empty state shows message + add button
- [ ] InstancesTable displayed when data loaded
- [ ] "Add Instance" button navigates to /admin/instances/new

Dodržuj constitution.md štandardy (TypeScript, loading states, error handling).
```

---

### Task 3.2: Create InstancesTable Component

```
Auggie, implementuj Task 3.2: Create InstancesTable Component

Požiadavky z tasks.md:

1. Vytvor components/instances/InstancesTable.tsx:
   - Use shadcn/ui Table component
   - Props: instances, loading, onEdit, onDelete, onTest
   - Columns:
     - Name (link to detail page)
     - Base URL
     - Auth Method (badge)
     - Status (badge: idle=green, syncing=blue, error=red)
     - Last Sync (relative time s date-fns)
     - Actions (dropdown: Edit, Delete, Test Connection)

2. Pridaj row hover effect

3. Pridaj responsive design (horizontal scroll on mobile)

Acceptance criteria:
- [ ] Table component created
- [ ] Všetky columns displayed correctly
- [ ] Status badge shows correct color
- [ ] Last sync shows relative time
- [ ] Actions dropdown funguje
- [ ] Table je responsive
- [ ] Row hover effect funguje

Dodržuj constitution.md štandardy (TypeScript, shadcn/ui, Tailwind).
```

---

## Continue with remaining tasks...

For the remaining tasks (3.3 - 8.3), follow the same pattern:

1. Copy task description from tasks.md
2. Create prompt with:
   - Task number and name
   - Requirements from tasks.md
   - Acceptance criteria
   - Reference to constitution.md standards
3. Paste into Auggie
4. Review and test implementation

---

## Tips for Using Auggie

### 1. Be Specific
- Reference exact file paths
- Include acceptance criteria
- Mention constitution.md standards

### 2. Iterate
- If implementation is not correct, provide feedback
- Ask Auggie to fix specific issues
- Reference error messages

### 3. Test After Each Task
- Run tests: `npm run test`
- Check TypeScript: `npm run type-check`
- Run linter: `npm run lint`

### 4. Verify Acceptance Criteria
After each task, verify all acceptance criteria are met:
```
Auggie, over či Task X.Y spĺňa všetky acceptance criteria z tasks.md.
Vytvor checklist a označ splnené kritériá.
```

### 5. Request Progress Report
After each phase:
```
Auggie, daj mi progress report pre Phase X:

Pre každý task (X.1 - X.Y):
- ✅ DONE / 🚧 IN PROGRESS / ❌ NOT STARTED
- Zoznam vytvorených súborov
- Test coverage %
- Acceptance criteria status
```

---

## Example: Complete Task Flow

### 1. Implement Task
```
Auggie, implementuj Task 1.1: Initialize Next.js Project
[paste full prompt from above]
```

### 2. Review Implementation
- Check generated files
- Review code quality
- Test functionality

### 3. Verify Acceptance Criteria
```
Auggie, over či Task 1.1 spĺňa všetky acceptance criteria.
```

### 4. Fix Issues (if any)
```
Auggie, Task 1.1 má problém: [describe issue]
Oprav podľa acceptance criteria.
```

### 5. Move to Next Task
```
Auggie, implementuj Task 1.2: Install and Configure shadcn/ui
[paste full prompt]
```

---

## Troubleshooting

### Auggie generates incorrect code
- Provide more context from constitution.md or spec.md
- Reference specific examples
- Break down task into smaller steps

### Tests fail
```
Auggie, testy pre Task X.Y zlyhali s chybou: [error message]
Oprav kód a testy.
```

### TypeScript errors
```
Auggie, TypeScript hlási chyby v Task X.Y: [error messages]
Oprav type errors podľa constitution.md (strict mode, no any).
```

---

## Next Steps

1. Start with Phase 1, Task 1.1
2. Follow prompts sequentially
3. Verify acceptance criteria after each task
4. Request progress reports after each phase
5. Continue through all phases (1-8)

Good luck! 🚀

