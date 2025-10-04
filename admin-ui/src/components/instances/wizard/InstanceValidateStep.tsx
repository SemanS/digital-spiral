'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { CheckCircle2, XCircle, Loader2, TestTube } from 'lucide-react';
import { useTestConnection } from '@/lib/hooks/useTestConnection';
import type { CreateInstanceRequest } from '@/lib/api/types';

interface InstanceValidateStepProps {
  data: CreateInstanceRequest;
  onNext: () => void;
  onBack: () => void;
  onTestSuccess: () => void;
}

export function InstanceValidateStep({
  data,
  onNext,
  onBack,
  onTestSuccess,
}: InstanceValidateStepProps) {
  const [testResult, setTestResult] = useState<{
    success: boolean;
    user?: { name: string; email: string; accountId: string };
    rateLimit?: { limit: number; remaining: number; reset: number };
    error?: string;
  } | null>(null);

  const testMutation = useTestConnection();

  const handleTest = () => {
    testMutation.mutate(data, {
      onSuccess: (result) => {
        setTestResult(result);
        if (result.success) {
          onTestSuccess();
        }
      },
      onError: (error) => {
        setTestResult({
          success: false,
          error: error.message || 'Failed to test connection',
        });
      },
    });
  };

  const isTestSuccessful = testResult?.success === true;

  return (
    <div
      className="space-y-6"
      data-testid="instance-validate-step"
    >
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Test the connection to your Jira instance to verify your credentials before saving.
        </p>

        <Button
          onClick={handleTest}
          disabled={testMutation.isPending}
          className="w-full"
          size="lg"
          data-testid="instance-test-connection-button"
          aria-label="Test connection to Jira instance"
        >
          {testMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              Testing Connection...
            </>
          ) : (
            <>
              <TestTube className="mr-2 h-4 w-4" aria-hidden="true" />
              Test Connection
            </>
          )}
        </Button>
      </div>

      {/* Test Result */}
      {testResult && (
        <Card data-testid="instance-test-result">
          <CardHeader>
            <CardTitle
              className="flex items-center gap-2"
              data-testid="instance-test-result-title"
            >
              {testResult.success ? (
                <>
                  <CheckCircle2
                    className="h-5 w-5 text-green-500"
                    aria-hidden="true"
                    data-testid="test-success-icon"
                  />
                  Connection Successful
                </>
              ) : (
                <>
                  <XCircle
                    className="h-5 w-5 text-destructive"
                    aria-hidden="true"
                    data-testid="test-failure-icon"
                  />
                  Connection Failed
                </>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {testResult.success && testResult.user && (
              <div
                className="space-y-2"
                data-testid="instance-test-user-info"
              >
                <div>
                  <p className="text-sm font-medium">User Information</p>
                  <p
                    className="text-sm text-muted-foreground"
                    data-testid="test-user-name"
                  >
                    Name: {testResult.user.name}
                  </p>
                  <p
                    className="text-sm text-muted-foreground"
                    data-testid="test-user-email"
                  >
                    Email: {testResult.user.email}
                  </p>
                  <p
                    className="text-sm text-muted-foreground"
                    data-testid="test-user-account-id"
                  >
                    Account ID: {testResult.user.accountId}
                  </p>
                </div>
                {testResult.rateLimit && (
                  <div data-testid="test-rate-limit">
                    <p className="text-sm font-medium">Rate Limit</p>
                    <p className="text-sm text-muted-foreground">
                      {testResult.rateLimit.remaining} / {testResult.rateLimit.limit} requests
                      remaining
                    </p>
                  </div>
                )}
              </div>
            )}
            {!testResult.success && testResult.error && (
              <Alert
                variant="destructive"
                data-testid="instance-test-error"
              >
                <XCircle className="h-4 w-4" aria-hidden="true" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription data-testid="test-error-message">
                  {testResult.error}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          data-testid="instance-validate-back-button"
          aria-label="Go back to authentication step"
        >
          Back
        </Button>
        <Button
          onClick={onNext}
          disabled={!isTestSuccessful}
          data-testid="instance-validate-next-button"
          aria-label="Continue to save step"
          aria-disabled={!isTestSuccessful}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

