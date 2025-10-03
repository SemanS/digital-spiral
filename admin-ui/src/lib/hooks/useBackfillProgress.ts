import { useQuery } from '@tanstack/react-query';
import { getBackfillProgress } from '../api/instances';

export function useBackfillProgress(jobId: string | null, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['backfillProgress', jobId],
    queryFn: () => getBackfillProgress(jobId!),
    enabled: options?.enabled !== false && !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling if job is completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
    staleTime: 0, // Always fetch fresh data
  });
}

