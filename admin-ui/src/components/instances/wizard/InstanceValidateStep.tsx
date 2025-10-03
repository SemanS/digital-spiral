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
    <div className="space-y-6">
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Test the connection to your Jira instance to verify your credentials before saving.
        </p>

        <Button
          onClick={handleTest}
          disabled={testMutation.isPending}
          className="w-full"
          size="lg"
        >
          {testMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Testing Connection...
            </>
          ) : (
            <>
              <TestTube className="mr-2 h-4 w-4" />
              Test Connection
            </>
          )}
        </Button>
      </div>

      {/* Test Result */}
      {testResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {testResult.success ? (
                <>
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  Connection Successful
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-destructive" />
                  Connection Failed
                </>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {testResult.success && testResult.user && (
              <div className="space-y-2">
                <div>
                  <p className="text-sm font-medium">User Information</p>
                  <p className="text-sm text-muted-foreground">
                    Name: {testResult.user.name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Email: {testResult.user.email}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Account ID: {testResult.user.accountId}
                  </p>
                </div>
                {testResult.rateLimit && (
                  <div>
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
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{testResult.error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <Button type="button" variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onNext} disabled={!isTestSuccessful}>
          Next
        </Button>
      </div>
    </div>
  );
}

