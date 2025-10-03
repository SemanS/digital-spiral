import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteInstance } from '../api/instances';
import { toast } from 'sonner';

export function useDeleteInstance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteInstance(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
      toast.success('Instance deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete instance');
    },
  });
}

