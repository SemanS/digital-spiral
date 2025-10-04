import { Page } from '@playwright/test';
import * as fs from 'fs/promises';
import * as path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

/**
 * Visual comparison result
 */
export interface VisualComparisonResult {
  passed: boolean;
  diffPixels: number;
  diffPercentage: number;
  threshold: number;
  baselineExists: boolean;
  diffImagePath?: string;
  message: string;
}

/**
 * Screenshot options
 */
export interface ScreenshotOptions {
  fullPage?: boolean;
  clip?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  mask?: string[]; // Selectors to mask
  animations?: 'disabled' | 'allow';
}

/**
 * Visual Regression Engine
 * Performs pixel-perfect visual comparisons
 */
export class VisualRegressionEngine {
  private baselinesDir: string;
  private diffsDir: string;
  private threshold: number;
  private updateBaselines: boolean;

  constructor(options?: {
    baselinesDir?: string;
    diffsDir?: string;
    threshold?: number;
    updateBaselines?: boolean;
  }) {
    this.baselinesDir = options?.baselinesDir || path.join(process.cwd(), 'test-results', 'visual-baselines');
    this.diffsDir = options?.diffsDir || path.join(process.cwd(), 'test-results', 'visual-diffs');
    this.threshold = options?.threshold ?? 0.1; // 0.1% difference allowed
    this.updateBaselines = options?.updateBaselines ?? false;
  }

  /**
   * Initialize visual regression engine
   */
  async initialize(): Promise<void> {
    await fs.mkdir(this.baselinesDir, { recursive: true });
    await fs.mkdir(this.diffsDir, { recursive: true });
  }

  /**
   * Compare screenshot with baseline
   */
  async compareScreenshot(
    page: Page,
    name: string,
    options?: ScreenshotOptions
  ): Promise<VisualComparisonResult> {
    const screenshotPath = await this.takeScreenshot(page, name, options);
    const baselinePath = this.getBaselinePath(name);
    const diffPath = this.getDiffPath(name);

    // Check if baseline exists
    const baselineExists = await this.fileExists(baselinePath);

    if (!baselineExists) {
      if (this.updateBaselines) {
        await fs.copyFile(screenshotPath, baselinePath);
        return {
          passed: true,
          diffPixels: 0,
          diffPercentage: 0,
          threshold: this.threshold,
          baselineExists: false,
          message: 'Baseline created',
        };
      } else {
        return {
          passed: false,
          diffPixels: 0,
          diffPercentage: 0,
          threshold: this.threshold,
          baselineExists: false,
          message: 'No baseline found. Run with --update-baselines to create one.',
        };
      }
    }

    // Compare images
    const comparison = await this.compareImages(screenshotPath, baselinePath, diffPath);

    // Update baseline if requested and test failed
    if (this.updateBaselines && !comparison.passed) {
      await fs.copyFile(screenshotPath, baselinePath);
      return {
        ...comparison,
        message: 'Baseline updated',
      };
    }

    return comparison;
  }

  /**
   * Take screenshot
   */
  private async takeScreenshot(
    page: Page,
    name: string,
    options?: ScreenshotOptions
  ): Promise<string> {
    const screenshotPath = path.join(this.diffsDir, `${name}-current.png`);

    // Mask elements if specified
    if (options?.mask && options.mask.length > 0) {
      for (const selector of options.mask) {
        try {
          await page.locator(selector).evaluate((el: HTMLElement) => {
            el.style.visibility = 'hidden';
          });
        } catch (error) {
          // Element not found, continue
        }
      }
    }

    // Disable animations if specified
    if (options?.animations === 'disabled') {
      await page.addStyleTag({
        content: `
          *, *::before, *::after {
            animation-duration: 0s !important;
            animation-delay: 0s !important;
            transition-duration: 0s !important;
            transition-delay: 0s !important;
          }
        `,
      });
    }

    // Take screenshot
    await page.screenshot({
      path: screenshotPath,
      fullPage: options?.fullPage ?? true,
      clip: options?.clip,
      animations: options?.animations ?? 'disabled',
    });

    return screenshotPath;
  }

  /**
   * Compare two images
   */
  private async compareImages(
    currentPath: string,
    baselinePath: string,
    diffPath: string
  ): Promise<VisualComparisonResult> {
    // Read images
    const currentImg = PNG.sync.read(await fs.readFile(currentPath));
    const baselineImg = PNG.sync.read(await fs.readFile(baselinePath));

    // Check dimensions match
    if (
      currentImg.width !== baselineImg.width ||
      currentImg.height !== baselineImg.height
    ) {
      return {
        passed: false,
        diffPixels: 0,
        diffPercentage: 100,
        threshold: this.threshold,
        baselineExists: true,
        message: `Image dimensions don't match. Current: ${currentImg.width}x${currentImg.height}, Baseline: ${baselineImg.width}x${baselineImg.height}`,
      };
    }

    // Create diff image
    const diff = new PNG({ width: currentImg.width, height: currentImg.height });

    // Compare pixels
    const diffPixels = pixelmatch(
      currentImg.data,
      baselineImg.data,
      diff.data,
      currentImg.width,
      currentImg.height,
      {
        threshold: 0.1,
        includeAA: false,
      }
    );

    const totalPixels = currentImg.width * currentImg.height;
    const diffPercentage = (diffPixels / totalPixels) * 100;

    // Save diff image if there are differences
    if (diffPixels > 0) {
      await fs.writeFile(diffPath, PNG.sync.write(diff));
    }

    const passed = diffPercentage <= this.threshold;

    return {
      passed,
      diffPixels,
      diffPercentage,
      threshold: this.threshold,
      baselineExists: true,
      diffImagePath: diffPixels > 0 ? diffPath : undefined,
      message: passed
        ? `Visual comparison passed (${diffPercentage.toFixed(3)}% difference)`
        : `Visual comparison failed (${diffPercentage.toFixed(3)}% difference, threshold: ${this.threshold}%)`,
    };
  }

