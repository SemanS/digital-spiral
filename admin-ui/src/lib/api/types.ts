// Instance types
export type AuthMethod = 'api_token' | 'oauth';
export type SyncStatusType = 'idle' | 'syncing' | 'error';

export interface Instance {
  id: string;
  name: string;
  baseUrl: string;
  authMethod: AuthMethod;
  email: string;
  projectFilter?: string;
  status: SyncStatusType;
  lastSync?: string;
  watermark?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateInstanceRequest {
  name: string;
  baseUrl: string;
  authMethod: AuthMethod;
  email: string;
  apiToken: string;
  projectFilter?: string;
}

export interface UpdateInstanceRequest {
  name?: string;
  baseUrl?: string;
  authMethod?: AuthMethod;
  email?: string;
  apiToken?: string;
  projectFilter?: string;
}

export interface TestConnectionResponse {
  success: boolean;
  user?: {
    name: string;
    email: string;
    accountId: string;
  };
  rateLimit?: {
    limit: number;
    remaining: number;
    reset: number;
  };
  error?: string;
}

export interface SyncStatus {
  status: SyncStatusType;
  progress?: {
    percentage: number;
    eta?: string;
    projects?: {
      total: number;
      completed: number;
    };
    issues?: {
      total: number;
      completed: number;
    };
    comments?: {
      total: number;
      completed: number;
    };
  };
  watermark?: string;
  statistics?: {
    totalIssues: number;
    totalProjects: number;
    totalUsers: number;
  };
  error?: string;
}

export interface BackfillProgress {
  jobId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: {
    percentage: number;
    eta?: string;
    projects: {
      total: number;
      completed: number;
    };
    issues: {
      total: number;
      completed: number;
    };
    comments: {
      total: number;
      completed: number;
    };
  };
  startedAt?: string;
  completedAt?: string;
  error?: string;
}

export interface SyncHistory {
  id: string;
  instanceId: string;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  status: 'completed' | 'failed' | 'cancelled';
  issuesSynced: number;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

export interface GetInstancesParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: SyncStatusType;
  authMethod?: AuthMethod;
  sortBy?: 'name' | 'status' | 'lastSync';
  sortOrder?: 'asc' | 'desc';
}

