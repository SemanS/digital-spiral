import { IssueGlance, Text, useProductContext, render, useState } from '@forge/ui';
import { getProjectConfig } from './lib/config';
import { fetchIssueCredit } from './lib/orchestrator';

const SPRINT_WINDOW_DAYS = 14;

type GlanceState = {
  label: string;
  value: string;
};

function sprintSince(): string {
  const windowMs = SPRINT_WINDOW_DAYS * 24 * 60 * 60 * 1000;
  return new Date(Date.now() - windowMs).toISOString();
}

function resolveActor(platformContext: any): { id?: string; display?: string } {
  const accountId =
    (platformContext as any)?.accountId ??
    (platformContext as any)?.userAccountId ??
    (platformContext as any)?.localId ??
    null;
  const id = accountId ? `human.${accountId}` : undefined;
  const display = (platformContext as any)?.displayName ?? undefined;
  return { id: id ?? undefined, display };
}

const Glance = () => {
  const { platformContext } = useProductContext();
  const issueKey = platformContext?.issueKey as string | undefined;
  const projectKey = platformContext?.projectKey as string | undefined;

  const [state] = useState<GlanceState>(async () => {
    if (!issueKey || !projectKey) {
      return { label: 'Digital Spiral', value: 'No issue context' };
    }
    const cfg = await getProjectConfig(projectKey);
    if (!cfg) {
      return { label: 'Digital Spiral', value: 'Configure orchestrator' };
    }
    const actor = resolveActor(platformContext);
    try {
      const credit = await fetchIssueCredit(cfg, issueKey, {
        actorId: actor.id,
        actorDisplay: actor.display,
        since: sprintSince(),
        limit: 3,
      });
      const windowSeconds =
        typeof credit.windowSecondsSaved === 'number'
          ? credit.windowSecondsSaved
          : credit.totalSecondsSaved;
      const rounded = Math.max(Math.round(windowSeconds), 0);
      return {
        label: 'Saved this sprint',
        value: `−${rounded}s`,
      };
    } catch (err) {
      return { label: 'Digital Spiral', value: 'No credit yet' };
    }
  });

  return (
    <IssueGlance>
      <Text>
        {state.label}: {state.value}
      </Text>
    </IssueGlance>
  );
};

export const run = render(<Glance />);
