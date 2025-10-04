# Auggie Implementation Guide: AI Agent Testing & Debugging Support

## 🎯 Overview

This guide helps Auggie (AI Assistant) implement **Feature 005: AI Agent Testing & Debugging Support** using the Spec-Driven Development methodology.

**Feature**: AI Agent Testing & Debugging Support  
**Timeline**: 5 weeks  
**Methodology**: GitHub Spec-Kit

---

## 📚 Required Reading (Before Starting)

### 1. Constitution (10 min)
Read `.specify/features/005-ai-agent-testing/constitution.md` to understand:
- Testing philosophy (AI-First, Spec-Driven, Self-Healing)
- Tech stack (Playwright, Vitest, React Testing Library, MSW, axe-core)
- Test ID system (naming convention, coverage requirements)
- State attributes (data-state, data-status, data-step, data-open)
- Semantic HTML & accessibility standards

### 2. Specification (10 min)
Read `.specify/features/005-ai-agent-testing/spec.md` to understand:
- User stories (15 total)
- Functional requirements
- Test coverage goals
- Success metrics

### 3. Implementation Plan (10 min)
Read `.specify/features/005-ai-agent-testing/plan.md` to understand:
- 5 implementation phases
- Architecture diagram
- File structure
- Testing strategy

### 4. Tasks (5 min)
Read `.specify/features/005-ai-agent-testing/tasks.md` to understand:
- Task breakdown (30+ tasks)
- Acceptance criteria
- Dependencies
- Estimated effort

---

## 🚀 Quick Start Command

To implement the entire feature, use:

```
/implement
```

This will:
1. Validate prerequisites (constitution, spec, plan, tasks)
2. Parse task breakdown from tasks.md
3. Execute tasks in order, respecting dependencies
4. Follow TDD approach
5. Provide progress updates

---

## 📋 Implementation Workflow

### Phase 1: Foundation (Week 1)

#### Task 1.1: Add Test IDs to Layout Components

```
Auggie, implement Task 1.1: Add Test IDs to Layout Components

Requirements:
- Modify admin-ui/src/components/layout/Header.tsx
- Modify admin-ui/src/components/layout/Sidebar.tsx
- Modify admin-ui/src/components/layout/Footer.tsx
- Add data-testid to all interactive elements
- Add ARIA labels to all links
- Use semantic <nav> element

Acceptance Criteria:
- [ ] Header has data-testid="app-header"
- [ ] Logo link has data-testid="header-logo"
- [ ] Navigation has data-testid="header-nav"
- [ ] All nav links have test IDs (header-nav-instances, header-nav-settings, etc.)
- [ ] User menu has data-testid="header-user-menu"
- [ ] All elements have ARIA labels
- [ ] Navigation uses <nav role="navigation">

Example:
<header data-testid="app-header">
  <Link href="/admin" data-testid="header-logo" aria-label="Go to home">
    <span>Admin UI</span>
  </Link>
  <nav data-testid="header-nav" role="navigation" aria-label="Main navigation">
    <Link href="/admin/instances" data-testid="header-nav-instances">
      Instances
    </Link>
  </nav>
</header>

Follow constitution.md standards:
- Test ID format: [component]-[element]-[action?]
- All interactive elements must have test IDs
- Use semantic HTML
- Add ARIA labels
```

#### Task 1.2: Add Test IDs to Instance Components

