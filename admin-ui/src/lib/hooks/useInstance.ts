import { useQuery } from '@tanstack/react-query';
import { getInstance } from '../api/instances';

export function useInstance(id: string) {
  return useQuery({
    queryKey: ['instance', id],
    queryFn: () => getInstance(id),
    enabled: !!id,
    staleTime: 30 * 1000, // 30 seconds
  });
}

