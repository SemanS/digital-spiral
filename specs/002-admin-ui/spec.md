# Feature Specification: Admin UI for Jira Instance Management

## Overview

Build a modern, secure Admin UI using Next.js 15 App Router and TypeScript for managing multiple Jira Cloud instances. The UI provides a wizard-based interface for adding instances, testing connections, and managing data synchronization.

## User Stories

### US1: Admin can view all Jira instances
**As an** admin user  
**I want to** see a list of all configured Jira instances  
**So that** I can manage them centrally

**Acceptance Criteria**:
- Display table with columns: Name, Base URL, Auth Method, Status, Last Sync, Actions
- Show sync status badge (idle, syncing, error)
- Show last sync timestamp (relative time)
- Pagination for large lists (20 per page)
- Search/filter by name or URL
- Sort by name, status, or last sync

### US2: Admin can add a new Jira instance
**As an** admin user  
**I want to** add a new Jira instance through a guided wizard  
**So that** I can connect to multiple Jira Cloud instances

**Acceptance Criteria**:
- Multi-step wizard: Details → Auth → Validate → Save
- Step 1 (Details): Name, Base URL, Project Filter (optional)
- Step 2 (Auth): Auth method (API token/OAuth), Email, API token
- Step 3 (Validate): Test connection button, show results
- Step 4 (Save): Confirm and save
- Form validation with Zod
- Inline error messages
- Can go back to previous steps
- Can cancel at any time

### US3: Admin can test Jira connection
**As an** admin user  
**I want to** test the connection to a Jira instance  
**So that** I can verify credentials before saving

**Acceptance Criteria**:
- "Test Connection" button in wizard and detail page
- Shows loading spinner during test
- On success: Display user info (name, email), rate limit headers
- On error: Display detailed error message (401, 403, 404, 500, network)
- Rate limit: Max 3 tests per minute per user
- Timeout: 30 seconds

### US4: Admin can view instance details
**As an** admin user  
**I want to** view detailed information about a Jira instance  
**So that** I can monitor its status and configuration

**Acceptance Criteria**:
- Display all configuration fields (read-only)
- Show sync status section:
  - Current status (idle, syncing, error)
  - Last sync timestamp
  - Watermark (last updated issue timestamp)
  - Number of synced issues/projects/users
- Show sync history (last 10 syncs)
- Actions: Edit, Test Connection, Backfill, Resync, Delete

### US5: Admin can trigger backfill
**As an** admin user  
**I want to** trigger a full backfill of data from Jira  
**So that** I can sync all historical data

**Acceptance Criteria**:
- "Start Backfill" button in detail page
- Confirmation dialog with warning (can take hours)
- Shows progress indicator (percentage, ETA)
- Can cancel backfill
- Shows detailed progress: Projects (5/10), Issues (500/1000), Comments (2000/5000)
- On completion: Success message, redirect to instance list
- On error: Error message with retry option

### US6: Admin can trigger incremental sync
**As an** admin user  
**I want to** trigger an incremental sync  
**So that** I can manually sync recent changes

**Acceptance Criteria**:
- "Resync" button in detail page
- Syncs only changes since last watermark
- Shows progress indicator
- Faster than backfill (minutes vs hours)
- Updates watermark on completion

### US7: Admin can edit instance configuration
**As an** admin user  
**I want to** edit an existing Jira instance configuration  
**So that** I can update credentials or settings

**Acceptance Criteria**:
- Edit form with same fields as add wizard
- Pre-filled with current values
- API token field shows "••••••••" (masked)
- Can update API token (optional)
- Test connection before saving
- Confirmation dialog if sync is running

### US8: Admin can delete instance
**As an** admin user  
**I want to** delete a Jira instance  
**So that** I can remove unused instances

**Acceptance Criteria**:
- "Delete" button in detail page
- Confirmation dialog with warning (data will be deleted)
- Requires typing instance name to confirm
- Soft delete (mark as inactive)
- Can restore within 30 days
- Hard delete after 30 days (background job)

## Functional Requirements

### FR1: Authentication
- Google OAuth 2.0 with NextAuth v5
- Only authenticated users can access /admin
- Role-based access: Admin role required
- Session timeout: 24 hours
- Automatic redirect to login if unauthenticated

### FR2: Authorization
- Check user role on every request
- Admin role required for write operations
- Viewer role can only view (read-only)
- Editor role can edit but not delete
- Role stored in JWT token

### FR3: Form Validation
- Client-side validation with Zod
- Server-side validation (double validation)
- Inline error messages
- Field-level validation on blur
- Form-level validation on submit
- Custom validators for URL, email, API token format

