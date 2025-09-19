import { fetch } from '@forge/api';
import { createHash } from 'crypto';
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
  inputs?: Record<string, any>;
  impact: { secondsSaved: number; quality?: number | null };
  attributions: CreditSplit[];
  attributionReason?: string | null;
  parents?: string[];
  prevHash?: string | null;
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
  creditEvent?: CreditEvent;
  result?: { status?: string; action?: string; details?: { id: string; kind?: string } };
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

function computeSignature(secret: string, body: string): string {
  return createHash('sha256').update(secret + body).digest('hex');
}

function buildAuthHeaders(cfg: ProjectConfig, body: string, opts?: RequestOptions) {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${cfg.token ?? cfg.secret}`,
    'X-Forge-Signature': `sha256=${computeSignature(cfg.secret, body)}`,
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

function mapCreditEvent(event: any): CreditEvent {
  const impact = event?.impact ?? {};
  const attributionSource = Array.isArray(event?.attributions)
    ? event.attributions
    : Array.isArray(event?.attribution?.split)
      ? event.attribution.split
      : [];
  const splits: CreditSplit[] = attributionSource.map((item: any) => ({
    id: String(item?.agentId ?? item?.agent_id ?? item?.id ?? ''),
    weight: typeof item?.weight === 'number' ? item.weight : 0,
  }));
  const attributionReason =
    event?.attributionReason ?? event?.attribution?.reason ?? event?.reason ?? null;
  return {
    id: String(event?.id ?? ''),
    ts: event?.ts ?? new Date().toISOString(),
    issueKey: String(event?.issueKey ?? event?.issue_key ?? ''),
    actor: (event?.actor as Record<string, any>) || {},
    action: String(event?.action ?? ''),
    inputs: event?.inputs ?? undefined,
    impact: {
      secondsSaved: Number(impact?.secondsSaved ?? 0),
      quality: impact?.quality ?? null,
    },
    attributions: splits,
    attributionReason,
    parents: Array.isArray(event?.parents)
      ? event.parents.map((value: any) => String(value))
      : [],
    prevHash: event?.prevHash ?? event?.prev ?? null,
    hash: event?.hash ?? null,
  };
}

function mapCreditInfo(event: CreditEvent): CreditInfo {
  return {
    secondsSaved: event.impact.secondsSaved,
    quality: event.impact.quality ?? undefined,
    splits: event.attributions,
    reason: event.attributionReason ?? undefined,
    eventId: event.id,
    hash: event.hash ?? undefined,
  };
}

function mapIssueCredit(raw: any): IssueCredit {
  const contributors: Contributor[] = Array.isArray(raw?.contributors)
    ? raw.contributors.map((item: any) => ({
        id: String(item?.agent_id ?? item?.id ?? ''),
        secondsSaved: Number(item?.seconds ?? item?.secondsSaved ?? 0),
        share: typeof item?.share === 'number' ? item.share : 0,
        events: Number(item?.events ?? 0),
      }))
    : [];
  const events = Array.isArray(raw?.events) ? raw.events.map(mapCreditEvent) : [];
  const windowSeconds = raw?.window_seconds ?? raw?.windowSecondsSaved;
  return {
    issueKey: String(raw?.issue ?? raw?.issueKey ?? ''),
    totalSecondsSaved: Number(raw?.total_seconds ?? raw?.totalSecondsSaved ?? 0),
    windowSecondsSaved:
      windowSeconds !== undefined && windowSeconds !== null ? Number(windowSeconds) : null,
    windowStart: raw?.window_start ?? raw?.windowStart ?? null,
    contributors,
    recentEvents: events,
  };
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
    headers: buildAuthHeaders(cfg, '', opts),
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
  const contextPayload: Record<string, string> = { source: 'panel' };
  if (opts?.actorId) {
    contextPayload.userId = opts.actorId;
  }
  const requestBody = JSON.stringify({ issueKey, action, context: contextPayload });
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idemKey,
      ...buildAuthHeaders(cfg, requestBody, opts),
    },
    body: requestBody,
  });

  if (!res.ok) {
    await raiseForResponseError(res, 'apply');
  }

  const payload = await res.json();
  const creditEvent = payload?.credit ? mapCreditEvent(payload.credit) : undefined;
  const applied = payload?.result?.details ?? payload?.applied;
  return {
    ok: Boolean(payload?.ok),
    applied,
    credit: creditEvent ? mapCreditInfo(creditEvent) : undefined,
    creditEvent,
    result: payload?.result,
  };
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
    headers: buildAuthHeaders(cfg, '', opts),
  });

  if (!res.ok) {
    await raiseForResponseError(res, 'credit issue');
  }

  const payload = await res.json();
  return mapIssueCredit(payload);
}
