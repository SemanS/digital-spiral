import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Layout components (Header, Sidebar, Footer)
 */
export class LayoutPage {
  readonly page: Page;
  
  // Header elements
  readonly header: Locator;
  readonly headerLogo: Locator;
  readonly headerNav: Locator;
  readonly headerNavInstances: Locator;
  readonly headerNavSettings: Locator;
  readonly headerNavLogs: Locator;
  readonly headerUserMenu: Locator;
  readonly headerUserMenuSignout: Locator;
  
  // Sidebar elements
  readonly sidebar: Locator;
  readonly sidebarNav: Locator;
  
  // Footer elements
  readonly footer: Locator;
  readonly footerLinkPrivacy: Locator;
  readonly footerLinkTerms: Locator;

  constructor(page: Page) {
    this.page = page;
    
    // Header
    this.header = page.getByTestId('app-header');
    this.headerLogo = page.getByTestId('header-logo');
    this.headerNav = page.getByTestId('header-nav');
    this.headerNavInstances = page.getByTestId('header-nav-instances');
    this.headerNavSettings = page.getByTestId('header-nav-settings');
    this.headerNavLogs = page.getByTestId('header-nav-logs');
    this.headerUserMenu = page.getByTestId('header-user-menu');
    this.headerUserMenuSignout = page.getByTestId('header-user-menu-signout');
    
    // Sidebar
    this.sidebar = page.getByTestId('app-sidebar');
    this.sidebarNav = page.getByTestId('sidebar-nav');
    
    // Footer
    this.footer = page.getByTestId('app-footer');
    this.footerLinkPrivacy = page.getByTestId('footer-link-privacy');
    this.footerLinkTerms = page.getByTestId('footer-link-terms');
  }

  /**
   * Navigate to instances page via header
   */
  async navigateToInstances() {
    await this.headerNavInstances.click();
    await this.page.waitForURL('/admin/instances');
  }

  /**
   * Navigate to settings page via header
   */
  async navigateToSettings() {
    await this.headerNavSettings.click();
    await this.page.waitForURL('/admin/settings');
  }

  /**
   * Navigate to logs page via header
   */
  async navigateToLogs() {
    await this.headerNavLogs.click();
    await this.page.waitForURL('/admin/logs');
  }

  /**
   * Click logo to go home
   */
  async clickLogo() {
    await this.headerLogo.click();
  }

  /**
   * Open user menu
   */
  async openUserMenu() {
    await this.headerUserMenu.click();
  }

  /**
   * Sign out
   */
  async signOut() {
    await this.openUserMenu();
    await this.headerUserMenuSignout.click();
    await this.page.waitForURL('/auth/signin');
  }

  /**
   * Navigate via sidebar
   */
  async navigateViaSidebar(itemName: string) {
    const sidebarItem = this.page.getByTestId(`sidebar-nav-${itemName.toLowerCase().replace(/\s+/g, '-')}`);
    await sidebarItem.click();
  }

  /**
   * Check if header is visible
   */
  async isHeaderVisible() {
    return await this.header.isVisible();
  }

  /**
   * Check if sidebar is visible
   */
  async isSidebarVisible() {
    return await this.sidebar.isVisible();
  }

  /**
   * Check if footer is visible
   */
  async isFooterVisible() {
    return await this.footer.isVisible();
  }

  /**
   * Get active navigation item
   */
  async getActiveNavItem() {
    const activeItem = this.page.locator('[data-testid^="header-nav-"][aria-current="page"]');
    return await activeItem.textContent();
  }

  /**
   * Verify layout is loaded
   */
  async verifyLayoutLoaded() {
    await this.header.waitFor({ state: 'visible' });
    await this.footer.waitFor({ state: 'visible' });
  }
}

