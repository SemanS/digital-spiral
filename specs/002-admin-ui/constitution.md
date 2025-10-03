# Admin UI - Project Constitution

## Core Principles

### 1. Frontend Architecture
- **Next.js 15 App Router**: Modern React framework with server components
- **TypeScript**: Type-safe development with strict mode
- **Component-driven**: Reusable, testable components
- **API-first**: All data fetching through typed API clients
- **Progressive enhancement**: Works without JavaScript where possible

### 2. Technology Stack

#### Frontend Core
- **Next.js 15**: App Router, Server Components, Server Actions
- **TypeScript 5.3+**: Strict mode, no implicit any
- **React 18+**: Hooks, Suspense, Error Boundaries
- **Tailwind CSS 3.4+**: Utility-first styling
- **shadcn/ui**: High-quality component library

#### Forms & Validation
- **React Hook Form 7.x**: Performant form management
- **Zod 3.x**: Schema validation
- **@hookform/resolvers**: RHF + Zod integration

#### Data Fetching
- **TanStack Query v5**: Server state management
- **axios**: HTTP client with interceptors
- **SWR**: Alternative for real-time data

#### Authentication
- **NextAuth v5**: Authentication for Next.js
- **Google OAuth 2.0**: Primary authentication provider
- **JWT**: Session management
- **Role-based access**: Admin, Editor, Viewer roles

### 3. Code Quality Standards

#### TypeScript
- Strict mode enabled
- No `any` types without explicit justification
- All props interfaces exported
- Discriminated unions for variants

#### React Components
- Functional components only
- Custom hooks for logic reuse
- Proper error boundaries
- Loading states for async operations
- Optimistic updates where appropriate

#### Styling
- Tailwind utility classes
- CSS modules for complex components
- Design tokens from shadcn/ui
- Responsive design (mobile-first)
- Dark mode support

#### Testing
- **Vitest**: Unit tests for utilities and hooks
- **React Testing Library**: Component tests
- **Playwright**: E2E tests
- **MSW**: API mocking
- Target: 80%+ coverage for business logic

### 4. Security

#### Authentication & Authorization
- Google OAuth 2.0 with NextAuth v5
- JWT tokens with secure httpOnly cookies
- CSRF protection enabled
- Role-based access control (RBAC)
- Session timeout: 24 hours

#### Data Protection
- API tokens encrypted before storage
- Secrets never in client-side code
- Environment variables for sensitive data
- Content Security Policy (CSP) headers
- HTTPS only in production

#### Input Validation
- Zod schemas for all forms
- Server-side validation (double validation)
- SQL injection prevention (parameterized queries)
- XSS prevention (React auto-escaping)

### 5. API Integration

#### Backend Communication
- RESTful API endpoints (FastAPI)
- Typed API client with axios
- Request/response DTOs with Zod
- Error handling with custom error types
- Retry logic with exponential backoff

#### MCP Integration
- MCP tools called via backend proxy
- Tools: `jira:test_connection`, `jira:add_instance`, `jira:start_backfill`
- Real-time status updates via polling or SSE
- Error messages displayed to user

### 6. User Experience

#### Design Principles
- **Clarity**: Clear labels, helpful error messages
- **Feedback**: Loading states, success/error toasts
- **Efficiency**: Keyboard shortcuts, autosave
- **Consistency**: Uniform patterns across UI
- **Accessibility**: WCAG 2.1 AA compliance

#### Forms
- Multi-step wizard for complex flows
- Inline validation with debounce
- Clear error messages
- Autosave drafts
- Confirmation dialogs for destructive actions

#### Performance
- Code splitting per route
- Image optimization (Next.js Image)
- Lazy loading for heavy components
- Debounced search inputs
- Optimistic UI updates

### 7. Observability

#### Logging
- Client-side errors sent to backend
- Structured logs with context (userId, tenantId, instanceId)
- Log levels: DEBUG, INFO, WARN, ERROR
- No sensitive data in logs

#### Metrics
- Page load times
- API response times
- Error rates
- User actions (button clicks, form submissions)

#### Monitoring
- Sentry for error tracking
- Vercel Analytics for performance
- Custom events for business metrics

### 8. Development Workflow

#### Version Control
- Git with feature branches
- Conventional commits
- Pull request reviews required
- CI/CD pipeline validation

#### Code Style
- ESLint with strict rules
- Prettier for formatting
- Husky for pre-commit hooks
- Lint-staged for staged files

#### Documentation
- JSDoc for complex functions
- README per feature
- Storybook for component library
- API documentation with OpenAPI

### 9. Deployment

#### Environments
- **Development**: Local with hot reload
- **Staging**: Vercel preview deployments
- **Production**: Vercel production

#### Build Process
- TypeScript compilation
- Tailwind CSS purging
- Image optimization
- Bundle analysis
- Environment variable validation

#### Monitoring
- Health checks
- Error tracking (Sentry)
- Performance monitoring (Vercel)
- Uptime monitoring

### 10. Jira Instance Management Specifics

#### Instance Configuration
- Name (display name)
- Base URL (Jira Cloud URL)
- Auth method (API token or OAuth)
- Email/Account ID
- API token (encrypted)
- Project filter (optional JQL)

#### Test Connection
- Validate credentials
- Check API access
- Fetch user info
- Display rate limit headers
- Show detailed error messages

#### Sync Management
- Display sync status (idle, running, error)
- Show last sync timestamp
- Show watermark (last updated issue)
- Buttons: Backfill, Resync, Pause
- Progress indicator for long-running jobs

## Non-Negotiables

1. **TypeScript strict mode** - No exceptions
2. **All forms validated with Zod** - Client and server
3. **No secrets in client code** - Environment variables only
4. **Authentication required** - No public access to admin UI
5. **Role-based access** - Admin role required for write operations
6. **Error boundaries** - All async operations wrapped
7. **Loading states** - All async operations show loading
8. **Optimistic updates** - Where appropriate
9. **Tests required** - No PR without tests
10. **Accessibility** - WCAG 2.1 AA compliance

## Success Metrics

- **Performance**: First Contentful Paint < 1.5s
- **Accessibility**: Lighthouse score > 90
- **Test Coverage**: >80% for business logic
- **Error Rate**: <0.1% of requests
- **User Satisfaction**: Positive feedback from admins

## References

- [Next.js 15 Documentation](https://nextjs.org/docs)
- [NextAuth v5 Documentation](https://authjs.dev/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod Documentation](https://zod.dev/)
- [TanStack Query](https://tanstack.com/query/latest)

