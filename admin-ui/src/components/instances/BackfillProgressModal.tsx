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
      <DialogContent
        className="sm:max-w-md"
        data-testid="backfill-progress-modal"
      >
        <DialogHeader>
          <DialogTitle
            className="flex items-center gap-2"
            data-testid="backfill-progress-title"
          >
            {isCompleted && (
              <CheckCircle2
                className="h-5 w-5 text-green-500"
                data-testid="backfill-status-completed-icon"
                aria-hidden="true"
              />
            )}
            {isFailed && (
              <XCircle
                className="h-5 w-5 text-destructive"
                data-testid="backfill-status-failed-icon"
                aria-hidden="true"
              />
            )}
            {isRunning && (
              <Loader2
                className="h-5 w-5 animate-spin"
                data-testid="backfill-status-running-icon"
                aria-hidden="true"
              />
            )}
            Backfill Progress
          </DialogTitle>
          <DialogDescription data-testid="backfill-progress-description">
            {isCompleted && 'Backfill completed successfully'}
            {isFailed && 'Backfill failed'}
            {isRunning && 'Syncing data from Jira...'}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div
            className="flex items-center justify-center py-8"
            data-testid="backfill-progress-loading"
          >
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" />
          </div>
        ) : progress ? (
          <div
            className="space-y-4"
            data-testid="backfill-progress-content"
          >
            {/* Overall Progress */}
            <div
              className="space-y-2"
              data-testid="backfill-overall-progress"
            >
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Overall Progress</span>
                <span
                  className="text-muted-foreground"
                  data-testid="backfill-overall-percentage"
                >
                  {progress.progress.percentage}%
                </span>
              </div>
              <Progress
                value={progress.progress.percentage}
                data-testid="backfill-overall-progress-bar"
                aria-label={`Overall progress: ${progress.progress.percentage}%`}
              />
              {progress.progress.eta && (
                <p
                  className="text-xs text-muted-foreground"
                  data-testid="backfill-eta"
                >
                  Estimated time remaining: {progress.progress.eta}
                </p>
              )}
            </div>

            {/* Detailed Progress */}
            <div
              className="space-y-3 pt-4 border-t"
              data-testid="backfill-detailed-progress"
            >
              <p className="text-sm font-medium">Detailed Progress</p>

              <div
                className="space-y-2"
                data-testid="backfill-projects-progress"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Projects</span>
                  <span data-testid="backfill-projects-count">
                    {progress.progress.projects.completed} / {progress.progress.projects.total}
                  </span>
                </div>
                <Progress
                  value={
                    (progress.progress.projects.completed / progress.progress.projects.total) * 100
                  }
                  className="h-2"
                  data-testid="backfill-projects-progress-bar"
                  aria-label={`Projects: ${progress.progress.projects.completed} of ${progress.progress.projects.total}`}
                />
              </div>

              <div
                className="space-y-2"
                data-testid="backfill-issues-progress"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Issues</span>
                  <span data-testid="backfill-issues-count">
                    {progress.progress.issues.completed.toLocaleString()} /{' '}
                    {progress.progress.issues.total.toLocaleString()}
                  </span>
                </div>
                <Progress
                  value={(progress.progress.issues.completed / progress.progress.issues.total) * 100}
                  className="h-2"
                  data-testid="backfill-issues-progress-bar"
                  aria-label={`Issues: ${progress.progress.issues.completed} of ${progress.progress.issues.total}`}
                />
              </div>

              <div
                className="space-y-2"
                data-testid="backfill-comments-progress"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Comments</span>
                  <span data-testid="backfill-comments-count">
                    {progress.progress.comments.completed.toLocaleString()} /{' '}
                    {progress.progress.comments.total.toLocaleString()}
                  </span>
                </div>
                <Progress
                  value={
                    (progress.progress.comments.completed / progress.progress.comments.total) * 100
                  }
                  className="h-2"
                  data-testid="backfill-comments-progress-bar"
                  aria-label={`Comments: ${progress.progress.comments.completed} of ${progress.progress.comments.total}`}
                />
              </div>
            </div>

            {/* Timestamps */}
            {progress.startedAt && (
              <div
                className="pt-4 border-t text-xs text-muted-foreground"
                data-testid="backfill-timestamps"
              >
                <p data-testid="backfill-started-at">
                  Started: {new Date(progress.startedAt).toLocaleString()}
                </p>
                {progress.completedAt && (
                  <p data-testid="backfill-completed-at">
                    Completed: {new Date(progress.completedAt).toLocaleString()}
                  </p>
                )}
              </div>
            )}

            {/* Error */}
            {isFailed && progress.error && (
              <Alert
                variant="destructive"
                data-testid="backfill-error-alert"
              >
                <XCircle className="h-4 w-4" aria-hidden="true" />
                <AlertDescription data-testid="backfill-error-message">
                  {progress.error}
                </AlertDescription>
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
              data-testid="backfill-cancel-button"
              aria-label="Cancel backfill operation"
              aria-disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? 'Cancelling...' : 'Cancel Backfill'}
            </Button>
          ) : (
            <Button
              onClick={() => onOpenChange(false)}
              data-testid="backfill-close-button"
              aria-label="Close progress modal"
            >
              Close
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