```
Auggie, implement Task 1.2: Add Test IDs to Instance Components

Requirements:
- Modify admin-ui/src/components/instances/InstancesTable.tsx
- Modify admin-ui/src/components/instances/InstanceFormWizard.tsx
- Modify all wizard step components
- Add data-testid to all interactive elements
- Add data-state attribute for loading states
- Add data-status attribute for instance status
- Add data-step attribute for wizard steps

Acceptance Criteria:
- [ ] InstancesTable has data-testid="instances-table"
- [ ] InstancesTable has data-state attribute (loading/success/error)
- [ ] Each instance row has data-testid="instance-row-{id}"
- [ ] Each instance row has data-status attribute (idle/syncing/error)
- [ ] InstanceFormWizard has data-testid="instance-wizard"
- [ ] InstanceFormWizard has data-step attribute (1-4)
- [ ] All wizard steps have test IDs (wizard-step-1, wizard-step-2, etc.)
- [ ] All form fields have test IDs (instance-name-input, instance-url-input, etc.)
- [ ] All buttons have test IDs (wizard-next-button, wizard-back-button, etc.)

Example:
<div 
  data-testid="instances-table"
  data-state={isLoading ? 'loading' : 'success'}
>
  <table>
    <tbody>
      {instances.map(instance => (
        <tr 
          key={instance.id}
          data-testid={`instance-row-${instance.id}`}
          data-status={instance.status}
        >
          <td>{instance.name}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>

Follow constitution.md standards:
- Test IDs must be unique
- State attributes must expose component state
- Use semantic HTML
```

#### Task 1.3: Add Test IDs to UI Components

```
Auggie, implement Task 1.3: Add Test IDs to UI Components

Requirements:
- Modify admin-ui/src/components/ui/button.tsx
- Modify admin-ui/src/components/ui/input.tsx
- Modify admin-ui/src/components/ui/dialog.tsx
- Modify admin-ui/src/components/ui/select.tsx
- Modify admin-ui/src/components/ui/form.tsx
- Add testId prop to all components
- Apply testId to root element

Acceptance Criteria:
- [ ] Button component accepts testId prop
- [ ] Input component accepts testId prop
- [ ] Dialog component accepts testId prop
- [ ] Select component accepts testId prop
- [ ] Form components accept testId prop
- [ ] All components apply testId to root element
- [ ] TypeScript types updated

Example:
// button.tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  testId?: string;
}

export function Button({ testId, children, ...props }: ButtonProps) {
  return (
    <button data-testid={testId} {...props}>
      {children}
    </button>
  );
}

// Usage
<Button testId="add-instance-button" onClick={handleAdd}>
  Add Instance
</Button>

Follow constitution.md standards:
- TypeScript types mandatory
- testId prop optional
- Apply to root element
```

---

### Phase 2: Testing Infrastructure (Week 2)

#### Task 2.1: Configure Playwright

```
Auggie, implement Task 2.1: Configure Playwright

Requirements:
- Create admin-ui/playwright.config.ts
- Configure multiple browsers (Chromium, Firefox, WebKit)
- Set base URL to http://localhost:3000
- Enable screenshots on failure
- Enable trace on retry
- Configure test directory structure

Acceptance Criteria:
- [ ] playwright.config.ts created
- [ ] Multiple browsers configured
- [ ] Base URL configured
- [ ] Screenshots on failure enabled
- [ ] Trace on retry enabled
- [ ] Test directory structure created (e2e/specs, e2e/fixtures, e2e/utils)

Example:
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});

Follow constitution.md standards:
- Multiple browsers for cross-browser testing
- Screenshots and traces for debugging
```

#### Task 2.2: Create Test Utilities

```
Auggie, implement Task 2.2: Create Test Utilities

Note: Selectors and helpers already created ✅
- admin-ui/e2e/utils/selectors.ts ✅
- admin-ui/e2e/utils/helpers.ts ✅

Requirements:
- Create admin-ui/e2e/utils/assertions.ts
- Add custom matchers for common assertions
- Add TypeScript types
- Add JSDoc comments

Acceptance Criteria:
- [ ] assertions.ts created
- [ ] Custom matchers implemented
- [ ] TypeScript types added
- [ ] JSDoc comments added

Follow constitution.md standards:
- Reusable utilities
- Type safety
- Clear documentation
```

#### Task 2.3: Create Fixtures

```
Auggie, implement Task 2.3: Create Fixtures

Note: Auth and instance fixtures already created ✅
- admin-ui/e2e/fixtures/auth.ts ✅
- admin-ui/e2e/fixtures/instances.ts ✅

Requirements:
- Create admin-ui/e2e/fixtures/sync.ts
- Add backfill fixtures
- Add progress fixtures
- Add TypeScript types

Acceptance Criteria:
- [ ] sync.ts created
- [ ] Backfill fixtures implemented
- [ ] Progress fixtures implemented
- [ ] TypeScript types added

Follow constitution.md standards:
- Reusable fixtures
- Type safety
- Mock API responses
```

