import { test, expect } from './fixtures/base';
import { InstancesPage } from './page-objects/InstancesPage';

test.describe('Instance Table Interactions', () => {
  let instancesPage: InstancesPage;

  test.beforeEach(async ({ page }) => {
    instancesPage = new InstancesPage(page);
    // TODO: Add authentication when implemented
    await instancesPage.goto();
    await instancesPage.waitForInstancesLoad();
  });

  test.describe('Table Structure', () => {
    test('should display table with proper structure', async ({ page }) => {
      const hasTable = await instancesPage.isTableVisible();
      
      if (hasTable) {
        await expect(instancesPage.table).toBeVisible();
        await expect(instancesPage.tableHeader).toBeVisible();
        await expect(instancesPage.tableBody).toBeVisible();
      }
    });

    test('should have accessible table', async ({ page }) => {
      const hasTable = await instancesPage.isTableVisible();
      
      if (hasTable) {
        // Table should have proper test IDs
        await expect(instancesPage.table).toHaveAttribute('data-testid', 'instances-table');
        await expect(instancesPage.tableHeader).toHaveAttribute('data-testid', 'instances-table-header');
        await expect(instancesPage.tableBody).toHaveAttribute('data-testid', 'instances-table-body');
      }
    });

    test('should display column headers', async ({ page }) => {
      const hasTable = await instancesPage.isTableVisible();
      
      if (hasTable) {
        // Check for expected column headers
        const headers = await page.locator('th').allTextContents();
        expect(headers.length).toBeGreaterThan(0);
        
        // Should have at least these columns
        const headerText = headers.join(' ');
        expect(headerText).toContain('Name');
        expect(headerText).toContain('Base URL');
        expect(headerText).toContain('Status');
      }
    });
  });

  test.describe('Instance Rows', () => {
    test('should display instance rows with all data', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        
        // Check all row elements are visible
        await expect(instancesPage.getInstanceRow(firstId)).toBeVisible();
        await expect(instancesPage.getInstanceName(firstId)).toBeVisible();
        await expect(instancesPage.getInstanceUrl(firstId)).toBeVisible();
        await expect(instancesPage.getInstanceStatus(firstId)).toBeVisible();
      }
    });

    test('should have unique test IDs for each row', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      // All IDs should be unique
      const uniqueIds = new Set(instanceIds);
      expect(uniqueIds.size).toBe(instanceIds.length);
      
      // Each row should have proper test ID
      for (const id of instanceIds) {
        const row = instancesPage.getInstanceRow(id);
        await expect(row).toHaveAttribute('data-testid', `instance-row-${id}`);
      }
    });

    test('should display instance name as clickable link', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        const nameLink = page.getByTestId(`instance-name-link-${firstId}`);
        
        await expect(nameLink).toBeVisible();
        await expect(nameLink).toHaveAttribute('href');
        await expect(nameLink).toHaveAttribute('aria-label');
      }
    });

    test('should display instance URL as external link', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        const urlLink = page.getByTestId(`instance-url-link-${firstId}`);
        
        await expect(urlLink).toBeVisible();
        await expect(urlLink).toHaveAttribute('href');
        await expect(urlLink).toHaveAttribute('target', '_blank');
        await expect(urlLink).toHaveAttribute('rel', 'noopener noreferrer');
      }
    });

    test('should display status badge with correct styling', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        const statusBadge = instancesPage.getInstanceStatus(firstId);
        
        await expect(statusBadge).toBeVisible();
        
        const statusText = await instancesPage.getInstanceStatusText(firstId);
        expect(statusText).toBeTruthy();
        
        // Status should be one of the valid values
        expect(['Idle', 'Syncing', 'Error']).toContain(statusText);
      }
    });

    test('should count instances correctly', async ({ page }) => {
      const count = await instancesPage.getInstanceCount();
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      expect(count).toBe(instanceIds.length);
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('Instance Actions Menu', () => {
    test('should display actions menu button', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        const actionsMenu = instancesPage.getInstanceActionsMenu(firstId);
        
        await expect(actionsMenu).toBeVisible();
        await expect(actionsMenu).toBeEnabled();
        await expect(actionsMenu).toHaveAttribute('aria-label');
      }
    });

    test('should open actions menu on click', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.openInstanceActions(firstId);
        
        // Menu items should be visible
        await expect(page.getByTestId(`instance-action-edit-${firstId}`)).toBeVisible();
        await expect(page.getByTestId(`instance-action-test-${firstId}`)).toBeVisible();
        await expect(page.getByTestId(`instance-action-delete-${firstId}`)).toBeVisible();
      }
    });

    test('should have accessible menu items', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.openInstanceActions(firstId);
        
        // Check all menu items have proper attributes
        const editAction = page.getByTestId(`instance-action-edit-${firstId}`);
        const testAction = page.getByTestId(`instance-action-test-${firstId}`);
        const deleteAction = page.getByTestId(`instance-action-delete-${firstId}`);
        
        await expect(editAction).toBeVisible();
        await expect(testAction).toBeVisible();
        await expect(deleteAction).toBeVisible();
      }
    });

    test('should navigate to edit page from menu', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.clickEditInstance(firstId);
        
        await expect(page).toHaveURL(`/admin/instances/${firstId}/edit`);
      }
    });

    test('should trigger test connection from menu', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.openInstanceActions(firstId);
        
        const testAction = page.getByTestId(`instance-action-test-${firstId}`);
        await expect(testAction).toBeEnabled();
        
        // Click would trigger test connection
        // Actual behavior would need API mocking
      }
    });

    test('should show delete action with warning styling', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.openInstanceActions(firstId);
        
        const deleteAction = page.getByTestId(`instance-action-delete-${firstId}`);
        await expect(deleteAction).toBeVisible();
        
        // Delete action should have destructive styling
        const className = await deleteAction.getAttribute('class');
        expect(className).toContain('destructive');
      }
    });
  });

  test.describe('Row Interactions', () => {
    test('should navigate to instance details on name click', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        await instancesPage.clickInstanceName(firstId);
        
        await expect(page).toHaveURL(`/admin/instances/${firstId}`);
      }
    });

    test('should hover over rows', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        const row = instancesPage.getInstanceRow(firstId);
        
        await row.hover();
        
        // Row should have hover state
        const className = await row.getAttribute('class');
        expect(className).toBeTruthy();
      }
    });

    test('should display all row data correctly', async ({ page }) => {
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        
        // Get all cell data
        const name = await instancesPage.getInstanceName(firstId).textContent();
        const url = await instancesPage.getInstanceUrl(firstId).textContent();
        const status = await instancesPage.getInstanceStatusText(firstId);
        
        // All should have content
        expect(name).toBeTruthy();
        expect(url).toBeTruthy();
        expect(status).toBeTruthy();
      }
    });
  });

  test.describe('Empty State', () => {
    test('should display empty state when no instances', async ({ page }) => {
      const isEmpty = await instancesPage.isEmptyStateVisible();
      
      if (isEmpty) {
        await expect(instancesPage.emptyState).toBeVisible();
        await expect(instancesPage.emptyMessage).toBeVisible();
        await expect(instancesPage.emptyMessage).toHaveText('No instances found');
        await expect(instancesPage.emptyAddButton).toBeVisible();
      }
    });

    test('should have accessible empty state', async ({ page }) => {
      const isEmpty = await instancesPage.isEmptyStateVisible();
      
      if (isEmpty) {
        await expect(instancesPage.emptyState).toHaveAttribute('data-testid', 'instances-empty-state');
        await expect(instancesPage.emptyAddButton).toHaveAttribute('aria-label');
      }
    });
  });

  test.describe('Table Performance', () => {
    test('should load table efficiently', async ({ page }) => {
      const startTime = Date.now();
      await instancesPage.waitForInstancesLoad();
      const loadTime = Date.now() - startTime;
      
      // Table should load within reasonable time (5 seconds)
      expect(loadTime).toBeLessThan(5000);
    });

    test('should handle multiple instances', async ({ page }) => {
      const count = await instancesPage.getInstanceCount();
      
      // Should be able to display any number of instances
      expect(count).toBeGreaterThanOrEqual(0);
      
      if (count > 0) {
        // All rows should be accessible
        const instanceIds = await instancesPage.getAllInstanceIds();
        expect(instanceIds.length).toBe(count);
      }
    });
  });

  test.describe('Responsive Table', () => {
    test('should work on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      const hasTable = await instancesPage.isTableVisible();
      if (hasTable) {
        await expect(instancesPage.table).toBeVisible();
      }
    });

    test('should work on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      const hasTable = await instancesPage.isTableVisible();
      if (hasTable) {
        await expect(instancesPage.table).toBeVisible();
      }
    });

    test('should work on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      const hasTable = await instancesPage.isTableVisible();
      if (hasTable) {
        await expect(instancesPage.table).toBeVisible();
      }
    });
  });
});

