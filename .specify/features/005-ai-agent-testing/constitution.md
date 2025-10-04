# AI Agent Testing & Debugging Support - Project Constitution

## Core Principles

### 1. Testing Philosophy
- **AI-First Testing**: Every element discoverable and testable by AI agents
- **Spec-Driven Tests**: Tests generated from specifications, not written manually
- **Self-Healing Tests**: Tests adapt to minor UI changes automatically
- **Debugging-First Design**: Components expose state for easy debugging
- **User Behavior Testing**: Test what users see, not implementation details

### 2. Technology Stack

#### Testing Frameworks
- **Playwright**: E2E testing with multi-browser support (Chromium, Firefox, WebKit)
- **Vitest**: Fast unit testing with hot reload and TypeScript support
- **React Testing Library**: Component testing with user-centric queries
- **MSW (Mock Service Worker)**: API mocking for integration tests
- **axe-core**: Accessibility testing (WCAG 2.1 Level AA)

#### Frontend Stack
- **Next.js 15**: App Router, Server Components, TypeScript
- **React 19**: Latest features, concurrent rendering
- **TanStack Query**: Data fetching, caching, optimistic updates
- **shadcn/ui**: Accessible component library
- **Tailwind CSS**: Utility-first styling

#### CI/CD
- **GitHub Actions**: Automated testing on push/PR
- **Playwright Test Reporter**: HTML reports with screenshots
- **Vitest Coverage**: Istanbul coverage reports
- **Visual Regression**: Screenshot comparison

### 3. Code Quality Standards

#### TypeScript
- Type safety mandatory (strict mode enabled)
- No `any` types without explicit justification
- Interfaces for all component props
- Type guards for runtime validation

#### Testing Standards
- **Unit Tests**: 80%+ coverage for hooks and utilities
- **Integration Tests**: 100% of API endpoints
- **E2E Tests**: 100% of critical user paths
- **Visual Tests**: All major components
- **Accessibility Tests**: Zero critical violations

#### Test Structure
- **AAA Pattern**: Arrange, Act, Assert
- **Independent Tests**: No shared state between tests
- **Descriptive Names**: Clear test intent
- **No Hard-Coded Waits**: Use explicit waits only

### 4. Test ID System

#### Naming Convention
- **Format**: `[component]-[element]-[action?]`
- **Examples**:
  - `instances-table`
  - `instance-row-{id}`
  - `add-instance-button`
  - `wizard-step-2-next`
  - `form-field-name`
  - `form-error-email`

#### Coverage Requirements
- **100% Interactive Elements**: Every button, link, input, select
- **All Forms**: Every field, error message, submit button
- **All Dialogs**: Container, title, confirm, cancel buttons
- **All Tables**: Table, rows, columns, action buttons
- **All Navigation**: Header, sidebar, footer links

#### Implementation Rules
- Test IDs must be unique within a page
- Test IDs must be stable (not change with content)
- Test IDs must be descriptive (not generic like "button-1")
- Test IDs must follow kebab-case convention

### 5. State Attributes

#### data-state
- **Purpose**: Expose component loading state
- **Values**: `loading | success | error | idle`
- **Usage**: Tables, forms, buttons, API calls
- **Example**: `<div data-testid="table" data-state="loading">`

#### data-status
- **Purpose**: Expose instance sync status
- **Values**: `idle | syncing | error`
- **Usage**: Instance rows, status badges
- **Example**: `<div data-testid="instance-row-1" data-status="syncing">`

#### data-step
- **Purpose**: Expose wizard current step
- **Values**: `1 | 2 | 3 | 4`
- **Usage**: Wizard container, step indicators
- **Example**: `<div data-testid="wizard" data-step="2">`

#### data-open
- **Purpose**: Expose dialog visibility
- **Values**: `true | false`
- **Usage**: Dialogs, dropdowns, modals
- **Example**: `<div data-testid="dialog" data-open="true">`

### 6. Semantic HTML & Accessibility

#### Semantic Elements
- Use `<nav>` for navigation (not `<div>`)
- Use `<form>` for forms (not `<div>`)
- Use `<button>` for buttons (not `<div>` with onClick)
- Use `<table>`, `<thead>`, `<tbody>` for tables
- Use `<header>`, `<footer>`, `<main>` for layout

#### ARIA Attributes
- **aria-label**: Descriptive labels for all interactive elements
- **aria-labelledby**: Link labels to form fields
- **aria-describedby**: Link descriptions to form fields
- **aria-invalid**: Mark invalid form fields
- **role**: Explicit roles for custom components

#### Keyboard Accessibility
- All interactive elements must be keyboard accessible
- Tab order must be logical
- Focus indicators must be visible
- Escape key closes dialogs/modals

### 7. Test Utilities

#### Selectors (e2e/utils/selectors.ts)
- **Centralized**: All selectors in one file
- **Typed**: TypeScript interfaces for type safety
- **Organized**: Grouped by component/feature
- **Dynamic**: Functions for parameterized selectors
- **200+ Selectors**: Cover all UI elements

