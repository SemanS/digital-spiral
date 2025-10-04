# 🤖 AI Agent Test Runner

Intelligent test execution and analysis system powered by AI.

## 🎯 Overview

The AI Agent Test Runner is an intelligent testing framework that:
- **Executes** Playwright tests programmatically
- **Analyzes** test results with AI-powered insights
- **Detects** patterns and common issues
- **Suggests** actionable fixes
- **Monitors** test health over time
- **Provides** intelligent recommendations

## 🚀 Features

### ✅ Intelligent Test Execution
- Run all tests or specific subsets
- Multi-browser support (Chrome, Firefox, Safari)
- Parallel execution for speed
- Automatic retry on failure
- Configurable timeouts and workers

### 🔍 AI-Powered Analysis
- **Pattern Detection**: Identifies common failure patterns
- **Root Cause Analysis**: Suggests likely causes of failures
- **Severity Classification**: Prioritizes issues (critical, high, medium, low)
- **Confidence Scoring**: Indicates analysis confidence (0-100%)
- **Actionable Suggestions**: Provides specific fix recommendations

### 📊 Health Metrics
- **Overall Health Score**: 0-100 rating of test suite health
- **Pass Rate**: Percentage of passing tests
- **Performance Metrics**: Average execution time
- **Flaky Test Detection**: Identifies unreliable tests
- **Slow Test Detection**: Finds performance bottlenecks

### 🎨 Rich Reporting
- Human-readable console output
- Structured JSON results
- Visual health indicators
- Detailed failure analysis
- Artifact management (screenshots, videos, traces)

## 📦 Installation

```bash
# Already installed as part of the project
cd admin-ui
npm install
```

## 🎮 Usage

### Command Line Interface

```bash
# Run all tests with AI analysis
npx ts-node tests/ai-agent/cli.ts test

# Run specific test file
npx ts-node tests/ai-agent/cli.ts test navigation.spec.ts

# Run tests for specific browser
npx ts-node tests/ai-agent/cli.ts test --project=chromium

# Filter tests by pattern
npx ts-node tests/ai-agent/cli.ts test --grep="Navigation"

# Check test suite health
npx ts-node tests/ai-agent/cli.ts health

# Analyze existing results
npx ts-node tests/ai-agent/cli.ts analyze

# Show help
npx ts-node tests/ai-agent/cli.ts help
```

### Programmatic API

```typescript
import { TestRunner } from './tests/ai-agent/TestRunner';
import { TestAnalyzer } from './tests/ai-agent/TestAnalyzer';

const runner = new TestRunner();
const analyzer = new TestAnalyzer();

// Run tests
const result = await runner.runAllTests();

// Analyze results
const analyses = analyzer.analyzeResults(result);

// Generate report
const report = analyzer.generateReport(result, analyses);
console.log(report);
```

## 📚 API Reference

### TestRunner

#### Methods

**`runAllTests(options?)`**
- Runs all tests in the suite
- Returns: `Promise<TestResult>`

**`runTestFile(testFile, options?)`**
- Runs a specific test file
- Returns: `Promise<TestResult>`

**`runTestsByPattern(pattern, options?)`**
- Runs tests matching a pattern
- Returns: `Promise<TestResult>`

**`runTestsForBrowser(browser, options?)`**
- Runs tests for a specific browser
- Returns: `Promise<TestResult>`

**`getTestArtifacts(testName)`**
- Gets screenshots, videos, and traces for a test
- Returns: `Promise<{ screenshots, videos, traces }>`

#### Options

```typescript
interface TestRunOptions {
  project?: string;      // Browser: chromium, firefox, webkit
  grep?: string;         // Test filter pattern
  headed?: boolean;      // Run in headed mode
  debug?: boolean;       // Run in debug mode
  workers?: number;      // Parallel workers (default: auto)
  retries?: number;      // Retry count (default: 0)
  timeout?: number;      // Test timeout in ms
  reporter?: string;     // Reporter type
}
```

### TestAnalyzer

#### Methods

**`analyzeResults(result)`**
- Analyzes test results and provides insights
- Returns: `AnalysisResult[]`

**`calculateHealthMetrics(results)`**
- Calculates health metrics from multiple test runs
- Returns: `TestHealthMetrics`

**`generateReport(result, analyses)`**
- Generates human-readable report
- Returns: `string`

#### Types

```typescript
interface AnalysisResult {
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  issue: string;
  suggestion: string;
  affectedTests: string[];
  confidence: number; // 0-1
}

interface TestHealthMetrics {
  overallHealth: number;      // 0-100
  passRate: number;           // 0-100
  avgDuration: number;        // milliseconds
  flakyTests: string[];
  slowTests: string[];
  failurePatterns: AnalysisResult[];
  recommendations: string[];
}
```

## 🎯 Use Cases

### 1. Local Development

```bash
# Quick test run with analysis
npx ts-node tests/ai-agent/cli.ts test --grep="Navigation"
```

### 2. CI/CD Integration

