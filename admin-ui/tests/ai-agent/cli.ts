#!/usr/bin/env node

import { TestRunner } from './TestRunner';
import { TestAnalyzer } from './TestAnalyzer';

/**
 * AI Agent CLI
 * Command-line interface for AI-powered test execution and analysis
 */
class AIAgentCLI {
  private runner: TestRunner;
  private analyzer: TestAnalyzer;

  constructor() {
    this.runner = new TestRunner();
    this.analyzer = new TestAnalyzer();
  }

  /**
   * Main entry point
   */
  async run(args: string[]): Promise<void> {
    const command = args[2] || 'help';

    try {
      switch (command) {
        case 'test':
          await this.runTests(args.slice(3));
          break;
        case 'analyze':
          await this.analyzeTests(args.slice(3));
          break;
        case 'health':
          await this.checkHealth(args.slice(3));
          break;
        case 'help':
          this.showHelp();
          break;
        default:
          console.error(`Unknown command: ${command}`);
          this.showHelp();
          process.exit(1);
      }
    } catch (error) {
      console.error('Error:', error);
      process.exit(1);
    }
  }

  /**
   * Run tests with AI analysis
   */
  private async runTests(args: string[]): Promise<void> {
    console.log('🤖 AI Agent Test Runner');
    console.log('═══════════════════════════════════════════════════════\n');

    // Parse options
    const options = this.parseOptions(args);
    const testPath = args.find(arg => !arg.startsWith('--')) || '';

    // Run tests
    console.log('🚀 Executing tests...\n');
    const result = await this.runner.runTests(testPath, options);

    // Analyze results
    console.log('\n🔍 Analyzing results...\n');
    const analyses = this.analyzer.analyzeResults(result);

    // Generate report
    const report = this.analyzer.generateReport(result, analyses);
    console.log(report);

    // Exit with appropriate code
    process.exit(result.success ? 0 : 1);
  }

  /**
   * Analyze existing test results
   */
  private async analyzeTests(args: string[]): Promise<void> {
    console.log('🤖 AI Agent Test Analyzer');
    console.log('═══════════════════════════════════════════════════════\n');

    // This would load existing results and analyze them
    console.log('📊 Loading test results...\n');
    
    // For now, run tests and analyze
    const result = await this.runner.runAllTests();
    const analyses = this.analyzer.analyzeResults(result);

    const report = this.analyzer.generateReport(result, analyses);
    console.log(report);
  }

  /**
   * Check test health
   */
  private async checkHealth(args: string[]): Promise<void> {
    console.log('🤖 AI Agent Health Check');
    console.log('═══════════════════════════════════════════════════════\n');

    // Run tests
    console.log('🚀 Running health check...\n');
    const result = await this.runner.runAllTests({ workers: 4 });

    // Calculate health metrics
    const metrics = this.analyzer.calculateHealthMetrics([result]);

    // Display health report
    this.displayHealthReport(metrics);

    // Exit with appropriate code
    const exitCode = metrics.overallHealth >= 80 ? 0 : 1;
    process.exit(exitCode);
  }

  /**
   * Display health report
   */
  private displayHealthReport(metrics: any): void {
    console.log('📊 HEALTH METRICS');
    console.log('─────────────────────────────────────────────────────');
    console.log(`Overall Health: ${this.getHealthIcon(metrics.overallHealth)} ${metrics.overallHealth}/100`);
    console.log(`Pass Rate: ${metrics.passRate.toFixed(1)}%`);
    console.log(`Avg Duration: ${(metrics.avgDuration / 1000).toFixed(2)}s`);
    console.log('');

    if (metrics.flakyTests.length > 0) {
      console.log(`🔄 Flaky Tests: ${metrics.flakyTests.length}`);
      metrics.flakyTests.slice(0, 5).forEach((test: string) => {
        console.log(`   - ${test}`);
      });
      console.log('');
    }

    if (metrics.slowTests.length > 0) {
      console.log(`⚡ Slow Tests: ${metrics.slowTests.length}`);
      metrics.slowTests.slice(0, 5).forEach((test: string) => {
        console.log(`   - ${test}`);
      });
      console.log('');
    }

    if (metrics.recommendations.length > 0) {
      console.log('💡 RECOMMENDATIONS');
      console.log('─────────────────────────────────────────────────────');
      metrics.recommendations.forEach((rec: string) => {
        console.log(`   ${rec}`);
      });
      console.log('');
    }

    console.log('═══════════════════════════════════════════════════════');
  }

  /**
   * Get health icon
   */
  private getHealthIcon(health: number): string {
    if (health >= 90) return '🟢';
    if (health >= 70) return '🟡';
    return '🔴';
  }

  /**
   * Parse command-line options
   */
  private parseOptions(args: string[]): any {
    const options: any = {};

    for (const arg of args) {
      if (arg.startsWith('--')) {
        const [key, value] = arg.substring(2).split('=');
        
        switch (key) {
          case 'project':
          case 'browser':
            options.project = value;
            break;
          case 'grep':
          case 'filter':
            options.grep = value;
            break;
          case 'headed':
            options.headed = true;
            break;
          case 'debug':
            options.debug = true;
            break;
          case 'workers':
            options.workers = parseInt(value);
            break;
          case 'retries':
            options.retries = parseInt(value);
            break;
          case 'timeout':
            options.timeout = parseInt(value);
            break;
        }
      }
    }

    return options;
  }

  /**
   * Show help
   */
  private showHelp(): void {
    console.log(`
🤖 AI Agent Test CLI

USAGE:
  ai-agent <command> [options]

COMMANDS:
  test [path]           Run tests with AI analysis
  analyze               Analyze existing test results
  health                Check test suite health
  help                  Show this help message

OPTIONS:
  --project=<name>      Run tests for specific browser (chromium, firefox, webkit)
  --grep=<pattern>      Filter tests by pattern
  --headed              Run tests in headed mode
  --debug               Run tests in debug mode
  --workers=<n>         Number of parallel workers
  --retries=<n>         Number of retries for failed tests
  --timeout=<ms>        Test timeout in milliseconds

EXAMPLES:
  # Run all tests with AI analysis
  ai-agent test

  # Run specific test file
  ai-agent test navigation.spec.ts

  # Run tests for Chrome only
  ai-agent test --project=chromium

  # Run tests matching pattern
  ai-agent test --grep="Navigation"

  # Check test suite health
  ai-agent health

  # Analyze existing results
  ai-agent analyze

FEATURES:
  ✅ Intelligent failure analysis
  ✅ Performance insights
  ✅ Pattern detection
  ✅ Health metrics
  ✅ Actionable recommendations
  ✅ Multi-browser support
  ✅ Parallel execution

For more information, visit: https://github.com/your-repo
    `);
  }
}

// Run CLI
const cli = new AIAgentCLI();
cli.run(process.argv);