  /**
   * Compare element screenshot
   */
  async compareElement(
    page: Page,
    selector: string,
    name: string,
    options?: ScreenshotOptions
  ): Promise<VisualComparisonResult> {
    const element = page.locator(selector).first();
    const screenshotPath = path.join(this.diffsDir, `${name}-current.png`);

    // Take element screenshot
    await element.screenshot({
      path: screenshotPath,
      animations: options?.animations ?? 'disabled',
    });

    const baselinePath = this.getBaselinePath(name);
    const diffPath = this.getDiffPath(name);

    // Check if baseline exists
    const baselineExists = await this.fileExists(baselinePath);

    if (!baselineExists) {
      if (this.updateBaselines) {
        await fs.copyFile(screenshotPath, baselinePath);
        return {
          passed: true,
          diffPixels: 0,
          diffPercentage: 0,
          threshold: this.threshold,
          baselineExists: false,
          message: 'Baseline created',
        };
      } else {
        return {
          passed: false,
          diffPixels: 0,
          diffPercentage: 0,
          threshold: this.threshold,
          baselineExists: false,
          message: 'No baseline found',
        };
      }
    }

    return await this.compareImages(screenshotPath, baselinePath, diffPath);
  }

  /**
   * Get baseline path
   */
  private getBaselinePath(name: string): string {
    return path.join(this.baselinesDir, `${name}.png`);
  }

  /**
   * Get diff path
   */
  private getDiffPath(name: string): string {
    return path.join(this.diffsDir, `${name}-diff.png`);
  }

  /**
   * Check if file exists
   */
  private async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get all baselines
   */
  async getBaselines(): Promise<string[]> {
    try {
      const files = await fs.readdir(this.baselinesDir);
      return files.filter(f => f.endsWith('.png')).map(f => f.replace('.png', ''));
    } catch {
      return [];
    }
  }

  /**
   * Delete baseline
   */
  async deleteBaseline(name: string): Promise<void> {
    const baselinePath = this.getBaselinePath(name);
    try {
      await fs.unlink(baselinePath);
    } catch (error) {
      // File doesn't exist
    }
  }

  /**
   * Clear all baselines
   */
  async clearBaselines(): Promise<void> {
    try {
      const files = await fs.readdir(this.baselinesDir);
      for (const file of files) {
        await fs.unlink(path.join(this.baselinesDir, file));
      }
    } catch (error) {
      // Directory doesn't exist
    }
  }

  /**
   * Clear all diffs
   */
  async clearDiffs(): Promise<void> {
    try {
      const files = await fs.readdir(this.diffsDir);
      for (const file of files) {
        await fs.unlink(path.join(this.diffsDir, file));
      }
    } catch (error) {
      // Directory doesn't exist
    }
  }

  /**
   * Generate visual regression report
   */
  async generateReport(results: Map<string, VisualComparisonResult>): Promise<string> {
    const lines: string[] = [];

    lines.push('═══════════════════════════════════════════════════════');
    lines.push('        VISUAL REGRESSION TEST REPORT');
    lines.push('═══════════════════════════════════════════════════════');
    lines.push('');

    const passed = Array.from(results.values()).filter(r => r.passed).length;
    const failed = Array.from(results.values()).filter(r => !r.passed).length;
    const total = results.size;

    lines.push('📊 SUMMARY');
    lines.push('─────────────────────────────────────────────────────');
    lines.push(`Total: ${total} | Passed: ${passed} | Failed: ${failed}`);
    lines.push(`Pass Rate: ${((passed / total) * 100).toFixed(1)}%`);
    lines.push('');

    if (failed > 0) {
      lines.push('❌ FAILURES');
      lines.push('─────────────────────────────────────────────────────');

      for (const [name, result] of results.entries()) {
        if (!result.passed) {
          lines.push(`${name}:`);
          lines.push(`  Difference: ${result.diffPercentage.toFixed(3)}%`);
          lines.push(`  Pixels: ${result.diffPixels.toLocaleString()}`);
          if (result.diffImagePath) {
            lines.push(`  Diff: ${result.diffImagePath}`);
          }
          lines.push('');
        }
      }
    }

    lines.push('═══════════════════════════════════════════════════════');

    return lines.join('\n');
  }
}

