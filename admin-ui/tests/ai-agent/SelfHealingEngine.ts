import { Page, Locator } from '@playwright/test';
import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * Selector suggestion with confidence score
 */
export interface SelectorSuggestion {
  selector: string;
  type: 'testid' | 'role' | 'label' | 'text' | 'css';
  confidence: number; // 0-1
  reason: string;
  element?: {
    tag: string;
    text?: string;
    attributes: Record<string, string>;
  };
}

/**
 * Healing result
 */
export interface HealingResult {
  originalSelector: string;
  healed: boolean;
  suggestions: SelectorSuggestion[];
  selectedSuggestion?: SelectorSuggestion;
  reason: string;
}

/**
 * Selector mapping for tracking changes
 */
interface SelectorMapping {
  testFile: string;
  testName: string;
  originalSelector: string;
  healedSelector: string;
  timestamp: number;
  confidence: number;
}

/**
 * Self-Healing Engine
 * Automatically detects UI changes and suggests/applies selector fixes
 */
export class SelfHealingEngine {
  private mappingsFile: string;
  private mappings: SelectorMapping[] = [];
  private healingEnabled: boolean = true;
  private autoApply: boolean = false;
  private confidenceThreshold: number = 0.8;

  constructor(options?: {
    healingEnabled?: boolean;
    autoApply?: boolean;
    confidenceThreshold?: number;
  }) {
    this.mappingsFile = path.join(process.cwd(), 'test-results', 'selector-mappings.json');
    this.healingEnabled = options?.healingEnabled ?? true;
    this.autoApply = options?.autoApply ?? false;
    this.confidenceThreshold = options?.confidenceThreshold ?? 0.8;
  }

  /**
   * Initialize healing engine
   */
  async initialize(): Promise<void> {
    await this.loadMappings();
  }

  /**
   * Attempt to heal a broken selector
   */
  async healSelector(
    page: Page,
    selector: string,
    context?: {
      testFile?: string;
      testName?: string;
    }
  ): Promise<HealingResult> {
    if (!this.healingEnabled) {
      return {
        originalSelector: selector,
        healed: false,
        suggestions: [],
        reason: 'Self-healing is disabled',
      };
    }

    // Try to find element with original selector
    const originalElement = await this.trySelector(page, selector);
    
    if (originalElement) {
      return {
        originalSelector: selector,
        healed: false,
        suggestions: [],
        reason: 'Original selector still works',
      };
    }

    // Check if we have a known mapping
    const knownMapping = this.findMapping(selector, context);
    if (knownMapping) {
      const mappedElement = await this.trySelector(page, knownMapping.healedSelector);
      if (mappedElement) {
        return {
          originalSelector: selector,
          healed: true,
          suggestions: [{
            selector: knownMapping.healedSelector,
            type: this.detectSelectorType(knownMapping.healedSelector),
            confidence: knownMapping.confidence,
            reason: 'Previously healed selector',
          }],
          selectedSuggestion: {
            selector: knownMapping.healedSelector,
            type: this.detectSelectorType(knownMapping.healedSelector),
            confidence: knownMapping.confidence,
            reason: 'Previously healed selector',
          },
          reason: 'Used known mapping',
        };
      }
    }

    // Generate new suggestions
    const suggestions = await this.generateSuggestions(page, selector);

    if (suggestions.length === 0) {
      return {
        originalSelector: selector,
        healed: false,
        suggestions: [],
        reason: 'No alternative selectors found',
      };
    }

    // Select best suggestion
    const bestSuggestion = suggestions[0];

    // Auto-apply if enabled and confidence is high
    if (this.autoApply && bestSuggestion.confidence >= this.confidenceThreshold) {
      await this.saveMapping({
        testFile: context?.testFile || 'unknown',
        testName: context?.testName || 'unknown',
        originalSelector: selector,
        healedSelector: bestSuggestion.selector,
        timestamp: Date.now(),
        confidence: bestSuggestion.confidence,
      });

      return {
        originalSelector: selector,
        healed: true,
        suggestions,
        selectedSuggestion: bestSuggestion,
        reason: 'Auto-applied high-confidence suggestion',
      };
    }

    return {
      originalSelector: selector,
      healed: false,
      suggestions,
      reason: 'Suggestions available, manual approval required',
    };
  }

