'use client';

import { useState } from 'react';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Eye, EyeOff } from 'lucide-react';
import { instanceAuthSchema, type InstanceAuthFormData } from '@/lib/schemas/instance';

interface InstanceAuthStepProps {
  data: Partial<InstanceAuthFormData>;
  onNext: (data: InstanceAuthFormData) => void;
  onBack: () => void;
}

export function InstanceAuthStep({ data, onNext, onBack }: InstanceAuthStepProps) {
  const [showToken, setShowToken] = useState(false);

  const form = useForm<InstanceAuthFormData>({
    resolver: zodResolver(instanceAuthSchema),
    defaultValues: {
      authMethod: data.authMethod || 'api_token',
      email: data.email || '',
      apiToken: data.apiToken || '',
    },
  });

  const onSubmit = (values: InstanceAuthFormData) => {
    onNext(values);
  };

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-6"
        data-testid="instance-auth-form"
      >
        <FormField
          control={form.control}
          name="authMethod"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Authentication Method</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger data-testid="instance-auth-method-select">
                    <SelectValue placeholder="Select authentication method" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem
                    value="api_token"
                    data-testid="auth-method-api-token"
                  >
                    API Token
                  </SelectItem>
                  <SelectItem
                    value="oauth"
                    data-testid="auth-method-oauth"
                  >
                    OAuth 2.0
                  </SelectItem>
                </SelectContent>
              </Select>
              <FormDescription>
                Choose how to authenticate with Jira
              </FormDescription>
              <FormMessage data-testid="instance-auth-method-error" />
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
                <Input
                  type="email"
                  placeholder="your-email@example.com"
                  {...field}
                  data-testid="instance-email-input"
                  aria-label="Email address"
                />
              </FormControl>
              <FormDescription>
                The email address associated with your Jira account
              </FormDescription>
              <FormMessage data-testid="instance-email-error" />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="apiToken"
          render={({ field }) => (
            <FormItem>
              <FormLabel>API Token</FormLabel>
              <FormControl>
                <div className="relative">
                  <Input
                    type={showToken ? 'text' : 'password'}
                    placeholder="Enter your Jira API token"
                    {...field}
                    data-testid="instance-api-token-input"
                    aria-label="API token"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowToken(!showToken)}
                    data-testid="instance-api-token-toggle"
                    aria-label={showToken ? "Hide API token" : "Show API token"}
                  >
                    {showToken ? (
                      <EyeOff className="h-4 w-4" aria-hidden="true" />
                    ) : (
                      <Eye className="h-4 w-4" aria-hidden="true" />
                    )}
                  </Button>
                </div>
              </FormControl>
              <FormDescription>
                Generate an API token from{' '}
                <a
                  href="https://id.atlassian.com/manage-profile/security/api-tokens"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                  data-testid="instance-api-token-link"
                  aria-label="Open Atlassian Account Settings in new tab"
                >
                  Atlassian Account Settings
                </a>
              </FormDescription>
              <FormMessage data-testid="instance-api-token-error" />
            </FormItem>
          )}
        />

        <div className="flex justify-between">
          <Button
            type="button"
            variant="outline"
            onClick={onBack}
            data-testid="instance-auth-back-button"
            aria-label="Go back to details step"
          >
            Back
          </Button>
          <Button
            type="submit"
            data-testid="instance-auth-next-button"
            aria-label="Continue to validation step"
          >
            Next
          </Button>
        </div>
      </form>
    </Form>
  );
}

