import { test, expect } from '@playwright/test'

test.describe('Instance Management', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to instances page
    await page.goto('/admin/instances')
  })

  test.describe('Add Instance Flow', () => {
    test('should complete full add instance flow', async ({ page }) => {
      // Click "Add Instance" button
      await page.click('text=Add Instance')

      // Step 1: Details
      await expect(page.locator('text=Details')).toBeVisible()
      await page.fill('input[name="name"]', 'Test Instance')
      await page.fill('input[name="baseUrl"]', 'https://test.atlassian.net')
      await page.fill('input[name="projectFilter"]', 'PROJ1,PROJ2')
      await page.click('text=Next')

      // Step 2: Authentication
      await expect(page.locator('text=Authentication')).toBeVisible()
      await page.selectOption('select[name="authMethod"]', 'api_token')
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="apiToken"]', 'a'.repeat(30))
      await page.click('text=Next')

      // Step 3: Validate
      await expect(page.locator('text=Validate')).toBeVisible()
      await page.click('text=Test Connection')
      
      // Wait for test to complete (mock success)
      await expect(page.locator('text=Success')).toBeVisible({ timeout: 10000 })
      await page.click('text=Next')

      // Step 4: Save
      await expect(page.locator('text=Save')).toBeVisible()
      await expect(page.locator('text=Test Instance')).toBeVisible()
      await page.click('text=Save Instance')

      // Should redirect to instances list
      await expect(page).toHaveURL('/admin/instances')
      await expect(page.locator('text=Test Instance')).toBeVisible()
    })

    test('should validate required fields in details step', async ({ page }) => {
      await page.click('text=Add Instance')

      // Try to proceed without filling fields
      await page.click('text=Next')

      // Should show validation errors
      await expect(page.locator('text=Name is required')).toBeVisible()
      await expect(page.locator('text=Base URL is required')).toBeVisible()
    })

    test('should validate Jira URL format', async ({ page }) => {
      await page.click('text=Add Instance')

      await page.fill('input[name="name"]', 'Test Instance')
      await page.fill('input[name="baseUrl"]', 'http://invalid-url.com')
      await page.click('text=Next')

      // Should show validation error
      await expect(page.locator('text=Must be a valid Jira Cloud URL')).toBeVisible()
    })

    test('should validate project filter format', async ({ page }) => {
      await page.click('text=Add Instance')

      await page.fill('input[name="name"]', 'Test Instance')
      await page.fill('input[name="baseUrl"]', 'https://test.atlassian.net')
      await page.fill('input[name="projectFilter"]', 'invalid-key')
      await page.click('text=Next')

      // Should show validation error
      await expect(page.locator('text=Project filter must be comma-separated')).toBeVisible()
    })

    test('should allow canceling wizard', async ({ page }) => {
      await page.click('text=Add Instance')

      await page.fill('input[name="name"]', 'Test Instance')
      
      // Click cancel
      await page.click('text=Cancel')

      // Should show confirmation dialog
      page.on('dialog', dialog => dialog.accept())
      
      // Should return to instances list
      await expect(page).toHaveURL('/admin/instances')
    })

    test('should save wizard progress to session storage', async ({ page }) => {
      await page.click('text=Add Instance')

      await page.fill('input[name="name"]', 'Test Instance')
      await page.fill('input[name="baseUrl"]', 'https://test.atlassian.net')

      // Check session storage
      const sessionData = await page.evaluate(() => {
        return sessionStorage.getItem('instanceWizardData')
      })

      expect(sessionData).toBeTruthy()
      const data = JSON.parse(sessionData!)
      expect(data.name).toBe('Test Instance')
      expect(data.baseUrl).toBe('https://test.atlassian.net')
    })
  })

  test.describe('Edit Instance Flow', () => {
    test('should edit existing instance', async ({ page }) => {
      // Assume there's an existing instance
      await page.click('text=Test Instance')
      await page.click('text=Edit')

      // Update name
      await page.fill('input[name="name"]', 'Updated Instance')
      await page.click('text=Save')

      // Should show success message
      await expect(page.locator('text=Instance updated successfully')).toBeVisible()
      await expect(page.locator('text=Updated Instance')).toBeVisible()
    })

    test('should validate edit form', async ({ page }) => {
      await page.click('text=Test Instance')
      await page.click('text=Edit')

      // Clear name field
      await page.fill('input[name="name"]', '')
      await page.click('text=Save')

      // Should show validation error
      await expect(page.locator('text=Name is required')).toBeVisible()
    })

    test('should allow canceling edit', async ({ page }) => {
      await page.click('text=Test Instance')
      await page.click('text=Edit')

      await page.fill('input[name="name"]', 'Updated Instance')
      await page.click('text=Cancel')

      // Should return to detail page without saving
      await expect(page.locator('text=Test Instance')).toBeVisible()
      await expect(page.locator('text=Updated Instance')).not.toBeVisible()
    })
  })

  test.describe('Delete Instance Flow', () => {
    test('should delete instance with confirmation', async ({ page }) => {
      // Find instance row
      const instanceRow = page.locator('tr:has-text("Test Instance")')
      
      // Click actions menu
      await instanceRow.locator('button[aria-label="Actions"]').click()
      
      // Click delete
      await page.click('text=Delete')

      // Should show confirmation dialog
      await expect(page.locator('text=Are you sure you want to delete')).toBeVisible()
      await page.click('text=Confirm')

      // Should show success message
      await expect(page.locator('text=Instance deleted successfully')).toBeVisible()
      
      // Instance should be removed from list
      await expect(page.locator('text=Test Instance')).not.toBeVisible()
    })

    test('should allow canceling delete', async ({ page }) => {
      const instanceRow = page.locator('tr:has-text("Test Instance")')
      await instanceRow.locator('button[aria-label="Actions"]').click()
      await page.click('text=Delete')

      // Cancel confirmation
      await page.click('text=Cancel')

      // Instance should still be visible
      await expect(page.locator('text=Test Instance')).toBeVisible()
    })
  })

  test.describe('Error Scenarios', () => {
    test('should handle network error gracefully', async ({ page }) => {
      // Simulate network error
      await page.route('**/api/instances', route => {
        route.abort('failed')
      })

      await page.goto('/admin/instances')

      // Should show error message
      await expect(page.locator('text=Failed to load instances')).toBeVisible()
    })

    test('should handle validation error from server', async ({ page }) => {
      await page.click('text=Add Instance')

      // Fill form
      await page.fill('input[name="name"]', 'Test Instance')
      await page.fill('input[name="baseUrl"]', 'https://test.atlassian.net')
      await page.click('text=Next')

      await page.selectOption('select[name="authMethod"]', 'api_token')
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="apiToken"]', 'a'.repeat(30))
      await page.click('text=Next')

      // Mock server validation error
      await page.route('**/api/instances/test-connection', route => {
        route.fulfill({
          status: 400,
          body: JSON.stringify({ error: 'Invalid credentials' }),
        })
      })

      await page.click('text=Test Connection')

      // Should show error message
      await expect(page.locator('text=Invalid credentials')).toBeVisible()
    })

    test('should handle timeout error', async ({ page }) => {
      await page.click('text=Add Instance')

      // Fill form
      await page.fill('input[name="name"]', 'Test Instance')
      await page.fill('input[name="baseUrl"]', 'https://test.atlassian.net')
      await page.click('text=Next')

      await page.selectOption('select[name="authMethod"]', 'api_token')
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="apiToken"]', 'a'.repeat(30))
      await page.click('text=Next')

      // Mock timeout
      await page.route('**/api/instances/test-connection', route => {
        // Never respond
      })

      await page.click('text=Test Connection')

      // Should show timeout error after some time
      await expect(page.locator('text=Request timeout')).toBeVisible({ timeout: 35000 })
    })
  })

  test.describe('Search and Filter', () => {
    test('should filter instances by search term', async ({ page }) => {
      await page.fill('input[placeholder="Search instances..."]', 'Test')

      // Should show only matching instances
      await expect(page.locator('text=Test Instance')).toBeVisible()
      await expect(page.locator('text=Other Instance')).not.toBeVisible()
    })

    test('should filter by status', async ({ page }) => {
      await page.selectOption('select[name="status"]', 'syncing')

      // Should show only syncing instances
      await expect(page.locator('text=Syncing')).toBeVisible()
    })

    test('should clear filters', async ({ page }) => {
      await page.fill('input[placeholder="Search instances..."]', 'Test')
      await page.click('text=Clear Filters')

      // Should show all instances
      const input = page.locator('input[placeholder="Search instances..."]')
      await expect(input).toHaveValue('')
    })
  })

  test.describe('Pagination', () => {
    test('should navigate between pages', async ({ page }) => {
      // Go to page 2
      await page.click('text=Next')

      // Should show page 2 instances
      await expect(page).toHaveURL(/page=2/)
    })

    test('should change page size', async ({ page }) => {
      await page.selectOption('select[name="pageSize"]', '20')

      // Should show 20 instances per page
      const rows = page.locator('tbody tr')
      await expect(rows).toHaveCount(20)
    })
  })
})

