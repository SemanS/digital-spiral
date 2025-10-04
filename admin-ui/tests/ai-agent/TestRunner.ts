import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';

const execAsync = promisify(exec);

/**
 * Test execution result
 */
export interface TestResult {
  success: boolean;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  skippedTests: number;
  duration: number;
  failures: TestFailure[];
  summary: string;
  rawOutput: string;
}

/**
 * Individual test failure
 */
export interface TestFailure {
  testName: string;
  testFile: string;
  errorMessage: string;
  stackTrace: string;
  screenshot?: string;
  video?: string;
  trace?: string;
}

/**
 * Test execution options
 */
export interface TestRunOptions {
  project?: string; // Browser project (chromium, firefox, webkit)
  grep?: string; // Test filter pattern
  headed?: boolean; // Run in headed mode
  debug?: boolean; // Run in debug mode
  workers?: number; // Number of parallel workers
  retries?: number; // Number of retries
  timeout?: number; // Test timeout in ms
  reporter?: string; // Reporter type
}

/**
 * AI Agent Test Runner
 * Executes Playwright tests and provides structured results for AI analysis
 */
export class TestRunner {
  private resultsDir: string;
  private reportsDir: string;

  constructor() {
    this.resultsDir = path.join(process.cwd(), 'test-results');
    this.reportsDir = path.join(process.cwd(), 'playwright-report');
  }

  /**
   * Run all tests
   */
  async runAllTests(options: TestRunOptions = {}): Promise<TestResult> {
    return this.runTests('', options);
  }

  /**
   * Run specific test file
   */
  async runTestFile(testFile: string, options: TestRunOptions = {}): Promise<TestResult> {
    return this.runTests(testFile, options);
  }

  /**
   * Run tests matching pattern
   */
  async runTestsByPattern(pattern: string, options: TestRunOptions = {}): Promise<TestResult> {
    return this.runTests('', { ...options, grep: pattern });
  }

  /**
   * Run tests for specific browser
   */
  async runTestsForBrowser(browser: string, options: TestRunOptions = {}): Promise<TestResult> {
    return this.runTests('', { ...options, project: browser });
  }

  /**
   * Execute Playwright tests
   */
  private async runTests(testPath: string, options: TestRunOptions): Promise<TestResult> {
    const startTime = Date.now();
    
    // Build command
    const command = this.buildCommand(testPath, options);
    
    console.log(`🚀 Running tests: ${command}`);
    
    try {
      const { stdout, stderr } = await execAsync(command, {
        cwd: process.cwd(),
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer
      });

      const duration = Date.now() - startTime;
      const rawOutput = stdout + stderr;

      // Parse results
      const result = await this.parseResults(rawOutput, duration);
      
      console.log(`✅ Tests completed in ${duration}ms`);
      console.log(`📊 Results: ${result.passedTests}/${result.totalTests} passed`);
      
      return result;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      const rawOutput = error.stdout + error.stderr;

      // Parse results even on failure
      const result = await this.parseResults(rawOutput, duration);
      
      console.log(`❌ Tests failed in ${duration}ms`);
      console.log(`📊 Results: ${result.passedTests}/${result.totalTests} passed`);
      
      return result;
    }
  }

  /**
   * Build Playwright command
   */
  private buildCommand(testPath: string, options: TestRunOptions): string {
    const parts = ['npx', 'playwright', 'test'];

    if (testPath) {
      parts.push(testPath);
    }

    if (options.project) {
      parts.push(`--project=${options.project}`);
    }

    if (options.grep) {
      parts.push(`--grep="${options.grep}"`);
    }

    if (options.headed) {
      parts.push('--headed');
    }

    if (options.debug) {
      parts.push('--debug');
    }

    if (options.workers !== undefined) {
      parts.push(`--workers=${options.workers}`);
    }

    if (options.retries !== undefined) {
      parts.push(`--retries=${options.retries}`);
    }

    if (options.timeout !== undefined) {
      parts.push(`--timeout=${options.timeout}`);
    }

    if (options.reporter) {
      parts.push(`--reporter=${options.reporter}`);
    }

    return parts.join(' ');
  }

  /**
   * Parse test results from output
   */
  private async parseResults(output: string, duration: number): Promise<TestResult> {
    // Parse JSON results if available
    const jsonResults = await this.loadJsonResults();
    
    if (jsonResults) {
      return this.parseJsonResults(jsonResults, duration, output);
    }

    // Fallback to parsing text output
    return this.parseTextOutput(output, duration);
  }

