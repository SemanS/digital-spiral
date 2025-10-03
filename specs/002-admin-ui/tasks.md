# Tasks: Admin UI for Jira Instance Management

## Phase 1: Project Setup & Authentication (Week 1)

### Task 1.1: Initialize Next.js Project
**Estimate**: 2 hours  
**Priority**: Critical  
**Dependencies**: None

**Description**:
Create a new Next.js 15 project with TypeScript, Tailwind CSS, and App Router in the `admin-ui/` directory.

**Steps**:
1. Run `npx create-next-app@latest admin-ui --typescript --tailwind --app --src-dir --import-alias "@/*"`
2. Install core dependencies:
   - `next-auth@beta @auth/core`
   - `@tanstack/react-query @tanstack/react-query-devtools`
   - `react-hook-form @hookform/resolvers zod`
   - `axios`
   - `lucide-react class-variance-authority clsx tailwind-merge`
   - `date-fns`
3. Install dev dependencies:
   - `@types/node @types/react @types/react-dom`
   - `eslint-config-prettier prettier`
   - `vitest @testing-library/react @testing-library/jest-dom`
   - `@playwright/test`
4. Configure ESLint and Prettier
5. Set up Git hooks with Husky

**Acceptance Criteria**:
- [X] Next.js project created in `admin-ui/` directory
- [X] All dependencies installed
- [X] ESLint and Prettier configured
- [X] Git hooks set up
- [X] `npm run dev` starts development server
- [X] TypeScript strict mode enabled

---

### Task 1.2: Install and Configure shadcn/ui
**Estimate**: 1 hour  
**Priority**: Critical  
**Dependencies**: Task 1.1

**Description**:
Initialize shadcn/ui and install all required components.

**Steps**:
1. Run `npx shadcn-ui@latest init`
2. Install components:
   - `button`, `input`, `label`, `table`, `dialog`, `card`, `badge`
   - `toast`, `form`, `select`, `tabs`, `progress`, `alert`, `dropdown-menu`
3. Verify components are in `components/ui/`
4. Test a sample component

**Acceptance Criteria**:
- [X] shadcn/ui initialized
- [X] All components installed in `components/ui/`
- [X] `components.json` configured
- [X] Sample component renders correctly

---

### Task 1.3: Configure Environment Variables
**Estimate**: 30 minutes  
**Priority**: Critical  
**Dependencies**: Task 1.1

**Description**:
Set up environment variables for NextAuth, Google OAuth, and backend API.

**Steps**:
1. Create `.env.local` with:
   - `NEXTAUTH_URL`, `NEXTAUTH_SECRET`
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `NEXT_PUBLIC_API_URL`, `API_URL`
2. Create `.env.example` (without sensitive values)
3. Add `.env.local` to `.gitignore`
4. Document environment variables in README

**Acceptance Criteria**:
- [X] `.env.local` created with all variables
- [X] `.env.example` created
- [X] `.env.local` in `.gitignore`
- [X] README documents environment variables

---

### Task 1.4: Configure NextAuth v5 with Google OAuth
**Estimate**: 3 hours  
**Priority**: Critical  
**Dependencies**: Task 1.3

**Description**:
Set up NextAuth v5 with Google OAuth provider and JWT session strategy.

**Steps**:
1. Create `lib/auth/config.ts`:
   - Configure Google provider
   - Set JWT session strategy
   - Add session callback (include user role)
2. Create `app/api/auth/[...nextauth]/route.ts`:
   - Export GET and POST handlers
3. Create `lib/auth/types.ts`:
   - Define Session, User types
4. Test Google OAuth flow

**Acceptance Criteria**:
- [X] NextAuth configured with Google provider
- [X] JWT session strategy enabled
- [X] Session callback includes user role
- [X] `/api/auth/signin` works
- [X] Google OAuth flow completes successfully
- [X] Session persists after refresh

---

### Task 1.5: Create Auth Middleware
**Estimate**: 2 hours  
**Priority**: Critical  
**Dependencies**: Task 1.4

**Description**:
Create middleware to protect `/admin` routes and check user roles.

**Steps**:
1. Create `middleware.ts`:
   - Check authentication status
   - Check user role (admin required)
   - Redirect to login if unauthenticated
   - Redirect to home if not admin
2. Configure matcher for `/admin/*` routes
3. Test middleware with authenticated and unauthenticated users

