import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Instance Creation Wizard
 */
export class InstanceWizardPage {
  readonly page: Page;
  
  // Wizard container
  readonly wizard: Locator;
  readonly stepIndicator: Locator;
  readonly stepContent: Locator;
  readonly stepTitle: Locator;
  readonly stepDescription: Locator;
  readonly navigation: Locator;
  readonly cancelButton: Locator;
  readonly stepCounter: Locator;
  
  // Step 1: Details
  readonly detailsForm: Locator;
  readonly nameInput: Locator;
  readonly baseUrlInput: Locator;
  readonly projectFilterInput: Locator;
  readonly detailsNextButton: Locator;
  
  // Step 2: Authentication
  readonly authForm: Locator;
  readonly authMethodSelect: Locator;
  readonly emailInput: Locator;
  readonly apiTokenInput: Locator;
  readonly apiTokenToggle: Locator;
  readonly authBackButton: Locator;
  readonly authNextButton: Locator;
  
  // Step 3: Validation
  readonly validateStep: Locator;
  readonly testConnectionButton: Locator;
  readonly testResult: Locator;
  readonly validateBackButton: Locator;
  readonly validateNextButton: Locator;
  
  // Step 4: Save
  readonly saveStep: Locator;
  readonly saveReview: Locator;
  readonly saveButton: Locator;
  readonly saveBackButton: Locator;

  constructor(page: Page) {
    this.page = page;
    
    // Wizard container
    this.wizard = page.getByTestId('instance-form-wizard');
    this.stepIndicator = page.getByTestId('wizard-step-indicator');
    this.stepContent = page.getByTestId('wizard-step-content');
    this.stepTitle = page.getByTestId('wizard-step-title');
    this.stepDescription = page.getByTestId('wizard-step-description');
    this.navigation = page.getByTestId('wizard-navigation');
    this.cancelButton = page.getByTestId('wizard-cancel-button');
    this.stepCounter = page.getByTestId('wizard-step-counter');
    
    // Step 1: Details
    this.detailsForm = page.getByTestId('instance-details-form');
    this.nameInput = page.getByTestId('instance-name-input');
    this.baseUrlInput = page.getByTestId('instance-base-url-input');
    this.projectFilterInput = page.getByTestId('instance-project-filter-input');
    this.detailsNextButton = page.getByTestId('instance-details-next-button');
    
    // Step 2: Authentication
    this.authForm = page.getByTestId('instance-auth-form');
    this.authMethodSelect = page.getByTestId('instance-auth-method-select');
    this.emailInput = page.getByTestId('instance-email-input');
    this.apiTokenInput = page.getByTestId('instance-api-token-input');
    this.apiTokenToggle = page.getByTestId('instance-api-token-toggle');
    this.authBackButton = page.getByTestId('instance-auth-back-button');
    this.authNextButton = page.getByTestId('instance-auth-next-button');
    
    // Step 3: Validation
    this.validateStep = page.getByTestId('instance-validate-step');
    this.testConnectionButton = page.getByTestId('instance-test-connection-button');
    this.testResult = page.getByTestId('instance-test-result');
    this.validateBackButton = page.getByTestId('instance-validate-back-button');
    this.validateNextButton = page.getByTestId('instance-validate-next-button');
    
    // Step 4: Save
    this.saveStep = page.getByTestId('instance-save-step');
    this.saveReview = page.getByTestId('instance-save-review');
    this.saveButton = page.getByTestId('instance-save-button');
    this.saveBackButton = page.getByTestId('instance-save-back-button');
  }

  /**
   * Navigate to wizard
   */
  async goto() {
    await this.page.goto('/admin/instances/new');
    await this.wizard.waitFor({ state: 'visible' });
  }

  /**
   * Fill instance details (Step 1)
   */
  async fillInstanceDetails(data: {
    name: string;
    baseUrl: string;
    projectFilter?: string;
  }) {
    await this.nameInput.fill(data.name);
    await this.baseUrlInput.fill(data.baseUrl);
    if (data.projectFilter) {
      await this.projectFilterInput.fill(data.projectFilter);
    }
  }

  /**
   * Click next on details step
   */
  async clickDetailsNext() {
    await this.detailsNextButton.click();
    await this.authForm.waitFor({ state: 'visible' });
  }

