import type { ProjectConfig } from './lib/config';
import { getProjectConfig } from './lib/config';
import type { Proposal } from './lib/orchestrator';
import { applyAction } from './lib/orchestrator';

type ActorOptions = {
  actorId?: string;
  actorDisplay?: string;
};

export type ApplyInput = {
  issueKey: string;
  action: Proposal;
};

function resolveActor(platformContext: any): ActorOptions | undefined {
  const accountId =
    (platformContext as any)?.accountId ??
    (platformContext as any)?.userAccountId ??
    (platformContext as any)?.localId ??
    null;
  const display = (platformContext as any)?.displayName ?? undefined;
  if (!accountId) {
    return display ? { actorDisplay: display } : undefined;
  }
  const actorId = `human.${accountId}`;
  return display ? { actorId, actorDisplay: display } : { actorId };
}

export async function executeApply(cfg: ProjectConfig, payload: ApplyInput, opts?: ActorOptions) {
  return applyAction(cfg, payload.issueKey, payload.action, opts);
}

export const run = async (event: any, context: any) => {
  const { issueKey, action } = event.payload as ApplyInput;
  const projectKey = context.platformContext.projectKey as string;
  const cfg = await getProjectConfig(projectKey);
  if (!cfg) {
    throw new Error('Digital Spiral not configured for this project.');
  }

  const actorOptions = resolveActor(context.platformContext);
  return executeApply(cfg, { issueKey, action }, actorOptions);
};
