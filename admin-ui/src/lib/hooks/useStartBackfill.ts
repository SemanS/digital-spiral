import { useMutation, useQueryClient } from '@tanstack/react-query';
import { startBackfill } from '../api/instances';
import { toast } from 'sonner';

export function useStartBackfill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (instanceId: string) => startBackfill(instanceId),
    onSuccess: (data, instanceId) => {
      queryClient.invalidateQueries({ queryKey: ['syncStatus', instanceId] });
      toast.success('Backfill started successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to start backfill');
    },
  });
}

