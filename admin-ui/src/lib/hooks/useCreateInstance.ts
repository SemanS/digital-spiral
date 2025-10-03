import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createInstance } from '../api/instances';
import type { CreateInstanceRequest } from '../api/types';
import { toast } from 'sonner';

export function useCreateInstance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateInstanceRequest) => createInstance(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
      toast.success('Instance created successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create instance');
    },
  });
}

