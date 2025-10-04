import { test, expect } from './fixtures/base';
import { checkAccessibility } from './fixtures/base';
import { LayoutPage } from './page-objects/LayoutPage';
import { InstancesPage } from './page-objects/InstancesPage';
import { InstanceWizardPage } from './page-objects/InstanceWizardPage';

test.describe('Accessibility Tests', () => {
  test.describe('Layout Accessibility', () => {
    let layoutPage: LayoutPage;

    test.beforeEach(async ({ page }) => {
      layoutPage = new LayoutPage(page);
      await page.goto('/admin/instances');
    });

    test('should have accessible header', async ({ page }) => {
      await expect(layoutPage.header).toHaveAttribute('role');
      await expect(layoutPage.headerNav).toHaveAttribute('role', 'navigation');
      await expect(layoutPage.headerNav).toHaveAttribute('aria-label');
      
      // Run axe accessibility check on header
      await checkAccessibility(page, {
        include: ['[data-testid="app-header"]'],
      });
    });

    test('should have accessible navigation links', async ({ page }) => {
      // All nav links should have aria-label
      await expect(layoutPage.headerNavInstances).toHaveAttribute('aria-label');
      await expect(layoutPage.headerNavSettings).toHaveAttribute('aria-label');
      await expect(layoutPage.headerNavLogs).toHaveAttribute('aria-label');
      
      // Active link should have aria-current
      const activeNav = page.locator('[aria-current="page"]');
      await expect(activeNav).toBeVisible();
    });

    test('should have accessible sidebar', async ({ page }) => {
      await expect(layoutPage.sidebarNav).toHaveAttribute('role', 'navigation');
      await expect(layoutPage.sidebarNav).toHaveAttribute('aria-label');
      
      // Run axe check on sidebar
      await checkAccessibility(page, {
        include: ['[data-testid="app-sidebar"]'],
      });
    });

    test('should have accessible footer', async ({ page }) => {
      await expect(layoutPage.footer).toHaveAttribute('role', 'contentinfo');
      
      // Footer links should have aria-label
      await expect(layoutPage.footerLinkPrivacy).toHaveAttribute('aria-label');
      await expect(layoutPage.footerLinkTerms).toHaveAttribute('aria-label');
      
      // Run axe check on footer
      await checkAccessibility(page, {
        include: ['[data-testid="app-footer"]'],
      });
    });

    test('should have accessible user menu', async ({ page }) => {
      await expect(layoutPage.headerUserMenu).toHaveAttribute('aria-label');
      
      await layoutPage.openUserMenu();
      await expect(layoutPage.headerUserMenuSignout).toBeVisible();
    });

    test('should pass full page accessibility check', async ({ page }) => {
      // Run full page accessibility check
      await checkAccessibility(page);
    });
  });

  test.describe('Instances Page Accessibility', () => {
    let instancesPage: InstancesPage;

    test.beforeEach(async ({ page }) => {
      instancesPage = new InstancesPage(page);
      await instancesPage.goto();
    });

    test('should have accessible page header', async ({ page }) => {
      await expect(instancesPage.pageTitle).toBeVisible();
      await expect(instancesPage.pageDescription).toBeVisible();
      
      // Add button should have aria-label
      await expect(instancesPage.addButton).toHaveAttribute('aria-label');
    });

    test('should have accessible table', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      
      const hasTable = await instancesPage.isTableVisible();
      
      if (hasTable) {
        // Run axe check on table
        await checkAccessibility(page, {
          include: ['[data-testid="instances-table"]'],
        });
      }
    });

    test('should have accessible instance rows', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      
      const instanceIds = await instancesPage.getAllInstanceIds();
      
      if (instanceIds.length > 0) {
        const firstId = instanceIds[0];
        
        // Name link should have aria-label
        const nameLink = page.getByTestId(`instance-name-link-${firstId}`);
        await expect(nameLink).toHaveAttribute('aria-label');
        
        // URL link should have aria-label
        const urlLink = page.getByTestId(`instance-url-link-${firstId}`);
        await expect(urlLink).toHaveAttribute('aria-label');
        
        // Actions menu should have aria-label
        const actionsMenu = instancesPage.getInstanceActionsMenu(firstId);
        await expect(actionsMenu).toHaveAttribute('aria-label');
      }
    });

    test('should have accessible empty state', async ({ page }) => {
      const isEmpty = await instancesPage.isEmptyStateVisible();
      
      if (isEmpty) {
        await expect(instancesPage.emptyAddButton).toHaveAttribute('aria-label');
        
        // Run axe check on empty state
        await checkAccessibility(page, {
          include: ['[data-testid="instances-empty-state"]'],
        });
      }
    });

    test('should have accessible error state', async ({ page }) => {
      const hasError = await instancesPage.isErrorStateVisible();
      
      if (hasError) {
        await expect(instancesPage.errorRetryButton).toHaveAttribute('aria-label');
        
        // Run axe check on error state
        await checkAccessibility(page, {
          include: ['[data-testid="instances-error-alert"]'],
        });
      }
    });

    test('should pass full page accessibility check', async ({ page }) => {
      await instancesPage.waitForInstancesLoad();
      await checkAccessibility(page);
    });
  });

  test.describe('Instance Wizard Accessibility', () => {
    let wizardPage: InstanceWizardPage;

    test.beforeEach(async ({ page }) => {
      wizardPage = new InstanceWizardPage(page);
      await wizardPage.goto();
    });

    test('should have accessible wizard container', async ({ page }) => {
      await expect(wizardPage.wizard).toBeVisible();
      await expect(wizardPage.navigation).toHaveAttribute('role', 'navigation');
      await expect(wizardPage.navigation).toHaveAttribute('aria-label');
    });

    test('should have accessible step indicator', async ({ page }) => {
      // Step counter should have aria-live for screen readers
      await expect(wizardPage.stepCounter).toHaveAttribute('aria-live');
    });

    test('should have accessible form fields in step 1', async ({ page }) => {
      // All inputs should have aria-label
      await expect(wizardPage.nameInput).toHaveAttribute('aria-label');
      await expect(wizardPage.baseUrlInput).toHaveAttribute('aria-label');
      await expect(wizardPage.projectFilterInput).toHaveAttribute('aria-label');
      
      // Next button should have aria-label
      await expect(wizardPage.detailsNextButton).toHaveAttribute('aria-label');
      
      // Run axe check on details form
      await checkAccessibility(page, {
        include: ['[data-testid="instance-details-form"]'],
      });
    });

    test('should have accessible form fields in step 2', async ({ page }) => {
      // Complete step 1
      await wizardPage.fillInstanceDetails({
        name: 'Test Instance',
        baseUrl: 'https://test.atlassian.net',
      });
      await wizardPage.clickDetailsNext();
      
      // All inputs should have aria-label
      await expect(wizardPage.emailInput).toHaveAttribute('aria-label');
      await expect(wizardPage.apiTokenInput).toHaveAttribute('aria-label');
      
      // Toggle button should have aria-label
      await expect(wizardPage.apiTokenToggle).toHaveAttribute('aria-label');
      
      // Navigation buttons should have aria-label
      await expect(wizardPage.authBackButton).toHaveAttribute('aria-label');
      await expect(wizardPage.authNextButton).toHaveAttribute('aria-label');
      
      // Run axe check on auth form
      await checkAccessibility(page, {
        include: ['[data-testid="instance-auth-form"]'],
      });
    });

    test('should have accessible validation step', async ({ page }) => {
      // Complete steps 1 and 2
      await wizardPage.completeDetailsStep({
        name: 'Test Instance',
        baseUrl: 'https://test.atlassian.net',
      });
      await wizardPage.completeAuthStep({
        email: 'test@example.com',
        apiToken: 'test-token',
      });
      
      // Test button should have aria-label
      await expect(wizardPage.testConnectionButton).toHaveAttribute('aria-label');
      
      // Next button should have aria-disabled when disabled
      const isDisabled = await wizardPage.validateNextButton.isDisabled();
      if (isDisabled) {
        await expect(wizardPage.validateNextButton).toHaveAttribute('aria-disabled');
      }
      
      // Run axe check on validate step
      await checkAccessibility(page, {
        include: ['[data-testid="instance-validate-step"]'],
      });
    });

    test('should have accessible cancel button', async ({ page }) => {
      await expect(wizardPage.cancelButton).toHaveAttribute('aria-label');
    });

    test('should pass full wizard accessibility check', async ({ page }) => {
      await checkAccessibility(page);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('should navigate header with keyboard', async ({ page }) => {
      await page.goto('/admin/instances');
      
      // Tab to first focusable element
      await page.keyboard.press('Tab');
      
      // Should be able to navigate through header
      const focusedElement = await page.evaluate(() => {
        return document.activeElement?.getAttribute('data-testid');
      });
      
      expect(focusedElement).toBeTruthy();
    });

    test('should activate buttons with Enter', async ({ page }) => {
      const instancesPage = new InstancesPage(page);
      await instancesPage.goto();
      
      // Focus add button
      await instancesPage.addButton.focus();
      
      // Press Enter
      await page.keyboard.press('Enter');
      
      // Should navigate to new instance page
      await expect(page).toHaveURL('/admin/instances/new');
    });

    test('should navigate wizard with keyboard', async ({ page }) => {
      const wizardPage = new InstanceWizardPage(page);
      await wizardPage.goto();
      
      // Should be able to tab through form fields
      await page.keyboard.press('Tab');
      
      const focusedElement = await page.evaluate(() => {
        return document.activeElement?.getAttribute('data-testid');
      });
      
      expect(focusedElement).toBeTruthy();
    });

    test('should close menus with Escape', async ({ page }) => {
      const layoutPage = new LayoutPage(page);
      await page.goto('/admin/instances');
      
      // Open user menu
      await layoutPage.openUserMenu();
      await expect(layoutPage.headerUserMenuSignout).toBeVisible();
      
      // Press Escape
      await page.keyboard.press('Escape');
      
      // Menu should close
      await expect(layoutPage.headerUserMenuSignout).not.toBeVisible();
    });
  });

  test.describe('Screen Reader Support', () => {
    test('should have proper ARIA landmarks', async ({ page }) => {
      await page.goto('/admin/instances');
      
      // Check for navigation landmarks
      const navLandmarks = await page.locator('[role="navigation"]').count();
      expect(navLandmarks).toBeGreaterThan(0);
      
      // Check for contentinfo landmark (footer)
      const contentInfo = await page.locator('[role="contentinfo"]').count();
      expect(contentInfo).toBeGreaterThan(0);
    });

    test('should have aria-live regions for dynamic content', async ({ page }) => {
      const wizardPage = new InstanceWizardPage(page);
      await wizardPage.goto();
      
      // Step counter should have aria-live
      await expect(wizardPage.stepCounter).toHaveAttribute('aria-live', 'polite');
    });

    test('should have aria-current for active navigation', async ({ page }) => {
      await page.goto('/admin/instances');
      
      // Active nav item should have aria-current
      const activeNav = page.locator('[aria-current="page"]');
      await expect(activeNav).toBeVisible();
    });

    test('should have descriptive aria-labels', async ({ page }) => {
      const instancesPage = new InstancesPage(page);
      await instancesPage.goto();
      
      // Check add button has descriptive label
      const ariaLabel = await instancesPage.addButton.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel?.length).toBeGreaterThan(5);
    });
  });
});

