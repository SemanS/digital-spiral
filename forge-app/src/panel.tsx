import {
  IssuePanel,
  SectionMessage,
  useProductContext,
  useState,
  Button,
  Text,
  Strong,
  ButtonSet,
  render,
} from '@forge/ui';
import { getProjectConfig, type ProjectConfig } from './lib/config';
import {
  applyAction,
  fetchIssueCredit,
  fetchProposals,
  type CreditInfo,
  type ApplyResponse,
  type IngestResponse,
  type IssueCredit,
  type Proposal,
} from './lib/orchestrator';

type ReadyState = {
  status: 'ready';
  cfg: ProjectConfig;
  issueKey: string;
  proposals: Proposal[];
  ledgerHint?: IngestResponse['estimated_savings'];
  applyingId: string | null;
  explainingId: string | null;
  lastResult: ApplyResponse | null;
  credit: IssueCredit | null;
  actorHeader?: string | null;
  actorDisplay?: string | null;
  sprintSince?: string | null;
};

type ErrorState = {
  status: 'error';
  message: string;
};

type PanelState = ReadyState | ErrorState;

function proposalTitle(proposal: Proposal): string {
  if (proposal.kind === 'comment') {
    return 'Add comment';
  }
  if (proposal.kind === 'transition') {
    return `Transition to ${proposal.transitionName || proposal.transitionId}`;
  }
  if (proposal.kind === 'set-labels') {
    return 'Update labels';
  }
  if (proposal.kind === 'link') {
    return 'Create link';
  }
  return proposal.id;
}

function extractPlainText(node: any): string {
  if (!node) {
    return '';
  }
  if (typeof node === 'string') {
    return node;
  }
  if (Array.isArray(node)) {
    return node.map(extractPlainText).join(' ');
  }
  if (typeof node === 'object' && node) {
    if (typeof node.text === 'string') {
      return node.text;
    }
    if (Array.isArray(node.content)) {
      return extractPlainText(node.content);
    }
  }
  return '';
}

const DEFAULT_SPRINT_WINDOW_DAYS = 14;

function sprintWindowSince(): string {
  const windowMs = DEFAULT_SPRINT_WINDOW_DAYS * 24 * 60 * 60 * 1000;
  return new Date(Date.now() - windowMs).toISOString();
}

function buildActorHeader(platformContext: any): { header: string | null; display: string | null } {
  const accountId =
    (platformContext as any)?.accountId ??
    (platformContext as any)?.userAccountId ??
    (platformContext as any)?.localId ??
    null;
  const header = accountId ? `human.${accountId}` : null;
  const display = (platformContext as any)?.displayName ?? null;
  return { header, display };
}

function participantLabel(participantId: string, actorId?: string | null): string {
  if (actorId && participantId === actorId) {
    return 'You';
  }
  if (participantId.startsWith('ai.')) {
    return 'AI';
  }
  if (participantId.startsWith('human.')) {
    return participantId.split('.', 2)[1] || participantId;
  }
  if (participantId.startsWith('tool.')) {
    return participantId.split('.', 2)[1] || participantId;
  }
  return participantId || 'unknown';
}

function describeCredit(credit: CreditInfo | null | undefined, actorId?: string | null): string {
  if (!credit?.secondsSaved) {
    return '';
  }
  const seconds = Math.round(credit.secondsSaved);
  const parts: string[] = [`−${seconds}s credited`];
  if (credit.splits && credit.splits.length > 0) {
    const splits = credit.splits
      .map((split) => {
        const shareSeconds = Math.round(seconds * split.weight);
        return `${participantLabel(split.id, actorId)} ${shareSeconds}s`;
      })
      .join(', ');
    if (splits) {
      parts.push(`(${splits})`);
    }
  }
  return parts.join(' ');
}

function formatSplitPercent(weight: number): string {
  return `${Math.round(weight * 100)}%`;
}

function formatEventSplits(
  credit: CreditInfo | null | undefined,
  actorId?: string | null,
): string {
  if (!credit?.splits || credit.splits.length === 0) {
    return '';
  }
  return credit.splits
    .map((split) => `${participantLabel(split.id, actorId)} ${formatSplitPercent(split.weight)}`)
    .join(', ');
}

function formatSavedSeconds(value?: number | null): string {
  if (!value) {
    return '0';
  }
  return `−${Math.round(value)}`;
}

