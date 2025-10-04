# Feature 005: AI Agent Testing & Debugging Support

## 🎯 Overview

Comprehensive testing infrastructure that enables AI agents to simulate user interactions, debug UI issues, and validate all functionality through automated testing. The system provides test IDs, state attributes, semantic HTML, and debugging tools for Next.js Admin UI application.

**Status**: 📋 Specification Phase  
**Timeline**: 5 weeks  
**Team**: Frontend (2), QA (1)

---

## 📚 Documentation

### Core Documents
1. **[constitution.md](constitution.md)** - Testing principles, standards, conventions
2. **[spec.md](spec.md)** - Requirements, user stories, technical specs
3. **[plan.md](plan.md)** - Implementation plan, phases, architecture
4. **[tasks.md](tasks.md)** - Detailed tasks with acceptance criteria
5. **[AUGGIE_GUIDE.md](AUGGIE_GUIDE.md)** - Guide for AI assistant implementation

### Quick Links
- [GitHub Spec Kit](https://github.com/github/spec-kit) - Methodology
- [SPEC_KIT_MASTER_GUIDE.md](../../SPEC_KIT_MASTER_GUIDE.md) - How to use Spec-Kit
- [Playwright Documentation](https://playwright.dev/) - E2E testing framework
- [Vitest Documentation](https://vitest.dev/) - Unit testing framework

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Playwright browsers

### Setup

```bash
# 1. Install dependencies
cd admin-ui
npm install

# 2. Install Playwright browsers
npx playwright install

# 3. Run unit tests
npm run test

# 4. Run E2E tests
npm run test:e2e

# 5. Run E2E tests with UI
npm run test:e2e:ui

# 6. Run tests with coverage
npm run test:coverage
```

### Example Test

```typescript
import { test, expect } from '@playwright/test';
import { selectors } from '../utils/selectors';
import { loginAsAdmin } from '../fixtures/auth';

test('user can view instances list', async ({ page }) => {
  // Setup
  await loginAsAdmin(page);
  await page.goto('/admin/instances');
  
  // Verify table is visible
  await expect(page.locator(selectors.instances.table)).toBeVisible();
  
  // Verify table has data
  const rows = page.locator(`${selectors.instances.table} tbody tr`);
  await expect(rows).toHaveCount(3);
});
```

---

## 🏗️ Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Next.js Admin UI (React)                   │
│  Components with Test IDs | State Attributes | ARIA Labels  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Testing Infrastructure                    │
│  Playwright E2E | Vitest Unit | React Testing Library       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────┬──────────────────┬──────────────────────┐
│   Test Utilities │   Fixtures       │   Debugging Tools    │
│   (Selectors)    │   (Auth, Data)   │   (Error Boundaries) │
└──────────────────┴──────────────────┴──────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         CI/CD Pipeline                       │
│  GitHub Actions | Coverage Reports | Visual Regression      │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

#### 1. Test ID System
- **Convention**: `[component]-[element]-[action?]`
- **Examples**: `instances-table`, `wizard-step-2-next`, `add-instance-button`
- **Coverage**: 100% of interactive elements
- **Discoverability**: AI agents can find all elements

#### 2. State Attributes
- **data-state**: `loading | success | error | idle`
- **data-status**: `idle | syncing | error`
- **data-step**: Current wizard step (1-4)
- **data-open**: Dialog open/closed state

#### 3. Test Utilities
- **Selectors**: 200+ centralized selectors
- **Helpers**: 30+ helper functions (wait, fill, verify)
- **Fixtures**: Auth mocking, API mocking, data fixtures
- **Self-Healing**: Multiple selector strategies with retry logic

#### 4. Debugging Tools
- **Error Boundaries**: Catch component crashes
- **Logging**: Structured logging with context
- **DevTools**: React DevTools integration
- **Screenshots**: Auto-capture on test failure

---

## 📊 Implementation Phases

### Phase 1: Foundation (Week 1)
- ✅ Add test IDs to all components
- ✅ Add state attributes for debugging
- ✅ Improve semantic HTML and ARIA labels
- ✅ Update UI components to accept testId prop

### Phase 2: Testing Infrastructure (Week 2)
- ✅ Configure Playwright for E2E testing
- ✅ Create test utilities (selectors, helpers)
- ✅ Create fixtures (auth, instances)
- ✅ Write E2E tests (auth, instances, wizard, sync)
- ✅ Configure Vitest for unit testing
- ✅ Write unit tests (hooks, API client)

### Phase 3: AI Agent Integration (Week 3)
- ✅ Create test generation script
- ✅ Implement Spec-Kit test commands
- ✅ Build self-healing test utilities
- ✅ Create visual regression tests

### Phase 4: Debugging Tools (Week 4)
- ✅ Implement error boundaries
- ✅ Create logging infrastructure
- ✅ Add DevTools integration

### Phase 5: Documentation & Refinement (Week 5)
- ✅ Create test ID reference
- ✅ Write testing patterns guide
- ✅ Write debugging guide
- ✅ Create AI agent guide
- ✅ Configure CI/CD pipeline

---

## 🧪 Testing

### Unit Tests (80%+ coverage)
```bash
npm run test
```

### E2E Tests
```bash
# Run all E2E tests
npm run test:e2e

# Run specific test file
npm run test:e2e e2e/specs/instances.spec.ts

# Run with UI mode
npm run test:e2e:ui

# Run in headed mode
npm run test:e2e -- --headed
```

### Visual Regression Tests
```bash
npm run test:visual
```

### Accessibility Tests
```bash
npm run test:a11y
```

---

## 📈 Success Metrics

### Coverage Goals
- ✅ 100% of interactive elements have test IDs
- ✅ 80%+ unit test coverage
- ✅ 100% of API endpoints have integration tests
- ✅ 100% of critical user paths have E2E tests
- ✅ Zero critical WCAG violations

### Performance Goals
- ✅ Unit tests complete in <5 seconds
- ✅ E2E tests complete in <5 minutes
- ✅ Flaky test rate <1%

### Quality Goals
- ✅ All tests pass in CI
- ✅ AI agents can discover 100% of elements
- ✅ AI agents can debug 80%+ of common issues
- ✅ Self-healing tests reduce maintenance by 50%

---

## 🔒 Testing Standards

### Test ID Naming
- **Format**: `[component]-[element]-[action?]`
- **Examples**: 
  - `instances-table`
  - `instance-row-1`
  - `add-instance-button`
  - `wizard-step-2-next`

### State Attributes
- **data-state**: Component loading state
- **data-status**: Instance sync status
- **data-step**: Wizard current step
- **data-open**: Dialog visibility

### Semantic HTML
- Use `<nav>` for navigation
- Use `<form>` for forms
- Add ARIA labels to all interactive elements
- Use proper table structure (thead, tbody)

---

## 📚 API Documentation

### Test Utilities

#### Selectors
```typescript
import { selectors } from './e2e/utils/selectors';

// Layout
selectors.layout.header
selectors.layout.sidebar

// Instances
selectors.instances.table
selectors.instances.addButton
selectors.instances.row('instance-1')

// Wizard
selectors.wizard.container
selectors.wizard.step(2)
selectors.wizard.nextButton
```

#### Helpers
```typescript
import { 
  waitForState,
  fillField,
  verifyNotification,
} from './e2e/utils/helpers';

// Wait for loading to complete
await waitForState(page, 'table', 'success');

// Fill form field
await fillField(page, 'name-input', 'Test Instance');

// Verify success notification
await verifyNotification(page, 'success', 'Instance created');
```

#### Fixtures
```typescript
import { loginAsAdmin } from './e2e/fixtures/auth';
import { mockInstancesListApi } from './e2e/fixtures/instances';

// Setup authentication
await loginAsAdmin(page);

// Mock API responses
await mockInstancesListApi(page);
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## 📞 Support

- **Documentation**: [.specify/features/005-ai-agent-testing/](.)
- **Issues**: [GitHub Issues](https://github.com/SemanS/digital-spiral/issues)
- **Email**: slavomir.seman@hotovo.com

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Owner**: Digital Spiral Team

