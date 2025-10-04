import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Instances page
 */
export class InstancesPage {
  readonly page: Page;
  
  // Page elements
  readonly pageContainer: Locator;
  readonly pageHeader: Locator;
  readonly pageTitle: Locator;
  readonly pageDescription: Locator;
  readonly addButton: Locator;
  
  // Table elements
  readonly table: Locator;
  readonly tableHeader: Locator;
  readonly tableBody: Locator;
  readonly emptyState: Locator;
  readonly emptyMessage: Locator;
  readonly emptyAddButton: Locator;
  
  // Error state
  readonly errorAlert: Locator;
  readonly errorMessage: Locator;
  readonly errorRetryButton: Locator;

  constructor(page: Page) {
    this.page = page;
    
    // Page elements
    this.pageContainer = page.getByTestId('instances-page');
    this.pageHeader = page.getByTestId('instances-page-header');
    this.pageTitle = page.getByTestId('instances-page-title');
    this.pageDescription = page.getByTestId('instances-page-description');
    this.addButton = page.getByTestId('instances-add-button');
    
    // Table elements
    this.table = page.getByTestId('instances-table');
    this.tableHeader = page.getByTestId('instances-table-header');
    this.tableBody = page.getByTestId('instances-table-body');
    this.emptyState = page.getByTestId('instances-empty-state');
    this.emptyMessage = page.getByTestId('instances-empty-message');
    this.emptyAddButton = page.getByTestId('instances-empty-add-button');
    
    // Error state
    this.errorAlert = page.getByTestId('instances-error-alert');
    this.errorMessage = page.getByTestId('instances-error-message');
    this.errorRetryButton = page.getByTestId('instances-error-retry-button');
  }

  /**
   * Navigate to instances page
   */
  async goto() {
    await this.page.goto('/admin/instances');
    await this.pageContainer.waitFor({ state: 'visible' });
  }

  /**
   * Click add instance button
   */
  async clickAddInstance() {
    await this.addButton.click();
    await this.page.waitForURL('/admin/instances/new');
  }

  /**
   * Click add instance button in empty state
   */
  async clickEmptyAddInstance() {
    await this.emptyAddButton.click();
    await this.page.waitForURL('/admin/instances/new');
  }

  /**
   * Get instance row by ID
   */
  getInstanceRow(instanceId: string) {
    return this.page.getByTestId(`instance-row-${instanceId}`);
  }

  /**
   * Get instance name by ID
   */
  getInstanceName(instanceId: string) {
    return this.page.getByTestId(`instance-name-${instanceId}`);
  }

  /**
   * Get instance URL by ID
   */
  getInstanceUrl(instanceId: string) {
    return this.page.getByTestId(`instance-url-${instanceId}`);
  }

  /**
   * Get instance status by ID
   */
  getInstanceStatus(instanceId: string) {
    return this.page.getByTestId(`instance-status-${instanceId}`);
  }

  /**
   * Get instance actions menu by ID
   */
  getInstanceActionsMenu(instanceId: string) {
    return this.page.getByTestId(`instance-actions-menu-${instanceId}`);
  }

  /**
   * Open instance actions menu
   */
  async openInstanceActions(instanceId: string) {
    await this.getInstanceActionsMenu(instanceId).click();
  }

  /**
   * Click edit action for instance
   */
  async clickEditInstance(instanceId: string) {
    await this.openInstanceActions(instanceId);
    await this.page.getByTestId(`instance-action-edit-${instanceId}`).click();
    await this.page.waitForURL(`/admin/instances/${instanceId}/edit`);
  }

  /**
   * Click test connection action for instance
   */
  async clickTestConnection(instanceId: string) {
    await this.openInstanceActions(instanceId);
    await this.page.getByTestId(`instance-action-test-${instanceId}`).click();
  }

  /**
   * Click delete action for instance
   */
  async clickDeleteInstance(instanceId: string) {
    await this.openInstanceActions(instanceId);
    await this.page.getByTestId(`instance-action-delete-${instanceId}`).click();
  }

  /**
   * Click instance name to view details
   */
  async clickInstanceName(instanceId: string) {
    await this.page.getByTestId(`instance-name-link-${instanceId}`).click();
    await this.page.waitForURL(`/admin/instances/${instanceId}`);
  }

  /**
   * Check if table is visible
   */
  async isTableVisible() {
    return await this.table.isVisible();
  }

  /**
   * Check if empty state is visible
   */
  async isEmptyStateVisible() {
    return await this.emptyState.isVisible();
  }

  /**
   * Check if error state is visible
   */
  async isErrorStateVisible() {
    return await this.errorAlert.isVisible();
  }

  /**
   * Get number of instances in table
   */
  async getInstanceCount() {
    const rows = await this.page.locator('[data-testid^="instance-row-"]').count();
    return rows;
  }

  /**
   * Get all instance IDs from table
   */
  async getAllInstanceIds() {
    const rows = await this.page.locator('[data-testid^="instance-row-"]').all();
    const ids = await Promise.all(
      rows.map(async (row) => {
        const testId = await row.getAttribute('data-testid');
        return testId?.replace('instance-row-', '') || '';
      })
    );
    return ids.filter(Boolean);
  }

  /**
   * Wait for instances to load
   */
  async waitForInstancesLoad() {
    // Wait for either table or empty state to be visible
    await Promise.race([
      this.table.waitFor({ state: 'visible' }),
      this.emptyState.waitFor({ state: 'visible' }),
    ]);
  }

  /**
   * Retry loading instances after error
   */
  async retryLoadInstances() {
    await this.errorRetryButton.click();
    await this.waitForInstancesLoad();
  }

  /**
   * Get instance status badge text
   */
  async getInstanceStatusText(instanceId: string) {
    const statusBadge = this.getInstanceStatus(instanceId);
    return await statusBadge.textContent();
  }

  /**
   * Verify page is loaded
   */
  async verifyPageLoaded() {
    await this.pageContainer.waitFor({ state: 'visible' });
    await this.pageTitle.waitFor({ state: 'visible' });
  }
}

