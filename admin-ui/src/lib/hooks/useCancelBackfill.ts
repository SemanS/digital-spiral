import { useMutation, useQueryClient } from '@tanstack/react-query';
import { cancelBackfill } from '../api/instances';
import { toast } from 'sonner';

export function useCancelBackfill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => cancelBackfill(jobId),
    onSuccess: (data, jobId) => {
      queryClient.invalidateQueries({ queryKey: ['backfillProgress', jobId] });
      toast.success('Backfill cancelled successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to cancel backfill');
    },
  });
}

