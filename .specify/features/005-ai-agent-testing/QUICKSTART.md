# Quick Start: AI Agent Testing & Debugging Support

**Get started in 5 minutes!**

---

## 🚀 For AI Agents (Auggie, Claude, Copilot)

### Step 1: Read the Documentation (2 minutes)

```bash
# Read in this order:
1. README.md          # Feature overview
2. constitution.md    # Testing principles
3. spec.md           # User stories (skim)
4. AUGGIE_GUIDE.md   # Your implementation guide
```

### Step 2: Start Implementation (3 minutes)

```bash
# Use Spec-Kit commands:
/implement Task 1.1  # Start with layout components
```

### Step 3: Verify Your Work

```bash
# Check that test IDs are added:
cd admin-ui
npm run test:e2e -- e2e/specs/instances.spec.ts
```

---

## 👨‍💻 For Human Developers

### Step 1: Install Dependencies

```bash
cd admin-ui

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install
```

### Step 2: Run Existing Tests

```bash
# Run unit tests
npm run test

# Run E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui
```

### Step 3: Add Test IDs to a Component

```typescript
// Before
export function Button({ children, onClick }) {
  return <button onClick={onClick}>{children}</button>;
}

// After
export function Button({ children, onClick, testId }) {
  return (
    <button 
      data-testid={testId}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

### Step 4: Write a Test

```typescript
// e2e/specs/my-feature.spec.ts
import { test, expect } from '@playwright/test';

test('my feature works', async ({ page }) => {
  await page.goto('/admin/instances');
  
  // Use test ID
  await page.click('[data-testid="my-button"]');
  
  // Verify result
  await expect(page.locator('[data-testid="result"]')).toBeVisible();
});
```

---

## 📝 Common Tasks

### Add Test ID to Component

```typescript
// 1. Add testId prop
interface Props {
  testId?: string;
  // ... other props
}

// 2. Apply to element
<div data-testid={testId}>
  {/* content */}
</div>

// 3. Use in parent
<MyComponent testId="my-component" />
```

### Add State Attribute

```typescript
// Expose component state
<div 
  data-testid="table"
  data-state={isLoading ? 'loading' : 'success'}
>
  {/* content */}
</div>
```

### Write E2E Test

```typescript
import { test, expect } from '@playwright/test';
import { selectors } from '../utils/selectors';
import { loginAsAdmin } from '../fixtures/auth';

test('user can do something', async ({ page }) => {
  // Setup
  await loginAsAdmin(page);
  await page.goto('/admin/instances');
  
  // Action
  await page.click(selectors.instances.addButton);
  
  // Verify
  await expect(page.locator(selectors.wizard.container)).toBeVisible();
});
```

### Mock API Response

```typescript
import { mockInstancesListApi } from '../fixtures/instances';

test.beforeEach(async ({ page }) => {
  await mockInstancesListApi(page);
});
```

---

## 🎯 Implementation Checklist

### Phase 1: Foundation (Week 1)

- [ ] **Task 1.1**: Add test IDs to layout components
  - [ ] Header.tsx
  - [ ] Sidebar.tsx
  - [ ] Footer.tsx

- [ ] **Task 1.2**: Add test IDs to instance components
  - [ ] InstancesTable.tsx
  - [ ] InstanceFormWizard.tsx
  - [ ] All wizard steps
  - [ ] InstanceEditForm.tsx
  - [ ] BackfillConfirmDialog.tsx
  - [ ] TestConnectionButton.tsx

- [ ] **Task 1.3**: Add test IDs to UI components
  - [ ] button.tsx
  - [ ] input.tsx
  - [ ] dialog.tsx
  - [ ] select.tsx
  - [ ] form.tsx
  - [ ] table.tsx

- [ ] **Task 1.4**: Add state attributes
  - [ ] InstancesTable (loading/success/error)
  - [ ] InstanceFormWizard (current step)
  - [ ] TestConnectionButton (testing/success/error)
  - [ ] BackfillProgressModal (progress state)
  - [ ] All dialogs (open/closed)

- [ ] **Task 1.5**: Improve semantic HTML
  - [ ] Use `<nav>` for navigation
  - [ ] Use `<form>` for forms
  - [ ] Add ARIA labels to buttons
  - [ ] Add labels to inputs
  - [ ] Add roles to dialogs
  - [ ] Proper table structure

### Phase 2: Testing Infrastructure (Week 2)

- [ ] **Task 2.1**: Configure Playwright
  - [ ] Create playwright.config.ts
  - [ ] Set up test directory structure
  - [ ] Configure browsers

- [ ] **Task 2.2**: Create test utilities
  - [ ] selectors.ts (✅ Done)
  - [ ] helpers.ts (✅ Done)
  - [ ] auth.ts fixtures (✅ Done)
  - [ ] instances.ts fixtures (✅ Done)

- [ ] **Task 2.3-2.6**: Write E2E tests
  - [ ] auth.spec.ts
  - [ ] instances.spec.ts (✅ Example done)
  - [ ] wizard.spec.ts
  - [ ] sync.spec.ts

- [ ] **Task 2.7**: Configure Vitest
  - [ ] Create vitest.config.ts
  - [ ] Set up test setup file
  - [ ] Configure coverage

- [ ] **Task 2.8-2.9**: Write unit tests
  - [ ] Hook tests
  - [ ] API client tests

---

## 🔍 Quick Reference

### Test ID Format

```
[component]-[element]-[action?]

