'use client';

import { use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import { useInstance } from '@/lib/hooks/useInstance';
import { InstanceOverviewTab } from '@/components/instances/detail/InstanceOverviewTab';
import { InstanceSyncTab } from '@/components/instances/detail/InstanceSyncTab';
import { InstanceHistoryTab } from '@/components/instances/detail/InstanceHistoryTab';
import { InstanceDetailSkeleton } from '@/components/instances/detail/InstanceDetailSkeleton';

interface InstanceDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function InstanceDetailPage({ params }: InstanceDetailPageProps) {
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
        <span className="text-foreground">{instance.name}</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{instance.name}</h1>
          <p className="text-muted-foreground mt-2">{instance.baseUrl}</p>
        </div>
        <Button variant="outline" asChild>
          <Link href={`/admin/instances/${id}/edit`}>Edit</Link>
        </Button>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sync">Sync</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <InstanceOverviewTab instance={instance} />
        </TabsContent>

        <TabsContent value="sync" className="space-y-4">
          <InstanceSyncTab instanceId={id} />
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <InstanceHistoryTab instanceId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

