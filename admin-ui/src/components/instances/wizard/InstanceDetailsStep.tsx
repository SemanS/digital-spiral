'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { instanceDetailsSchema, type InstanceDetailsFormData } from '@/lib/schemas/instance';

interface InstanceDetailsStepProps {
  data: Partial<InstanceDetailsFormData>;
  onNext: (data: InstanceDetailsFormData) => void;
}

export function InstanceDetailsStep({ data, onNext }: InstanceDetailsStepProps) {
  const form = useForm<InstanceDetailsFormData>({
    resolver: zodResolver(instanceDetailsSchema),
    defaultValues: {
      name: data.name || '',
      baseUrl: data.baseUrl || '',
      projectFilter: data.projectFilter || '',
    },
  });

  const onSubmit = (values: InstanceDetailsFormData) => {
    onNext(values);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Instance Name</FormLabel>
              <FormControl>
                <Input placeholder="My Jira Instance" {...field} />
              </FormControl>
              <FormDescription>
                A friendly name to identify this Jira instance
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="baseUrl"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Base URL</FormLabel>
              <FormControl>
                <Input
                  placeholder="https://your-domain.atlassian.net"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                The base URL of your Jira Cloud instance
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="projectFilter"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Filter (Optional)</FormLabel>
              <FormControl>
                <Input
                  placeholder="PROJ1,PROJ2"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                Comma-separated list of project keys to sync. Leave empty to sync all projects.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end">
          <Button type="submit">Next</Button>
        </div>
      </form>
    </Form>
  );
}

