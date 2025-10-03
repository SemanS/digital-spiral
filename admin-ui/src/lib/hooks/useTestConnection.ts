import { useMutation } from '@tanstack/react-query';
import { testConnection, testConnectionWithCredentials } from '../api/instances';
import type { CreateInstanceRequest } from '../api/types';
import { toast } from 'sonner';

export function useTestConnection(id?: string) {
  return useMutation({
    mutationFn: (data?: CreateInstanceRequest) => {
      if (id) {
        return testConnection(id);
      }
      if (data) {
        return testConnectionWithCredentials(data);
      }
      throw new Error('Either id or data must be provided');
    },
    onSuccess: (result) => {
      if (result.success) {
        toast.success('Connection test successful');
      } else {
        toast.error(result.error || 'Connection test failed');
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to test connection');
    },
  });
}

