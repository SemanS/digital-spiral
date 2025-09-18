import { requestJira } from '@forge/api';

export async function addComment(issueKey: string, adf: any) {
  const res = await requestJira(`/rest/api/3/issue/${issueKey}/comment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ body: adf }),
  });
  if (!res.ok) {
    throw new Error(`addComment: ${res.status}`);
  }
}

export async function transition(issueKey: string, transitionId: string) {
  const res = await requestJira(`/rest/api/3/issue/${issueKey}/transitions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transition: { id: transitionId } }),
  });
  if (!res.ok) {
    throw new Error(`transition: ${res.status}`);
  }
}

export async function addLabel(issueKey: string, label: string) {
  const res = await requestJira(`/rest/api/3/issue/${issueKey}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fields: { labels: [label] } }),
  });
  if (!res.ok) {
    throw new Error(`addLabel: ${res.status}`);
  }
}
