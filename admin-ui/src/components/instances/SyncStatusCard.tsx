'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { formatDistanceToNow } from 'date-fns';
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import type { Instance } from '@/lib/api/types';

interface SyncStatusCardProps {
  instance: Instance;
  syncProgress?: {
    current: number;
    total: number;
    percentage: number;
  };
}

export function SyncStatusCard({ instance, syncProgress }: SyncStatusCardProps) {
  const getStatusIcon = () => {
    switch (instance.status) {
      case 'syncing':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-destructive" />;
      case 'idle':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusLabel = () => {
    switch (instance.status) {
      case 'syncing':
        return 'Syncing';
      case 'error':
        return 'Error';
      case 'idle':
        return 'Idle';
      default:
        return 'Unknown';
    }
  };

  const getStatusVariant = (): 'default' | 'secondary' | 'destructive' => {
    switch (instance.status) {
      case 'syncing':
        return 'secondary';
      case 'error':
        return 'destructive';
      default:
        return 'default';
    }
  };

  const formatLastSync = () => {
    if (!instance.lastSyncAt) return 'Never';
    try {
      return formatDistanceToNow(new Date(instance.lastSyncAt), { addSuffix: true });
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <CardTitle className="text-lg">Sync Status</CardTitle>
          </div>
          <Badge variant={getStatusVariant()}>{getStatusLabel()}</Badge>
        </div>
        <CardDescription>Current synchronization status</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Last Sync</span>
            <span className="font-medium">{formatLastSync()}</span>
          </div>

          {instance.status === 'syncing' && syncProgress && (
            <>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Progress</span>
                <span className="font-medium">
                  {syncProgress.current} / {syncProgress.total}
                </span>
              </div>
              <Progress value={syncProgress.percentage} className="h-2" />
              <div className="text-xs text-muted-foreground text-right">
                {syncProgress.percentage.toFixed(1)}% complete
              </div>
            </>
          )}

          {instance.status === 'error' && instance.lastError && (
            <div className="mt-2 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive font-medium">Error Details</p>
              <p className="text-xs text-destructive/80 mt-1">{instance.lastError}</p>
            </div>
          )}

          {instance.isActive ? (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              <span>Instance is active</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <XCircle className="h-4 w-4" />
              <span>Instance is inactive</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