```typescript
// In your CI pipeline
const runner = new TestRunner();
const result = await runner.runAllTests({
  workers: 1,
  retries: 2,
});

if (!result.success) {
  console.error('Tests failed!');
  process.exit(1);
}
```

### 3. Continuous Monitoring

```typescript
// Monitor test health every hour
setInterval(async () => {
  const result = await runner.runAllTests();
  const analyses = analyzer.analyzeResults(result);
  
  if (analyses.some(a => a.severity === 'critical')) {
    await sendAlert('Critical test failures detected!');
  }
}, 60 * 60 * 1000);
```

### 4. Test Health Dashboard

```typescript
// Collect metrics for dashboard
const results = await Promise.all([
  runner.runAllTests(),
  runner.runTestsForBrowser('chromium'),
  runner.runTestsForBrowser('firefox'),
]);

const metrics = analyzer.calculateHealthMetrics(results);
await updateDashboard(metrics);
```

## 🔍 Analysis Categories

The AI Agent detects and categorizes issues:

### 🔴 Critical
- Network failures
- High failure rates (>50%)
- System-level errors

### 🟠 High
- Timeout errors (multiple tests)
- Element not found errors
- Elevated failure rates (>20%)

### 🟡 Medium
- Assertion failures
- Performance issues
- Unknown error patterns

### 🟢 Low
- Minor issues
- Warnings
- Optimization suggestions

## 📊 Example Output

```
═══════════════════════════════════════════════════════
           AI AGENT TEST ANALYSIS REPORT
═══════════════════════════════════════════════════════

📊 SUMMARY
─────────────────────────────────────────────────────
Total: 130 tests | Passed: 125 | Failed: 5 | Pass rate: 96.2%
Duration: 45.32s
Status: ❌ FAILED

🔍 ANALYSIS
─────────────────────────────────────────────────────
🟠 [HIGH] Timeout
   Issue: 3 test(s) failed due to timeout
   Suggestion: Consider increasing timeout values or optimizing slow operations.
   Confidence: 90%
   Affected: should navigate to instances, should load table...

🟡 [MEDIUM] Assertion
   Issue: 2 test(s) failed assertion checks
   Suggestion: Verify expected behavior matches actual implementation.
   Confidence: 80%
   Affected: should display correct title, should show status...

═══════════════════════════════════════════════════════
```

## 🛠️ Advanced Features

### Custom Analysis

```typescript
// Add custom analysis logic
const customAnalyzer = new TestAnalyzer();

// Extend with custom patterns
const result = await runner.runAllTests();
const analyses = customAnalyzer.analyzeResults(result);

// Filter by severity
const critical = analyses.filter(a => a.severity === 'critical');
```

### Artifact Management

```typescript
// Get artifacts for failed tests
for (const failure of result.failures) {
  const artifacts = await runner.getTestArtifacts(failure.testName);
  
  console.log('Screenshots:', artifacts.screenshots);
  console.log('Videos:', artifacts.videos);
  console.log('Traces:', artifacts.traces);
}
```

### Historical Analysis

```typescript
// Track metrics over time
const history: TestResult[] = [];

setInterval(async () => {
  const result = await runner.runAllTests();
  history.push(result);
  
  // Keep last 100 runs
  if (history.length > 100) {
    history.shift();
  }
  
  // Analyze trends
  const metrics = analyzer.calculateHealthMetrics(history);
  console.log('Health trend:', metrics.overallHealth);
}, 60 * 60 * 1000);
```

## 🎓 Best Practices

1. **Run regularly**: Execute tests frequently to catch issues early
2. **Monitor health**: Track health metrics over time
3. **Act on insights**: Follow AI suggestions to improve test quality
4. **Review patterns**: Look for recurring issues
5. **Optimize slow tests**: Address performance bottlenecks
6. **Fix flaky tests**: Eliminate unreliable tests
7. **Use in CI/CD**: Integrate into your deployment pipeline

## 🤝 Contributing

To add new analysis patterns:

1. Extend `TestAnalyzer` class
2. Add new detection logic in `analyzeFailures()`
3. Define severity and suggestions
4. Add tests for new patterns

## 📝 Examples

See `example.ts` for comprehensive usage examples:

```bash
npx ts-node tests/ai-agent/example.ts
```

## 🐛 Troubleshooting

**Tests not running?**
- Check Playwright is installed: `npx playwright install`
- Verify test files exist in `tests/e2e/`

**Analysis not working?**
- Ensure JSON reporter is enabled in `playwright.config.ts`
- Check `test-results/results.json` exists

**No artifacts found?**
- Verify screenshot/video capture is enabled
- Check `test-results/` directory

## 📚 Resources

- [Playwright Documentation](https://playwright.dev)
- [Test Best Practices](../e2e/README.md)
- [Example Usage](./example.ts)

## 🎉 Summary

The AI Agent Test Runner provides:
- ✅ Intelligent test execution
- ✅ AI-powered analysis
- ✅ Actionable insights
- ✅ Health monitoring
- ✅ Rich reporting
- ✅ Easy integration

Start using it today to improve your test quality!

