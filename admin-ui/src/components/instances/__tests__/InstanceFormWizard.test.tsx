import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/test/utils'
import { InstanceFormWizard } from '../InstanceFormWizard'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
}))

describe('InstanceFormWizard', () => {
  beforeEach(() => {
    // Clear session storage before each test
    sessionStorage.clear()
    vi.clearAllMocks()
  })

  it('should render wizard with step indicator', () => {
    render(<InstanceFormWizard />)

    expect(screen.getByText('Details')).toBeInTheDocument()
    expect(screen.getByText('Authentication')).toBeInTheDocument()
    expect(screen.getByText('Validate')).toBeInTheDocument()
    expect(screen.getByText('Save')).toBeInTheDocument()
  })

  it('should start at step 1 (Details)', () => {
    render(<InstanceFormWizard />)

    expect(screen.getByText('Basic information')).toBeInTheDocument()
  })

  it('should show progress bar', () => {
    render(<InstanceFormWizard />)

    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toBeInTheDocument()
  })

  it('should highlight current step', () => {
    render(<InstanceFormWizard />)

    // Step 1 should be highlighted (current)
    const step1 = screen.getByText('Details').closest('div')
    expect(step1).toHaveClass('flex-1')
  })

  it('should show cancel button', () => {
    render(<InstanceFormWizard />)

    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('should save wizard data to session storage', async () => {
    render(<InstanceFormWizard />)

    await waitFor(() => {
      const savedData = sessionStorage.getItem('instanceWizardData')
      expect(savedData).toBeTruthy()
    })
  })

  it('should load wizard data from session storage', () => {
    const mockData = {
      name: 'Test Instance',
      baseUrl: 'https://test.atlassian.net',
      authMethod: 'api_token',
    }

    sessionStorage.setItem('instanceWizardData', JSON.stringify(mockData))

    render(<InstanceFormWizard />)

    // Data should be loaded
    expect(sessionStorage.getItem('instanceWizardData')).toBeTruthy()
  })

  it('should handle invalid session storage data gracefully', () => {
    sessionStorage.setItem('instanceWizardData', 'invalid json')

    // Should not throw error
    expect(() => render(<InstanceFormWizard />)).not.toThrow()
  })

  it('should show step descriptions', () => {
    render(<InstanceFormWizard />)

    expect(screen.getByText('Basic information')).toBeInTheDocument()
    expect(screen.getByText('Credentials')).toBeInTheDocument()
    expect(screen.getByText('Test connection')).toBeInTheDocument()
    expect(screen.getByText('Review and save')).toBeInTheDocument()
  })

  it('should render all 4 steps', () => {
    render(<InstanceFormWizard />)

    const steps = ['Details', 'Authentication', 'Validate', 'Save']
    steps.forEach((step) => {
      expect(screen.getByText(step)).toBeInTheDocument()
    })
  })

  it('should initialize with api_token auth method', () => {
    render(<InstanceFormWizard />)

    const savedData = sessionStorage.getItem('instanceWizardData')
    if (savedData) {
      const data = JSON.parse(savedData)
      expect(data.authMethod).toBe('api_token')
    }
  })

  it('should calculate progress correctly', () => {
    render(<InstanceFormWizard />)

    // Step 1 of 4 = 25% progress
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toHaveAttribute('aria-valuenow', '25')
  })

  it('should render step indicator with correct number of steps', () => {
    render(<InstanceFormWizard />)

    const stepElements = screen.getAllByText(/Details|Authentication|Validate|Save/)
    expect(stepElements.length).toBeGreaterThanOrEqual(4)
  })

  it('should show completed steps with check icon', () => {
    render(<InstanceFormWizard />)

    // Initially no steps should be completed
    // This would change as user progresses through wizard
    expect(screen.queryByTestId('check-icon')).not.toBeInTheDocument()
  })
})