  /**
   * Generate selector suggestions
   */
  private async generateSuggestions(
    page: Page,
    originalSelector: string
  ): Promise<SelectorSuggestion[]> {
    const suggestions: SelectorSuggestion[] = [];

    // Extract information from original selector
    const selectorInfo = this.parseSelector(originalSelector);

    // Strategy 1: Find by test ID variations
    if (selectorInfo.testId) {
      const testIdSuggestions = await this.findByTestIdVariations(page, selectorInfo.testId);
      suggestions.push(...testIdSuggestions);
    }

    // Strategy 2: Find by ARIA role and label
    if (selectorInfo.role || selectorInfo.label) {
      const ariaSuggestions = await this.findByAria(page, selectorInfo);
      suggestions.push(...ariaSuggestions);
    }

    // Strategy 3: Find by text content
    if (selectorInfo.text) {
      const textSuggestions = await this.findByText(page, selectorInfo.text);
      suggestions.push(...textSuggestions);
    }

    // Strategy 4: Find by similar structure
    const structureSuggestions = await this.findBySimilarStructure(page, selectorInfo);
    suggestions.push(...structureSuggestions);

    // Sort by confidence
    return suggestions.sort((a, b) => b.confidence - a.confidence);
  }

  /**
   * Find by test ID variations
   */
  private async findByTestIdVariations(
    page: Page,
    testId: string
  ): Promise<SelectorSuggestion[]> {
    const suggestions: SelectorSuggestion[] = [];
    const variations = this.generateTestIdVariations(testId);

    for (const variation of variations) {
      const selector = `[data-testid="${variation}"]`;
      const element = await this.trySelector(page, selector);

      if (element) {
        const elementInfo = await this.getElementInfo(element);
        suggestions.push({
          selector,
          type: 'testid',
          confidence: this.calculateSimilarity(testId, variation),
          reason: `Similar test ID: ${variation}`,
          element: elementInfo,
        });
      }
    }

    return suggestions;
  }

  /**
   * Find by ARIA attributes
   */
  private async findByAria(
    page: Page,
    selectorInfo: any
  ): Promise<SelectorSuggestion[]> {
    const suggestions: SelectorSuggestion[] = [];

    if (selectorInfo.role && selectorInfo.label) {
      const selector = `[role="${selectorInfo.role}"][aria-label*="${selectorInfo.label}"]`;
      const elements = await page.locator(selector).all();

      for (const element of elements) {
        const elementInfo = await this.getElementInfo(element);
        suggestions.push({
          selector,
          type: 'role',
          confidence: 0.85,
          reason: `Matching role and label`,
          element: elementInfo,
        });
      }
    }

    return suggestions;
  }

  /**
   * Find by text content
   */
  private async findByText(
    page: Page,
    text: string
  ): Promise<SelectorSuggestion[]> {
    const suggestions: SelectorSuggestion[] = [];

    try {
      const elements = await page.getByText(text, { exact: false }).all();

      for (const element of elements.slice(0, 5)) {
        const elementInfo = await this.getElementInfo(element);
        const selector = await this.generateSelectorForElement(element);

        if (selector) {
          suggestions.push({
            selector,
            type: 'text',
            confidence: 0.7,
            reason: `Contains text: "${text}"`,
            element: elementInfo,
          });
        }
      }
    } catch (error) {
      // Text not found
    }

    return suggestions;
  }

  /**
   * Find by similar structure
   */
  private async findBySimilarStructure(
    page: Page,
    selectorInfo: any
  ): Promise<SelectorSuggestion[]> {
    const suggestions: SelectorSuggestion[] = [];

    // This would use more advanced DOM analysis
    // For now, return empty array
    return suggestions;
  }

  /**
   * Generate test ID variations
   */
  private generateTestIdVariations(testId: string): string[] {
    const variations: string[] = [];

    // Remove numbers
    variations.push(testId.replace(/\d+/g, ''));

    // Kebab to camel case
    variations.push(testId.replace(/-([a-z])/g, (g) => g[1].toUpperCase()));

    // Camel to kebab case
    variations.push(testId.replace(/([A-Z])/g, '-$1').toLowerCase());

    // Add/remove common prefixes
    const prefixes = ['btn-', 'input-', 'form-', 'modal-', 'dialog-'];
    for (const prefix of prefixes) {
      if (testId.startsWith(prefix)) {
        variations.push(testId.substring(prefix.length));
      } else {
        variations.push(prefix + testId);
      }
    }

    // Remove duplicates
    return [...new Set(variations)];
  }