#### Helpers (e2e/utils/helpers.ts)
- **Reusable**: Common test operations
- **Async**: All helpers are async
- **Error Handling**: Graceful failures with retries
- **30+ Helpers**: Wait, fill, verify, navigate, etc.

#### Fixtures (e2e/fixtures/)
- **Auth**: Mock authentication (Google OAuth, sessions)
- **Data**: Mock API responses (instances, sync history)
- **Reusable**: Setup functions for common scenarios
- **Isolated**: Each test gets fresh fixtures

### 8. Self-Healing Tests

#### Multiple Selector Strategies
1. **Primary**: Test ID (`[data-testid="button"]`)
2. **Fallback 1**: Semantic query (`button:has-text("Add")`)
3. **Fallback 2**: ARIA label (`[aria-label="Add instance"]`)
4. **Fallback 3**: Role + name (`role=button[name="Add"]`)

#### Retry Logic
- **Exponential Backoff**: 1s, 2s, 4s delays
- **Max Retries**: 3 attempts
- **Timeout**: 30s default, configurable
- **Graceful Degradation**: Try all strategies before failing

#### Flexible Assertions
- **Partial Matches**: `toContainText` instead of `toHaveText`
- **Visibility Checks**: `toBeVisible` instead of `toExist`
- **Count Ranges**: `toHaveCount(3)` or `toHaveCount({ min: 1 })`

### 9. Performance

#### Test Execution
- **Parallel Execution**: Run tests in parallel (4 workers)
- **Test Isolation**: Each test in fresh browser context
- **Fast Feedback**: Unit tests <5s, E2E tests <5min
- **Selective Running**: Run only affected tests

#### Resource Management
- **Browser Reuse**: Reuse browser instances
- **Context Cleanup**: Close contexts after tests
- **Memory Limits**: Monitor memory usage
- **Timeout Limits**: 30s per test, 5min per suite

### 10. Debugging Tools

#### Error Boundaries
- **React Error Boundaries**: Catch component crashes
- **Fallback UI**: User-friendly error messages
- **Error Logging**: Log errors to console/service
- **Reset Functionality**: Allow users to recover

#### Logging
- **Structured Logging**: JSON format with context
- **Log Levels**: DEBUG, INFO, WARN, ERROR
- **Context**: User ID, tenant ID, component name
- **Dev vs Prod**: Verbose in dev, minimal in prod

#### DevTools Integration
- **React DevTools**: Component inspection
- **Chrome DevTools Protocol**: Advanced debugging
- **Performance Monitoring**: Measure render times
- **Network Inspection**: Monitor API calls

### 11. CI/CD Integration

#### GitHub Actions Workflow
- **On Push**: Run unit tests, linting
- **On PR**: Run all tests (unit, integration, E2E, visual, a11y)
- **On Merge**: Run smoke tests
- **Nightly**: Run full test suite with load tests

#### Test Reports
- **HTML Reports**: Playwright test results with screenshots
- **Coverage Reports**: Istanbul coverage with thresholds
- **Visual Diffs**: Screenshot comparisons
- **Accessibility Reports**: axe-core violations

#### Quality Gates
- **80%+ Unit Coverage**: Fail if below threshold
- **100% E2E Critical Paths**: All critical flows tested
- **Zero Critical A11y Violations**: WCAG Level AA compliance
- **<1% Flaky Tests**: Retry flaky tests, fail if persistent

---

## Non-Negotiables

### Must Have
1. ✅ Every interactive element has a test ID
2. ✅ All components expose state via data attributes
3. ✅ All tests use centralized selectors
4. ✅ All tests are independent (no shared state)
5. ✅ All tests have descriptive names
6. ✅ No hard-coded waits (use explicit waits)
7. ✅ All forms have proper labels and ARIA attributes
8. ✅ All tests pass in CI before merge

### Must Not Have
1. ❌ No test IDs in production code (use data-testid)
2. ❌ No implementation detail testing (test user behavior)
3. ❌ No shared state between tests
4. ❌ No hard-coded waits (page.waitForTimeout)
5. ❌ No generic test IDs (button-1, div-2)
6. ❌ No skipped tests without justification
7. ❌ No tests that depend on external services
8. ❌ No tests that modify production data

---

## Success Criteria

### Coverage
- ✅ 100% of interactive elements have test IDs
- ✅ 80%+ unit test coverage
- ✅ 100% of API endpoints have integration tests
- ✅ 100% of critical user paths have E2E tests
- ✅ Zero critical accessibility violations

### Performance
- ✅ Unit tests complete in <5 seconds
- ✅ E2E tests complete in <5 minutes
- ✅ Flaky test rate <1%
- ✅ Test execution time stable over time

### Quality
- ✅ All tests pass in CI
- ✅ AI agents can discover 100% of elements
- ✅ AI agents can debug 80%+ of common issues
- ✅ Self-healing tests reduce maintenance by 50%
- ✅ Zero false positives in test failures

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Owner**: Digital Spiral Team

