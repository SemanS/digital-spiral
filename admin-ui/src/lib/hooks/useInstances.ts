import { useQuery } from '@tanstack/react-query';
import { getInstances } from '../api/instances';
import type { GetInstancesParams } from '../api/types';

export function useInstances(params?: GetInstancesParams) {
  return useQuery({
    queryKey: ['instances', params],
    queryFn: () => getInstances(params),
    staleTime: 30 * 1000, // 30 seconds
  });
}

