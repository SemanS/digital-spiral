import { TestRunner } from './TestRunner';
import { TestAnalyzer } from './TestAnalyzer';

/**
 * Example: Using AI Agent Test Runner and Analyzer
 * 
 * This example demonstrates how to use the AI Agent to:
 * 1. Run tests programmatically
 * 2. Analyze results
 * 3. Get intelligent insights
 * 4. Make data-driven decisions
 */

async function main() {
  console.log('🤖 AI Agent Test Runner - Example Usage\n');

  const runner = new TestRunner();
  const analyzer = new TestAnalyzer();

  // ============================================================
  // Example 1: Run all tests and analyze
  // ============================================================
  console.log('📝 Example 1: Run all tests and analyze');
  console.log('─────────────────────────────────────────────────────\n');

  const allTestsResult = await runner.runAllTests();
  const allTestsAnalysis = analyzer.analyzeResults(allTestsResult);

  console.log('Results:', allTestsResult.summary);
  console.log('Analyses found:', allTestsAnalysis.length);
  console.log('');

  // Display top 3 issues
  if (allTestsAnalysis.length > 0) {
    console.log('Top issues:');
    allTestsAnalysis.slice(0, 3).forEach((analysis, i) => {
      console.log(`${i + 1}. [${analysis.severity}] ${analysis.issue}`);
      console.log(`   ${analysis.suggestion}`);
    });
    console.log('');
  }

  // ============================================================
  // Example 2: Run specific test file
  // ============================================================
  console.log('📝 Example 2: Run specific test file');
  console.log('─────────────────────────────────────────────────────\n');

  const navigationResult = await runner.runTestFile('tests/e2e/navigation.spec.ts');
  console.log('Navigation tests:', navigationResult.summary);
  console.log('');

  // ============================================================
  // Example 3: Run tests for specific browser
  // ============================================================
  console.log('📝 Example 3: Run tests for specific browser');
  console.log('─────────────────────────────────────────────────────\n');

  const chromeResult = await runner.runTestsForBrowser('chromium', {
    workers: 4,
    retries: 1,
  });
  console.log('Chrome tests:', chromeResult.summary);
  console.log('');

  // ============================================================
  // Example 4: Run tests matching pattern
  // ============================================================
  console.log('📝 Example 4: Run tests matching pattern');
  console.log('─────────────────────────────────────────────────────\n');

  const accessibilityResult = await runner.runTestsByPattern('accessibility');
  console.log('Accessibility tests:', accessibilityResult.summary);
  console.log('');

  // ============================================================
  // Example 5: Calculate health metrics
  // ============================================================
  console.log('📝 Example 5: Calculate health metrics');
  console.log('─────────────────────────────────────────────────────\n');

  const healthMetrics = analyzer.calculateHealthMetrics([
    allTestsResult,
    navigationResult,
    chromeResult,
    accessibilityResult,
  ]);

  console.log('Overall Health:', healthMetrics.overallHealth, '/100');
  console.log('Pass Rate:', healthMetrics.passRate.toFixed(1), '%');
  console.log('Avg Duration:', (healthMetrics.avgDuration / 1000).toFixed(2), 's');
  console.log('');

  if (healthMetrics.recommendations.length > 0) {
    console.log('Recommendations:');
    healthMetrics.recommendations.forEach(rec => {
      console.log(`  ${rec}`);
    });
    console.log('');
  }

  // ============================================================
  // Example 6: Generate full report
  // ============================================================
  console.log('📝 Example 6: Generate full report');
  console.log('─────────────────────────────────────────────────────\n');

  const report = analyzer.generateReport(allTestsResult, allTestsAnalysis);
  console.log(report);
  console.log('');

  // ============================================================
  // Example 7: Get test artifacts
  // ============================================================
  console.log('📝 Example 7: Get test artifacts');
  console.log('─────────────────────────────────────────────────────\n');

  if (allTestsResult.failures.length > 0) {
    const firstFailure = allTestsResult.failures[0];
    const artifacts = await runner.getTestArtifacts(firstFailure.testName);

    console.log('Artifacts for failed test:', firstFailure.testName);
    console.log('Screenshots:', artifacts.screenshots.length);
    console.log('Videos:', artifacts.videos.length);
    console.log('Traces:', artifacts.traces.length);
    console.log('');
  }

  // ============================================================
  // Example 8: Continuous monitoring
  // ============================================================
  console.log('📝 Example 8: Continuous monitoring');
  console.log('─────────────────────────────────────────────────────\n');

  console.log('Running tests every 5 minutes for monitoring...');
  console.log('(This is just an example - not actually running)\n');

  // Example monitoring loop (commented out)
  /*
  setInterval(async () => {
    const result = await runner.runAllTests({ workers: 4 });
    const analyses = analyzer.analyzeResults(result);
    
    if (!result.success) {
      console.log('⚠️ Tests failed! Sending alert...');
      // Send alert to Slack, email, etc.
    }
    
    if (analyses.some(a => a.severity === 'critical')) {
      console.log('🔴 Critical issues detected!');
      // Send urgent notification
    }
  }, 5 * 60 * 1000); // Every 5 minutes
  */

  // ============================================================
  // Example 9: Integration with CI/CD
  // ============================================================
  console.log('📝 Example 9: Integration with CI/CD');
  console.log('─────────────────────────────────────────────────────\n');

  console.log('Example CI/CD integration:');
  console.log(`
  // In your CI/CD pipeline:
  
  const runner = new TestRunner();
  const analyzer = new TestAnalyzer();
  
  // Run tests
  const result = await runner.runAllTests({
    workers: process.env.CI ? 1 : 4,
    retries: process.env.CI ? 2 : 0,
  });
  
  // Analyze
  const analyses = analyzer.analyzeResults(result);
  
  // Post results to PR
  if (process.env.GITHUB_TOKEN) {
    await postToPR(result, analyses);
  }
  
  // Fail build if critical issues
  const hasCritical = analyses.some(a => a.severity === 'critical');
  if (hasCritical) {
    process.exit(1);
  }
  `);
  console.log('');

  // ============================================================
  // Example 10: Custom analysis
  // ============================================================
  console.log('📝 Example 10: Custom analysis');
  console.log('─────────────────────────────────────────────────────\n');

  console.log('Custom analysis example:');
  
  // Analyze specific patterns
  const timeoutFailures = allTestsResult.failures.filter(f => 
    f.errorMessage.toLowerCase().includes('timeout')
  );
  
  if (timeoutFailures.length > 0) {
    console.log(`Found ${timeoutFailures.length} timeout failures:`);
    timeoutFailures.forEach(f => {
      console.log(`  - ${f.testName}`);
    });
    console.log('');
    console.log('Recommendation: Consider increasing timeout or optimizing slow operations');
  }

  // Analyze test distribution
  const testsByFile: Record<string, number> = {};
  allTestsResult.failures.forEach(f => {
    testsByFile[f.testFile] = (testsByFile[f.testFile] || 0) + 1;
  });

  if (Object.keys(testsByFile).length > 0) {
    console.log('\nFailures by file:');
    Object.entries(testsByFile)
      .sort((a, b) => b[1] - a[1])
      .forEach(([file, count]) => {
        console.log(`  ${file}: ${count} failure(s)`);
      });
  }

  console.log('\n✅ Examples completed!');
}

// Run examples
if (require.main === module) {
  main().catch(console.error);
}

export { main };

