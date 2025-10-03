'use client';

import { useState, useEffect } from 'react';
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
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, ExternalLink, CheckCircle2 } from 'lucide-react';
import { instanceAuthSchema, type InstanceAuthFormData } from '@/lib/schemas/instance';

interface InstanceAuthStepProps {
  data: Partial<InstanceAuthFormData>;
  onNext: (data: InstanceAuthFormData) => void;
  onBack: () => void;
}

export function InstanceAuthStep({ data, onNext, onBack }: InstanceAuthStepProps) {
  const [showToken, setShowToken] = useState(false);
  const [isLoadingOAuth, setIsLoadingOAuth] = useState(false);
  const [oauthSuccess, setOauthSuccess] = useState(false);

  const form = useForm<InstanceAuthFormData>({
    resolver: zodResolver(instanceAuthSchema),
    defaultValues: {
      authMethod: data.authMethod || 'api_token',
      email: data.email || '',
      apiToken: data.apiToken || '',
    },
  });

  const authMethod = form.watch('authMethod');

  // Check for OAuth callback params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const success = params.get('success');
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    const siteUrl = params.get('site_url');
    const siteName = params.get('site_name');
    const error = params.get('error');

    if (error) {
      alert(`OAuth failed: ${error}\n${params.get('error_description') || ''}`);
      return;
    }

    if (success === 'true' && accessToken) {
      // Store OAuth tokens
      form.setValue('authMethod', 'oauth');
      form.setValue('apiToken', accessToken);
      if (refreshToken) {
        // Store refresh token in session storage for later use
        sessionStorage.setItem('oauth_refresh_token', refreshToken);
      }
      setOauthSuccess(true);

      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [form]);

  const handleOAuthStart = async () => {
    setIsLoadingOAuth(true);
    try {
      console.log('Starting OAuth flow...');
      const response = await fetch('http://localhost:8000/api/oauth/start');
      console.log('OAuth response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('OAuth response error:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('OAuth data:', data);

      if (data.auth_url) {
        // Redirect to Atlassian OAuth
        console.log('Redirecting to:', data.auth_url);
        window.location.href = data.auth_url;
      } else {
        throw new Error('No auth URL returned');
      }
    } catch (error) {
      console.error('OAuth start failed:', error);
      alert(`Failed to start OAuth flow: ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease check:\n1. Backend is running on http://localhost:8000\n2. Browser console for details`);
      setIsLoadingOAuth(false);
    }
  };

  const onSubmit = (values: InstanceAuthFormData) => {
    onNext(values);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
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
              <FormDescription>
                Choose how to authenticate with Jira
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {authMethod === 'oauth' && oauthSuccess && (
          <Alert>
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>
              OAuth authentication successful! You can now proceed to the next step.
            </AlertDescription>
          </Alert>
        )}

        {authMethod === 'oauth' && !oauthSuccess ? (
          <div className="space-y-4">
            <Alert>
              <AlertDescription>
                Click the button below to authenticate with Atlassian. You will be redirected to Atlassian's login page.
              </AlertDescription>
            </Alert>
            <Button
              type="button"
              onClick={handleOAuthStart}
              disabled={isLoadingOAuth}
              className="w-full"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              {isLoadingOAuth ? 'Redirecting...' : 'Connect with Atlassian'}
            </Button>
          </div>
        ) : authMethod === 'api_token' ? (
          <>
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
                    />
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
                  <FormLabel>API Token</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input
                        type={showToken ? 'text' : 'password'}
                        placeholder="Enter your Jira API token"
                        {...field}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowToken(!showToken)}
                      >
                        {showToken ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
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
                    >
                      Atlassian Account Settings
                    </a>
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </>
        ) : null}

        <div className="flex justify-between">
          <Button type="button" variant="outline" onClick={onBack}>
            Back
          </Button>
          <Button
            type="submit"
            disabled={authMethod === 'oauth' && !oauthSuccess}
          >
            Next
          </Button>
        </div>
      </form>
    </Form>
  );
}