### FR4: API Integration
- All data fetching via typed API client
- Endpoints:
  - `GET /api/instances` - List instances
  - `POST /api/instances` - Create instance
  - `GET /api/instances/:id` - Get instance details
  - `PUT /api/instances/:id` - Update instance
  - `DELETE /api/instances/:id` - Delete instance
  - `POST /api/instances/:id/test` - Test connection
  - `POST /api/instances/:id/backfill` - Start backfill
  - `POST /api/instances/:id/resync` - Start resync
  - `GET /api/instances/:id/status` - Get sync status
- Error handling with custom error types
- Retry logic with exponential backoff (3 retries)

### FR5: MCP Integration
- Backend proxies MCP tool calls
- Tools:
  - `jira:test_connection(baseUrl, email, apiToken)` → {success, user, rateLimit}
  - `jira:add_instance(config)` → {instanceId}
  - `jira:start_backfill(instanceId)` → {jobId}
  - `jira:get_sync_status(instanceId)` → {status, progress, watermark}
- Real-time status updates via polling (every 5 seconds)

### FR6: Data Security
- API tokens encrypted before storage (AES-256)
- Secrets stored in HashiCorp Vault or AWS KMS
- Database stores only encrypted reference
- API tokens never sent to client (masked)
- HTTPS only in production
- CSRF protection enabled

### FR7: Observability
- Client-side errors sent to backend
- Structured logs: `{userId, tenantId, instanceId, action, timestamp}`
- Metrics: `/metrics` endpoint (Prometheus format)
- Error tracking with Sentry
- Performance monitoring with Vercel Analytics

## Non-Functional Requirements

### NFR1: Performance
- First Contentful Paint < 1.5s
- Time to Interactive < 3s
- Lighthouse Performance score > 90
- API response time < 200ms (p95)
- Optimistic UI updates for instant feedback

### NFR2: Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader support
- Focus indicators
- Color contrast ratio > 4.5:1
- Lighthouse Accessibility score > 90

### NFR3: Responsiveness
- Mobile-first design
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Touch-friendly buttons (min 44x44px)
- Responsive tables (horizontal scroll on mobile)

### NFR4: Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- No IE11 support

### NFR5: Scalability
- Handle 100+ Jira instances per tenant
- Pagination for large lists
- Lazy loading for heavy components
- Code splitting per route

## UI/UX Design

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  Header: Logo | Navigation | User Menu                  │
├─────────────────────────────────────────────────────────┤
│  Sidebar          │  Main Content                       │
│  - Dashboard      │  ┌───────────────────────────────┐ │
│  - Instances      │  │  Page Title                   │ │
│  - Settings       │  │  Breadcrumbs                  │ │
│  - Logs           │  ├───────────────────────────────┤ │
│                   │  │  Content Area                 │ │
│                   │  │                               │ │
│                   │  │                               │ │
│                   │  └───────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  Footer: © 2024 Digital Spiral | Privacy | Terms       │
└─────────────────────────────────────────────────────────┘
```

### Pages

#### 1. `/admin/instances` (List)
- Table with instances
- Search bar
- "Add Instance" button (top right)
- Filters: Status, Auth Method
- Sort: Name, Status, Last Sync

#### 2. `/admin/instances/new` (Wizard)
- Step indicator (1/4, 2/4, 3/4, 4/4)
- Form fields per step
- "Back", "Next", "Cancel" buttons
- Progress saved in session storage

#### 3. `/admin/instances/[id]` (Detail)
- Tabs: Overview, Sync, History, Settings
- Overview: Configuration (read-only)
- Sync: Status, Watermark, Actions (Backfill, Resync)
- History: Sync history table
- Settings: Edit, Delete buttons

#### 4. `/admin/instances/[id]/edit` (Edit)
- Same form as wizard
- Pre-filled with current values
- "Save", "Cancel" buttons

### Components

#### InstancesTable
- Props: `instances`, `loading`, `onEdit`, `onDelete`, `onTest`
- Columns: Name, Base URL, Auth Method, Status, Last Sync, Actions
- Actions: Edit, Delete, Test Connection

#### InstanceFormWizard
- Props: `initialValues`, `onSubmit`, `onCancel`
- Steps: Details, Auth, Validate, Save
- Validation: Zod schemas per step

#### TestConnectionButton
- Props: `instanceId`, `onSuccess`, `onError`
- Shows loading spinner
- Displays result (success/error)

#### SyncStatusCard
- Props: `instanceId`
- Displays: Status, Watermark, Progress
- Actions: Backfill, Resync, Pause

#### BackfillProgressModal
- Props: `instanceId`, `onClose`
- Shows: Progress bar, ETA, Details
- Actions: Cancel

## Technical Architecture

### Directory Structure
```
admin-ui/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── admin/
│   │   │   ├── instances/
│   │   │   │   ├── page.tsx              # List
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx          # Wizard
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx          # Detail
│   │   │   │       └── edit/
│   │   │   │           └── page.tsx      # Edit
│   │   │   ├── settings/
│   │   │   └── logs/
│   │   └── layout.tsx
│   ├── api/
│   │   ├── auth/
│   │   │   └── [...nextauth]/
│   │   │       └── route.ts
│   │   └── instances/
│   │       ├── route.ts                  # GET, POST
│   │       └── [id]/
│   │           ├── route.ts              # GET, PUT, DELETE
│   │           ├── test/
│   │           │   └── route.ts          # POST
│   │           ├── backfill/
│   │           │   └── route.ts          # POST
│   │           └── status/
│   │               └── route.ts          # GET
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                               # shadcn/ui components
│   ├── instances/
│   │   ├── InstancesTable.tsx
│   │   ├── InstanceFormWizard.tsx
│   │   ├── TestConnectionButton.tsx
│   │   ├── SyncStatusCard.tsx
│   │   └── BackfillProgressModal.tsx
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   └── providers/
│       ├── AuthProvider.tsx
│       └── QueryProvider.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts                     # Axios client
│   │   ├── instances.ts                  # API functions
│   │   └── types.ts                      # DTOs
│   ├── auth/
│   │   ├── config.ts                     # NextAuth config
│   │   └── middleware.ts                 # Auth middleware
│   ├── hooks/
│   │   ├── useInstances.ts
│   │   ├── useCreateInstance.ts
│   │   ├── useTestConnection.ts
│   │   └── useSyncStatus.ts
│   ├── schemas/
│   │   └── instance.ts                   # Zod schemas
│   └── utils/
│       ├── cn.ts                         # Class name utility
│       └── format.ts                     # Date/time formatting
├── public/
├── styles/
│   └── globals.css
├── .env.local
├── .env.example
├── next.config.js
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## Data Models

