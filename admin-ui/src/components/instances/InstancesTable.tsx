'use client';

import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { MoreHorizontal, Edit, Trash2, TestTube } from 'lucide-react';
import type { Instance } from '@/lib/api/types';

interface InstancesTableProps {
  instances: Instance[];
  onDelete?: (id: string) => void;
  onTestConnection?: (id: string) => void;
}

export function InstancesTable({ instances, onDelete, onTestConnection }: InstancesTableProps) {
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

    return (
      <Badge variant={variants[status] || 'default'}>
        {labels[status] || status}
      </Badge>
    );
  };

  const formatLastSync = (lastSync?: string) => {
    if (!lastSync) return 'Never';
    try {
      return formatDistanceToNow(new Date(lastSync), { addSuffix: true });
    } catch {
      return 'Invalid date';
    }
  };

  const getAuthMethodLabel = (authMethod: Instance['authMethod']) => {
    return authMethod === 'api_token' ? 'API Token' : 'OAuth';
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Base URL</TableHead>
            <TableHead>Auth Method</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last Sync</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {instances.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                No instances found
              </TableCell>
            </TableRow>
          ) : (
            instances.map((instance) => (
              <TableRow key={instance.id} className="hover:bg-muted/50">
                <TableCell className="font-medium">
                  <Link
                    href={`/admin/instances/${instance.id}`}
                    className="hover:underline"
                  >
                    {instance.name}
                  </Link>
                </TableCell>
                <TableCell>
                  <a
                    href={instance.baseUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-muted-foreground hover:underline"
                  >
                    {instance.baseUrl}
                  </a>
                </TableCell>
                <TableCell>{getAuthMethodLabel(instance.authMethod)}</TableCell>
                <TableCell>{getStatusBadge(instance.status)}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatLastSync(instance.lastSync)}
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <Link href={`/admin/instances/${instance.id}/edit`}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onTestConnection?.(instance.id)}
                      >
                        <TestTube className="mr-2 h-4 w-4" />
                        Test Connection
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => onDelete?.(instance.id)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}