  /**
   * Load JSON results file
   */
  private async loadJsonResults(): Promise<any> {
    try {
      const jsonPath = path.join(this.resultsDir, 'results.json');
      const content = await fs.readFile(jsonPath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      return null;
    }
  }

  /**
   * Parse JSON results
   */
  private parseJsonResults(json: any, duration: number, rawOutput: string): TestResult {
    const stats = json.stats || {};
    const failures: TestFailure[] = [];

    // Extract failures
    if (json.suites) {
      this.extractFailuresFromSuites(json.suites, failures);
    }

    const totalTests = stats.expected || 0;
    const passedTests = stats.ok || 0;
    const failedTests = stats.unexpected || 0;
    const skippedTests = stats.skipped || 0;

    return {
      success: failedTests === 0,
      totalTests,
      passedTests,
      failedTests,
      skippedTests,
      duration,
      failures,
      summary: this.generateSummary(totalTests, passedTests, failedTests, skippedTests),
      rawOutput,
    };
  }

  /**
   * Extract failures from test suites
   */
  private extractFailuresFromSuites(suites: any[], failures: TestFailure[]): void {
    for (const suite of suites) {
      if (suite.specs) {
        for (const spec of suite.specs) {
          if (spec.tests) {
            for (const test of spec.tests) {
              if (test.status === 'unexpected' || test.status === 'failed') {
                failures.push({
                  testName: spec.title,
                  testFile: suite.file || '',
                  errorMessage: test.error?.message || 'Test failed',
                  stackTrace: test.error?.stack || '',
                  screenshot: test.attachments?.find((a: any) => a.name === 'screenshot')?.path,
                  video: test.attachments?.find((a: any) => a.name === 'video')?.path,
                  trace: test.attachments?.find((a: any) => a.name === 'trace')?.path,
                });
              }
            }
          }
        }
      }

      if (suite.suites) {
        this.extractFailuresFromSuites(suite.suites, failures);
      }
    }
  }

  /**
   * Parse text output (fallback)
   */
  private parseTextOutput(output: string, duration: number): TestResult {
    const lines = output.split('\n');
    
    let totalTests = 0;
    let passedTests = 0;
    let failedTests = 0;
    let skippedTests = 0;

    // Parse summary line
    for (const line of lines) {
      if (line.includes('passed') || line.includes('failed')) {
        const passedMatch = line.match(/(\d+)\s+passed/);
        const failedMatch = line.match(/(\d+)\s+failed/);
        const skippedMatch = line.match(/(\d+)\s+skipped/);

        if (passedMatch) passedTests = parseInt(passedMatch[1]);
        if (failedMatch) failedTests = parseInt(failedMatch[1]);
        if (skippedMatch) skippedTests = parseInt(skippedMatch[1]);
      }
    }

    totalTests = passedTests + failedTests + skippedTests;

    return {
      success: failedTests === 0,
      totalTests,
      passedTests,
      failedTests,
      skippedTests,
      duration,
      failures: [],
      summary: this.generateSummary(totalTests, passedTests, failedTests, skippedTests),
      rawOutput: output,
    };
  }

  /**
   * Generate summary text
   */
  private generateSummary(total: number, passed: number, failed: number, skipped: number): string {
    const parts = [];
    
    parts.push(`Total: ${total} tests`);
    parts.push(`Passed: ${passed}`);
    
    if (failed > 0) {
      parts.push(`Failed: ${failed}`);
    }
    
    if (skipped > 0) {
      parts.push(`Skipped: ${skipped}`);
    }

    const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : '0';
    parts.push(`Pass rate: ${passRate}%`);

    return parts.join(' | ');
  }

  /**
   * Get test artifacts (screenshots, videos, traces)
   */
  async getTestArtifacts(testName: string): Promise<{
    screenshots: string[];
    videos: string[];
    traces: string[];
  }> {
    const artifacts = {
      screenshots: [] as string[],
      videos: [] as string[],
      traces: [] as string[],
    };

    try {
      const files = await fs.readdir(this.resultsDir, { recursive: true });
      
      for (const file of files) {
        const filePath = path.join(this.resultsDir, file.toString());
        
        if (file.toString().includes(testName)) {
          if (file.toString().endsWith('.png')) {
            artifacts.screenshots.push(filePath);
          } else if (file.toString().endsWith('.webm')) {
            artifacts.videos.push(filePath);
          } else if (file.toString().endsWith('.zip')) {
            artifacts.traces.push(filePath);
          }
        }
      }
    } catch (error) {
      console.error('Error reading artifacts:', error);
    }

    return artifacts;
  }
}