  /**
   * Complete details step
   */
  async completeDetailsStep(data: {
    name: string;
    baseUrl: string;
    projectFilter?: string;
  }) {
    await this.fillInstanceDetails(data);
    await this.clickDetailsNext();
  }

  /**
   * Fill authentication details (Step 2)
   */
  async fillAuthDetails(data: {
    email: string;
    apiToken: string;
    authMethod?: string;
  }) {
    if (data.authMethod) {
      await this.authMethodSelect.click();
      await this.page.getByTestId(`auth-method-${data.authMethod}`).click();
    }
    await this.emailInput.fill(data.email);
    await this.apiTokenInput.fill(data.apiToken);
  }

  /**
   * Toggle API token visibility
   */
  async toggleApiTokenVisibility() {
    await this.apiTokenToggle.click();
  }

  /**
   * Click next on auth step
   */
  async clickAuthNext() {
    await this.authNextButton.click();
    await this.validateStep.waitFor({ state: 'visible' });
  }

  /**
   * Click back on auth step
   */
  async clickAuthBack() {
    await this.authBackButton.click();
    await this.detailsForm.waitFor({ state: 'visible' });
  }

  /**
   * Complete auth step
   */
  async completeAuthStep(data: {
    email: string;
    apiToken: string;
    authMethod?: string;
  }) {
    await this.fillAuthDetails(data);
    await this.clickAuthNext();
  }

  /**
   * Test connection (Step 3)
   */
  async testConnection() {
    await this.testConnectionButton.click();
    await this.testResult.waitFor({ state: 'visible' });
  }

  /**
   * Wait for test success
   */
  async waitForTestSuccess() {
    await this.page.getByTestId('test-success-icon').waitFor({ state: 'visible' });
  }

  /**
   * Wait for test failure
   */
  async waitForTestFailure() {
    await this.page.getByTestId('test-failure-icon').waitFor({ state: 'visible' });
  }

  /**
   * Click next on validate step
   */
  async clickValidateNext() {
    await this.validateNextButton.click();
    await this.saveStep.waitFor({ state: 'visible' });
  }

  /**
   * Click back on validate step
   */
  async clickValidateBack() {
    await this.validateBackButton.click();
    await this.authForm.waitFor({ state: 'visible' });
  }

  /**
   * Complete validate step
   */
  async completeValidateStep() {
    await this.testConnection();
    await this.waitForTestSuccess();
    await this.clickValidateNext();
  }

  /**
   * Save instance (Step 4)
   */
  async saveInstance() {
    await this.saveButton.click();
  }

  /**
   * Wait for save success
   */
  async waitForSaveSuccess() {
    await this.page.getByTestId('instance-save-success').waitFor({ state: 'visible' });
  }

  /**
   * Click back on save step
   */
  async clickSaveBack() {
    await this.saveBackButton.click();
    await this.validateStep.waitFor({ state: 'visible' });
  }

  /**
   * Cancel wizard
   */
  async cancel() {
    await this.cancelButton.click();
  }

  /**
   * Get current step number
   */
  async getCurrentStep() {
    const text = await this.stepCounter.textContent();
    const match = text?.match(/Step (\d+) of (\d+)/);
    return match ? parseInt(match[1]) : 0;
  }

  /**
   * Get step status
   */
  async getStepStatus(stepId: string) {
    const step = this.page.getByTestId(`wizard-step-${stepId}`);
    return await step.getAttribute('data-step-status');
  }

  /**
   * Complete entire wizard
   */
  async completeWizard(data: {
    name: string;
    baseUrl: string;
    email: string;
    apiToken: string;
    projectFilter?: string;
  }) {
    await this.completeDetailsStep({
      name: data.name,
      baseUrl: data.baseUrl,
      projectFilter: data.projectFilter,
    });
    
    await this.completeAuthStep({
      email: data.email,
      apiToken: data.apiToken,
    });
    
    await this.completeValidateStep();
    
    await this.saveInstance();
    await this.waitForSaveSuccess();
  }

  /**
   * Verify wizard is loaded
   */
  async verifyWizardLoaded() {
    await this.wizard.waitFor({ state: 'visible' });
    await this.stepIndicator.waitFor({ state: 'visible' });
  }
}

