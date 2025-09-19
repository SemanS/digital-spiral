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
    return (
      stored ?? {
        orchestratorUrl: '',
        secret: '',
        tenantId: '',
      }
    );
  });

  const onSubmit = async (data: { orchestratorUrl: string; secret: string; tenantId?: string }) => {
    await setProjectConfig(projectKey, {
      orchestratorUrl: data.orchestratorUrl?.trim() ?? '',
      secret: data.secret?.trim() ?? '',
      tenantId: data.tenantId?.trim() ? data.tenantId.trim() : undefined,
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
        <TextField
          name="tenantId"
          label="Tenant identifier (optional)"
          defaultValue={config.tenantId}
          description="Used to scope orchestrator storage and allowlist entries."
        />
      </Form>
    </ProjectSettingsPage>
  );
};

export const run = render(<Settings />);