  /**
   * Parse selector to extract information
   */
  private parseSelector(selector: string): any {
    const info: any = {};

    // Extract test ID
    const testIdMatch = selector.match(/data-testid="([^"]+)"/);
    if (testIdMatch) {
      info.testId = testIdMatch[1];
    }

    // Extract role
    const roleMatch = selector.match(/role="([^"]+)"/);
    if (roleMatch) {
      info.role = roleMatch[1];
    }

    // Extract aria-label
    const labelMatch = selector.match(/aria-label="([^"]+)"/);
    if (labelMatch) {
      info.label = labelMatch[1];
    }

    // Extract text
    const textMatch = selector.match(/text="([^"]+)"/);
    if (textMatch) {
      info.text = textMatch[1];
    }

    return info;
  }

  /**
   * Try a selector
   */
  private async trySelector(page: Page, selector: string): Promise<Locator | null> {
    try {
      const element = page.locator(selector).first();
      const isVisible = await element.isVisible({ timeout: 1000 });
      return isVisible ? element : null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get element information
   */
  private async getElementInfo(element: Locator): Promise<any> {
    try {
      const tag = await element.evaluate((el) => el.tagName.toLowerCase());
      const text = await element.textContent();
      const attributes: Record<string, string> = {};

      const attrNames = await element.evaluate((el) => 
        Array.from(el.attributes).map(attr => attr.name)
      );

      for (const name of attrNames) {
        const value = await element.getAttribute(name);
        if (value) {
          attributes[name] = value;
        }
      }

      return { tag, text: text?.substring(0, 50), attributes };
    } catch (error) {
      return null;
    }
  }

  /**
   * Generate selector for element
   */
  private async generateSelectorForElement(element: Locator): Promise<string | null> {
    try {
      const testId = await element.getAttribute('data-testid');
      if (testId) {
        return `[data-testid="${testId}"]`;
      }

      const id = await element.getAttribute('id');
      if (id) {
        return `#${id}`;
      }

      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Calculate similarity between strings
   */
  private calculateSimilarity(str1: string, str2: string): number {
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;

    if (longer.length === 0) {
      return 1.0;
    }

    const editDistance = this.levenshteinDistance(longer, shorter);
    return (longer.length - editDistance) / longer.length;
  }

  /**
   * Calculate Levenshtein distance
   */
  private levenshteinDistance(str1: string, str2: string): number {
    const matrix: number[][] = [];

    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }

    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }

    return matrix[str2.length][str1.length];
  }

  /**
   * Detect selector type
   */
  private detectSelectorType(selector: string): 'testid' | 'role' | 'label' | 'text' | 'css' {
    if (selector.includes('data-testid')) return 'testid';
    if (selector.includes('role=')) return 'role';
    if (selector.includes('aria-label')) return 'label';
    if (selector.includes('text=')) return 'text';
    return 'css';
  }

  /**
   * Find existing mapping
   */
  private findMapping(
    selector: string,
    context?: { testFile?: string; testName?: string }
  ): SelectorMapping | undefined {
    return this.mappings.find(m => 
      m.originalSelector === selector &&
      (!context?.testFile || m.testFile === context.testFile) &&
      (!context?.testName || m.testName === context.testName)
    );
  }

  /**
   * Save mapping
   */
  private async saveMapping(mapping: SelectorMapping): Promise<void> {
    this.mappings.push(mapping);
    await this.saveMappings();
  }

  /**
   * Load mappings from file
   */
  private async loadMappings(): Promise<void> {
    try {
      const content = await fs.readFile(this.mappingsFile, 'utf-8');
      this.mappings = JSON.parse(content);
    } catch (error) {
      this.mappings = [];
    }
  }

  /**
   * Save mappings to file
   */
  private async saveMappings(): Promise<void> {
    try {
      await fs.mkdir(path.dirname(this.mappingsFile), { recursive: true });
      await fs.writeFile(
        this.mappingsFile,
        JSON.stringify(this.mappings, null, 2)
      );
    } catch (error) {
      console.error('Failed to save mappings:', error);
    }
  }

  /**
   * Get all mappings
   */
  getMappings(): SelectorMapping[] {
    return [...this.mappings];
  }

  /**
   * Clear all mappings
   */
  async clearMappings(): Promise<void> {
    this.mappings = [];
    await this.saveMappings();
  }
}

