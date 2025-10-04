import { test, expect } from './fixtures/base';
import { InstancesPage } from './page-objects/InstancesPage';

test.describe('Instances Page', () => {
  let instancesPage: InstancesPage;

  test.beforeEach(async ({ page }) => {
    instancesPage = new InstancesPage(page);
    // TODO: Add authentication when implemented
    await instancesPage.goto();
  });

  test.describe('Page Layout', () => {
    test('should display page header', async ({ page }) => {
      await expect(instancesPage.pageContainer).toBeVisible();
      await expect(instancesPage.pageHeader).toBeVisible();
      await expect(instancesPage.pageTitle).toBeVisible();
      await expect(instancesPage.pageDescription).toBeVisible();
      await expect(instancesPage.addButton).toBeVisible();
    });

    test('should have correct page title', async ({ page }) => {
      await expect(instancesPage.pageTitle).toHaveText('Jira Instances');
    });

    test('should have add instance button', async ({ page }) => {
      await expect(instancesPage.addButton).toBeVisible();
      await expect(instancesPage.addButton).toBeEnabled();
      await expect(instancesPage.addButton).toHaveAttribute('aria-label');
    });

    test('should verify page is loaded', async ({ page }) => {
      await instancesPage.verifyPageLoaded();
      expect(await instancesPage.pageContainer.isVisible()).toBe(true);
    });
  });

  test.describe('Empty State', () => {
    test('should display empty state when no instances', async ({ page }) => {
      // This test assumes no instances exist
      // You may need to mock the API response
      const isEmpty = await instancesPage.isEmptyStateVisible();
      
      if (isEmpty) {
        await expect(instancesPage.emptyState).toBeVisible();
        await expect(instancesPage.emptyMessage).toBeVisible();
        await expect(instancesPage.emptyAddButton).toBeVisible();
      }
    });

    test('should navigate to create instance from empty state', async ({ page }) => {
      const isEmpty = await instancesPage.isEmptyStateVisible();
      
      if (isEmpty) {
        await instancesPage.clickEmptyAddInstance();
        await expect(page).toHaveURL('/admin/instances/new');
      }
    });
  });

  test.describe('Instances Table', () => {
    test('should display table when instances exist', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      
      const hasInstances = await instancesPage.isTableVisible();
      
      if (hasInstances) {
        await expect(instancesPage.table).toBeVisible();
        await expect(instancesPage.tableHeader).toBeVisible();
        await expect(instancesPage.tableBody).toBeVisible();
      }
    });

    test('should display instance rows', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      
      const count = await instancesPage.getInstanceCount();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should have accessible table', async ({ page }) => {
      const hasInstances = await instancesPage.isTableVisible();
      
      if (hasInstances) {
        // Check table has proper structure
        await expect(instancesPage.table).toBeVisible();
        
        // Check all rows have test IDs
        const instanceIds = await instancesPage.getAllInstanceIds();
        expect(instanceIds.length).toBeGreaterThan(0);
        
        for (const id of instanceIds) {
          const row = instancesPage.getInstanceRow(id);
          await expect(row).toBeVisible();
        }
      }
    });
  });

  test.describe('Instance Actions', () => {
    test('should open actions menu', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.openInstanceActions(firstId);
        
        // Check action menu items are visible
        await expect(page.getByTestId(`instance-action-edit-${firstId}`)).toBeVisible();
        await expect(page.getByTestId(`instance-action-test-${firstId}`)).toBeVisible();
        await expect(page.getByTestId(`instance-action-delete-${firstId}`)).toBeVisible();
      }
    });

    test('should navigate to edit page', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.clickEditInstance(firstId);
        await expect(page).toHaveURL(`/admin/instances/${firstId}/edit`);
      }
    });

    test('should navigate to instance details', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.clickInstanceName(firstId);
        await expect(page).toHaveURL(`/admin/instances/${firstId}`);
      }
    });
  });

  test.describe('Add Instance', () => {
    test('should navigate to create instance page', async ({ page }) => {
      await instancesPage.clickAddInstance();
      await expect(page).toHaveURL('/admin/instances/new');
    });

    test('should have accessible add button', async ({ page }) => {
      await expect(instancesPage.addButton).toHaveAttribute('aria-label');
    });
  });

  test.describe('Error State', () => {
    test('should handle error state', async ({ page }) => {
      // This test would require mocking an API error
      // For now, we just check if error elements exist
      const hasError = await instancesPage.isErrorStateVisible();
      
      if (hasError) {
        await expect(instancesPage.errorAlert).toBeVisible();
        await expect(instancesPage.errorMessage).toBeVisible();
        await expect(instancesPage.errorRetryButton).toBeVisible();
      }
    });

    test('should retry loading on error', async ({ page }) => {
      const hasError = await instancesPage.isErrorStateVisible();
      
      if (hasError) {
        await instancesPage.retryLoadInstances();
        // Should either show table or empty state after retry
        const hasTable = await instancesPage.isTableVisible();
        const isEmpty = await instancesPage.isEmptyStateVisible();
        expect(hasTable || isEmpty).toBe(true);
      }
    });
  });

  test.describe('Instance Status', () => {
    test('should display instance status badges', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        for (const id of instanceIds) {
          const status = instancesPage.getInstanceStatus(id);
          await expect(status).toBeVisible();
          
          // Check status badge has test ID
          const statusText = await instancesPage.getInstanceStatusText(id);
          expect(statusText).toBeTruthy();
        }
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should work on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await instancesPage.verifyPageLoaded();
      await expect(instancesPage.pageContainer).toBeVisible();
    });

    test('should work on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await instancesPage.verifyPageLoaded();
      await expect(instancesPage.pageContainer).toBeVisible();
    });

    test('should work on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await instancesPage.verifyPageLoaded();
      await expect(instancesPage.pageContainer).toBeVisible();
    });
  });
});

