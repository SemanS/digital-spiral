'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { TestTube, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { useTestConnection } from '@/lib/hooks/useTestConnection';

interface TestConnectionButtonProps {
  instanceId?: string;
  instanceData?: {
    baseUrl: string;
    email: string;
    apiToken: string;
  };
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

export function TestConnectionButton({
  instanceId,
  instanceData,
  onSuccess,
  onError,
}: TestConnectionButtonProps) {
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const testConnection = useTestConnection();

  const handleTest = async () => {
    setTestStatus('testing');

    try {
      if (instanceId) {
        await testConnection.mutateAsync({ instanceId });
      } else if (instanceData) {
        await testConnection.mutateAsync({ data: instanceData });
      }

      setTestStatus('success');
      onSuccess?.();

      // Reset status after 3 seconds
      setTimeout(() => setTestStatus('idle'), 3000);
    } catch (error) {
      setTestStatus('error');
      onError?.(error as Error);

      // Reset status after 3 seconds
      setTimeout(() => setTestStatus('idle'), 3000);
    }
  };

  const getButtonContent = () => {
    switch (testStatus) {
      case 'testing':
        return (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Testing...
          </>
        );
      case 'success':
        return (
          <>
            <CheckCircle2 className="mr-2 h-4 w-4" />
            Success
          </>
        );
      case 'error':
        return (
          <>
            <XCircle className="mr-2 h-4 w-4" />
            Failed
          </>
        );
      default:
        return (
          <>
            <TestTube className="mr-2 h-4 w-4" />
            Test Connection
          </>
        );
    }
  };

  const getButtonVariant = () => {
    switch (testStatus) {
      case 'success':
        return 'default';
      case 'error':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <Button
      type="button"
      variant={getButtonVariant()}
      onClick={handleTest}
      disabled={testStatus === 'testing' || (!instanceId && !instanceData)}
    >
      {getButtonContent()}
    </Button>
  );
}

