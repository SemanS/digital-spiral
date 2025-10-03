'use client';

import { useState } from 'react';
import { formatDistanceToNow, formatDuration, intervalToDuration } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useSyncHistory } from '@/lib/hooks/useSyncHistory';
import { InstancesPagination } from '../InstancesPagination';

interface InstanceHistoryTabProps {
  instanceId: string;
}

export function InstanceHistoryTab({ instanceId }: InstanceHistoryTabProps) {
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, isError, error } = useSyncHistory(instanceId, {
    page,
    pageSize,
  });

  const getStatusBadge = (status: string) => {
    const variants = {
      completed: 'default',
      failed: 'destructive',
      cancelled: 'secondary',
    } as const;

    const labels = {
      completed: 'Completed',
      failed: 'Failed',
      cancelled: 'Cancelled',
    };

    return (
      <Badge variant={variants[status as keyof typeof variants] || 'default'}>
        {labels[status as keyof typeof labels] || status}
      </Badge>
    );
  };

  const formatDurationMs = (ms?: number) => {
    if (!ms) return 'N/A';
    const duration = intervalToDuration({ start: 0, end: ms });
    return formatDuration(duration, { format: ['hours', 'minutes', 'seconds'] });
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
          {error?.message || 'Failed to load sync history'}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Sync History</CardTitle>
          <CardDescription>Recent synchronization runs</CardDescription>
        </CardHeader>
        <CardContent>
          {data && data.data.length > 0 ? (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Started At</TableHead>
                      <TableHead>Completed At</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Issues Synced</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.data.map((history) => (
                      <TableRow key={history.id}>
                        <TableCell className="text-sm">
                          {formatDistanceToNow(new Date(history.startedAt), {
                            addSuffix: true,
                          })}
                        </TableCell>
                        <TableCell className="text-sm">
                          {history.completedAt
                            ? formatDistanceToNow(new Date(history.completedAt), {
                                addSuffix: true,
                              })
                            : 'In progress'}
                        </TableCell>
                        <TableCell className="text-sm">
                          {formatDurationMs(history.duration)}
                        </TableCell>
                        <TableCell>{getStatusBadge(history.status)}</TableCell>
                        <TableCell className="text-right font-medium">
                          {history.issuesSynced.toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              {data.pagination.total > pageSize && (
                <div className="mt-4">
                  <InstancesPagination
                    currentPage={data.pagination.page}
                    totalPages={data.pagination.totalPages}
                    totalItems={data.pagination.total}
                    pageSize={data.pagination.pageSize}
                    onPageChange={setPage}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No sync history available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