#### Task 2.4: Write E2E Tests for Authentication

```
Auggie, implement Task 2.4: Write E2E Tests for Authentication

Requirements:
- Create admin-ui/e2e/specs/auth.spec.ts
- Test successful Google OAuth login
- Test protected route redirect
- Test logout functionality
- Test session persistence

Acceptance Criteria:
- [ ] auth.spec.ts created
- [ ] Test successful login
- [ ] Test protected route redirect
- [ ] Test logout
- [ ] Test session persistence
- [ ] All tests pass

Example:
import { test, expect } from '@playwright/test';
import { selectors } from '../utils/selectors';
import { mockGoogleOAuth } from '../fixtures/auth';

test('user can log in with Google', async ({ page }) => {
  await mockGoogleOAuth(page);
  await page.goto('/auth/signin');
  
  await page.click(selectors.auth.signInButton);
  
  await page.waitForURL('/admin/instances');
  await expect(page.locator(selectors.layout.header)).toBeVisible();
});

Follow constitution.md standards:
- AAA pattern (Arrange, Act, Assert)
- Use centralized selectors
- Descriptive test names
- No hard-coded waits
```

---

### Phase 3: AI Agent Integration (Week 3)

#### Task 3.1: Create Test Generation Script

```
Auggie, implement Task 3.1: Create Test Generation Script

Requirements:
- Create admin-ui/scripts/generate-tests.ts
- Parse spec.md for user stories
- Extract acceptance criteria
- Generate Playwright tests
- Generate Vitest tests

Acceptance Criteria:
- [ ] generate-tests.ts created
- [ ] Parses spec.md correctly
- [ ] Extracts user stories
- [ ] Generates Playwright tests
- [ ] Generated tests follow conventions

Follow constitution.md standards:
- TypeScript with type safety
- Follow test naming conventions
- Use centralized selectors
```

---

### Phase 4: Debugging Tools (Week 4)

#### Task 4.1: Implement Error Boundary

```
Auggie, implement Task 4.1: Implement Error Boundary

Requirements:
- Create admin-ui/src/components/ErrorBoundary.tsx
- Implement error logging
- Create fallback UI
- Add reset functionality

Acceptance Criteria:
- [ ] ErrorBoundary.tsx created
- [ ] Catches component errors
- [ ] Logs errors to console
- [ ] Shows fallback UI
- [ ] Provides reset button

Example:
export class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div data-testid="error-boundary">
          <h2>Something went wrong</h2>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

Follow constitution.md standards:
- Error logging
- User-friendly fallback UI
- Reset functionality
```

---

### Phase 5: Documentation & Refinement (Week 5)

#### Task 5.1: Create Test ID Reference

```
Auggie, implement Task 5.1: Create Test ID Reference

Requirements:
- Create admin-ui/docs/testing/test-ids.md
- Document all test IDs
- Organize by component
- Add usage examples

Acceptance Criteria:
- [ ] test-ids.md created
- [ ] All test IDs documented
- [ ] Organized by component
- [ ] Usage examples provided

Follow constitution.md standards:
- Complete documentation
- Clear organization
- Practical examples
```

---

## 🎯 Success Criteria

After completing all tasks, verify:

### Coverage
- ✅ 100% of interactive elements have test IDs
- ✅ 80%+ unit test coverage
- ✅ 100% of critical paths have E2E tests

### Performance
- ✅ Unit tests complete in <5 seconds
- ✅ E2E tests complete in <5 minutes
- ✅ Flaky test rate <1%

### Quality
- ✅ All tests pass in CI
- ✅ AI agents can discover 100% of elements
- ✅ Zero critical accessibility violations

---

## 📞 Support

For questions or issues:
1. Check constitution.md for standards
2. Check spec.md for requirements
3. Check plan.md for architecture
4. Check tasks.md for detailed tasks

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Owner**: Digital Spiral Team

