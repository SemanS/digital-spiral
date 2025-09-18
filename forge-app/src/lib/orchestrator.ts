import { fetch } from '@forge/api';
import * as crypto from 'crypto';
import type { ProjectConfig } from './config';

export function signBody(secret: string, body: string) {
  const hash = crypto.createHash('sha256');
  hash.update(secret + body, 'utf8');
  return `sha256=${hash.digest('hex')}`;
}

function normalizeBaseUrl(url: string) {
  return url.replace(/\/$/, '');
}

export async function getSuggestions(cfg: ProjectConfig, issueKey: string) {
  const url = `${normalizeBaseUrl(cfg.orchestratorUrl)}/suggestions/${issueKey}`;
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) {
    return null;
  }
  return res.json();
}

export async function ingest(cfg: ProjectConfig, snapshot: any) {
  const url = `${normalizeBaseUrl(cfg.orchestratorUrl)}/ingest`;
  const body = JSON.stringify({ issue: snapshot });
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-DS-Signature': signBody(cfg.secret, body),
    },
    body,
  });

  if (!res.ok) {
    throw new Error(`ingest failed: ${res.status}`);
  }

  return res.json();
}

export async function applyPlan(cfg: ProjectConfig, input: {
  issueKey: string;
  accepted_action_ids: string[];
  draft_reply_adf: any;
  playbook_id?: string;
}) {
  const url = `${normalizeBaseUrl(cfg.orchestratorUrl)}/apply`;
  const body = JSON.stringify(input);
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-DS-Signature': signBody(cfg.secret, body),
    },
    body,
  });

  if (!res.ok) {
    throw new Error(`apply failed: ${res.status}`);
  }

  return res.json();
}
