import { Page } from '@playwright/test';
import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * Generated test case
 */
export interface GeneratedTest {
  name: string;
  description: string;
  code: string;
  confidence: number;
  category: 'navigation' | 'form' | 'interaction' | 'validation' | 'accessibility';
  priority: 'high' | 'medium' | 'low';
}

/**
 * Page analysis result
 */
export interface PageAnalysis {
  url: string;
  title: string;
  elements: ElementInfo[];
  forms: FormInfo[];
  links: LinkInfo[];
  buttons: ButtonInfo[];
  inputs: InputInfo[];
  suggestedTests: GeneratedTest[];
}

/**
 * Element information
 */
interface ElementInfo {
  tag: string;
  testId?: string;
  role?: string;
  ariaLabel?: string;
  text?: string;
  type?: string;
}

/**
 * Form information
 */
interface FormInfo {
  testId?: string;
  action?: string;
  method?: string;
  inputs: InputInfo[];
}

/**
 * Link information
 */
interface LinkInfo {
  testId?: string;
  href: string;
  text: string;
  ariaLabel?: string;
}

/**
 * Button information
 */
interface ButtonInfo {
  testId?: string;
  text: string;
  type?: string;
  ariaLabel?: string;
}

/**
 * Input information
 */
interface InputInfo {
  testId?: string;
  name?: string;
  type: string;
  placeholder?: string;
  required?: boolean;
  ariaLabel?: string;
}

/**
 * Test Generation Engine
 * Automatically generates test cases from UI analysis
 */
export class TestGenerationEngine {
  private outputDir: string;

  constructor(options?: { outputDir?: string }) {
    this.outputDir = options?.outputDir || path.join(process.cwd(), 'tests', 'generated');
  }

  /**
   * Analyze page and generate tests
   */
  async analyzePage(page: Page): Promise<PageAnalysis> {
    const url = page.url();
    const title = await page.title();

    // Analyze page elements
    const elements = await this.analyzeElements(page);
    const forms = await this.analyzeForms(page);
    const links = await this.analyzeLinks(page);
    const buttons = await this.analyzeButtons(page);
    const inputs = await this.analyzeInputs(page);

    // Generate test suggestions
    const suggestedTests = this.generateTestSuggestions({
      url,
      title,
      elements,
      forms,
      links,
      buttons,
      inputs,
      suggestedTests: [],
    });

    return {
      url,
      title,
      elements,
      forms,
      links,
      buttons,
      inputs,
      suggestedTests,
    };
  }

  /**
   * Analyze page elements
   */
  private async analyzeElements(page: Page): Promise<ElementInfo[]> {
    return await page.evaluate(() => {
      const elements: ElementInfo[] = [];
      const allElements = document.querySelectorAll('[data-testid]');

      allElements.forEach((el) => {
        elements.push({
          tag: el.tagName.toLowerCase(),
          testId: el.getAttribute('data-testid') || undefined,
          role: el.getAttribute('role') || undefined,
          ariaLabel: el.getAttribute('aria-label') || undefined,
          text: el.textContent?.substring(0, 50) || undefined,
          type: el.getAttribute('type') || undefined,
        });
      });

      return elements;
    });
  }

  /**
   * Analyze forms
   */
  private async analyzeForms(page: Page): Promise<FormInfo[]> {
    return await page.evaluate(() => {
      const forms: FormInfo[] = [];
      const formElements = document.querySelectorAll('form');

      formElements.forEach((form) => {
        const inputs: InputInfo[] = [];
        const inputElements = form.querySelectorAll('input, textarea, select');

        inputElements.forEach((input) => {
          inputs.push({
            testId: input.getAttribute('data-testid') || undefined,
            name: input.getAttribute('name') || undefined,
            type: input.getAttribute('type') || 'text',
            placeholder: input.getAttribute('placeholder') || undefined,
            required: input.hasAttribute('required'),
            ariaLabel: input.getAttribute('aria-label') || undefined,
          });
        });

        forms.push({
          testId: form.getAttribute('data-testid') || undefined,
          action: form.getAttribute('action') || undefined,
          method: form.getAttribute('method') || undefined,
          inputs,
        });
      });

      return forms;
    });
  }

