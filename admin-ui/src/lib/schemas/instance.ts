import { z } from 'zod';

// Custom validators
const jiraUrlValidator = z
  .string()
  .url({ message: 'Must be a valid URL' })
  .refine(
    (url) => {
      try {
        const parsed = new URL(url);
        return (
          parsed.protocol === 'https:' &&
          (parsed.hostname.endsWith('.atlassian.net') || parsed.hostname.includes('jira'))
        );
      } catch {
        return false;
      }
    },
    { message: 'Must be a valid Jira Cloud URL (e.g., https://your-domain.atlassian.net)' }
  );

const emailValidator = z.string().email({ message: 'Must be a valid email address' });

const apiTokenValidator = z
  .string()
  .min(20, { message: 'API token must be at least 20 characters' })
  .max(200, { message: 'API token must be at most 200 characters' });

// Instance details schema (Step 1)
export const instanceDetailsSchema = z.object({
  name: z
    .string()
    .min(1, { message: 'Name is required' })
    .min(3, { message: 'Name must be at least 3 characters' })
    .max(100, { message: 'Name must be at most 100 characters' }),
  baseUrl: jiraUrlValidator,
  projectFilter: z
    .string()
    .optional()
    .refine(
      (val) => {
        if (!val) return true;
        // Validate comma-separated project keys (e.g., "PROJ1,PROJ2")
        const keys = val.split(',').map((k) => k.trim());
        return keys.every((key) => /^[A-Z][A-Z0-9]{1,9}$/.test(key));
      },
      {
        message:
          'Project filter must be comma-separated project keys (e.g., "PROJ1,PROJ2"). Each key must be 2-10 uppercase letters/numbers.',
      }
    ),
});

// Instance auth schema (Step 2)
export const instanceAuthSchema = z.object({
  authMethod: z.enum(['api_token', 'oauth'], {
    required_error: 'Authentication method is required',
  }),
  email: emailValidator,
  apiToken: apiTokenValidator,
});

// Create instance schema (combines details + auth)
export const createInstanceSchema = instanceDetailsSchema.merge(instanceAuthSchema);

// Update instance schema (all fields optional except those that shouldn't change)
export const updateInstanceSchema = z.object({
  name: z
    .string()
    .min(3, { message: 'Name must be at least 3 characters' })
    .max(100, { message: 'Name must be at most 100 characters' })
    .optional(),
  baseUrl: jiraUrlValidator.optional(),
  authMethod: z.enum(['api_token', 'oauth']).optional(),
  email: emailValidator.optional(),
  apiToken: apiTokenValidator.optional(),
  projectFilter: z
    .string()
    .optional()
    .refine(
      (val) => {
        if (!val) return true;
        const keys = val.split(',').map((k) => k.trim());
        return keys.every((key) => /^[A-Z][A-Z0-9]{1,9}$/.test(key));
      },
      {
        message:
          'Project filter must be comma-separated project keys (e.g., "PROJ1,PROJ2"). Each key must be 2-10 uppercase letters/numbers.',
      }
    ),
});

// Type exports
export type InstanceDetailsFormData = z.infer<typeof instanceDetailsSchema>;
export type InstanceAuthFormData = z.infer<typeof instanceAuthSchema>;
export type CreateInstanceFormData = z.infer<typeof createInstanceSchema>;
export type UpdateInstanceFormData = z.infer<typeof updateInstanceSchema>;

