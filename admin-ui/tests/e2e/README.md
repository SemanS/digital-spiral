# E2E Tests for Digital Spiral Admin UI

This directory contains end-to-end tests for the Digital Spiral Admin UI using Playwright.

## 📁 Structure

```
tests/e2e/
├── fixtures/
│   └── base.ts              # Test fixtures and helpers
├── page-objects/
│   ├── LayoutPage.ts        # Layout components POM
│   ├── InstancesPage.ts     # Instances page POM
│   └── InstanceWizardPage.ts # Instance wizard POM
├── navigation.spec.ts       # Navigation tests (19 tests)
├── instances.spec.ts        # Instances page tests (23 tests)
├── instance-wizard.spec.ts  # Wizard tests (35 tests)
├── instance-table.spec.ts   # Table interaction tests (28 tests)
├── accessibility.spec.ts    # Accessibility tests (25 tests)
└── README.md               # This file
```

## 🧪 Test Suites

### 1. Navigation Tests (`navigation.spec.ts`)
- **19 tests** covering header, sidebar, footer navigation
- Responsive navigation testing
- Keyboard navigation testing
- Layout consistency across pages

### 2. Instances Page Tests (`instances.spec.ts`)
- **23 tests** covering instances page functionality
- Page layout and structure
- Empty state handling
- Error state handling
- Table display and interactions
- Responsive design testing

### 3. Instance Wizard Tests (`instance-wizard.spec.ts`)
- **35 tests** covering the 4-step instance creation wizard
- Form validation testing
- Step navigation testing
- Data persistence across steps
- Responsive wizard testing

### 4. Instance Table Tests (`instance-table.spec.ts`)
- **28 tests** covering table interactions
- Row display and structure
- Actions menu functionality
- Table performance testing
- Responsive table testing

### 5. Accessibility Tests (`accessibility.spec.ts`)
- **25 tests** covering WCAG 2.1 AA compliance
- ARIA attributes testing
- Keyboard navigation testing
- Screen reader support testing
- Automated axe-core checks

## 🚀 Running Tests

### Prerequisites

```bash
# Install dependencies
npm install

# Install Playwright browsers (first time only)
npx playwright install
```

### Run All Tests

```bash
# Run all tests
npm run test:e2e

# Run tests in UI mode (recommended for development)
npx playwright test --ui

# Run tests in headed mode (see browser)
npx playwright test --headed

# Run tests in debug mode
npx playwright test --debug
```

### Run Specific Tests

```bash
# Run specific test file
npx playwright test navigation.spec.ts

# Run specific test suite
npx playwright test --grep "Navigation"

# Run specific test
npx playwright test --grep "should display header"
```

### Run Tests by Browser

```bash
# Run in Chromium only
npx playwright test --project=chromium

# Run in Firefox only
npx playwright test --project=firefox

# Run in WebKit only
npx playwright test --project=webkit

# Run in Mobile Chrome
npx playwright test --project="Mobile Chrome"

# Run in Mobile Safari
npx playwright test --project="Mobile Safari"
```

### View Test Reports

```bash
# Generate and open HTML report
npx playwright show-report

# View test results
cat test-results/results.json
```

## 📊 Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Navigation | 19 | ✅ |
| Instances Page | 23 | ✅ |
| Instance Wizard | 35 | ✅ |
| Instance Table | 28 | ✅ |
| Accessibility | 25 | ✅ |
| **Total** | **130** | **✅** |

## 🎯 Page Object Model

All tests use the Page Object Model (POM) pattern for better maintainability:

### LayoutPage
```typescript
const layoutPage = new LayoutPage(page);
await layoutPage.navigateToInstances();
await layoutPage.signOut();
```

### InstancesPage
```typescript
const instancesPage = new InstancesPage(page);
await instancesPage.goto();
await instancesPage.clickAddInstance();
await instancesPage.clickEditInstance(instanceId);
```

### InstanceWizardPage
```typescript
const wizardPage = new InstanceWizardPage(page);
await wizardPage.goto();
await wizardPage.completeWizard({
  name: 'Test Instance',
  baseUrl: 'https://test.atlassian.net',
  email: 'test@example.com',
  apiToken: 'token',
});
```