### Instance (DTO)
```typescript
interface Instance {
  id: string;
  tenantId: string;
  name: string;
  baseUrl: string;
  authMethod: 'api_token' | 'oauth';
  email: string;
  apiTokenEncrypted: string;  // Never sent to client
  projectFilter?: string;
  status: 'idle' | 'syncing' | 'error';
  lastSyncAt?: string;
  watermark?: string;
  createdAt: string;
  updatedAt: string;
}
```

### CreateInstanceRequest
```typescript
interface CreateInstanceRequest {
  name: string;
  baseUrl: string;
  authMethod: 'api_token' | 'oauth';
  email: string;
  apiToken: string;
  projectFilter?: string;
}
```

### TestConnectionResponse
```typescript
interface TestConnectionResponse {
  success: boolean;
  user?: {
    accountId: string;
    displayName: string;
    emailAddress: string;
  };
  rateLimit?: {
    limit: number;
    remaining: number;
    reset: number;
  };
  error?: {
    code: string;
    message: string;
  };
}
```

### SyncStatus
```typescript
interface SyncStatus {
  status: 'idle' | 'syncing' | 'error';
  progress?: {
    projects: { current: number; total: number };
    issues: { current: number; total: number };
    comments: { current: number; total: number };
  };
  watermark?: string;
  startedAt?: string;
  estimatedCompletion?: string;
  error?: string;
}
```

## Success Criteria

1. **Functional**: All user stories implemented and tested
2. **Performance**: Lighthouse score > 90 (Performance, Accessibility)
3. **Security**: No secrets in client code, all API tokens encrypted
4. **UX**: Positive feedback from admin users
5. **Test Coverage**: >80% for business logic
6. **Error Rate**: <0.1% of requests fail
7. **Accessibility**: WCAG 2.1 AA compliant

## Out of Scope

- Multi-tenant UI (single tenant only)
- Advanced analytics dashboard
- Bulk operations (import/export)
- Custom auth providers (Google only)
- Mobile app
- Real-time collaboration

## Dependencies

- Next.js 15
- NextAuth v5
- shadcn/ui
- React Hook Form
- Zod
- TanStack Query
- Tailwind CSS
- Backend API (FastAPI)
- MCP server (jira-adapter)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| NextAuth v5 breaking changes | High | Pin version, test thoroughly |
| API token security | Critical | Encrypt before storage, use Vault/KMS |
| Long-running backfill | Medium | Progress indicator, cancel option |
| Rate limiting from Jira | Medium | Implement client-side rate limiting |
| Browser compatibility | Low | Test on all major browsers |

