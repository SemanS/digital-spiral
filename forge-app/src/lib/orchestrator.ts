import { fetch } from '@forge/api';
import type { ProjectConfig } from './config';

export type EstimatedSavings = {
  seconds?: number;
};

export type CreditSplit = {
  id: string;
  weight: number;
};

export type CreditEvent = {
  id: string;
  ts: string;
  issueKey: string;
  actor: { type?: string; id?: string; display?: string };
  action: string;
  impact: { secondsSaved: number; quality?: number | null };
  attribution: { split: CreditSplit[]; reason?: string | null };
  hash?: string | null;
};

export type Contributor = {
  id: string;
  secondsSaved: number;
  share: number;
  events: number;
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
  estimatedSeconds?: number;
};

export type IngestResponse = {
  issueKey: string;
  proposals: Proposal[];
  estimated_savings?: EstimatedSavings;
};

export type CreditInfo = {
  secondsSaved?: number;
  quality?: number | null;
  splits?: CreditSplit[];
  reason?: string | null;
  eventId?: string;
  hash?: string | null;
};

export type ApplyResponse = {
  ok: boolean;
  applied?: { id: string; kind?: string };
  credit?: CreditInfo;
  ledger?: Record<string, any>;
  error?: string;
};

export type IssueCredit = {
  issueKey: string;
  totalSecondsSaved: number;
  windowSecondsSaved?: number | null;
  windowStart?: string | null;
  contributors: Contributor[];
  recentEvents: CreditEvent[];
};

type RequestOptions = {
  actorId?: string;
  actorDisplay?: string;
  since?: string;
  limit?: number;
};

function normalizeBaseUrl(url: string) {
  return url.replace(/\/$/, '');
}

function buildAuthHeaders(cfg: ProjectConfig, opts?: RequestOptions) {
  const headers: Record<string, string> = {
    'X-DS-Secret': cfg.secret,
  };
  if (cfg.tenantId) {
    headers['X-DS-Tenant'] = cfg.tenantId;
  }
  if (opts?.actorId) {
    headers['X-DS-Actor'] = opts.actorId;
  }
  if (opts?.actorDisplay) {
    headers['X-DS-Actor-Display'] = opts.actorDisplay;
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

export async function fetchProposals(
  cfg: ProjectConfig,
  issueKey: string,
  opts?: RequestOptions,
): Promise<IngestResponse> {
  const url = `${normalizeBaseUrl(cfg.orchestratorUrl)}/v1/jira/ingest?issueKey=${encodeURIComponent(issueKey)}`;
  const res = await fetch(url, {
    method: 'GET',
    headers: buildAuthHeaders(cfg, opts),
  });

  if (!res.ok) {
    await raiseForResponseError(res, 'ingest');
  }

  return (await res.json()) as IngestResponse;
}

export async function applyAction(
  cfg: ProjectConfig,
  issueKey: string,
  action: Proposal,
  opts?: RequestOptions,
): Promise<ApplyResponse> {
  const url = `${normalizeBaseUrl(cfg.orchestratorUrl)}/v1/jira/apply`;
  const idemKey = `${issueKey}:${action.id}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idemKey,
      ...buildAuthHeaders(cfg, opts),
    },
    body: JSON.stringify({ issueKey, action }),
  });

  if (!res.ok) {
    await raiseForResponseError(res, 'apply');
  }

  return (await res.json()) as ApplyResponse;
}

export async function fetchIssueCredit(
  cfg: ProjectConfig,
  issueKey: string,
  opts?: RequestOptions,
): Promise<IssueCredit> {
  const params = new URLSearchParams();
  if (opts?.since) {
    params.set('since', opts.since);
  }
  if (typeof opts?.limit === 'number') {
    params.set('limit', String(opts.limit));
  }
  const query = params.toString();
  const url = `${normalizeBaseUrl(cfg.orchestratorUrl)}/v1/credit/issue/${encodeURIComponent(issueKey)}${
    query ? `?${query}` : ''
  }`;
  const res = await fetch(url, {
    method: 'GET',
    headers: buildAuthHeaders(cfg, opts),
  });

  if (!res.ok) {
    await raiseForResponseError(res, 'credit issue');
  }

  return (await res.json()) as IssueCredit;
}
