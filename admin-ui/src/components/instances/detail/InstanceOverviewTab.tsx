'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Edit, Trash2 } from 'lucide-react';
import { useDeleteInstance } from '@/lib/hooks/useDeleteInstance';
import type { Instance } from '@/lib/api/types';

interface InstanceOverviewTabProps {
  instance: Instance;
}

export function InstanceOverviewTab({ instance }: InstanceOverviewTabProps) {
  const router = useRouter();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [confirmName, setConfirmName] = useState('');
  const deleteMutation = useDeleteInstance();

  const handleDelete = () => {
    if (confirmName !== instance.name) {
      return;
    }

    deleteMutation.mutate(instance.id, {
      onSuccess: () => {
        router.push('/admin/instances');
      },
    });
  };

  const getStatusBadge = (status: Instance['status']) => {
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

    return <Badge variant={variants[status] || 'default'}>{labels[status] || status}</Badge>;
  };

  const maskToken = (token: string = '••••••••') => {
    return '••••••••';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <CardDescription>Instance configuration details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p className="text-sm mt-1">{instance.name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Status</p>
              <div className="mt-1">{getStatusBadge(instance.status)}</div>
            </div>
            <div className="md:col-span-2">
              <p className="text-sm font-medium text-muted-foreground">Base URL</p>
              <a
                href={instance.baseUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm mt-1 text-primary hover:underline break-all"
              >
                {instance.baseUrl}
              </a>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Authentication Method</p>
              <p className="text-sm mt-1">
                {instance.authMethod === 'api_token' ? 'API Token' : 'OAuth 2.0'}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Email</p>
              <p className="text-sm mt-1">{instance.email}</p>
            </div>
            {instance.projectFilter && (
              <div className="md:col-span-2">
                <p className="text-sm font-medium text-muted-foreground">Project Filter</p>
                <p className="text-sm mt-1">{instance.projectFilter}</p>
              </div>
            )}
            <div className="md:col-span-2">
              <p className="text-sm font-medium text-muted-foreground">API Token</p>
              <p className="text-sm mt-1 font-mono">{maskToken()}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Created At</p>
              <p className="text-sm mt-1">
                {new Date(instance.createdAt).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Updated At</p>
              <p className="text-sm mt-1">
                {new Date(instance.updatedAt).toLocaleString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-4">
        <Button asChild>
          <Link href={`/admin/instances/${instance.id}/edit`}>
            <Edit className="mr-2 h-4 w-4" />
            Edit Instance
          </Link>
        </Button>
        <Button variant="destructive" onClick={() => setShowDeleteDialog(true)}>
          <Trash2 className="mr-2 h-4 w-4" />
          Delete Instance
        </Button>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Instance</DialogTitle>
            <DialogDescription>
              This action cannot be undone. This will permanently delete the instance and all
              associated data.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="confirm-name">
                Type <span className="font-bold">{instance.name}</span> to confirm
              </Label>
              <Input
                id="confirm-name"
                value={confirmName}
                onChange={(e) => setConfirmName(e.target.value)}
                placeholder="Instance name"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={confirmName !== instance.name || deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete Instance'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

