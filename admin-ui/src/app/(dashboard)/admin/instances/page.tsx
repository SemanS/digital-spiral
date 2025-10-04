'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Plus, AlertCircle } from 'lucide-react';
import { useInstances } from '@/lib/hooks/useInstances';
import { useDeleteInstance } from '@/lib/hooks/useDeleteInstance';
import { useTestConnection } from '@/lib/hooks/useTestConnection';
import { InstancesTable } from '@/components/instances/InstancesTable';
import { InstancesTableSkeleton } from '@/components/instances/InstancesTableSkeleton';
import { InstancesFilters } from '@/components/instances/InstancesFilters';
import { InstancesPagination } from '@/components/instances/InstancesPagination';
import type { SyncStatusType, AuthMethod } from '@/lib/api/types';

export default function InstancesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Get initial values from URL - only once on mount
  const [search, setSearch] = useState(() => searchParams.get('search') || '');
  const [status, setStatus] = useState<SyncStatusType | 'all'>(
    () => (searchParams.get('status') as SyncStatusType) || 'all'
  );
  const [authMethod, setAuthMethod] = useState<AuthMethod | 'all'>(
    () => (searchParams.get('authMethod') as AuthMethod) || 'all'
  );
  const [page, setPage] = useState(() => Number(searchParams.get('page')) || 1);

  // Fetch instances
  const { data, isLoading, isError, error, refetch } = useInstances({
    page,
    pageSize: 20,
    search: search || undefined,
    status: status !== 'all' ? status : undefined,
    authMethod: authMethod !== 'all' ? authMethod : undefined,
  });

  const deleteMutation = useDeleteInstance();
  const testConnectionMutation = useTestConnection();

  // Update URL without causing re-render loop
  const updateURL = useCallback((newParams: Record<string, string | number>) => {
    const params = new URLSearchParams();

    // Build params from current state + new params
    const allParams = {
      search,
      status,
      authMethod,
      page,
      ...newParams,
    };

    Object.entries(allParams).forEach(([key, value]) => {
      if (value && value !== 'all' && value !== '') {
        params.set(key, String(value));
      }
    });

    router.replace(`/admin/instances?${params.toString()}`, { scroll: false });
  }, [router, search, status, authMethod, page]);

  const handleSearchChange = (newSearch: string) => {
    setSearch(newSearch);
    setPage(1);
  };

  const handleStatusChange = (newStatus: SyncStatusType | 'all') => {
    setStatus(newStatus);
    setPage(1);
  };

  const handleAuthMethodChange = (newAuthMethod: AuthMethod | 'all') => {
    setAuthMethod(newAuthMethod);
    setPage(1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  // Update URL when state changes
  useEffect(() => {
    updateURL({});
  }, [search, status, authMethod, page]);

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this instance?')) {
      deleteMutation.mutate(id, {
        onSuccess: () => {
          refetch();
        },
      });
    }
  };

  const handleTestConnection = (id: string) => {
    testConnectionMutation.mutate(undefined, {
      onSuccess: () => {
        refetch();
      },
    });
  };

  return (
    <div
      className="space-y-6"
      data-testid="instances-page"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between"
        data-testid="instances-page-header"
      >
        <div>
          <h1
            className="text-3xl font-bold"
            data-testid="instances-page-title"
          >
            Jira Instances
          </h1>
          <p
            className="text-muted-foreground mt-2"
            data-testid="instances-page-description"
          >
            Manage your Jira Cloud instances
          </p>
        </div>
        <Button
          asChild
          data-testid="instances-add-button"
        >
          <Link
            href="/admin/instances/new"
            aria-label="Add new Jira instance"
          >
            <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
            Add Instance
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <InstancesFilters
        onSearchChange={handleSearchChange}
        onStatusChange={handleStatusChange}
        onAuthMethodChange={handleAuthMethodChange}
        defaultSearch={search}
        defaultStatus={status}
        defaultAuthMethod={authMethod}
      />

      {/* Error State */}
      {isError && (
        <Alert
          variant="destructive"
          data-testid="instances-error-alert"
        >
          <AlertCircle className="h-4 w-4" aria-hidden="true" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            <span data-testid="instances-error-message">
              {error?.message || 'Failed to load instances. Please try again.'}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="ml-4"
              data-testid="instances-error-retry-button"
              aria-label="Retry loading instances"
            >
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && <InstancesTableSkeleton />}

      {/* Table */}
      {!isLoading && !isError && data && (
        <>
          <InstancesTable
            instances={data.data}
            onDelete={handleDelete}
            onTestConnection={handleTestConnection}
          />
          {data.pagination.total > 0 && (
            <InstancesPagination
              currentPage={data.pagination.page}
              totalPages={data.pagination.totalPages}
              totalItems={data.pagination.total}
              pageSize={data.pagination.pageSize}
              onPageChange={handlePageChange}
            />
          )}
        </>
      )}

      {/* Empty State */}
      {!isLoading && !isError && data?.data.length === 0 && (
        <div
          className="text-center py-12"
          data-testid="instances-empty-state"
        >
          <p
            className="text-muted-foreground mb-4"
            data-testid="instances-empty-message"
          >
            No instances found
          </p>
          <Button
            asChild
            data-testid="instances-empty-add-button"
          >
            <Link
              href="/admin/instances/new"
              aria-label="Add your first Jira instance"
            >
              <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
              Add Your First Instance
            </Link>
          </Button>
        </div>
      )}
    </div>
  );
}

