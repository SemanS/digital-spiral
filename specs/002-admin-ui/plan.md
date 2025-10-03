# Implementation Plan: Admin UI for Jira Instance Management

## Technology Stack

### Frontend
- **Next.js 15.1.0**: App Router, Server Components, Server Actions
- **React 18.3.1**: Hooks, Suspense, Error Boundaries
- **TypeScript 5.3+**: Strict mode, no implicit any
- **Tailwind CSS 3.4+**: Utility-first styling
- **shadcn/ui**: Component library (Button, Input, Table, Dialog, etc.)

### Forms & Validation
- **React Hook Form 7.50+**: Form state management
- **Zod 3.22+**: Schema validation
- **@hookform/resolvers 3.3+**: RHF + Zod integration

### Data Fetching
- **TanStack Query v5**: Server state management, caching
- **axios 1.6+**: HTTP client with interceptors

### Authentication
- **NextAuth v5 (Auth.js)**: Authentication
- **@auth/core**: Core authentication logic
- **Google OAuth 2.0**: Primary provider

### Development Tools
- **ESLint**: Linting with Next.js config
- **Prettier**: Code formatting
- **Husky**: Git hooks
- **lint-staged**: Pre-commit linting
- **Vitest**: Unit testing
- **Playwright**: E2E testing

## Project Setup

### 1. Initialize Next.js Project

```bash
# Create Next.js app in admin-ui directory
npx create-next-app@latest admin-ui --typescript --tailwind --app --src-dir --import-alias "@/*"

cd admin-ui

# Install dependencies
npm install next-auth@beta @auth/core
npm install @tanstack/react-query @tanstack/react-query-devtools
npm install react-hook-form @hookform/resolvers zod
npm install axios
npm install lucide-react class-variance-authority clsx tailwind-merge
npm install date-fns

# Install dev dependencies
npm install -D @types/node @types/react @types/react-dom
npm install -D eslint-config-prettier prettier
npm install -D vitest @testing-library/react @testing-library/jest-dom
npm install -D @playwright/test
```

### 2. Install shadcn/ui

```bash
# Initialize shadcn/ui
npx shadcn-ui@latest init

# Install components
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
```

### 3. Environment Variables

Create `.env.local`:

```bash
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-generated-secret-change-in-production

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000

# Environment
NODE_ENV=development
```

Create `.env.example`:

```bash
# Copy .env.local to .env.example and remove sensitive values
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000
NODE_ENV=development
```

## Implementation Phases

### Phase 1: Project Setup & Authentication (Week 1)

#### Task 1.1: Initialize Project
- Create Next.js app with TypeScript and Tailwind
- Install all dependencies
- Configure ESLint and Prettier
- Set up Git hooks with Husky

#### Task 1.2: Configure NextAuth v5
- Create `lib/auth/config.ts` with NextAuth configuration
- Add Google OAuth provider
- Configure JWT session strategy
- Add role-based access control
- Create `app/api/auth/[...nextauth]/route.ts`

#### Task 1.3: Create Auth Middleware
- Create `middleware.ts` to protect /admin routes
- Check authentication status
- Check user role (admin required)
- Redirect to login if unauthenticated

#### Task 1.4: Create Layout Components
- Create `components/layout/Header.tsx`
- Create `components/layout/Sidebar.tsx`
- Create `components/layout/Footer.tsx`
- Create `app/(dashboard)/layout.tsx`

#### Task 1.5: Set Up TanStack Query
- Create `components/providers/QueryProvider.tsx`
- Configure query client with defaults
- Add React Query DevTools

### Phase 2: API Client & Types (Week 1-2)

#### Task 2.1: Create API Client
- Create `lib/api/client.ts` with axios instance
- Add request interceptor (auth token)
- Add response interceptor (error handling)
- Add retry logic with exponential backoff

#### Task 2.2: Define DTOs and Types
- Create `lib/api/types.ts` with TypeScript interfaces
- Define: Instance, CreateInstanceRequest, UpdateInstanceRequest
- Define: TestConnectionResponse, SyncStatus, BackfillProgress

#### Task 2.3: Create Zod Schemas
- Create `lib/schemas/instance.ts`
- Define schemas for all forms
- Add custom validators (URL, email, API token format)

