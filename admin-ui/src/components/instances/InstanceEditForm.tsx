'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, Loader2, TestTube } from 'lucide-react';
import { useUpdateInstance } from '@/lib/hooks/useUpdateInstance';
import { useTestConnection } from '@/lib/hooks/useTestConnection';
import { updateInstanceSchema, type UpdateInstanceFormData } from '@/lib/schemas/instance';
import type { Instance } from '@/lib/api/types';

interface InstanceEditFormProps {
  instance: Instance;
}

export function InstanceEditForm({ instance }: InstanceEditFormProps) {
  const router = useRouter();
  const [showToken, setShowToken] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; error?: string } | null>(null);

  const updateMutation = useUpdateInstance(instance.id);
  const testMutation = useTestConnection(instance.id);

  const form = useForm<UpdateInstanceFormData>({
    resolver: zodResolver(updateInstanceSchema),
    defaultValues: {
      name: instance.name,
      baseUrl: instance.baseUrl,
      authMethod: instance.authMethod,
      email: instance.email,
      apiToken: '', // Don't pre-fill for security
      projectFilter: instance.projectFilter || '',
    },
  });

  const onSubmit = (values: UpdateInstanceFormData) => {
    // Remove empty fields
    const data = Object.fromEntries(
      Object.entries(values).filter(([_, v]) => v !== '' && v !== undefined)
    ) as UpdateInstanceFormData;

    updateMutation.mutate(data, {
      onSuccess: () => {
        router.push(`/admin/instances/${instance.id}`);
      },
    });
  };

  const handleTestConnection = () => {
    testMutation.mutate(undefined, {
      onSuccess: (result) => {
        setTestResult(result);
      },
      onError: (error) => {
        setTestResult({
          success: false,
          error: error.message || 'Failed to test connection',
        });
      },
    });
  };

  const handleCancel = () => {
    router.push(`/admin/instances/${instance.id}`);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Instance Configuration</CardTitle>
        <CardDescription>
          Update the configuration for this Jira instance. Leave fields empty to keep current
          values.
        </CardDescription>
      </CardHeader>
      <CardContent>
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
                    <Input placeholder="https://your-domain.atlassian.net" {...field} />
                  </FormControl>
                  <FormDescription>The base URL of your Jira Cloud instance</FormDescription>
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
                    <Input placeholder="PROJ1,PROJ2" {...field} />
                  </FormControl>
                  <FormDescription>
                    Comma-separated list of project keys to sync. Leave empty to sync all projects.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="authMethod"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Authentication Method</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select authentication method" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="api_token">API Token</SelectItem>
                      <SelectItem value="oauth">OAuth 2.0</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>Choose how to authenticate with Jira</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="your-email@example.com" {...field} />
                  </FormControl>
                  <FormDescription>
                    The email address associated with your Jira account
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="apiToken"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>API Token (Optional)</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input
                        type={showToken ? 'text' : 'password'}
                        placeholder="Leave empty to keep current token"
                        {...field}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowToken(!showToken)}
                      >
                        {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </FormControl>
                  <FormDescription>
                    Only provide a new token if you want to update it. Generate from{' '}
                    <a
                      href="https://id.atlassian.com/manage-profile/security/api-tokens"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      Atlassian Account Settings
                    </a>
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Test Connection */}
            <div className="space-y-4 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={handleTestConnection}
                disabled={testMutation.isPending}
              >
                {testMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <TestTube className="mr-2 h-4 w-4" />
                    Test Connection
                  </>
                )}
              </Button>

              {testResult && (
                <Alert variant={testResult.success ? 'default' : 'destructive'}>
                  <AlertDescription>
                    {testResult.success
                      ? 'Connection test successful!'
                      : testResult.error || 'Connection test failed'}
                  </AlertDescription>
                </Alert>
              )}
            </div>

            {/* Error */}
            {updateMutation.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {updateMutation.error?.message || 'Failed to update instance. Please try again.'}
                </AlertDescription>
              </Alert>
            )}

            {/* Actions */}
            <div className="flex justify-between pt-4">
              <Button type="button" variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Changes'
                )}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

