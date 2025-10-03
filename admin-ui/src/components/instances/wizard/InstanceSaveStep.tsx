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
    <div className="space-y-6">
      <Alert>
        <CheckCircle2 className="h-4 w-4" />
        <AlertDescription>
          Review your configuration below and click "Save" to create the instance.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Instance Configuration</CardTitle>
          <CardDescription>Review the details before saving</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p className="text-sm">{data.name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Base URL</p>
              <p className="text-sm break-all">{data.baseUrl}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Auth Method</p>
              <p className="text-sm">
                {data.authMethod === 'api_token' ? 'API Token' : 'OAuth 2.0'}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Email</p>
              <p className="text-sm">{data.email}</p>
            </div>
            {data.projectFilter && (
              <div className="col-span-2">
                <p className="text-sm font-medium text-muted-foreground">Project Filter</p>
                <p className="text-sm">{data.projectFilter}</p>
              </div>
            )}
            <div className="col-span-2">
              <p className="text-sm font-medium text-muted-foreground">API Token</p>
              <p className="text-sm font-mono">{maskToken(data.apiToken)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {createMutation.isError && (
        <Alert variant="destructive">
          <AlertDescription>
            {createMutation.error?.message || 'Failed to create instance. Please try again.'}
          </AlertDescription>
        </Alert>
      )}

      {createMutation.isSuccess && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
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
        >
          Back
        </Button>
        <Button
          onClick={handleSave}
          disabled={createMutation.isPending || createMutation.isSuccess}
        >
          {createMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : createMutation.isSuccess ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
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

