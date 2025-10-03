'use client';

import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

const errorMessages: Record<string, { title: string; description: string }> = {
  Configuration: {
    title: 'Configuration Error',
    description: 'There is a problem with the server configuration. Please contact support.',
  },
  AccessDenied: {
    title: 'Access Denied',
    description: 'You do not have permission to sign in.',
  },
  Verification: {
    title: 'Verification Failed',
    description: 'The verification token has expired or has already been used.',
  },
  OAuthSignin: {
    title: 'OAuth Sign In Error',
    description: 'Error occurred during OAuth sign in. Please try again.',
  },
  OAuthCallback: {
    title: 'OAuth Callback Error',
    description: 'Error occurred during OAuth callback. Please check your configuration.',
  },
  OAuthCreateAccount: {
    title: 'OAuth Account Creation Error',
    description: 'Could not create OAuth account. Please try again.',
  },
  EmailCreateAccount: {
    title: 'Email Account Creation Error',
    description: 'Could not create email account. Please try again.',
  },
  Callback: {
    title: 'Callback Error',
    description: 'Error occurred during callback. Please try again.',
  },
  OAuthAccountNotLinked: {
    title: 'Account Not Linked',
    description: 'This email is already associated with another account. Please sign in with the original provider.',
  },
  EmailSignin: {
    title: 'Email Sign In Error',
    description: 'Could not send sign in email. Please try again.',
  },
  CredentialsSignin: {
    title: 'Credentials Sign In Error',
    description: 'Sign in failed. Check the details you provided are correct.',
  },
  SessionRequired: {
    title: 'Session Required',
    description: 'Please sign in to access this page.',
  },
  Default: {
    title: 'Authentication Error',
    description: 'An error occurred during authentication. Please try again.',
  },
};

export default function AuthErrorPage() {
  const searchParams = useSearchParams();
  const error = searchParams.get('error') || 'Default';
  
  const errorInfo = errorMessages[error] || errorMessages.Default;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center text-2xl">Authentication Error</CardTitle>
          <CardDescription className="text-center">
            There was a problem signing you in
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>{errorInfo.title}</AlertTitle>
            <AlertDescription>{errorInfo.description}</AlertDescription>
          </Alert>

          {error === 'OAuthCallback' && (
            <Alert>
              <AlertDescription>
                <strong>Common causes:</strong>
                <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
                  <li>Invalid Google OAuth credentials</li>
                  <li>Incorrect redirect URI in Google Cloud Console</li>
                  <li>NEXTAUTH_URL environment variable mismatch</li>
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {error === 'Configuration' && (
            <Alert>
              <AlertDescription>
                <strong>Check your configuration:</strong>
                <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
                  <li>GOOGLE_CLIENT_ID is set correctly</li>
                  <li>GOOGLE_CLIENT_SECRET is set correctly</li>
                  <li>NEXTAUTH_SECRET is generated</li>
                  <li>NEXTAUTH_URL matches your domain</li>
                </ul>
              </AlertDescription>
            </Alert>
          )}

          <div className="flex flex-col gap-2">
            <Button asChild className="w-full">
              <Link href="/auth/signin">Try Again</Link>
            </Button>
            <Button asChild variant="outline" className="w-full">
              <Link href="/">Go Home</Link>
            </Button>
          </div>

          <div className="mt-4 rounded-md bg-gray-50 p-4">
            <p className="text-xs text-gray-500">
              <strong>Error Code:</strong> {error}
            </p>
            {process.env.NODE_ENV === 'development' && (
              <p className="mt-2 text-xs text-gray-500">
                <strong>Debug Info:</strong> Check the console for more details
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