**Acceptance Criteria**:
- [X] Middleware protects `/admin` routes
- [X] Unauthenticated users redirected to login
- [X] Non-admin users redirected to home
- [X] Admin users can access `/admin` routes
- [X] Middleware runs on all `/admin/*` routes

---

### Task 1.6: Create Layout Components
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 1.2

**Description**:
Create reusable layout components: Header, Sidebar, Footer.

**Steps**:
1. Create `components/layout/Header.tsx`:
   - Logo, navigation, user menu
   - Sign out button
2. Create `components/layout/Sidebar.tsx`:
   - Navigation links (Dashboard, Instances, Settings, Logs)
   - Active link highlighting
3. Create `components/layout/Footer.tsx`:
   - Copyright, links (Privacy, Terms)
4. Create `app/(dashboard)/layout.tsx`:
   - Use Header, Sidebar, Footer
   - Responsive layout (mobile-first)
5. Style with Tailwind CSS

**Acceptance Criteria**:
- [X] Header component created with logo, nav, user menu
- [X] Sidebar component created with navigation links
- [X] Footer component created
- [X] Dashboard layout uses all components
- [X] Layout is responsive (mobile, tablet, desktop)
- [X] Active link highlighted in sidebar

---

### Task 1.7: Set Up TanStack Query
**Estimate**: 1 hour  
**Priority**: High  
**Dependencies**: Task 1.1

**Description**:
Configure TanStack Query for server state management.

**Steps**:
1. Create `components/providers/QueryProvider.tsx`:
   - Configure QueryClient with defaults
   - Add QueryClientProvider
   - Add React Query DevTools (dev only)
2. Wrap app in QueryProvider in `app/layout.tsx`
3. Test with a sample query

**Acceptance Criteria**:
- [X] QueryProvider created
- [X] QueryClient configured with defaults (staleTime, cacheTime, retry)
- [X] React Query DevTools visible in dev mode
- [X] App wrapped in QueryProvider
- [X] Sample query works

---

## Phase 2: API Client & Types (Week 1-2)

### Task 2.1: Create API Client with Axios
**Estimate**: 3 hours  
**Priority**: Critical  
**Dependencies**: Task 1.3

**Description**:
Create a typed axios client with interceptors for authentication and error handling.

**Steps**:
1. Create `lib/api/client.ts`:
   - Create axios instance with base URL
   - Add request interceptor (add auth token)
   - Add response interceptor (handle errors)
   - Add retry logic with exponential backoff (3 retries)
2. Create `lib/api/errors.ts`:
   - Define custom error types (ApiError, NetworkError, ValidationError)
3. Test with sample request

**Acceptance Criteria**:
- [X] Axios client created with base URL
- [X] Request interceptor adds auth token
- [X] Response interceptor handles errors
- [X] Retry logic works (3 retries with exponential backoff)
- [X] Custom error types defined
- [X] Sample request works

---

### Task 2.2: Define TypeScript Types and DTOs
**Estimate**: 2 hours  
**Priority**: Critical  
**Dependencies**: None

**Description**:
Define all TypeScript interfaces for API requests and responses.

**Steps**:
1. Create `lib/api/types.ts`:
   - Define `Instance` interface
   - Define `CreateInstanceRequest`, `UpdateInstanceRequest`
   - Define `TestConnectionResponse`
   - Define `SyncStatus`, `BackfillProgress`
   - Define `PaginatedResponse<T>`
2. Export all types

**Acceptance Criteria**:
- [X] All types defined in `lib/api/types.ts`
- [X] Types match backend API schema
- [X] All fields have correct types
- [X] Optional fields marked with `?`
- [X] Types exported

---

### Task 2.3: Create Zod Validation Schemas
**Estimate**: 3 hours  
**Priority**: Critical  
**Dependencies**: Task 2.2

**Description**:
Create Zod schemas for form validation.

**Steps**:
1. Create `lib/schemas/instance.ts`:
   - Define `instanceDetailsSchema` (name, baseUrl, projectFilter)
   - Define `instanceAuthSchema` (authMethod, email, apiToken)
   - Define `createInstanceSchema` (combine details + auth)
   - Define `updateInstanceSchema`
2. Add custom validators:
   - URL validator (must be valid Jira Cloud URL)
   - Email validator
   - API token format validator
3. Add error messages for each field

**Acceptance Criteria**:
- [X] All schemas defined in `lib/schemas/instance.ts`
- [X] Custom validators implemented
- [X] Error messages defined for each field
- [X] Schemas match TypeScript types
- [X] Test schemas with valid and invalid data

