import apiClient from './client';
import type {
  Instance,
  CreateInstanceRequest,
  UpdateInstanceRequest,
  TestConnectionResponse,
  SyncStatus,
  BackfillProgress,
  SyncHistory,
  PaginatedResponse,
  GetInstancesParams,
} from './types';

/**
 * Get paginated list of instances
 * @param params - Query parameters for filtering, sorting, and pagination
 * @returns Paginated list of instances
 */
export async function getInstances(
  params?: GetInstancesParams
): Promise<PaginatedResponse<Instance>> {
  return apiClient.get<PaginatedResponse<Instance>>('/api/instances', { params });
}

/**
 * Get a single instance by ID
 * @param id - Instance ID
 * @returns Instance details
 */
export async function getInstance(id: string): Promise<Instance> {
  return apiClient.get<Instance>(`/api/instances/${id}`);
}

/**
 * Create a new instance
 * @param data - Instance creation data
 * @returns Created instance
 */
export async function createInstance(data: CreateInstanceRequest): Promise<Instance> {
  return apiClient.post<Instance>('/api/instances', data);
}

/**
 * Update an existing instance
 * @param id - Instance ID
 * @param data - Instance update data
 * @returns Updated instance
 */
export async function updateInstance(
  id: string,
  data: UpdateInstanceRequest
): Promise<Instance> {
  return apiClient.put<Instance>(`/api/instances/${id}`, data);
}

/**
 * Delete an instance
 * @param id - Instance ID
 */
export async function deleteInstance(id: string): Promise<void> {
  return apiClient.delete<void>(`/api/instances/${id}`);
}

/**
 * Test connection to a Jira instance
 * @param id - Instance ID
 * @returns Test connection result
 */
export async function testConnection(id: string): Promise<TestConnectionResponse> {
  return apiClient.post<TestConnectionResponse>(`/api/instances/${id}/test`);
}

/**
 * Test connection with credentials (before creating instance)
 * @param data - Connection test data
 * @returns Test connection result
 */
export async function testConnectionWithCredentials(
  data: CreateInstanceRequest
): Promise<TestConnectionResponse> {
  return apiClient.post<TestConnectionResponse>('/api/instances/test-connection', data);
}

/**
 * Start a full backfill for an instance
 * @param id - Instance ID
 * @returns Job ID
 */
export async function startBackfill(id: string): Promise<{ jobId: string }> {
  return apiClient.post<{ jobId: string }>(`/api/instances/${id}/backfill`);
}

/**
 * Start an incremental resync for an instance
 * @param id - Instance ID
 * @returns Job ID
 */
export async function startResync(id: string): Promise<{ jobId: string }> {
  return apiClient.post<{ jobId: string }>(`/api/instances/${id}/resync`);
}

/**
 * Get sync status for an instance
 * @param id - Instance ID
 * @returns Sync status
 */
export async function getSyncStatus(id: string): Promise<SyncStatus> {
  return apiClient.get<SyncStatus>(`/api/instances/${id}/status`);
}

/**
 * Get backfill progress for a job
 * @param jobId - Job ID
 * @returns Backfill progress
 */
export async function getBackfillProgress(jobId: string): Promise<BackfillProgress> {
  return apiClient.get<BackfillProgress>(`/api/jobs/${jobId}`);
}

/**
 * Cancel a running backfill job
 * @param jobId - Job ID
 */
export async function cancelBackfill(jobId: string): Promise<void> {
  return apiClient.post<void>(`/api/jobs/${jobId}/cancel`);
}

/**
 * Get sync history for an instance
 * @param id - Instance ID
 * @param params - Pagination parameters
 * @returns Paginated sync history
 */
export async function getSyncHistory(
  id: string,
  params?: { page?: number; pageSize?: number }
): Promise<PaginatedResponse<SyncHistory>> {
  return apiClient.get<PaginatedResponse<SyncHistory>>(`/api/instances/${id}/history`, {
    params,
  });
}

