'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';

interface BackfillConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading?: boolean;
}

export function BackfillConfirmDialog({
  open,
  onOpenChange,
  onConfirm,
  isLoading,
}: BackfillConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="backfill-confirm-dialog">
        <DialogHeader>
          <DialogTitle data-testid="backfill-dialog-title">
            Start Full Backfill
          </DialogTitle>
          <DialogDescription data-testid="backfill-dialog-description">
            This will sync all historical data from your Jira instance
          </DialogDescription>
        </DialogHeader>

        <Alert
          variant="destructive"
          data-testid="backfill-warning-alert"
        >
          <AlertTriangle className="h-4 w-4" aria-hidden="true" />
          <AlertTitle>Warning</AlertTitle>
          <AlertDescription>
            <ul
              className="list-disc list-inside space-y-1 mt-2"
              data-testid="backfill-warning-list"
            >
              <li>This process can take several hours depending on your data size</li>
              <li>It will sync all projects, issues, comments, and attachments</li>
              <li>The instance will be in "syncing" state during this time</li>
              <li>You can monitor progress in the Sync tab</li>
            </ul>
          </AlertDescription>
        </Alert>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
            data-testid="backfill-cancel-button"
            aria-label="Cancel backfill"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            data-testid="backfill-confirm-button"
            aria-label="Confirm and start backfill"
            aria-disabled={isLoading}
          >
            {isLoading ? 'Starting...' : 'Start Backfill'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