---

### Task 2.4: Create API Functions for Instances
**Estimate**: 4 hours  
**Priority**: Critical  
**Dependencies**: Task 2.1, Task 2.2

**Description**:
Create typed API functions for all instance operations.

**Steps**:
1. Create `lib/api/instances.ts`:
   - `getInstances(params?)` → `PaginatedResponse<Instance>`
   - `getInstance(id)` → `Instance`
   - `createInstance(data)` → `Instance`
   - `updateInstance(id, data)` → `Instance`
   - `deleteInstance(id)` → `void`
   - `testConnection(id)` → `TestConnectionResponse`
   - `startBackfill(id)` → `{ jobId: string }`
   - `startResync(id)` → `{ jobId: string }`
   - `getSyncStatus(id)` → `SyncStatus`
2. Add JSDoc comments for each function
3. Handle errors with custom error types

**Acceptance Criteria**:
- [X] All API functions implemented
- [X] Functions use axios client
- [X] Functions return typed responses
- [X] Errors handled with custom error types
- [X] JSDoc comments added
- [X] Test with mock server

---

### Task 2.5: Create Custom Hooks for Data Fetching
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 2.4, Task 1.7

**Description**:
Create custom hooks using TanStack Query for data fetching.

**Steps**:
1. Create `lib/hooks/useInstances.ts`:
   - Use `useQuery` to fetch instances
   - Add pagination, search, filters
2. Create `lib/hooks/useInstance.ts`:
   - Use `useQuery` to fetch single instance
3. Create `lib/hooks/useCreateInstance.ts`:
   - Use `useMutation` to create instance
   - Invalidate instances query on success
4. Create `lib/hooks/useUpdateInstance.ts`:
   - Use `useMutation` to update instance
5. Create `lib/hooks/useDeleteInstance.ts`:
   - Use `useMutation` to delete instance
6. Create `lib/hooks/useTestConnection.ts`:
   - Use `useMutation` to test connection
7. Create `lib/hooks/useSyncStatus.ts`:
   - Use `useQuery` with polling (every 5 seconds)

**Acceptance Criteria**:
- [X] All hooks created
- [X] Hooks use TanStack Query
- [X] Mutations invalidate queries on success
- [X] Polling works for sync status
- [X] Hooks handle loading and error states
- [X] Test hooks with mock data

---

## Phase 3: Instances List Page (Week 2)

### Task 3.1: Create Instances List Page
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 2.5, Task 1.6

**Description**:
Create the main instances list page with loading, error, and empty states.

**Steps**:
1. Create `app/(dashboard)/admin/instances/page.tsx`:
   - Use `useInstances()` hook
   - Display loading state (skeleton)
   - Display error state (error message + retry button)
   - Display empty state (no instances message + add button)
   - Display instances table
2. Add page title and breadcrumbs
3. Add "Add Instance" button (top right)

**Acceptance Criteria**:
- [ ] Page created at `/admin/instances`
- [ ] Loading state shows skeleton
- [ ] Error state shows message + retry button
- [ ] Empty state shows message + add button
- [ ] Instances table displayed when data loaded
- [ ] "Add Instance" button navigates to `/admin/instances/new`

---

### Task 3.2: Create InstancesTable Component
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 3.1

**Description**:
Create a table component to display instances with actions.

**Steps**:
1. Create `components/instances/InstancesTable.tsx`:
   - Use shadcn/ui Table component
   - Columns: Name, Base URL, Auth Method, Status, Last Sync, Actions
   - Status badge (idle=green, syncing=blue, error=red)
   - Last sync with relative time (date-fns)
   - Actions dropdown (Edit, Delete, Test Connection)
2. Add row hover effect
3. Add responsive design (horizontal scroll on mobile)

**Acceptance Criteria**:
- [ ] Table component created
- [ ] All columns displayed correctly
- [ ] Status badge shows correct color
- [ ] Last sync shows relative time
- [ ] Actions dropdown works
- [ ] Table is responsive
- [ ] Row hover effect works

---

### Task 3.3: Add Search and Filters
**Estimate**: 3 hours  
**Priority**: Medium  
**Dependencies**: Task 3.2

**Description**:
Add search input and filter dropdowns for instances list.

**Steps**:
1. Add search input (debounced, 300ms)
2. Add status filter dropdown (All, Idle, Syncing, Error)
3. Add auth method filter dropdown (All, API Token, OAuth)
4. Implement client-side filtering
5. Update URL query params with filters

