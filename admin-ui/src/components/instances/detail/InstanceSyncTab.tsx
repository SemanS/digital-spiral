'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { RefreshCw, Database, AlertCircle, Loader2 } from 'lucide-react';
import { useSyncStatus } from '@/lib/hooks/useSyncStatus';
import { useStartBackfill } from '@/lib/hooks/useStartBackfill';
import { useStartResync } from '@/lib/hooks/useStartResync';
import { BackfillConfirmDialog } from '../BackfillConfirmDialog';
import { BackfillProgressModal } from '../BackfillProgressModal';
import { formatDistanceToNow } from 'date-fns';

interface InstanceSyncTabProps {
  instanceId: string;
}

export function InstanceSyncTab({ instanceId }: InstanceSyncTabProps) {
  const [showBackfillDialog, setShowBackfillDialog] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const { data: syncStatus, isLoading, isError, error, refetch } = useSyncStatus(instanceId, {
    enabled: true,
    refetchInterval: 5000, // Always poll for real-time updates
  });

  const startBackfillMutation = useStartBackfill();
  const startResyncMutation = useStartResync();

  const getStatusBadge = (status: string) => {
    const variants = {
      idle: 'default',
      syncing: 'secondary',
      error: 'destructive',
    } as const;

    const labels = {
      idle: 'Idle',
      syncing: 'Syncing',
      error: 'Error',
    };

    return (
      <Badge variant={variants[status as keyof typeof variants] || 'default'}>
        {labels[status as keyof typeof labels] || status}
      </Badge>
    );
  };

  const handleBackfill = () => {
    setShowBackfillDialog(true);
  };

  const handleConfirmBackfill = () => {
    startBackfillMutation.mutate(instanceId, {
      onSuccess: (data) => {
        setCurrentJobId(data.jobId);
        setShowBackfillDialog(false);
        setShowProgressModal(true);
      },
    });
  };

  const handleResync = () => {
    startResyncMutation.mutate(instanceId, {
      onSuccess: (data) => {
        setCurrentJobId(data.jobId);
        setShowProgressModal(true);
      },
    });
  };

  const handleProgressComplete = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          {error?.message || 'Failed to load sync status'}
        </AlertDescription>
      </Alert>
    );
  }

  const isSyncing = syncStatus?.status === 'syncing';

  return (
    <div className="space-y-6">
      {/* Sync Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Sync Status</CardTitle>
              <CardDescription>Current synchronization status</CardDescription>
            </div>
            {syncStatus && getStatusBadge(syncStatus.status)}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Watermark */}
          {syncStatus?.watermark && (
            <div>
              <p className="text-sm font-medium text-muted-foreground">Last Updated Issue</p>
              <p className="text-sm mt-1">
                {formatDistanceToNow(new Date(syncStatus.watermark), { addSuffix: true })}
              </p>
            </div>
          )}

          {/* Progress (if syncing) */}
          {isSyncing && syncStatus?.progress && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Progress</p>
                <p className="text-sm text-muted-foreground">
                  {syncStatus.progress.percentage}%
                </p>
              </div>
              <Progress value={syncStatus.progress.percentage} />
              {syncStatus.progress.eta && (
                <p className="text-xs text-muted-foreground">
                  Estimated time remaining: {syncStatus.progress.eta}
                </p>
              )}
            </div>
          )}

          {/* Statistics */}
          {syncStatus?.statistics && (
            <div className="grid grid-cols-3 gap-4 pt-4 border-t">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Issues</p>
                <p className="text-2xl font-bold">{syncStatus.statistics.totalIssues}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Projects</p>
                <p className="text-2xl font-bold">{syncStatus.statistics.totalProjects}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Users</p>
                <p className="text-2xl font-bold">{syncStatus.statistics.totalUsers}</p>
              </div>
            </div>
          )}

          {/* Detailed Progress (if syncing) */}
          {isSyncing && syncStatus?.progress && (
            <div className="space-y-3 pt-4 border-t">
              <p className="text-sm font-medium">Detailed Progress</p>
              {syncStatus.progress.projects && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Projects</span>
                  <span>
                    {syncStatus.progress.projects.completed} / {syncStatus.progress.projects.total}
                  </span>
                </div>
              )}
              {syncStatus.progress.issues && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Issues</span>
                  <span>
                    {syncStatus.progress.issues.completed} / {syncStatus.progress.issues.total}
                  </span>
                </div>
              )}
              {syncStatus.progress.comments && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Comments</span>
                  <span>
                    {syncStatus.progress.comments.completed} /{' '}
                    {syncStatus.progress.comments.total}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Error */}
          {syncStatus?.error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{syncStatus.error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-4">
        <Button onClick={handleBackfill} disabled={isSyncing}>
          <Database className="mr-2 h-4 w-4" />
          Start Backfill
        </Button>
        <Button variant="outline" onClick={handleResync} disabled={isSyncing}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Resync
        </Button>
      </div>

      {/* Backfill Confirmation Dialog */}
      <BackfillConfirmDialog
        open={showBackfillDialog}
        onOpenChange={setShowBackfillDialog}
        onConfirm={handleConfirmBackfill}
        isLoading={startBackfillMutation.isPending}
      />

      {/* Backfill Progress Modal */}
      <BackfillProgressModal
        open={showProgressModal}
        onOpenChange={setShowProgressModal}
        jobId={currentJobId}
        onComplete={handleProgressComplete}
      />
    </div>
  );
}