#### Task 2.4: Create API Functions
- Create `lib/api/instances.ts`
- Implement: `getInstances()`, `getInstance(id)`, `createInstance(data)`
- Implement: `updateInstance(id, data)`, `deleteInstance(id)`
- Implement: `testConnection(id)`, `startBackfill(id)`, `getSyncStatus(id)`

### Phase 3: Instances List Page (Week 2)

#### Task 3.1: Create Instances List Page
- Create `app/(dashboard)/admin/instances/page.tsx`
- Fetch instances with TanStack Query
- Display loading state
- Display error state
- Display empty state

#### Task 3.2: Create InstancesTable Component
- Create `components/instances/InstancesTable.tsx`
- Display table with columns: Name, Base URL, Auth Method, Status, Last Sync, Actions
- Add status badge (idle, syncing, error)
- Add relative time for last sync
- Add actions dropdown (Edit, Delete, Test)

#### Task 3.3: Add Search and Filters
- Add search input (debounced)
- Add status filter dropdown
- Add auth method filter dropdown
- Implement client-side filtering

#### Task 3.4: Add Pagination
- Implement pagination (20 per page)
- Add page navigation buttons
- Show total count

### Phase 4: Add Instance Wizard (Week 2-3)

#### Task 4.1: Create Wizard Layout
- Create `app/(dashboard)/admin/instances/new/page.tsx`
- Create `components/instances/InstanceFormWizard.tsx`
- Add step indicator (1/4, 2/4, 3/4, 4/4)
- Add navigation buttons (Back, Next, Cancel)

#### Task 4.2: Implement Step 1 (Details)
- Add form fields: Name, Base URL, Project Filter
- Add Zod validation
- Add inline error messages
- Save to session storage

#### Task 4.3: Implement Step 2 (Auth)
- Add form fields: Auth Method, Email, API Token
- Add password input with show/hide toggle
- Add Zod validation
- Save to session storage

#### Task 4.4: Implement Step 3 (Validate)
- Create `components/instances/TestConnectionButton.tsx`
- Call `testConnection()` API
- Display loading spinner
- Display success result (user info, rate limit)
- Display error result (detailed message)

#### Task 4.5: Implement Step 4 (Save)
- Display summary of configuration
- Add "Save" button
- Call `createInstance()` API
- Show success toast
- Redirect to instances list

### Phase 5: Instance Detail Page (Week 3)

#### Task 5.1: Create Detail Page
- Create `app/(dashboard)/admin/instances/[id]/page.tsx`
- Fetch instance details with TanStack Query
- Display loading state
- Display error state (404)

#### Task 5.2: Create Overview Tab
- Display all configuration fields (read-only)
- Mask API token (show "••••••••")
- Add "Edit" button
- Add "Delete" button

#### Task 5.3: Create Sync Tab
- Create `components/instances/SyncStatusCard.tsx`
- Display sync status (idle, syncing, error)
- Display watermark (last updated issue timestamp)
- Display sync statistics (issues, projects, users)
- Add "Backfill" button
- Add "Resync" button

#### Task 5.4: Create History Tab
- Display sync history table (last 10 syncs)
- Columns: Started At, Completed At, Duration, Status, Issues Synced
- Add pagination

### Phase 6: Backfill & Sync (Week 3-4)

#### Task 6.1: Create Backfill Modal
- Create `components/instances/BackfillProgressModal.tsx`
- Display confirmation dialog
- Show warning (can take hours)
- Add "Start" and "Cancel" buttons

#### Task 6.2: Implement Backfill Progress
- Call `startBackfill()` API
- Poll `getSyncStatus()` every 5 seconds
- Display progress bar
- Display ETA
- Display detailed progress (projects, issues, comments)
- Add "Cancel" button

#### Task 6.3: Implement Resync
- Similar to backfill but faster
- Only syncs changes since last watermark
- Display progress

### Phase 7: Edit & Delete (Week 4)

#### Task 7.1: Create Edit Page
- Create `app/(dashboard)/admin/instances/[id]/edit/page.tsx`
- Reuse wizard form
- Pre-fill with current values
- Mask API token (optional update)
- Add "Save" button

