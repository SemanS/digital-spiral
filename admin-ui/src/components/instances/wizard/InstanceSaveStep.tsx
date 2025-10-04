'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { useCreateInstance } from '@/lib/hooks/useCreateInstance';
import type { CreateInstanceFormData } from '@/lib/schemas/instance';

interface InstanceSaveStepProps {
  data: CreateInstanceFormData;
  onComplete: () => void;
  onBack: () => void;
}

export function InstanceSaveStep({ data, onComplete, onBack }: InstanceSaveStepProps) {
  const createMutation = useCreateInstance();

  const handleSave = () => {
    createMutation.mutate(data, {
      onSuccess: () => {
        setTimeout(() => {
          onComplete();
        }, 1500);
      },
    });
  };

  const maskToken = (token: string) => {
    if (token.length <= 8) return '••••••••';
    return token.substring(0, 4) + '••••••••' + token.substring(token.length - 4);
  };

  return (
    <div
      className="space-y-6"
      data-testid="instance-save-step"
    >
      <Alert data-testid="instance-save-info">
        <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
        <AlertDescription>
          Review your configuration below and click "Save" to create the instance.
        </AlertDescription>
      </Alert>

      <Card data-testid="instance-save-review">
        <CardHeader>
          <CardTitle>Instance Configuration</CardTitle>
          <CardDescription>Review the details before saving</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p
                className="text-sm"
                data-testid="review-instance-name"
              >
                {data.name}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Base URL</p>
              <p
                className="text-sm break-all"
                data-testid="review-instance-base-url"
              >
                {data.baseUrl}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Auth Method</p>
              <p
                className="text-sm"
                data-testid="review-instance-auth-method"
              >
                {data.authMethod === 'api_token' ? 'API Token' : 'OAuth 2.0'}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Email</p>
              <p
                className="text-sm"
                data-testid="review-instance-email"
              >
                {data.email}
              </p>
            </div>
            {data.projectFilter && (
              <div className="col-span-2">
                <p className="text-sm font-medium text-muted-foreground">Project Filter</p>
                <p
                  className="text-sm"
                  data-testid="review-instance-project-filter"
                >
                  {data.projectFilter}
                </p>
              </div>
            )}
            <div className="col-span-2">
              <p className="text-sm font-medium text-muted-foreground">API Token</p>
              <p
                className="text-sm font-mono"
                data-testid="review-instance-api-token"
              >
                {maskToken(data.apiToken)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {createMutation.isError && (
        <Alert
          variant="destructive"
          data-testid="instance-save-error"
        >
          <AlertDescription data-testid="save-error-message">
            {createMutation.error?.message || 'Failed to create instance. Please try again.'}
          </AlertDescription>
        </Alert>
      )}

      {createMutation.isSuccess && (
        <Alert data-testid="instance-save-success">
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
          <AlertDescription>
            Instance created successfully! Redirecting...
          </AlertDescription>
        </Alert>
      )}

      <div className="flex justify-between">
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          disabled={createMutation.isPending || createMutation.isSuccess}
          data-testid="instance-save-back-button"
          aria-label="Go back to validation step"
        >
          Back
        </Button>
        <Button
          onClick={handleSave}
          disabled={createMutation.isPending || createMutation.isSuccess}
          data-testid="instance-save-button"
          aria-label="Save instance configuration"
          aria-disabled={createMutation.isPending || createMutation.isSuccess}
        >
          {createMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              Saving...
            </>
          ) : createMutation.isSuccess ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" aria-hidden="true" />
              Saved
            </>
          ) : (
            'Save Instance'
          )}
        </Button>
      </div>
    </div>
  );
}

