import { describe, it, expect } from 'vitest'
import {
  instanceDetailsSchema,
  instanceAuthSchema,
  createInstanceSchema,
  updateInstanceSchema,
} from '../instance'

describe('Instance Schemas', () => {
  describe('instanceDetailsSchema', () => {
    it('should validate correct instance details', () => {
      const validData = {
        name: 'My Jira Instance',
        baseUrl: 'https://mycompany.atlassian.net',
        projectFilter: 'PROJ1,PROJ2',
      }

      const result = instanceDetailsSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject name that is too short', () => {
      const invalidData = {
        name: 'AB',
        baseUrl: 'https://mycompany.atlassian.net',
      }

      const result = instanceDetailsSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at least 3 characters')
      }
    })

    it('should reject name that is too long', () => {
      const invalidData = {
        name: 'A'.repeat(101),
        baseUrl: 'https://mycompany.atlassian.net',
      }

      const result = instanceDetailsSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at most 100 characters')
      }
    })

    it('should reject invalid Jira URL', () => {
      const invalidData = {
        name: 'My Instance',
        baseUrl: 'http://invalid-url.com',
      }

      const result = instanceDetailsSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('valid Jira Cloud URL')
      }
    })

    it('should accept valid Jira Cloud URL', () => {
      const validData = {
        name: 'My Instance',
        baseUrl: 'https://company.atlassian.net',
      }

      const result = instanceDetailsSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should accept URL with jira in hostname', () => {
      const validData = {
        name: 'My Instance',
        baseUrl: 'https://jira.company.com',
      }

      const result = instanceDetailsSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject non-HTTPS URL', () => {
      const invalidData = {
        name: 'My Instance',
        baseUrl: 'http://company.atlassian.net',
      }

      const result = instanceDetailsSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('should validate project filter with valid keys', () => {
      const validData = {
        name: 'My Instance',
        baseUrl: 'https://company.atlassian.net',
        projectFilter: 'PROJ1,PROJ2,ABC123',
      }

      const result = instanceDetailsSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid project filter keys', () => {
      const invalidData = {
        name: 'My Instance',
        baseUrl: 'https://company.atlassian.net',
        projectFilter: 'proj1,PROJ2', // lowercase not allowed
      }

      const result = instanceDetailsSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('should allow empty project filter', () => {
      const validData = {
        name: 'My Instance',
        baseUrl: 'https://company.atlassian.net',
      }

      const result = instanceDetailsSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('instanceAuthSchema', () => {
    it('should validate correct auth details', () => {
      const validData = {
        authMethod: 'api_token' as const,
        email: 'user@example.com',
        apiToken: 'a'.repeat(30),
      }

      const result = instanceAuthSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid email', () => {
      const invalidData = {
        authMethod: 'api_token' as const,
        email: 'invalid-email',
        apiToken: 'a'.repeat(30),
      }

      const result = instanceAuthSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('valid email')
      }
    })

    it('should reject API token that is too short', () => {
      const invalidData = {
        authMethod: 'api_token' as const,
        email: 'user@example.com',
        apiToken: 'short',
      }

      const result = instanceAuthSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at least 20 characters')
      }
    })

    it('should reject API token that is too long', () => {
      const invalidData = {
        authMethod: 'api_token' as const,
        email: 'user@example.com',
        apiToken: 'a'.repeat(201),
      }

      const result = instanceAuthSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at most 200 characters')
      }
    })

    it('should accept oauth auth method', () => {
      const validData = {
        authMethod: 'oauth' as const,
        email: 'user@example.com',
        apiToken: 'a'.repeat(30),
      }

      const result = instanceAuthSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid auth method', () => {
      const invalidData = {
        authMethod: 'invalid' as any,
        email: 'user@example.com',
        apiToken: 'a'.repeat(30),
      }

      const result = instanceAuthSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('createInstanceSchema', () => {
    it('should validate complete instance data', () => {
      const validData = {
        name: 'My Jira Instance',
        baseUrl: 'https://company.atlassian.net',
        projectFilter: 'PROJ1,PROJ2',
        authMethod: 'api_token' as const,
        email: 'user@example.com',
        apiToken: 'a'.repeat(30),
      }

      const result = createInstanceSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject incomplete data', () => {
      const invalidData = {
        name: 'My Instance',
        baseUrl: 'https://company.atlassian.net',
        // Missing auth fields
      }

      const result = createInstanceSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('updateInstanceSchema', () => {
    it('should validate partial update data', () => {
      const validData = {
        name: 'Updated Name',
      }

      const result = updateInstanceSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should validate multiple fields update', () => {
      const validData = {
        name: 'Updated Name',
        email: 'newemail@example.com',
      }

      const result = updateInstanceSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should allow empty update', () => {
      const validData = {}

      const result = updateInstanceSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid field values', () => {
      const invalidData = {
        name: 'AB', // Too short
      }

      const result = updateInstanceSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })
})