Examples:
- instances-table
- instance-row-1
- add-instance-button
- wizard-step-2-next
- form-field-name
```

### State Attributes

```typescript
data-state="loading" | "success" | "error" | "idle"
data-status="idle" | "syncing" | "error"
data-step="1" | "2" | "3" | "4"
```

### Common Selectors

```typescript
import { selectors } from './e2e/utils/selectors';

selectors.instances.table
selectors.instances.addButton
selectors.wizard.step(2)
selectors.form.field('name')
```

### Common Helpers

```typescript
import { 
  waitForState,
  fillField,
  verifyNotification,
} from './e2e/utils/helpers';

await waitForState(page, 'table', 'success');
await fillField(page, 'name-input', 'Test');
await verifyNotification(page, 'success');
```

---

## 🐛 Troubleshooting

### Test ID not found

```typescript
// Check if element exists
const count = await page.locator('[data-testid="my-element"]').count();
console.log('Element count:', count);

// List all test IDs on page
const testIds = await page.$$eval('[data-testid]', 
  els => els.map(el => el.getAttribute('data-testid'))
);
console.log('Available test IDs:', testIds);
```

### Test is flaky

```typescript
// Add explicit wait
await page.waitForSelector('[data-testid="element"]');

// Wait for state
await page.waitForSelector('[data-testid="element"][data-state="success"]');

// Increase timeout
await page.click('[data-testid="button"]', { timeout: 30000 });
```

### API mock not working

```typescript
// Verify route is registered
await page.route('**/api/instances', route => {
  console.log('Route intercepted:', route.request().url());
  route.fulfill({ ... });
});

// Check network tab
page.on('request', req => console.log('Request:', req.url()));
page.on('response', res => console.log('Response:', res.url(), res.status()));
```

---

## 📚 Next Steps

1. **Read Full Documentation**
   - [Constitution](./constitution.md) - Testing principles
   - [Specification](./spec.md) - All user stories
   - [Plan](./plan.md) - Technical details
   - [Tasks](./tasks.md) - Complete task list

2. **Review Examples**
   - [Test Utilities](../../admin-ui/e2e/utils/)
   - [Fixtures](../../admin-ui/e2e/fixtures/)
   - [Test Specs](../../admin-ui/e2e/specs/)

3. **Start Implementing**
   - Follow task order in `tasks.md`
   - Use `AUGGIE_GUIDE.md` for guidance
   - Run tests frequently

4. **Get Help**
   - Check [Debugging Guide](../../admin-ui/docs/testing/debugging.md)
   - Review [Testing Patterns](../../admin-ui/docs/testing/patterns.md)
   - Open an issue on GitHub

---

## 🎉 Success Criteria

You'll know you're done when:

- ✅ All interactive elements have test IDs
- ✅ All components expose state attributes
- ✅ All tests pass consistently
- ✅ Test coverage meets goals (80%+ unit, 100% E2E)
- ✅ AI agents can discover and interact with all elements
- ✅ Documentation is complete and accurate

---

**Happy Testing! 🚀**

For questions: Check `AUGGIE_GUIDE.md` or open an issue on GitHub.

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04

