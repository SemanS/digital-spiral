import type { ProjectConfig } from './lib/config';
import { getProjectConfig } from './lib/config';
import { applyPlan } from './lib/orchestrator';
import { addComment, transition, addLabel } from './lib/jira';

type ForgeStep =
  | { kind: 'jira.add_comment'; args: { issueKey: string; bodyAdf: any } }
  | { kind: 'jira.transition'; args: { issueKey: string; transitionId: string } }
  | { kind: 'jira.add_label'; args: { issueKey: string; value: string } }
  | { kind: 'jira.create_linked_issue'; args: { projectKey: string; summary: string; linkType?: string } };

type ApplyInput = {
  issueKey: string;
  accepted_action_ids: string[];
  draft_reply_adf: any;
  playbook_id?: string;
};

async function performStep(step: ForgeStep) {
  if (step.kind === 'jira.add_comment') {
    await addComment(step.args.issueKey, step.args.bodyAdf);
  } else if (step.kind === 'jira.transition') {
    await transition(step.args.issueKey, step.args.transitionId);
  } else if (step.kind === 'jira.add_label') {
    await addLabel(step.args.issueKey, step.args.value);
  }
  // jira.create_linked_issue intentionally left for future implementation
}

export async function executeForgePlan(cfg: ProjectConfig, payload: ApplyInput) {
  const result = await applyPlan(cfg, payload);
  const plan: ForgeStep[] = Array.isArray(result.forge_plan) ? result.forge_plan : [];

  for (const step of plan) {
    await performStep(step);
  }

  return {
    ok: true,
    applied: plan.length,
    ledger: result.ledger_delta ?? {},
    raw: result,
  };
}

export const run = async (event: any, context: any) => {
  const { issueKey, accepted_action_ids, draft_reply_adf, playbook_id } = event.payload as ApplyInput;
  const projectKey = context.platformContext.projectKey as string;
  const cfg = await getProjectConfig(projectKey);
  if (!cfg) {
    throw new Error('Digital Spiral not configured for this project.');
  }

  return executeForgePlan(cfg, {
    issueKey,
    accepted_action_ids,
    draft_reply_adf,
    playbook_id,
  });
};