const Panel = () => {
  const { platformContext } = useProductContext();
  const issueKey = platformContext?.issueKey as string | undefined;
  const projectKey = platformContext?.projectKey as string | undefined;

  const [state, setState] = useState<PanelState>(async () => {
    if (!issueKey || !projectKey) {
      return { status: 'error', message: 'Missing Jira context.' };
    }
    const cfg = await getProjectConfig(projectKey);
    if (!cfg) {
      return {
        status: 'error',
        message: 'Configure orchestrator in Project Settings first.',
      };
    }
    const actorInfo = buildActorHeader(platformContext);
    const actorOptions = actorInfo.header
      ? { actorId: actorInfo.header, actorDisplay: actorInfo.display ?? undefined }
      : undefined;
    const sprintSince = sprintWindowSince();
    try {
      const data = await fetchProposals(cfg, issueKey, actorOptions);
      let creditData: IssueCredit | null = null;
      try {
        creditData = await fetchIssueCredit(cfg, issueKey, {
          ...(actorOptions || {}),
          since: sprintSince,
          limit: 5,
        });
      } catch (err) {
        creditData = null;
      }
      return {
        status: 'ready',
        cfg,
        issueKey,
        proposals: data.proposals || [],
        ledgerHint: data.estimated_savings,
        applyingId: null,
        explainingId: null,
        lastResult: null,
        credit: creditData,
        actorHeader: actorInfo.header,
        actorDisplay: actorInfo.display,
        sprintSince,
      };
    } catch (err: any) {
      return {
        status: 'error',
        message: err?.message || 'Failed to load proposals from orchestrator.',
      };
    }
  });

  const refresh = async () => {
    if (state.status !== 'ready') {
      return;
    }
    const actorOptions = state.actorHeader
      ? { actorId: state.actorHeader, actorDisplay: state.actorDisplay ?? undefined }
      : undefined;
    const since = state.sprintSince ?? sprintWindowSince();
    try {
      const creditPromise = fetchIssueCredit(state.cfg, state.issueKey, {
        ...(actorOptions || {}),
        since,
        limit: 5,
      }).catch(() => null);
      const data = await fetchProposals(state.cfg, state.issueKey, actorOptions);
      const creditData = await creditPromise;
      setState({
        ...state,
        proposals: data.proposals || [],
        ledgerHint: data.estimated_savings,
        applyingId: null,
        lastResult: null,
        credit: creditData,
      });
    } catch (err: any) {
      setState({
        status: 'error',
        message: err?.message || 'Failed to refresh proposals.',
      });
    }
  };

  const applyProposal = async (proposal: Proposal) => {
    if (state.status !== 'ready') {
      return;
    }
    const actorOptions = state.actorHeader
      ? { actorId: state.actorHeader, actorDisplay: state.actorDisplay ?? undefined }
      : undefined;
    const since = state.sprintSince ?? sprintWindowSince();
    setState({ ...state, applyingId: proposal.id });
    try {
      const result = await applyAction(state.cfg, state.issueKey, proposal, actorOptions);
      const creditPromise = fetchIssueCredit(state.cfg, state.issueKey, {
        ...(actorOptions || {}),
        since,
        limit: 5,
      }).catch(() => null);
      const data = await fetchProposals(state.cfg, state.issueKey, actorOptions);
      const creditData = await creditPromise;
      const nextCredit = creditData ?? state.credit ?? null;
      setState({
        status: 'ready',
        cfg: state.cfg,
        issueKey: state.issueKey,
        proposals: data.proposals || [],
        ledgerHint: data.estimated_savings,
        applyingId: null,
        explainingId: state.explainingId,
        lastResult: result,
        credit: nextCredit,
        actorHeader: state.actorHeader ?? actorOptions?.actorId ?? null,
        actorDisplay: state.actorDisplay ?? actorOptions?.actorDisplay ?? null,
        sprintSince: since,
      });
    } catch (err: any) {
      setState({
        status: 'error',
        message: err?.message || 'Apply failed.',
      });
    }
  };

  const toggleExplain = (proposalId: string) => {
    if (state.status !== 'ready') {
      return;
    }
    setState({
      ...state,
      explainingId: state.explainingId === proposalId ? null : proposalId,
    });
  };

  if (state.status === 'error') {
    return (
      <IssuePanel>
        <SectionMessage appearance="error" title="Digital Spiral">
          {state.message}
        </SectionMessage>
      </IssuePanel>
    );
  }

  const appliedCredit = state.status === 'ready'
    ? describeCredit(state.lastResult?.credit, state.actorHeader)
    : '';
  const issueCredit = state.status === 'ready' ? state.credit : null;

  return (
    <IssuePanel>
      {issueCredit ? (
        <SectionMessage appearance="information" title="Saved time">
          <Text>
            Saved this issue: <Strong>{formatSavedSeconds(issueCredit.totalSecondsSaved)}</Strong> seconds.
          </Text>
          {issueCredit.windowSecondsSaved !== undefined && issueCredit.windowSecondsSaved !== null ? (
            <Text>
              Saved this sprint:{' '}
              <Strong>{formatSavedSeconds(issueCredit.windowSecondsSaved)}</Strong> seconds.
            </Text>
          ) : null}
        </SectionMessage>
      ) : null}
      {issueCredit?.contributors?.length ? (
        <SectionMessage appearance="information" title="Contributors">
          {issueCredit.contributors.slice(0, 5).map((contributor) => (
            <Text key={contributor.id}>
              <Strong>{participantLabel(contributor.id, state.actorHeader)}</Strong> ·{' '}
              {formatSavedSeconds(contributor.secondsSaved)}s ({Math.round(contributor.share * 100)}%)
            </Text>
          ))}
        </SectionMessage>
      ) : null}
      {issueCredit?.recentEvents?.length ? (
        <SectionMessage appearance="information" title="Recent credit events">
          {issueCredit.recentEvents.slice(0, 5).map((event) => {
            const splits = formatEventSplits({ splits: event.attribution?.split || [] }, state.actorHeader);
            const actorLabel = participantLabel(event.actor?.id || event.actor?.type || '', state.actorHeader);
            return (
              <Text key={event.id}>
                {event.ts} · <Strong>{event.action}</Strong> · {actorLabel} ·{' '}
                {formatSavedSeconds(event.impact?.secondsSaved)}s
                {splits ? ` • ${splits}` : ''}
                {event.attribution?.reason ? ` • ${event.attribution.reason}` : ''}
              </Text>
            );
          })}
        </SectionMessage>
      ) : null}
      {state.ledgerHint?.seconds ? (
        <SectionMessage appearance="information" title="Estimated savings">
          <Text>
            Potential time saved:{' '}
            <Strong>{formatSavedSeconds(state.ledgerHint.seconds)}</Strong> seconds.
          </Text>
        </SectionMessage>
      ) : null}
      {state.lastResult?.ok ? (
        <SectionMessage appearance="confirmation" title="Applied">
          <Text>
            Applied action <Strong>{state.lastResult.applied?.id}</Strong>
            {appliedCredit ? ` • ${appliedCredit}` : ''}.
          </Text>
          {state.lastResult.credit?.reason ? <Text>Reason: {state.lastResult.credit.reason}</Text> : null}
        </SectionMessage>
      ) : null}
      {state.proposals.length === 0 ? (
        <SectionMessage appearance="warning" title="Digital Spiral">
          No proposals available for this issue. Try refreshing.
        </SectionMessage>
      ) : (
        state.proposals.map((proposal) => {
          const commentPreview =
            proposal.kind === 'comment' && proposal.body_adf
              ? extractPlainText(proposal.body_adf).slice(0, 280)
              : '';
          return (
            <SectionMessage key={proposal.id} title={proposalTitle(proposal)} appearance="information">
              {proposal.kind === 'comment' && commentPreview ? (
                <Text>
                  Draft reply preview: <Strong>{commentPreview}</Strong>
                </Text>
              ) : null}
              {proposal.kind === 'transition' && proposal.transitionId ? (
                <Text>
                  Transition ID: <Strong>{proposal.transitionId}</Strong>
                </Text>
              ) : null}
              {proposal.kind === 'set-labels' && proposal.labels ? (
                <Text>
                  Labels: <Strong>{proposal.labels.join(', ')}</Strong>{' '}
                  ({proposal.mode || 'merge'})
                </Text>
              ) : null}
              {proposal.kind === 'link' && proposal.url ? (
                <Text>
                  Link to <Strong>{proposal.title || proposal.url}</Strong>
                </Text>
              ) : null}
              {typeof proposal.estimatedSeconds === 'number' ? (
                <Text>
                  Estimated savings:{' '}
                  <Strong>{formatSavedSeconds(proposal.estimatedSeconds)}</Strong> seconds
                </Text>
              ) : null}
              {state.explainingId === proposal.id && proposal.explain ? (
                <Text>{proposal.explain}</Text>
              ) : null}
              <ButtonSet>
                <Button
                  text={state.applyingId === proposal.id ? 'Applying…' : 'Apply'}
                  onClick={() => applyProposal(proposal)}
                  isDisabled={state.applyingId !== null && state.applyingId !== proposal.id}
                />
                {proposal.explain ? (
                  <Button
                    text={state.explainingId === proposal.id ? 'Hide explanation' : 'Explain'}
                    appearance="subtle"
                    onClick={() => toggleExplain(proposal.id)}
                  />
                ) : null}
              </ButtonSet>
            </SectionMessage>
          );
        })
      )}
      <Button text="Refresh proposals" onClick={refresh} />
    </IssuePanel>
  );
};

export const run = render(<Panel />);
