import { useMutation, useQueryClient } from '@tanstack/react-query';
import { startResync } from '../api/instances';
import { toast } from 'sonner';

export function useStartResync() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (instanceId: string) => startResync(instanceId),
    onSuccess: (data, instanceId) => {
      queryClient.invalidateQueries({ queryKey: ['syncStatus', instanceId] });
      toast.success('Resync started successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to start resync');
    },
  });
}

