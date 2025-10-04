import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/test/utils'
import { TestConnectionButton } from '../TestConnectionButton'
import * as useTestConnectionHook from '@/lib/hooks/useTestConnection'

vi.mock('@/lib/hooks/useTestConnection')

describe('TestConnectionButton', () => {
  const mockMutateAsync = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useTestConnectionHook.useTestConnection).mockReturnValue({
      mutateAsync: mockMutateAsync,
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      isSuccess: false,
      data: undefined,
      error: null,
      reset: vi.fn(),
      status: 'idle',
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      isIdle: true,
      isPaused: false,
      submittedAt: 0,
    } as any)
  })

  it('should render test connection button', () => {
    render(<TestConnectionButton instanceId="123" />)

    expect(screen.getByText('Test Connection')).toBeInTheDocument()
  })

  it('should show testing state when clicked', async () => {
    mockMutateAsync.mockImplementation(() => new Promise(() => {})) // Never resolves

    const { user } = render(<TestConnectionButton instanceId="123" />)

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('Testing...')).toBeInTheDocument()
    })
  })

  it('should show success state on successful test', async () => {
    mockMutateAsync.mockResolvedValue({ success: true })

    const { user } = render(<TestConnectionButton instanceId="123" />)

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument()
    })
  })

  it('should show error state on failed test', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Connection failed'))

    const { user } = render(<TestConnectionButton instanceId="123" />)

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })
  })

  it('should call onSuccess callback on successful test', async () => {
    mockMutateAsync.mockResolvedValue({ success: true })
    const onSuccess = vi.fn()

    const { user } = render(
      <TestConnectionButton instanceId="123" onSuccess={onSuccess} />
    )

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled()
    })
  })

  it('should call onError callback on failed test', async () => {
    const error = new Error('Connection failed')
    mockMutateAsync.mockRejectedValue(error)
    const onError = vi.fn()

    const { user } = render(
      <TestConnectionButton instanceId="123" onError={onError} />
    )

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(error)
    })
  })

  it('should test with instance data when provided', async () => {
    mockMutateAsync.mockResolvedValue({ success: true })
    const instanceData = {
      baseUrl: 'https://test.atlassian.net',
      email: 'test@example.com',
      apiToken: 'test-token',
    }

    const { user } = render(<TestConnectionButton instanceData={instanceData} />)

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({ data: instanceData })
    })
  })

  it('should test with instance ID when provided', async () => {
    mockMutateAsync.mockResolvedValue({ success: true })

    const { user } = render(<TestConnectionButton instanceId="123" />)

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({ instanceId: '123' })
    })
  })

  it('should be disabled when testing', async () => {
    mockMutateAsync.mockImplementation(() => new Promise(() => {}))

    const { user } = render(<TestConnectionButton instanceId="123" />)

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(button).toBeDisabled()
    })
  })

  it('should be disabled when no instance ID or data provided', () => {
    render(<TestConnectionButton />)

    const button = screen.getByRole('button', { name: /test connection/i })
    expect(button).toBeDisabled()
  })

  it('should reset to idle state after success', async () => {
    vi.useFakeTimers()
    mockMutateAsync.mockResolvedValue({ success: true })

    const { user } = render(<TestConnectionButton instanceId="123" />)

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument()
    })

    // Fast-forward 3 seconds
    vi.advanceTimersByTime(3000)

    await waitFor(() => {
      expect(screen.getByText('Test Connection')).toBeInTheDocument()
    })

    vi.useRealTimers()
  })

  it('should reset to idle state after error', async () => {
    vi.useFakeTimers()
    mockMutateAsync.mockRejectedValue(new Error('Failed'))

    const { user } = render(<TestConnectionButton instanceId="123" />)

    const button = screen.getByRole('button', { name: /test connection/i })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })

    // Fast-forward 3 seconds
    vi.advanceTimersByTime(3000)

    await waitFor(() => {
      expect(screen.getByText('Test Connection')).toBeInTheDocument()
    })

    vi.useRealTimers()
  })
})

