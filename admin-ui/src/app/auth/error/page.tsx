import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

export default function AuthErrorPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const error = searchParams.error;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <AlertCircle className="h-12 w-12 text-destructive" />
          </div>
          <CardTitle className="text-2xl font-bold text-center">Authentication Error</CardTitle>
          <CardDescription className="text-center">
            {error === 'Configuration'
              ? 'There is a problem with the server configuration.'
              : error === 'AccessDenied'
              ? 'You do not have permission to sign in.'
              : error === 'Verification'
              ? 'The verification token has expired or has already been used.'
              : 'An error occurred during authentication.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild className="w-full" size="lg">
            <Link href="/auth/signin">Try again</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