**Acceptance Criteria**:
- [ ] Search input added (debounced)
- [ ] Status filter dropdown added
- [ ] Auth method filter dropdown added
- [ ] Filtering works correctly
- [ ] URL query params updated
- [ ] Filters persist on page refresh

---

### Task 3.4: Add Pagination
**Estimate**: 2 hours  
**Priority**: Medium  
**Dependencies**: Task 3.2

**Description**:
Add pagination for instances list (20 per page).

**Steps**:
1. Add pagination component (shadcn/ui)
2. Add page navigation buttons (Previous, Next, page numbers)
3. Show total count
4. Update URL query params with page number
5. Scroll to top on page change

**Acceptance Criteria**:
- [ ] Pagination component added
- [ ] Page navigation works
- [ ] Total count displayed
- [ ] URL query params updated
- [ ] Scroll to top on page change
- [ ] Pagination persists on page refresh

---

## Phase 4: Add Instance Wizard (Week 2-3)

### Task 4.1: Create Wizard Layout and Step Indicator
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 1.6

**Description**:
Create the wizard layout with step indicator and navigation.

**Steps**:
1. Create `app/(dashboard)/admin/instances/new/page.tsx`
2. Create `components/instances/InstanceFormWizard.tsx`:
   - Step indicator (1/4, 2/4, 3/4, 4/4)
   - Step titles (Details, Auth, Validate, Save)
   - Navigation buttons (Back, Next, Cancel)
   - Progress bar
3. Manage wizard state with useState
4. Save progress to session storage

**Acceptance Criteria**:
- [ ] Wizard page created at `/admin/instances/new`
- [ ] Step indicator shows current step
- [ ] Navigation buttons work
- [ ] Progress bar updates
- [ ] State saved to session storage
- [ ] Can navigate back and forth

---

### Task 4.2: Implement Step 1 (Details)
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 4.1, Task 2.3

**Description**:
Implement the first step of the wizard (instance details).

**Steps**:
1. Create form with React Hook Form
2. Add fields: Name, Base URL, Project Filter (optional)
3. Add Zod validation with `instanceDetailsSchema`
4. Add inline error messages
5. Save to wizard state on "Next"

**Acceptance Criteria**:
- [ ] Form created with RHF
- [ ] All fields added
- [ ] Zod validation works
- [ ] Inline error messages displayed
- [ ] "Next" button disabled if invalid
- [ ] State saved on "Next"

---

### Task 4.3: Implement Step 2 (Auth)
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 4.2

**Description**:
Implement the second step of the wizard (authentication).

**Steps**:
1. Add fields: Auth Method (select), Email, API Token
2. Add password input with show/hide toggle
3. Add Zod validation with `instanceAuthSchema`
4. Add inline error messages
5. Save to wizard state on "Next"

**Acceptance Criteria**:
- [ ] Form created with RHF
- [ ] All fields added
- [ ] Auth method select works
- [ ] Password show/hide toggle works
- [ ] Zod validation works
- [ ] State saved on "Next"

---

### Task 4.4: Implement Step 3 (Validate)
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 4.3, Task 2.5

**Description**:
Implement the third step of the wizard (test connection).

**Steps**:
1. Create `components/instances/TestConnectionButton.tsx`:
   - "Test Connection" button
   - Loading spinner during test
   - Success result (user info, rate limit)
   - Error result (detailed message)
2. Use `useTestConnection()` hook
3. Display result in card
4. "Next" button enabled only if test successful

**Acceptance Criteria**:
- [ ] Test connection button created
- [ ] Loading spinner shows during test
- [ ] Success result displayed (user info, rate limit)
- [ ] Error result displayed (detailed message)
- [ ] "Next" enabled only if test successful
- [ ] Can retry test

---

### Task 4.5: Implement Step 4 (Save)
**Estimate**: 2 hours  
**Priority**: High  
**Dependencies**: Task 4.4, Task 2.5

**Description**:
Implement the fourth step of the wizard (save instance).

**Steps**:
1. Display summary of configuration
2. Add "Save" button
3. Use `useCreateInstance()` hook
4. Show loading spinner during save
5. Show success toast on success
6. Redirect to instances list on success
7. Show error message on error

**Acceptance Criteria**:
- [ ] Summary displayed
- [ ] "Save" button works
- [ ] Loading spinner shows during save
- [ ] Success toast displayed
- [ ] Redirect to instances list on success
- [ ] Error message displayed on error

