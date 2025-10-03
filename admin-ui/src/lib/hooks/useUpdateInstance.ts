import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateInstance } from '../api/instances';
import type { UpdateInstanceRequest } from '../api/types';
import { toast } from 'sonner';

export function useUpdateInstance(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateInstanceRequest) => updateInstance(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
      queryClient.invalidateQueries({ queryKey: ['instance', id] });
      toast.success('Instance updated successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update instance');
    },
  });
}

