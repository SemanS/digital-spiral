import { test, expect } from './fixtures/base';
import { LayoutPage } from './page-objects/LayoutPage';

test.describe('Navigation', () => {
  let layoutPage: LayoutPage;

  test.beforeEach(async ({ page }) => {
    layoutPage = new LayoutPage(page);
    // TODO: Add authentication when implemented
    await page.goto('/admin/instances');
  });

  test.describe('Header Navigation', () => {
    test('should display header with all navigation items', async ({ page }) => {
      await expect(layoutPage.header).toBeVisible();
      await expect(layoutPage.headerLogo).toBeVisible();
      await expect(layoutPage.headerNav).toBeVisible();
      await expect(layoutPage.headerNavInstances).toBeVisible();
      await expect(layoutPage.headerNavSettings).toBeVisible();
      await expect(layoutPage.headerNavLogs).toBeVisible();
      await expect(layoutPage.headerUserMenu).toBeVisible();
    });

    test('should navigate to instances page', async ({ page }) => {
      await layoutPage.navigateToInstances();
      await expect(page).toHaveURL('/admin/instances');
      await expect(layoutPage.headerNavInstances).toHaveAttribute('aria-current', 'page');
    });

    test('should navigate to settings page', async ({ page }) => {
      await layoutPage.navigateToSettings();
      await expect(page).toHaveURL('/admin/settings');
      await expect(layoutPage.headerNavSettings).toHaveAttribute('aria-current', 'page');
    });

    test('should navigate to logs page', async ({ page }) => {
      await layoutPage.navigateToLogs();
      await expect(page).toHaveURL('/admin/logs');
      await expect(layoutPage.headerNavLogs).toHaveAttribute('aria-current', 'page');
    });

    test('should open user menu', async ({ page }) => {
      await layoutPage.openUserMenu();
      await expect(layoutPage.headerUserMenuSignout).toBeVisible();
    });

    test('should have accessible navigation', async ({ page }) => {
      // Check ARIA labels
      await expect(layoutPage.headerNav).toHaveAttribute('role', 'navigation');
      await expect(layoutPage.headerNav).toHaveAttribute('aria-label');
      
      // Check navigation items have aria-current
      const activeNav = await layoutPage.getActiveNavItem();
      expect(activeNav).toBeTruthy();
    });
  });

  test.describe('Sidebar Navigation', () => {
    test('should display sidebar', async ({ page }) => {
      await expect(layoutPage.sidebar).toBeVisible();
      await expect(layoutPage.sidebarNav).toBeVisible();
    });

    test('should have accessible sidebar', async ({ page }) => {
      await expect(layoutPage.sidebarNav).toHaveAttribute('role', 'navigation');
      await expect(layoutPage.sidebarNav).toHaveAttribute('aria-label');
    });

    test('should navigate via sidebar items', async ({ page }) => {
      // This test assumes sidebar items exist
      // Adjust based on actual sidebar implementation
      const sidebarItems = await page.locator('[data-testid^="sidebar-nav-"]').all();
      expect(sidebarItems.length).toBeGreaterThan(0);
    });
  });

  test.describe('Footer', () => {
    test('should display footer with links', async ({ page }) => {
      await expect(layoutPage.footer).toBeVisible();
      await expect(layoutPage.footerLinkPrivacy).toBeVisible();
      await expect(layoutPage.footerLinkTerms).toBeVisible();
    });

    test('should have accessible footer', async ({ page }) => {
      await expect(layoutPage.footer).toHaveAttribute('role', 'contentinfo');
    });

    test('should have working footer links', async ({ page }) => {
      // Check privacy link
      await expect(layoutPage.footerLinkPrivacy).toHaveAttribute('href');
      await expect(layoutPage.footerLinkPrivacy).toHaveAttribute('aria-label');
      
      // Check terms link
      await expect(layoutPage.footerLinkTerms).toHaveAttribute('href');
      await expect(layoutPage.footerLinkTerms).toHaveAttribute('aria-label');
    });
  });

  test.describe('Layout Consistency', () => {
    test('should maintain layout across pages', async ({ page }) => {
      // Check instances page
      await layoutPage.navigateToInstances();
      await expect(layoutPage.header).toBeVisible();
      await expect(layoutPage.footer).toBeVisible();
      
      // Check settings page
      await layoutPage.navigateToSettings();
      await expect(layoutPage.header).toBeVisible();
      await expect(layoutPage.footer).toBeVisible();
      
      // Check logs page
      await layoutPage.navigateToLogs();
      await expect(layoutPage.header).toBeVisible();
      await expect(layoutPage.footer).toBeVisible();
    });

    test('should verify layout is loaded', async ({ page }) => {
      await layoutPage.verifyLayoutLoaded();
      expect(await layoutPage.isHeaderVisible()).toBe(true);
      expect(await layoutPage.isFooterVisible()).toBe(true);
    });
  });

  test.describe('Responsive Navigation', () => {
    test('should work on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(layoutPage.header).toBeVisible();
      await expect(layoutPage.footer).toBeVisible();
    });

    test('should work on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(layoutPage.header).toBeVisible();
      await expect(layoutPage.footer).toBeVisible();
    });

    test('should work on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await expect(layoutPage.header).toBeVisible();
      await expect(layoutPage.footer).toBeVisible();
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('should navigate with keyboard', async ({ page }) => {
      // Tab through navigation items
      await page.keyboard.press('Tab');
      
      // Check if focus is on a navigation element
      const focusedElement = await page.evaluate(() => {
        const el = document.activeElement;
        return el?.getAttribute('data-testid');
      });
      
      expect(focusedElement).toBeTruthy();
    });

    test('should activate links with Enter key', async ({ page }) => {
      await layoutPage.headerNavSettings.focus();
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL('/admin/settings');
    });
  });
});