---

## Phase 5: Instance Detail Page (Week 3)

### Task 5.1: Create Instance Detail Page
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 2.5

**Description**:
Create the instance detail page with tabs.

**Steps**:
1. Create `app/(dashboard)/admin/instances/[id]/page.tsx`
2. Use `useInstance(id)` hook
3. Display loading state (skeleton)
4. Display error state (404 message)
5. Add tabs: Overview, Sync, History, Settings
6. Add breadcrumbs

**Acceptance Criteria**:
- [ ] Page created at `/admin/instances/[id]`
- [ ] Loading state shows skeleton
- [ ] Error state shows 404 message
- [ ] Tabs work correctly
- [ ] Breadcrumbs show correct path
- [ ] Active tab highlighted

---

### Task 5.2: Implement Overview Tab
**Estimate**: 2 hours  
**Priority**: High  
**Dependencies**: Task 5.1

**Description**:
Display instance configuration in read-only format.

**Steps**:
1. Display all fields in card
2. Mask API token (show "••••••••")
3. Add "Edit" button (navigates to edit page)
4. Add "Delete" button (shows confirmation dialog)
5. Style with Tailwind CSS

**Acceptance Criteria**:
- [ ] All fields displayed
- [ ] API token masked
- [ ] "Edit" button navigates to edit page
- [ ] "Delete" button shows confirmation dialog
- [ ] Card styled correctly

---

### Task 5.3: Implement Sync Tab
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 5.1, Task 2.5

**Description**:
Display sync status and actions.

**Steps**:
1. Create `components/instances/SyncStatusCard.tsx`:
   - Display sync status (idle, syncing, error)
   - Display watermark (last updated issue timestamp)
   - Display sync statistics (issues, projects, users)
   - Add "Backfill" button
   - Add "Resync" button
2. Use `useSyncStatus(id)` hook with polling
3. Disable buttons if sync is running

**Acceptance Criteria**:
- [ ] Sync status card created
- [ ] Status displayed correctly
- [ ] Watermark displayed
- [ ] Statistics displayed
- [ ] "Backfill" button works
- [ ] "Resync" button works
- [ ] Buttons disabled if sync running
- [ ] Polling works (every 5 seconds)

---

### Task 5.4: Implement History Tab
**Estimate**: 2 hours  
**Priority**: Medium  
**Dependencies**: Task 5.1

**Description**:
Display sync history table.

**Steps**:
1. Create sync history table
2. Columns: Started At, Completed At, Duration, Status, Issues Synced
3. Add pagination (10 per page)
4. Add relative time for timestamps

**Acceptance Criteria**:
- [ ] History table created
- [ ] All columns displayed
- [ ] Pagination works
- [ ] Relative time displayed
- [ ] Empty state if no history

---

## Phase 6: Backfill & Sync (Week 3-4)

### Task 6.1: Create Backfill Confirmation Dialog
**Estimate**: 2 hours  
**Priority**: High  
**Dependencies**: Task 5.3

**Description**:
Create a confirmation dialog for starting backfill.

**Steps**:
1. Create `components/instances/BackfillConfirmDialog.tsx`:
   - Warning message (can take hours)
   - "Start" and "Cancel" buttons
2. Use shadcn/ui Dialog component
3. Trigger from "Backfill" button in Sync tab

**Acceptance Criteria**:
- [ ] Dialog created
- [ ] Warning message displayed
- [ ] "Start" button triggers backfill
- [ ] "Cancel" button closes dialog
- [ ] Dialog styled correctly

---

### Task 6.2: Create Backfill Progress Modal
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 6.1, Task 2.5

**Description**:
Display backfill progress with real-time updates.

**Steps**:
1. Create `components/instances/BackfillProgressModal.tsx`:
   - Progress bar (percentage)
   - ETA (estimated time remaining)
   - Detailed progress (projects, issues, comments)
   - "Cancel" button
2. Use `useSyncStatus(id)` hook with polling
3. Update progress every 5 seconds
4. Close modal on completion

**Acceptance Criteria**:
- [ ] Progress modal created
- [ ] Progress bar updates
- [ ] ETA displayed
- [ ] Detailed progress displayed
- [ ] "Cancel" button works
- [ ] Polling works (every 5 seconds)
- [ ] Modal closes on completion
- [ ] Success toast on completion

---

### Task 6.3: Implement Resync
**Estimate**: 2 hours  
**Priority**: Medium  
**Dependencies**: Task 6.2

