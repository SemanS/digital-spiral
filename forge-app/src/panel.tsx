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
  fetchProposals,
  type ApplyResponse,
  type IngestResponse,
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
    try {
      const data = await fetchProposals(cfg, issueKey);
      return {
        status: 'ready',
        cfg,
        issueKey,
        proposals: data.proposals || [],
        ledgerHint: data.estimated_savings,
        applyingId: null,
        explainingId: null,
        lastResult: null,
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
    try {
      const data = await fetchProposals(state.cfg, state.issueKey);
      setState({
        ...state,
        proposals: data.proposals || [],
        ledgerHint: data.estimated_savings,
        applyingId: null,
        lastResult: null,
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
    setState({ ...state, applyingId: proposal.id });
    try {
      const result = await applyAction(state.cfg, state.issueKey, proposal);
      const data = await fetchProposals(state.cfg, state.issueKey);
      setState({
        status: 'ready',
        cfg: state.cfg,
        issueKey: state.issueKey,
        proposals: data.proposals || [],
        ledgerHint: data.estimated_savings,
        applyingId: null,
        explainingId: state.explainingId,
        lastResult: result,
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

  return (
    <IssuePanel>
      {state.ledgerHint?.seconds ? (
        <SectionMessage appearance="information" title="Estimated savings">
          <Text>
            Potential time saved: <Strong>{state.ledgerHint.seconds}</Strong> seconds.
          </Text>
        </SectionMessage>
      ) : null}
      {state.lastResult?.ok ? (
        <SectionMessage appearance="confirmation" title="Applied">
          <Text>
            Applied action <Strong>{state.lastResult.applied?.id}</Strong>
            {state.lastResult.credit?.seconds
              ? ` · credited ${state.lastResult.credit.seconds} seconds`
              : ''}
            .
          </Text>
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