## 🛠️ Test Helpers

### Test Fixtures (`fixtures/base.ts`)

```typescript
import { test, expect } from './fixtures/base';

// Use extended test with axe-core
test('should be accessible', async ({ page }) => {
  await checkAccessibility(page);
});

// Use helper functions
await fillByTestId(page, 'instance-name-input', 'Test');
await clickByTestId(page, 'submit-button');
const isVisible = await isVisibleByTestId(page, 'success-message');
```

### Test Data Generators

```typescript
import { testData } from './fixtures/base';

// Use predefined test data
await wizardPage.fillInstanceDetails(testData.instance.valid);
await wizardPage.fillAuthDetails(testData.instance.valid);
```

## 🔍 Debugging Tests

### Visual Debugging

```bash
# Run in UI mode (best for debugging)
npx playwright test --ui

# Run in headed mode
npx playwright test --headed

# Run in debug mode (step through)
npx playwright test --debug
```

### Screenshots and Videos

Tests automatically capture:
- Screenshots on failure
- Videos on failure
- Traces on first retry

Find them in:
- `test-results/` - Screenshots and videos
- `playwright-report/` - HTML report with traces

### Trace Viewer

```bash
# View trace for failed test
npx playwright show-trace test-results/.../trace.zip
```

## 📝 Writing New Tests

### 1. Create Test File

```typescript
import { test, expect } from './fixtures/base';
import { YourPage } from './page-objects/YourPage';

test.describe('Your Feature', () => {
  let yourPage: YourPage;

  test.beforeEach(async ({ page }) => {
    yourPage = new YourPage(page);
    await yourPage.goto();
  });

  test('should do something', async ({ page }) => {
    // Your test code
  });
});
```

### 2. Create Page Object

```typescript
import { Page, Locator } from '@playwright/test';

export class YourPage {
  readonly page: Page;
  readonly element: Locator;

  constructor(page: Page) {
    this.page = page;
    this.element = page.getByTestId('your-element');
  }

  async goto() {
    await this.page.goto('/your-path');
  }

  async doSomething() {
    await this.element.click();
  }
}
```

### 3. Use Test IDs

Always use test IDs for selecting elements:

```typescript
// ✅ Good - using test ID
const button = page.getByTestId('submit-button');

// ❌ Bad - using CSS selector
const button = page.locator('.btn-primary');

// ❌ Bad - using text
const button = page.getByText('Submit');
```

## 🎨 Best Practices

1. **Use Page Objects** - Keep tests DRY and maintainable
2. **Use Test IDs** - Stable selectors that don't break with UI changes
3. **Test User Flows** - Test complete user journeys, not just individual actions
4. **Test Accessibility** - Include accessibility checks in all tests
5. **Test Responsiveness** - Test on multiple viewport sizes
6. **Mock API Calls** - Use `mockApiResponse()` for predictable tests
7. **Keep Tests Independent** - Each test should be able to run in isolation
8. **Use Descriptive Names** - Test names should clearly describe what they test
9. **Add Comments** - Explain complex test logic
10. **Clean Up** - Reset state after tests if needed

## 🐛 Common Issues

### Tests Timing Out

```typescript
// Increase timeout for slow operations
test('slow test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // ...
});
```

### Element Not Found

```typescript
// Wait for element before interacting
await element.waitFor({ state: 'visible' });
await element.click();
```

### Flaky Tests

```typescript
// Use proper waits instead of sleep
await page.waitForLoadState('networkidle');
await element.waitFor({ state: 'visible' });

// Don't use arbitrary timeouts
// ❌ await page.waitForTimeout(1000);
```

## 📚 Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Page Object Model](https://playwright.dev/docs/pom)
- [Accessibility Testing](https://playwright.dev/docs/accessibility-testing)
- [axe-core Documentation](https://github.com/dequelabs/axe-core)

## 🤝 Contributing

When adding new tests:

1. Follow the existing structure
2. Use Page Object Model
3. Add accessibility tests
4. Test on multiple browsers
5. Update this README if needed
6. Run all tests before committing

## 📊 CI/CD Integration

Tests run automatically on:
- Pull requests
- Commits to main branch
- Nightly builds

See `.github/workflows/` for CI configuration.

