import { TestResult, TestFailure } from './TestRunner';

/**
 * Analysis result
 */
export interface AnalysisResult {
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  issue: string;
  suggestion: string;
  affectedTests: string[];
  confidence: number; // 0-1
}

/**
 * Test health metrics
 */
export interface TestHealthMetrics {
  overallHealth: number; // 0-100
  passRate: number;
  avgDuration: number;
  flakyTests: string[];
  slowTests: string[];
  failurePatterns: AnalysisResult[];
  recommendations: string[];
}

/**
 * AI Agent Test Analyzer
 * Analyzes test results and provides intelligent insights
 */
export class TestAnalyzer {
  /**
   * Analyze test results
   */
  analyzeResults(result: TestResult): AnalysisResult[] {
    const analyses: AnalysisResult[] = [];

    // Analyze failures
    if (result.failures.length > 0) {
      analyses.push(...this.analyzeFailures(result.failures));
    }

    // Analyze performance
    analyses.push(...this.analyzePerformance(result));

    // Analyze patterns
    analyses.push(...this.analyzePatterns(result));

    return analyses.sort((a, b) => {
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      return severityOrder[a.severity] - severityOrder[b.severity];
    });
  }

  /**
   * Analyze test failures
   */
  private analyzeFailures(failures: TestFailure[]): AnalysisResult[] {
    const analyses: AnalysisResult[] = [];

    // Group failures by error type
    const errorGroups = this.groupFailuresByError(failures);

    for (const [errorType, groupFailures] of Object.entries(errorGroups)) {
      const analysis = this.analyzeErrorGroup(errorType, groupFailures);
      if (analysis) {
        analyses.push(analysis);
      }
    }

    return analyses;
  }

  /**
   * Group failures by error message
   */
  private groupFailuresByError(failures: TestFailure[]): Record<string, TestFailure[]> {
    const groups: Record<string, TestFailure[]> = {};

    for (const failure of failures) {
      const errorKey = this.extractErrorKey(failure.errorMessage);
      
      if (!groups[errorKey]) {
        groups[errorKey] = [];
      }
      
      groups[errorKey].push(failure);
    }

    return groups;
  }

  /**
   * Extract error key from error message
   */
  private extractErrorKey(errorMessage: string): string {
    // Remove dynamic parts (numbers, IDs, etc.)
    return errorMessage
      .replace(/\d+/g, 'N')
      .replace(/[a-f0-9-]{36}/g, 'UUID')
      .replace(/https?:\/\/[^\s]+/g, 'URL')
      .substring(0, 100);
  }

  /**
   * Analyze error group
   */
  private analyzeErrorGroup(errorType: string, failures: TestFailure[]): AnalysisResult | null {
    const affectedTests = failures.map(f => f.testName);
    
    // Timeout errors
    if (errorType.toLowerCase().includes('timeout')) {
      return {
        severity: failures.length > 3 ? 'critical' : 'high',
        category: 'Timeout',
        issue: `${failures.length} test(s) failed due to timeout`,
        suggestion: 'Consider increasing timeout values or optimizing slow operations. Check for network issues or slow API responses.',
        affectedTests,
        confidence: 0.9,
      };
    }

    // Element not found errors
    if (errorType.toLowerCase().includes('not found') || errorType.toLowerCase().includes('locator')) {
      return {
        severity: 'high',
        category: 'Selector',
        issue: `${failures.length} test(s) failed to find elements`,
        suggestion: 'UI structure may have changed. Verify test IDs are still present. Consider using more stable selectors.',
        affectedTests,
        confidence: 0.85,
      };
    }

    // Assertion errors
    if (errorType.toLowerCase().includes('expect') || errorType.toLowerCase().includes('assertion')) {
      return {
        severity: 'medium',
        category: 'Assertion',
        issue: `${failures.length} test(s) failed assertion checks`,
        suggestion: 'Verify expected behavior matches actual implementation. Check if requirements have changed.',
        affectedTests,
        confidence: 0.8,
      };
    }

    // Network errors
    if (errorType.toLowerCase().includes('network') || errorType.toLowerCase().includes('fetch')) {
      return {
        severity: 'critical',
        category: 'Network',
        issue: `${failures.length} test(s) failed due to network issues`,
        suggestion: 'Check API availability and network connectivity. Consider adding API mocking for more stable tests.',
        affectedTests,
        confidence: 0.95,
      };
    }

    // Generic error
    return {
      severity: 'medium',
      category: 'Unknown',
      issue: `${failures.length} test(s) failed with similar errors`,
      suggestion: 'Review error messages and stack traces for common patterns. May require manual investigation.',
      affectedTests,
      confidence: 0.6,
    };
  }

  /**
   * Analyze performance
   */
  private analyzePerformance(result: TestResult): AnalysisResult[] {
    const analyses: AnalysisResult[] = [];

    // Slow test execution
    if (result.duration > 300000) { // 5 minutes
      analyses.push({
        severity: 'medium',
        category: 'Performance',
        issue: 'Test suite execution is slow',
        suggestion: 'Consider running tests in parallel, optimizing slow tests, or splitting into smaller suites.',
        affectedTests: [],
        confidence: 0.9,
      });
    }

    return analyses;
  }

  /**
   * Analyze patterns
   */
  private analyzePatterns(result: TestResult): AnalysisResult[] {
    const analyses: AnalysisResult[] = [];

    // High failure rate
    const failureRate = result.totalTests > 0 ? result.failedTests / result.totalTests : 0;
    
    if (failureRate > 0.5) {
      analyses.push({
        severity: 'critical',
        category: 'Stability',
        issue: `High failure rate: ${(failureRate * 100).toFixed(1)}%`,
        suggestion: 'Major issues detected. Review recent code changes, check test environment, and verify dependencies.',
        affectedTests: [],
        confidence: 0.95,
      });
    } else if (failureRate > 0.2) {
      analyses.push({
        severity: 'high',
        category: 'Stability',
        issue: `Elevated failure rate: ${(failureRate * 100).toFixed(1)}%`,
        suggestion: 'Multiple tests failing. Review recent changes and check for environmental issues.',
        affectedTests: [],
        confidence: 0.85,
      });
    }

    return analyses;
  }