#### Task 7.2: Implement Delete
- Add confirmation dialog
- Require typing instance name to confirm
- Call `deleteInstance()` API
- Show success toast
- Redirect to instances list

### Phase 8: Testing (Week 4-5)

#### Task 8.1: Unit Tests
- Test API client functions
- Test Zod schemas
- Test utility functions
- Test custom hooks
- Target: 80%+ coverage

#### Task 8.2: Component Tests
- Test InstancesTable
- Test InstanceFormWizard
- Test TestConnectionButton
- Test SyncStatusCard
- Use React Testing Library

#### Task 8.3: E2E Tests
- Test full flow: Add instance → Test → Save → Backfill
- Test edit flow
- Test delete flow
- Use Playwright

### Phase 9: Backend API Endpoints (Week 5)

#### Task 9.1: Create Instances Router
- Create `src/interfaces/rest/instances.py`
- Implement: `GET /api/instances` (list)
- Implement: `POST /api/instances` (create)
- Implement: `GET /api/instances/:id` (get)
- Implement: `PUT /api/instances/:id` (update)
- Implement: `DELETE /api/instances/:id` (delete)

#### Task 9.2: Create Test Connection Endpoint
- Implement: `POST /api/instances/:id/test`
- Call MCP tool: `jira:test_connection`
- Return: {success, user, rateLimit, error}

#### Task 9.3: Create Backfill Endpoint
- Implement: `POST /api/instances/:id/backfill`
- Call MCP tool: `jira:start_backfill`
- Return: {jobId}

#### Task 9.4: Create Sync Status Endpoint
- Implement: `GET /api/instances/:id/status`
- Call MCP tool: `jira:get_sync_status`
- Return: {status, progress, watermark}

### Phase 10: MCP Tools (Week 5)

#### Task 10.1: Implement jira:test_connection
- Create tool in `mcp_jira/tools.py`
- Test Jira API connection
- Fetch user info
- Return rate limit headers

#### Task 10.2: Implement jira:add_instance
- Create tool in `mcp_jira/tools.py`
- Validate credentials
- Encrypt API token
- Store in database

#### Task 10.3: Implement jira:start_backfill
- Create tool in `mcp_jira/tools.py`
- Create Celery task
- Return job ID

#### Task 10.4: Implement jira:get_sync_status
- Create tool in `mcp_jira/tools.py`
- Query sync status from database
- Return progress

## Configuration Files

### next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['lh3.googleusercontent.com'], // Google profile images
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

module.exports = nextConfig;
```

### tailwind.config.ts

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        // ... other shadcn/ui colors
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to Vercel
vercel

# Set environment variables in Vercel dashboard
# - NEXTAUTH_URL
# - NEXTAUTH_SECRET
# - GOOGLE_CLIENT_ID
# - GOOGLE_CLIENT_SECRET
# - NEXT_PUBLIC_API_URL
# - API_URL
```

### Docker

```dockerfile
# Dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

## Success Metrics

- **Performance**: Lighthouse score > 90
- **Accessibility**: WCAG 2.1 AA compliant
- **Test Coverage**: >80% for business logic
- **Error Rate**: <0.1% of requests
- **User Satisfaction**: Positive feedback from admins

## Testing Strategy

### Unit Tests (Vitest)
- Test API client functions
- Test Zod schemas
- Test utility functions (formatDate, cn, etc.)
- Test custom hooks (useInstances, useTestConnection, etc.)
- Mock axios with vi.mock()
- Target: 80%+ coverage

### Component Tests (React Testing Library)
- Test InstancesTable rendering
- Test InstanceFormWizard steps
- Test TestConnectionButton states
- Test SyncStatusCard display
- Mock TanStack Query with QueryClientProvider
- Test user interactions (click, type, submit)

### E2E Tests (Playwright)
- Test full flow: Login → Add instance → Test → Save → Backfill
- Test edit flow: Edit instance → Update → Save
- Test delete flow: Delete instance → Confirm
- Test error scenarios (network error, validation error)
- Run against local dev server

## Next Steps

Run `/tasks` to generate detailed task breakdown for implementation.

