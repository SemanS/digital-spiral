import { useQuery } from '@tanstack/react-query';
import { getSyncHistory } from '../api/instances';

export function useSyncHistory(
  instanceId: string,
  params?: { page?: number; pageSize?: number }
) {
  return useQuery({
    queryKey: ['syncHistory', instanceId, params],
    queryFn: () => getSyncHistory(instanceId, params),
    enabled: !!instanceId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