  /**
   * Calculate test health metrics
   */
  calculateHealthMetrics(results: TestResult[]): TestHealthMetrics {
    if (results.length === 0) {
      return {
        overallHealth: 100,
        passRate: 100,
        avgDuration: 0,
        flakyTests: [],
        slowTests: [],
        failurePatterns: [],
        recommendations: [],
      };
    }

    const totalTests = results.reduce((sum, r) => sum + r.totalTests, 0);
    const passedTests = results.reduce((sum, r) => sum + r.passedTests, 0);
    const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / results.length;

    const passRate = totalTests > 0 ? (passedTests / totalTests) * 100 : 100;
    const overallHealth = this.calculateOverallHealth(passRate, avgDuration);

    // Detect flaky tests (tests that sometimes pass, sometimes fail)
    const flakyTests = this.detectFlakyTests(results);

    // Detect slow tests
    const slowTests = this.detectSlowTests(results);

    // Analyze failure patterns
    const failurePatterns = this.analyzeFailurePatterns(results);

    // Generate recommendations
    const recommendations = this.generateRecommendations({
      overallHealth,
      passRate,
      avgDuration,
      flakyTests,
      slowTests,
      failurePatterns,
      recommendations: [],
    });

    return {
      overallHealth,
      passRate,
      avgDuration,
      flakyTests,
      slowTests,
      failurePatterns,
      recommendations,
    };
  }

  /**
   * Calculate overall health score
   */
  private calculateOverallHealth(passRate: number, avgDuration: number): number {
    // Weight: 70% pass rate, 30% performance
    const passScore = passRate;
    const perfScore = avgDuration < 60000 ? 100 : Math.max(0, 100 - (avgDuration - 60000) / 1000);
    
    return Math.round(passScore * 0.7 + perfScore * 0.3);
  }

  /**
   * Detect flaky tests
   */
  private detectFlakyTests(results: TestResult[]): string[] {
    // This would require historical data
    // For now, return empty array
    return [];
  }

  /**
   * Detect slow tests
   */
  private detectSlowTests(results: TestResult[]): string[] {
    // This would require per-test timing data
    // For now, return empty array
    return [];
  }

  /**
   * Analyze failure patterns across multiple runs
   */
  private analyzeFailurePatterns(results: TestResult[]): AnalysisResult[] {
    const allFailures = results.flatMap(r => r.failures);
    return this.analyzeFailures(allFailures);
  }

  /**
   * Generate recommendations
   */
  private generateRecommendations(metrics: TestHealthMetrics): string[] {
    const recommendations: string[] = [];

    if (metrics.passRate < 80) {
      recommendations.push('🔴 Critical: Pass rate below 80%. Immediate attention required.');
    } else if (metrics.passRate < 95) {
      recommendations.push('🟡 Warning: Pass rate below 95%. Review failing tests.');
    }

    if (metrics.avgDuration > 300000) {
      recommendations.push('⚡ Performance: Tests are slow. Consider parallelization or optimization.');
    }

    if (metrics.flakyTests.length > 0) {
      recommendations.push(`🔄 Stability: ${metrics.flakyTests.length} flaky test(s) detected. Investigate and fix.`);
    }

    if (metrics.failurePatterns.length > 0) {
      const critical = metrics.failurePatterns.filter(p => p.severity === 'critical');
      if (critical.length > 0) {
        recommendations.push(`⚠️ Critical Issues: ${critical.length} critical pattern(s) detected.`);
      }
    }

    if (recommendations.length === 0) {
      recommendations.push('✅ All metrics look good! Keep up the great work.');
    }

    return recommendations;
  }

  /**
   * Generate human-readable report
   */
  generateReport(result: TestResult, analyses: AnalysisResult[]): string {
    const lines: string[] = [];

    lines.push('═══════════════════════════════════════════════════════');
    lines.push('           AI AGENT TEST ANALYSIS REPORT');
    lines.push('═══════════════════════════════════════════════════════');
    lines.push('');

    // Summary
    lines.push('📊 SUMMARY');
    lines.push('─────────────────────────────────────────────────────');
    lines.push(result.summary);
    lines.push(`Duration: ${(result.duration / 1000).toFixed(2)}s`);
    lines.push(`Status: ${result.success ? '✅ PASSED' : '❌ FAILED'}`);
    lines.push('');

    // Analyses
    if (analyses.length > 0) {
      lines.push('🔍 ANALYSIS');
      lines.push('─────────────────────────────────────────────────────');
      
      for (const analysis of analyses) {
        const icon = {
          critical: '🔴',
          high: '🟠',
          medium: '🟡',
          low: '🟢',
        }[analysis.severity];

        lines.push(`${icon} [${analysis.severity.toUpperCase()}] ${analysis.category}`);
        lines.push(`   Issue: ${analysis.issue}`);
        lines.push(`   Suggestion: ${analysis.suggestion}`);
        lines.push(`   Confidence: ${(analysis.confidence * 100).toFixed(0)}%`);
        
        if (analysis.affectedTests.length > 0) {
          lines.push(`   Affected: ${analysis.affectedTests.slice(0, 3).join(', ')}${analysis.affectedTests.length > 3 ? '...' : ''}`);
        }
        
        lines.push('');
      }
    }

    lines.push('═══════════════════════════════════════════════════════');

    return lines.join('\n');
  }
}

