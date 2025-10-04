'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Instances page error:', error);
  }, [error]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Jira Instances</h1>
        <p className="text-muted-foreground mt-2">Manage your Jira Cloud instances</p>
      </div>

      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>An unexpected error occurred</AlertTitle>
        <AlertDescription>
          {error.message || 'Failed to load instances. Please try again.'}
        </AlertDescription>
      </Alert>

      <div className="flex gap-4">
        <Button onClick={reset}>Try again</Button>
        <Button variant="outline" onClick={() => window.location.href = '/admin/instances'}>
          Refresh page
        </Button>
      </div>
    </div>
  );
}

