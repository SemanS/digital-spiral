'use client';

import { use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import { useInstance } from '@/lib/hooks/useInstance';
import { InstanceEditForm } from '@/components/instances/InstanceEditForm';
import { InstanceDetailSkeleton } from '@/components/instances/detail/InstanceDetailSkeleton';

interface EditInstancePageProps {
  params: Promise<{ id: string }>;
}

export default function EditInstancePage({ params }: EditInstancePageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { data: instance, isLoading, isError, error } = useInstance(id);

  if (isLoading) {
    return <InstanceDetailSkeleton />;
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            {error?.message || 'Failed to load instance. The instance may not exist.'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!instance) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Not Found</AlertTitle>
          <AlertDescription>Instance not found.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/admin/instances" className="hover:text-foreground">
          Instances
        </Link>
        <span>/</span>
        <Link href={`/admin/instances/${id}`} className="hover:text-foreground">
          {instance.name}
        </Link>
        <span>/</span>
        <span className="text-foreground">Edit</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Edit Instance</h1>
        <p className="text-muted-foreground mt-2">Update the configuration for {instance.name}</p>
      </div>

      {/* Edit Form */}
      <InstanceEditForm instance={instance} />
    </div>
  );
}

