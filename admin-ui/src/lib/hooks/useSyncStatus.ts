import { useQuery } from '@tanstack/react-query';
import { getSyncStatus } from '../api/instances';

export function useSyncStatus(id: string, options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: ['syncStatus', id],
    queryFn: () => getSyncStatus(id),
    enabled: options?.enabled !== false && !!id,
    refetchInterval: options?.refetchInterval || 5000, // Poll every 5 seconds by default
    staleTime: 0, // Always fetch fresh data
  });
}

