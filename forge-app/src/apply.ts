import type { ProjectConfig } from './lib/config';
import { getProjectConfig } from './lib/config';
import type { Proposal } from './lib/orchestrator';
import { applyAction } from './lib/orchestrator';

export type ApplyInput = {
  issueKey: string;
  action: Proposal;
};

export async function executeApply(cfg: ProjectConfig, payload: ApplyInput) {
  return applyAction(cfg, payload.issueKey, payload.action);
}

export const run = async (event: any, context: any) => {
  const { issueKey, action } = event.payload as ApplyInput;
  const projectKey = context.platformContext.projectKey as string;
  const cfg = await getProjectConfig(projectKey);
  if (!cfg) {
    throw new Error('Digital Spiral not configured for this project.');
  }

  return executeApply(cfg, { issueKey, action });
};
