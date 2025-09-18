import {
  ProjectSettingsPage,
  SectionMessage,
  Form,
  TextField,
  useProductContext,
  useState,
  render,
} from '@forge/ui';
import { getProjectConfig, setProjectConfig } from './lib/config';

const Settings = () => {
  const { platformContext } = useProductContext();
  const projectKey = platformContext?.projectKey as string;

  const [config] = useState(async () => {
    const stored = await getProjectConfig(projectKey);
    return stored ?? { orchestratorUrl: '', secret: '' };
  });

  const onSubmit = async (data: { orchestratorUrl: string; secret: string }) => {
    await setProjectConfig(projectKey, {
      orchestratorUrl: data.orchestratorUrl,
      secret: data.secret,
    });
    return true;
  };

  return (
    <ProjectSettingsPage>
      <SectionMessage title="Digital Spiral" appearance="information">
        Configure orchestrator endpoint and shared secret. URL must target /v1/jira (for example, https://example.ngrok.io/v1/jira).
      </SectionMessage>
      <Form onSubmit={onSubmit} submitButtonText="Save">
        <TextField name="orchestratorUrl" label="Orchestrator URL" defaultValue={config.orchestratorUrl} />
        <TextField name="secret" label="Shared secret" defaultValue={config.secret} />
      </Form>
    </ProjectSettingsPage>
  );
};

export const run = render(<Settings />);
