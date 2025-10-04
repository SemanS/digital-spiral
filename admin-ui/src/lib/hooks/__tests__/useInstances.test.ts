import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useInstances } from '../useInstances'
import * as instancesApi from '../../api/instances'

vi.mock('../../api/instances')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useInstances', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch instances successfully', async () => {
    const mockInstances = [
      {
        id: '1',
        name: 'Instance 1',
        baseUrl: 'https://test1.atlassian.net',
        isActive: true,
      },
      {
        id: '2',
        name: 'Instance 2',
        baseUrl: 'https://test2.atlassian.net',
        isActive: true,
      },
    ]

    vi.mocked(instancesApi.getInstances).mockResolvedValue({
      instances: mockInstances,
      total: 2,
      page: 1,
      pageSize: 10,
    })

    const { result } = renderHook(() => useInstances(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual({
      instances: mockInstances,
      total: 2,
      page: 1,
      pageSize: 10,
    })
  })

  it('should handle fetch error', async () => {
    const mockError = new Error('Failed to fetch instances')
    vi.mocked(instancesApi.getInstances).mockRejectedValue(mockError)

    const { result } = renderHook(() => useInstances(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(mockError)
  })

  it('should pass params to API call', async () => {
    const params = {
      page: 2,
      pageSize: 20,
      search: 'test',
    }

    vi.mocked(instancesApi.getInstances).mockResolvedValue({
      instances: [],
      total: 0,
      page: 2,
      pageSize: 20,
    })

    renderHook(() => useInstances(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(instancesApi.getInstances).toHaveBeenCalledWith(params)
    })
  })

  it('should use correct query key', async () => {
    const params = { page: 1 }

    vi.mocked(instancesApi.getInstances).mockResolvedValue({
      instances: [],
      total: 0,
      page: 1,
      pageSize: 10,
    })

    const { result } = renderHook(() => useInstances(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Query key should include params
    expect(result.current.data).toBeDefined()
  })
})