  /**
   * Analyze links
   */
  private async analyzeLinks(page: Page): Promise<LinkInfo[]> {
    return await page.evaluate(() => {
      const links: LinkInfo[] = [];
      const linkElements = document.querySelectorAll('a[href]');

      linkElements.forEach((link) => {
        links.push({
          testId: link.getAttribute('data-testid') || undefined,
          href: link.getAttribute('href') || '',
          text: link.textContent?.trim() || '',
          ariaLabel: link.getAttribute('aria-label') || undefined,
        });
      });

      return links;
    });
  }

  /**
   * Analyze buttons
   */
  private async analyzeButtons(page: Page): Promise<ButtonInfo[]> {
    return await page.evaluate(() => {
      const buttons: ButtonInfo[] = [];
      const buttonElements = document.querySelectorAll('button, [role="button"]');

      buttonElements.forEach((button) => {
        buttons.push({
          testId: button.getAttribute('data-testid') || undefined,
          text: button.textContent?.trim() || '',
          type: button.getAttribute('type') || undefined,
          ariaLabel: button.getAttribute('aria-label') || undefined,
        });
      });

      return buttons;
    });
  }

  /**
   * Analyze inputs
   */
  private async analyzeInputs(page: Page): Promise<InputInfo[]> {
    return await page.evaluate(() => {
      const inputs: InputInfo[] = [];
      const inputElements = document.querySelectorAll('input, textarea, select');

      inputElements.forEach((input) => {
        inputs.push({
          testId: input.getAttribute('data-testid') || undefined,
          name: input.getAttribute('name') || undefined,
          type: input.getAttribute('type') || 'text',
          placeholder: input.getAttribute('placeholder') || undefined,
          required: input.hasAttribute('required'),
          ariaLabel: input.getAttribute('aria-label') || undefined,
        });
      });

      return inputs;
    });
  }

  /**
   * Generate test suggestions
   */
  private generateTestSuggestions(analysis: PageAnalysis): GeneratedTest[] {
    const tests: GeneratedTest[] = [];

    // Generate navigation tests
    tests.push(...this.generateNavigationTests(analysis));

    // Generate form tests
    tests.push(...this.generateFormTests(analysis));

    // Generate interaction tests
    tests.push(...this.generateInteractionTests(analysis));

    // Generate accessibility tests
    tests.push(...this.generateAccessibilityTests(analysis));

    return tests.sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
  }

  /**
   * Generate navigation tests
   */
  private generateNavigationTests(analysis: PageAnalysis): GeneratedTest[] {
    const tests: GeneratedTest[] = [];

    for (const link of analysis.links) {
      if (link.testId) {
        tests.push({
          name: `should navigate via ${link.text || link.testId}`,
          description: `Test navigation to ${link.href}`,
          code: this.generateNavigationTestCode(link),
          confidence: 0.9,
          category: 'navigation',
          priority: 'high',
        });
      }
    }

    return tests;
  }

  /**
   * Generate form tests
   */
  private generateFormTests(analysis: PageAnalysis): GeneratedTest[] {
    const tests: GeneratedTest[] = [];

    for (const form of analysis.forms) {
      if (form.testId) {
        tests.push({
          name: `should submit ${form.testId} form`,
          description: 'Test form submission with valid data',
          code: this.generateFormTestCode(form),
          confidence: 0.85,
          category: 'form',
          priority: 'high',
        });

        // Validation tests
        const requiredInputs = form.inputs.filter(i => i.required);
        if (requiredInputs.length > 0) {
          tests.push({
            name: `should validate ${form.testId} required fields`,
            description: 'Test form validation for required fields',
            code: this.generateValidationTestCode(form),
            confidence: 0.8,
            category: 'validation',
            priority: 'medium',
          });
        }
      }
    }

    return tests;
  }

