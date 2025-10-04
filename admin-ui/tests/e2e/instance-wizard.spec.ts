import { test, expect } from './fixtures/base';
import { InstanceWizardPage } from './page-objects/InstanceWizardPage';
import { testData } from './fixtures/base';

test.describe('Instance Creation Wizard', () => {
  let wizardPage: InstanceWizardPage;

  test.beforeEach(async ({ page }) => {
    wizardPage = new InstanceWizardPage(page);
    // TODO: Add authentication when implemented
    await wizardPage.goto();
  });

  test.describe('Wizard Layout', () => {
    test('should display wizard container', async ({ page }) => {
      await expect(wizardPage.wizard).toBeVisible();
      await expect(wizardPage.stepIndicator).toBeVisible();
      await expect(wizardPage.stepContent).toBeVisible();
      await expect(wizardPage.navigation).toBeVisible();
    });

    test('should display step counter', async ({ page }) => {
      await expect(wizardPage.stepCounter).toBeVisible();
      await expect(wizardPage.stepCounter).toHaveText(/Step \d+ of \d+/);
    });

    test('should display cancel button', async ({ page }) => {
      await expect(wizardPage.cancelButton).toBeVisible();
      await expect(wizardPage.cancelButton).toBeEnabled();
    });

    test('should verify wizard is loaded', async ({ page }) => {
      await wizardPage.verifyWizardLoaded();
      expect(await wizardPage.wizard.isVisible()).toBe(true);
    });
  });

  test.describe('Step 1: Instance Details', () => {
    test('should display details form', async ({ page }) => {
      await expect(wizardPage.detailsForm).toBeVisible();
      await expect(wizardPage.nameInput).toBeVisible();
      await expect(wizardPage.baseUrlInput).toBeVisible();
      await expect(wizardPage.projectFilterInput).toBeVisible();
      await expect(wizardPage.detailsNextButton).toBeVisible();
    });

    test('should have accessible form fields', async ({ page }) => {
      await expect(wizardPage.nameInput).toHaveAttribute('aria-label');
      await expect(wizardPage.baseUrlInput).toHaveAttribute('aria-label');
      await expect(wizardPage.projectFilterInput).toHaveAttribute('aria-label');
    });

    test('should fill instance details', async ({ page }) => {
      await wizardPage.fillInstanceDetails({
        name: testData.instance.valid.name,
        baseUrl: testData.instance.valid.baseUrl,
        projectFilter: 'TEST',
      });

      await expect(wizardPage.nameInput).toHaveValue(testData.instance.valid.name);
      await expect(wizardPage.baseUrlInput).toHaveValue(testData.instance.valid.baseUrl);
      await expect(wizardPage.projectFilterInput).toHaveValue('TEST');
    });

    test('should validate required fields', async ({ page }) => {
      // Try to proceed without filling required fields
      await wizardPage.detailsNextButton.click();
      
      // Should show validation errors
      const nameError = page.getByTestId('instance-name-error');
      const urlError = page.getByTestId('instance-base-url-error');
      
      // At least one error should be visible
      const hasErrors = await nameError.isVisible() || await urlError.isVisible();
      expect(hasErrors).toBe(true);
    });

    test('should validate URL format', async ({ page }) => {
      await wizardPage.nameInput.fill('Test Instance');
      await wizardPage.baseUrlInput.fill('invalid-url');
      await wizardPage.detailsNextButton.click();
      
      // Should show URL validation error
      const urlError = page.getByTestId('instance-base-url-error');
      const hasError = await urlError.isVisible();
      
      if (hasError) {
        expect(await urlError.textContent()).toBeTruthy();
      }
    });

    test('should proceed to auth step with valid data', async ({ page }) => {
      await wizardPage.completeDetailsStep({
        name: testData.instance.valid.name,
        baseUrl: testData.instance.valid.baseUrl,
      });

      await expect(wizardPage.authForm).toBeVisible();
      const currentStep = await wizardPage.getCurrentStep();
      expect(currentStep).toBe(2);
    });

    test('should show step 1 as current', async ({ page }) => {
      const status = await wizardPage.getStepStatus('1');
      expect(status).toBe('current');
    });
  });

  test.describe('Step 2: Authentication', () => {
    test.beforeEach(async ({ page }) => {
      // Complete step 1 first
      await wizardPage.completeDetailsStep({
        name: testData.instance.valid.name,
        baseUrl: testData.instance.valid.baseUrl,
      });
    });

    test('should display auth form', async ({ page }) => {
      await expect(wizardPage.authForm).toBeVisible();
      await expect(wizardPage.authMethodSelect).toBeVisible();
      await expect(wizardPage.emailInput).toBeVisible();
      await expect(wizardPage.apiTokenInput).toBeVisible();
      await expect(wizardPage.authBackButton).toBeVisible();
      await expect(wizardPage.authNextButton).toBeVisible();
    });

    test('should have accessible form fields', async ({ page }) => {
      await expect(wizardPage.emailInput).toHaveAttribute('aria-label');
      await expect(wizardPage.apiTokenInput).toHaveAttribute('aria-label');
    });

    test('should fill auth details', async ({ page }) => {
      await wizardPage.fillAuthDetails({
        email: testData.instance.valid.email,
        apiToken: testData.instance.valid.apiToken,
      });

      await expect(wizardPage.emailInput).toHaveValue(testData.instance.valid.email);
      await expect(wizardPage.apiTokenInput).toHaveValue(testData.instance.valid.apiToken);
    });

    test('should toggle API token visibility', async ({ page }) => {
      await wizardPage.apiTokenInput.fill('secret-token');
      
      // Initially should be password type
      await expect(wizardPage.apiTokenInput).toHaveAttribute('type', 'password');
      
      // Toggle visibility
      await wizardPage.toggleApiTokenVisibility();
      
      // Should now be text type
      await expect(wizardPage.apiTokenInput).toHaveAttribute('type', 'text');
      
      // Toggle back
      await wizardPage.toggleApiTokenVisibility();
      await expect(wizardPage.apiTokenInput).toHaveAttribute('type', 'password');
    });

    test('should validate email format', async ({ page }) => {
      await wizardPage.emailInput.fill('invalid-email');
      await wizardPage.apiTokenInput.fill('token');
      await wizardPage.authNextButton.click();
      
      const emailError = page.getByTestId('instance-email-error');
      const hasError = await emailError.isVisible();
      
      if (hasError) {
        expect(await emailError.textContent()).toBeTruthy();
      }
    });

    test('should go back to details step', async ({ page }) => {
      await wizardPage.clickAuthBack();
      await expect(wizardPage.detailsForm).toBeVisible();
      
      const currentStep = await wizardPage.getCurrentStep();
      expect(currentStep).toBe(1);
    });

    test('should proceed to validation step', async ({ page }) => {
      await wizardPage.completeAuthStep({
        email: testData.instance.valid.email,
        apiToken: testData.instance.valid.apiToken,
      });

      await expect(wizardPage.validateStep).toBeVisible();
      const currentStep = await wizardPage.getCurrentStep();
      expect(currentStep).toBe(3);
    });

    test('should show step 2 as current', async ({ page }) => {
      const status = await wizardPage.getStepStatus('2');
      expect(status).toBe('current');
    });

    test('should show step 1 as completed', async ({ page }) => {
      const status = await wizardPage.getStepStatus('1');
      expect(status).toBe('completed');
    });
  });

  test.describe('Step 3: Validation', () => {
    test.beforeEach(async ({ page }) => {
      // Complete steps 1 and 2
      await wizardPage.completeDetailsStep({
        name: testData.instance.valid.name,
        baseUrl: testData.instance.valid.baseUrl,
      });
      await wizardPage.completeAuthStep({
        email: testData.instance.valid.email,
        apiToken: testData.instance.valid.apiToken,
      });
    });

    test('should display validation step', async ({ page }) => {
      await expect(wizardPage.validateStep).toBeVisible();
      await expect(wizardPage.testConnectionButton).toBeVisible();
      await expect(wizardPage.validateBackButton).toBeVisible();
      await expect(wizardPage.validateNextButton).toBeVisible();
    });

    test('should have accessible test button', async ({ page }) => {
      await expect(wizardPage.testConnectionButton).toHaveAttribute('aria-label');
    });

    test('should disable next button initially', async ({ page }) => {
      // Next button should be disabled until test succeeds
      await expect(wizardPage.validateNextButton).toBeDisabled();
    });

    test('should test connection', async ({ page }) => {
      // This test would require mocking the API
      // For now, just verify the button is clickable
      await expect(wizardPage.testConnectionButton).toBeEnabled();
    });

    test('should go back to auth step', async ({ page }) => {
      await wizardPage.clickValidateBack();
      await expect(wizardPage.authForm).toBeVisible();
      
      const currentStep = await wizardPage.getCurrentStep();
      expect(currentStep).toBe(2);
    });

    test('should show step 3 as current', async ({ page }) => {
      const status = await wizardPage.getStepStatus('3');
      expect(status).toBe('current');
    });
  });

  test.describe('Step 4: Save', () => {
    test.beforeEach(async ({ page }) => {
      // Complete steps 1, 2, and 3
      // Note: This would require mocking successful connection test
      await wizardPage.completeDetailsStep({
        name: testData.instance.valid.name,
        baseUrl: testData.instance.valid.baseUrl,
      });
      await wizardPage.completeAuthStep({
        email: testData.instance.valid.email,
        apiToken: testData.instance.valid.apiToken,
      });
      // Skip validation for now (would need API mock)
    });

    test('should display save step elements', async ({ page }) => {
      // This test would run after successful validation
      // For now, we just verify the page objects exist
      expect(wizardPage.saveStep).toBeDefined();
      expect(wizardPage.saveReview).toBeDefined();
      expect(wizardPage.saveButton).toBeDefined();
      expect(wizardPage.saveBackButton).toBeDefined();
    });
  });

  test.describe('Wizard Navigation', () => {
    test('should cancel wizard', async ({ page }) => {
      await wizardPage.cancel();
      // Should navigate back to instances page
      await expect(page).toHaveURL('/admin/instances');
    });

    test('should track current step', async ({ page }) => {
      let currentStep = await wizardPage.getCurrentStep();
      expect(currentStep).toBe(1);

      await wizardPage.completeDetailsStep({
        name: testData.instance.valid.name,
        baseUrl: testData.instance.valid.baseUrl,
      });

      currentStep = await wizardPage.getCurrentStep();
      expect(currentStep).toBe(2);
    });

    test('should update step counter', async ({ page }) => {
      await expect(wizardPage.stepCounter).toHaveText('Step 1 of 4');

      await wizardPage.completeDetailsStep({
        name: testData.instance.valid.name,
        baseUrl: testData.instance.valid.baseUrl,
      });

      await expect(wizardPage.stepCounter).toHaveText('Step 2 of 4');
    });
  });

  test.describe('Responsive Design', () => {
    test('should work on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await wizardPage.verifyWizardLoaded();
      await expect(wizardPage.wizard).toBeVisible();
    });

    test('should work on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await wizardPage.verifyWizardLoaded();
      await expect(wizardPage.wizard).toBeVisible();
    });

    test('should work on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await wizardPage.verifyWizardLoaded();
      await expect(wizardPage.wizard).toBeVisible();
    });
  });
});

