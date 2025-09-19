import { storage } from '@forge/api';

export type ProjectConfig = {
  orchestratorUrl: string;
  secret: string;
  tenantId?: string;
  token?: string;
};

const configKey = (projectKey: string) => `ds/config/${projectKey}`;

function configFromEnv(): ProjectConfig | null {
  const url = process.env.ORCH_URL;
  const secret = process.env.ORCH_SECRET;
  const token = process.env.ORCH_TOKEN;
  if (!url || !secret) {
    return null;
  }
  const tenantId = process.env.TENANT_ID;
  return {
    orchestratorUrl: url,
    secret,
    tenantId: tenantId || undefined,
    token: token || undefined,
  };
}

export async function getProjectConfig(projectKey: string): Promise<ProjectConfig | null> {
  const value = (await storage.get(configKey(projectKey))) as ProjectConfig | undefined;
  if (value && value.orchestratorUrl && value.secret) {
    return value;
  }
  return configFromEnv();
}

export async function setProjectConfig(projectKey: string, cfg: ProjectConfig) {
  await storage.set(configKey(projectKey), cfg);
}
