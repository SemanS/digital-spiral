'use client';

import { useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useBackfillProgress } from '@/lib/hooks/useBackfillProgress';
import { useCancelBackfill } from '@/lib/hooks/useCancelBackfill';
import { toast } from 'sonner';

interface BackfillProgressModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  jobId: string | null;
  onComplete?: () => void;
}

export function BackfillProgressModal({
  open,
  onOpenChange,
  jobId,
  onComplete,
}: BackfillProgressModalProps) {
  const { data: progress, isLoading } = useBackfillProgress(jobId, { enabled: open && !!jobId });
  const cancelMutation = useCancelBackfill();

  // Handle completion
  useEffect(() => {
    if (progress?.status === 'completed') {
      toast.success('Backfill completed successfully!');
      setTimeout(() => {
        onComplete?.();
        onOpenChange(false);
      }, 2000);
    } else if (progress?.status === 'failed') {
      toast.error('Backfill failed');
    }
  }, [progress?.status, onComplete, onOpenChange]);

  const handleCancel = () => {
    if (jobId && confirm('Are you sure you want to cancel the backfill?')) {
      cancelMutation.mutate(jobId, {
        onSuccess: () => {
          onOpenChange(false);
        },
      });
    }
  };

  const isRunning = progress?.status === 'running' || progress?.status === 'pending';
  const isCompleted = progress?.status === 'completed';
  const isFailed = progress?.status === 'failed';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isCompleted && <CheckCircle2 className="h-5 w-5 text-green-500" />}
            {isFailed && <XCircle className="h-5 w-5 text-destructive" />}
            {isRunning && <Loader2 className="h-5 w-5 animate-spin" />}
            Backfill Progress
          </DialogTitle>
          <DialogDescription>
            {isCompleted && 'Backfill completed successfully'}
            {isFailed && 'Backfill failed'}
            {isRunning && 'Syncing data from Jira...'}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : progress ? (
          <div className="space-y-4">
            {/* Overall Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Overall Progress</span>
                <span className="text-muted-foreground">
                  {progress.progress.percentage}%
                </span>
              </div>
              <Progress value={progress.progress.percentage} />
              {progress.progress.eta && (
                <p className="text-xs text-muted-foreground">
                  Estimated time remaining: {progress.progress.eta}
                </p>
              )}
            </div>

            {/* Detailed Progress */}
            <div className="space-y-3 pt-4 border-t">
              <p className="text-sm font-medium">Detailed Progress</p>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Projects</span>
                  <span>
                    {progress.progress.projects.completed} / {progress.progress.projects.total}
                  </span>
                </div>
                <Progress
                  value={
                    (progress.progress.projects.completed / progress.progress.projects.total) * 100
                  }
                  className="h-2"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Issues</span>
                  <span>
                    {progress.progress.issues.completed.toLocaleString()} /{' '}
                    {progress.progress.issues.total.toLocaleString()}
                  </span>
                </div>
                <Progress
                  value={(progress.progress.issues.completed / progress.progress.issues.total) * 100}
                  className="h-2"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Comments</span>
                  <span>
                    {progress.progress.comments.completed.toLocaleString()} /{' '}
                    {progress.progress.comments.total.toLocaleString()}
                  </span>
                </div>
                <Progress
                  value={
                    (progress.progress.comments.completed / progress.progress.comments.total) * 100
                  }
                  className="h-2"
                />
              </div>
            </div>

            {/* Timestamps */}
            {progress.startedAt && (
              <div className="pt-4 border-t text-xs text-muted-foreground">
                <p>Started: {new Date(progress.startedAt).toLocaleString()}</p>
                {progress.completedAt && (
                  <p>Completed: {new Date(progress.completedAt).toLocaleString()}</p>
                )}
              </div>
            )}

            {/* Error */}
            {isFailed && progress.error && (
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertDescription>{progress.error}</AlertDescription>
              </Alert>
            )}
          </div>
        ) : null}

        <DialogFooter>
          {isRunning ? (
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? 'Cancelling...' : 'Cancel Backfill'}
            </Button>
          ) : (
            <Button onClick={() => onOpenChange(false)}>Close</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

