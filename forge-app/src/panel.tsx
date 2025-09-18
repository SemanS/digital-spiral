import {
  IssuePanel,
  Form,
  CheckboxGroup,
  Checkbox,
  SectionMessage,
  useProductContext,
  useState,
  Button,
  render,
} from '@forge/ui';
import { requestJira } from '@forge/api';
import { getProjectConfig } from './lib/config';
import { getSuggestions, ingest } from './lib/orchestrator';
import { executeForgePlan } from './apply';

const Panel = () => {
  const { platformContext } = useProductContext();
  const issueKey = platformContext?.issueKey as string;
  const projectKey = platformContext?.projectKey as string;

  const [state, setState] = useState(async () => {
    const cfg = await getProjectConfig(projectKey);
    if (!cfg) {
      return { error: 'Configure orchestrator in Project Settings first.' } as const;
    }

    const res = await requestJira(`/rest/api/3/issue/${issueKey}?fields=summary,description`);
    if (!res.ok) {
      return { error: `Failed to load issue: ${res.status}` } as const;
    }
    const issue = await res.json();

    let suggestions = await getSuggestions(cfg, issueKey);
    if (!suggestions || !suggestions.actions) {
      try {
        suggestions = await ingest(cfg, {
          key: issueKey,
          fields: issue.fields,
          project: { key: projectKey },
        });
      } catch (err: any) {
        return { error: `Ingest failed: ${err.message}` } as const;
      }
    }

    return {
      cfg,
      suggestions,
      lastResult: null,
    } as const;
  });

  if ('error' in state) {
    return (
      <IssuePanel>
        <SectionMessage appearance="error" title="Digital Spiral">
          {state.error}
        </SectionMessage>
      </IssuePanel>
    );
  }

  const submit = async (formData: { actions: string[] }) => {
    const payload = {
      issueKey,
      accepted_action_ids: formData.actions || [],
      draft_reply_adf: state.suggestions?.draft_reply_adf,
      playbook_id: state.suggestions?.playbook_id,
    };

    const result = await executeForgePlan(state.cfg, payload);
    setState({ ...state, lastResult: result });

    return result;
  };

  const refresh = async () => {
    setState(async () => {
      const cfg = await getProjectConfig(projectKey);
      if (!cfg) {
        return { error: 'Configure orchestrator in Project Settings first.' } as const;
      }
      const res = await requestJira(`/rest/api/3/issue/${issueKey}?fields=summary,description`);
      if (!res.ok) {
        return { error: `Failed to load issue: ${res.status}` } as const;
      }
      try {
        const suggestions = await ingest(cfg, {
          key: issueKey,
          fields: (await res.json()).fields,
          project: { key: projectKey },
        });
        return {
          cfg,
          suggestions,
          lastResult: null,
        } as const;
      } catch (err: any) {
        return { error: `Ingest failed: ${err.message}` } as const;
      }
    });
  };

  return (
    <IssuePanel>
      {Array.isArray(state.suggestions?.actions) && state.suggestions.actions.length > 0 ? (
        <Form onSubmit={submit} submitButtonText="Apply">
          <CheckboxGroup label="Planned actions" name="actions">
            {state.suggestions.actions.map((action: any) => (
              <Checkbox
                key={action.id}
                value={action.id}
                label={action.type || action.summary || action.id}
                defaultChecked
              />
            ))}
          </CheckboxGroup>
        </Form>
      ) : (
        <SectionMessage title="Digital Spiral" appearance="warning">
          No actions received from orchestrator.
        </SectionMessage>
      )}
      {state.lastResult ? (
        <SectionMessage title="Applied" appearance="confirmation">
          Applied {state.lastResult.applied} action(s).
        </SectionMessage>
      ) : null}
      <Button text="Regenerate" onClick={refresh} />
    </IssuePanel>
  );
};

export const run = render(<Panel />);
