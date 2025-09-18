import { storage } from '@forge/api';

export type ProjectConfig = {
  orchestratorUrl: string;
  secret: string;
  playbookId?: string;
};

const configKey = (projectKey: string) => `ds/config/${projectKey}`;

export async function getProjectConfig(projectKey: string): Promise<ProjectConfig | null> {
  const value = await storage.get(configKey(projectKey));
  return (value as ProjectConfig) ?? null;
}

export async function setProjectConfig(projectKey: string, cfg: ProjectConfig) {
  await storage.set(configKey(projectKey), cfg);
}