  /**
   * Generate interaction tests
   */
  private generateInteractionTests(analysis: PageAnalysis): GeneratedTest[] {
    const tests: GeneratedTest[] = [];

    for (const button of analysis.buttons) {
      if (button.testId) {
        tests.push({
          name: `should click ${button.text || button.testId}`,
          description: `Test clicking ${button.text || button.testId} button`,
          code: this.generateButtonTestCode(button),
          confidence: 0.75,
          category: 'interaction',
          priority: 'medium',
        });
      }
    }

    return tests;
  }

  /**
   * Generate accessibility tests
   */
  private generateAccessibilityTests(analysis: PageAnalysis): GeneratedTest[] {
    const tests: GeneratedTest[] = [];

    // Check for elements without aria-label
    const elementsWithoutLabel = analysis.buttons.filter(b => !b.ariaLabel);
    
    if (elementsWithoutLabel.length > 0) {
      tests.push({
        name: 'should have accessible buttons',
        description: 'Verify all buttons have aria-label',
        code: this.generateAccessibilityTestCode(),
        confidence: 0.9,
        category: 'accessibility',
        priority: 'high',
      });
    }

    return tests;
  }

  /**
   * Generate navigation test code
   */
  private generateNavigationTestCode(link: LinkInfo): string {
    return `
test('should navigate via ${link.text || link.testId}', async ({ page }) => {
  await page.getByTestId('${link.testId}').click();
  await expect(page).toHaveURL('${link.href}');
});
`.trim();
  }

  /**
   * Generate form test code
   */
  private generateFormTestCode(form: FormInfo): string {
    const fillStatements = form.inputs
      .filter(i => i.testId)
      .map(i => `  await page.getByTestId('${i.testId}').fill('test-value');`)
      .join('\n');

    return `
test('should submit ${form.testId} form', async ({ page }) => {
${fillStatements}
  await page.getByTestId('${form.testId}').locator('button[type="submit"]').click();
  // Add assertion for success
});
`.trim();
  }

  /**
   * Generate validation test code
   */
  private generateValidationTestCode(form: FormInfo): string {
    return `
test('should validate ${form.testId} required fields', async ({ page }) => {
  await page.getByTestId('${form.testId}').locator('button[type="submit"]').click();
  // Should show validation errors
  await expect(page.locator('[role="alert"]')).toBeVisible();
});
`.trim();
  }

  /**
   * Generate button test code
   */
  private generateButtonTestCode(button: ButtonInfo): string {
    return `
test('should click ${button.text || button.testId}', async ({ page }) => {
  await page.getByTestId('${button.testId}').click();
  // Add assertion for expected behavior
});
`.trim();
  }

  /**
   * Generate accessibility test code
   */
  private generateAccessibilityTestCode(): string {
    return `
test('should have accessible buttons', async ({ page }) => {
  const buttons = await page.locator('button').all();
  for (const button of buttons) {
    await expect(button).toHaveAttribute('aria-label');
  }
});
`.trim();
  }

  /**
   * Save generated tests to file
   */
  async saveTests(analysis: PageAnalysis, filename: string): Promise<string> {
    await fs.mkdir(this.outputDir, { recursive: true });

    const filePath = path.join(this.outputDir, filename);
    const content = this.generateTestFile(analysis);

    await fs.writeFile(filePath, content);

    return filePath;
  }

  /**
   * Generate complete test file
   */
  private generateTestFile(analysis: PageAnalysis): string {
    const imports = `import { test, expect } from '@playwright/test';`;
    
    const tests = analysis.suggestedTests
      .map(t => `\n// ${t.description}\n// Confidence: ${(t.confidence * 100).toFixed(0)}%\n// Priority: ${t.priority}\n${t.code}`)
      .join('\n\n');

    return `${imports}\n\ntest.describe('${analysis.title}', () => {${tests}\n});\n`;
  }
}

