import { fetch } from '@forge/api';
import type { ProjectConfig } from './config';

export type EstimatedSavings = {
  seconds?: number;
};

export type Proposal = {
  id: string;
  kind: 'comment' | 'transition' | 'set-labels' | 'link';
  explain?: string;
  body_adf?: any;
  transitionId?: string;
  transitionName?: string;
  labels?: string[];
  mode?: string;
  url?: string;
  title?: string;
};

export type IngestResponse = {
  issueKey: string;
  proposals: Proposal[];
  estimated_savings?: EstimatedSavings;
};

export type ApplyResponse = {
  ok: boolean;
  applied?: { id: string; kind?: string };
  credit?: EstimatedSavings;
  ledger?: Record<string, any>;
  error?: string;
};

function normalizeBaseUrl(url: string) {
  return url.replace(/\/$/, '');
}

function buildAuthHeaders(cfg: ProjectConfig) {
  const headers: Record<string, string> = {
    'X-DS-Secret': cfg.secret,
  };
  if (cfg.tenantId) {
    headers['X-DS-Tenant'] = cfg.tenantId;
  }
  return headers;
}

async function raiseForResponseError(res: any, context: string): Promise<never> {
  let message = `${context} failed: ${res.status}`;
  try {
    const text = await res.text();
    if (text) {
      message += ` – ${text}`;
    }
  } catch (err) {
    // ignore parsing error
  }
  throw new Error(message);
}

export async function fetchProposals(cfg: ProjectConfig, issueKey: string): Promise<IngestResponse> {
  const url = `${normalizeBaseUrl(cfg.orchestratorUrl)}/v1/jira/ingest?issueKey=${encodeURIComponent(issueKey)}`;
  const res = await fetch(url, {
    method: 'GET',
    headers: buildAuthHeaders(cfg),
  });

  if (!res.ok) {
    await raiseForResponseError(res, 'ingest');
  }

  return (await res.json()) as IngestResponse;
}

export async function applyAction(cfg: ProjectConfig, issueKey: string, action: Proposal): Promise<ApplyResponse> {
  const url = `${normalizeBaseUrl(cfg.orchestratorUrl)}/v1/jira/apply`;
  const idemKey = `${issueKey}:${action.id}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idemKey,
      ...buildAuthHeaders(cfg),
    },
    body: JSON.stringify({ issueKey, action }),
  });

  if (!res.ok) {
    await raiseForResponseError(res, 'apply');
  }

  return (await res.json()) as ApplyResponse;
}