**Description**:
Implement incremental resync (similar to backfill but faster).

**Steps**:
1. Reuse BackfillProgressModal
2. Call `startResync()` API
3. Display progress
4. Update watermark on completion

**Acceptance Criteria**:
- [ ] Resync button works
- [ ] Progress modal displayed
- [ ] Progress updates
- [ ] Watermark updated on completion
- [ ] Success toast on completion

---

## Phase 7: Edit & Delete (Week 4)

### Task 7.1: Create Edit Page
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 4.5

**Description**:
Create edit page for updating instance configuration.

**Steps**:
1. Create `app/(dashboard)/admin/instances/[id]/edit/page.tsx`
2. Reuse InstanceFormWizard component
3. Pre-fill form with current values
4. Mask API token (show "••••••••", optional update)
5. Add "Save" button
6. Use `useUpdateInstance()` hook

**Acceptance Criteria**:
- [ ] Edit page created at `/admin/instances/[id]/edit`
- [ ] Form pre-filled with current values
- [ ] API token masked
- [ ] "Save" button works
- [ ] Success toast on save
- [ ] Redirect to detail page on save

---

### Task 7.2: Implement Delete with Confirmation
**Estimate**: 2 hours  
**Priority**: High  
**Dependencies**: Task 5.2

**Description**:
Implement delete functionality with confirmation dialog.

**Steps**:
1. Create confirmation dialog
2. Require typing instance name to confirm
3. Use `useDeleteInstance()` hook
4. Show success toast
5. Redirect to instances list

**Acceptance Criteria**:
- [ ] Confirmation dialog created
- [ ] Requires typing instance name
- [ ] "Delete" button works
- [ ] Success toast displayed
- [ ] Redirect to instances list
- [ ] Error message if delete fails

---

## Phase 8: Testing (Week 4-5)

### Task 8.1: Write Unit Tests
**Estimate**: 6 hours  
**Priority**: High  
**Dependencies**: All previous tasks

**Description**:
Write unit tests for API client, schemas, and utilities.

**Steps**:
1. Test API client functions (mock axios)
2. Test Zod schemas (valid and invalid data)
3. Test utility functions (formatDate, cn, etc.)
4. Test custom hooks (mock TanStack Query)
5. Target: 80%+ coverage

**Acceptance Criteria**:
- [ ] API client tests written
- [ ] Schema tests written
- [ ] Utility tests written
- [ ] Hook tests written
- [ ] All tests passing
- [ ] Coverage >80%

---

### Task 8.2: Write Component Tests
**Estimate**: 6 hours  
**Priority**: High  
**Dependencies**: All previous tasks

**Description**:
Write component tests with React Testing Library.

**Steps**:
1. Test InstancesTable rendering
2. Test InstanceFormWizard steps
3. Test TestConnectionButton states
4. Test SyncStatusCard display
5. Mock TanStack Query with QueryClientProvider
6. Test user interactions (click, type, submit)

**Acceptance Criteria**:
- [ ] InstancesTable tests written
- [ ] InstanceFormWizard tests written
- [ ] TestConnectionButton tests written
- [ ] SyncStatusCard tests written
- [ ] All tests passing
- [ ] User interactions tested

---

### Task 8.3: Write E2E Tests
**Estimate**: 8 hours  
**Priority**: Medium  
**Dependencies**: All previous tasks

**Description**:
Write E2E tests with Playwright.

**Steps**:
1. Test full flow: Login → Add instance → Test → Save → Backfill
2. Test edit flow: Edit instance → Update → Save
3. Test delete flow: Delete instance → Confirm
4. Test error scenarios (network error, validation error)
5. Run against local dev server

**Acceptance Criteria**:
- [ ] Add instance flow tested
- [ ] Edit flow tested
- [ ] Delete flow tested
- [ ] Error scenarios tested
- [ ] All tests passing
- [ ] Tests run in CI/CD

---

## Summary

**Total Tasks**: 40+  
**Total Estimate**: ~100 hours (~2.5 weeks for 1 developer)  
**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8

**Key Milestones**:
- Week 1: Project setup, authentication, API client
- Week 2: Instances list, add wizard
- Week 3: Instance detail, sync management
- Week 4: Edit/delete, testing
- Week 5: Backend API, MCP tools, deployment

**Success Criteria**:
- All user stories implemented
- All acceptance criteria met
- Test coverage >80%
- Lighthouse score >90
- WCAG 2.1 AA compliant

