import { test as base, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

/**
 * Extended test fixtures with custom utilities
 */
export const test = base.extend({
  /**
   * Automatically inject axe-core for accessibility testing
   */
  page: async ({ page }, use) => {
    // Inject axe-core on every page
    await injectAxe(page);
    await use(page);
  },
});

/**
 * Custom expect matchers
 */
export { expect };

/**
 * Helper to check accessibility
 */
export async function checkAccessibility(page: any, options?: any) {
  await checkA11y(page, undefined, {
    detailedReport: true,
    detailedReportOptions: {
      html: true,
    },
    ...options,
  });
}

/**
 * Helper to wait for network idle
 */
export async function waitForNetworkIdle(page: any, timeout = 5000) {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Helper to take screenshot with timestamp
 */
export async function takeScreenshot(page: any, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({
    path: `test-results/screenshots/${name}-${timestamp}.png`,
    fullPage: true,
  });
}

/**
 * Helper to get element by test ID
 */
export function getByTestId(page: any, testId: string) {
  return page.locator(`[data-testid="${testId}"]`);
}

/**
 * Helper to wait for element by test ID
 */
export async function waitForTestId(page: any, testId: string, options?: any) {
  return await getByTestId(page, testId).waitFor(options);
}

/**
 * Helper to click element by test ID
 */
export async function clickByTestId(page: any, testId: string) {
  await getByTestId(page, testId).click();
}

/**
 * Helper to fill input by test ID
 */
export async function fillByTestId(page: any, testId: string, value: string) {
  await getByTestId(page, testId).fill(value);
}

/**
 * Helper to check if element is visible by test ID
 */
export async function isVisibleByTestId(page: any, testId: string) {
  return await getByTestId(page, testId).isVisible();
}

/**
 * Helper to get text content by test ID
 */
export async function getTextByTestId(page: any, testId: string) {
  return await getByTestId(page, testId).textContent();
}

/**
 * Helper to wait for API response
 */
export async function waitForApiResponse(
  page: any,
  urlPattern: string | RegExp,
  callback: () => Promise<void>
) {
  const responsePromise = page.waitForResponse(urlPattern);
  await callback();
  return await responsePromise;
}

/**
 * Helper to mock API response
 */
export async function mockApiResponse(
  page: any,
  urlPattern: string | RegExp,
  response: any
) {
  await page.route(urlPattern, (route: any) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Helper to login (mock authentication)
 */
export async function login(page: any, credentials?: { email: string; password: string }) {
  // TODO: Implement actual login flow
  // For now, we'll mock the session
  await page.goto('/auth/signin');
  
  if (credentials) {
    await fillByTestId(page, 'email-input', credentials.email);
    await fillByTestId(page, 'password-input', credentials.password);
    await clickByTestId(page, 'signin-button');
  }
  
  await page.waitForURL('/admin/instances');
}

/**
 * Helper to logout
 */
export async function logout(page: any) {
  await clickByTestId(page, 'header-user-menu');
  await clickByTestId(page, 'header-user-menu-signout');
  await page.waitForURL('/auth/signin');
}

/**
 * Test data generators
 */
export const testData = {
  instance: {
    valid: {
      name: 'Test Instance',
      baseUrl: 'https://test.atlassian.net',
      email: 'test@example.com',
      apiToken: 'test-api-token-123',
      authMethod: 'api_token',
    },
    invalid: {
      name: '',
      baseUrl: 'invalid-url',
      email: 'invalid-email',
      apiToken: '',
    },
  },
  
  user: {
    admin: {
      email: 'admin@example.com',
      password: 'admin123',
    },
    regular: {
      email: 'user@example.com',
      password: 'user123',
    },
  },
};

/**
 * Custom assertions
 */
export const customExpect = {
  /**
   * Assert element is visible by test ID
   */
  async toBeVisibleByTestId(page: any, testId: string) {
    const element = getByTestId(page, testId);
    await expect(element).toBeVisible();
  },
  
  /**
   * Assert element has text by test ID
   */
  async toHaveTextByTestId(page: any, testId: string, text: string | RegExp) {
    const element = getByTestId(page, testId);
    await expect(element).toHaveText(text);
  },
  
  /**
   * Assert element is enabled by test ID
   */
  async toBeEnabledByTestId(page: any, testId: string) {
    const element = getByTestId(page, testId);
    await expect(element).toBeEnabled();
  },
  
  /**
   * Assert element is disabled by test ID
   */
  async toBeDisabledByTestId(page: any, testId: string) {
    const element = getByTestId(page, testId);
    await expect(element).toBeDisabled();
  },
};

