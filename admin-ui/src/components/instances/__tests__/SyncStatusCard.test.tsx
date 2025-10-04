import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import { SyncStatusCard } from '../SyncStatusCard'
import type { Instance } from '@/lib/api/types'

const baseInstance: Instance = {
  id: '1',
  name: 'Test Instance',
  baseUrl: 'https://test.atlassian.net',
  authMethod: 'api_token',
  status: 'idle',
  isActive: true,
  lastSyncAt: '2024-01-01T12:00:00Z',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T12:00:00Z',
}

describe('SyncStatusCard', () => {
  it('should render sync status card', () => {
    render(<SyncStatusCard instance={baseInstance} />)

    expect(screen.getByText('Sync Status')).toBeInTheDocument()
    expect(screen.getByText('Current synchronization status')).toBeInTheDocument()
  })

  it('should show idle status', () => {
    render(<SyncStatusCard instance={baseInstance} />)

    expect(screen.getByText('Idle')).toBeInTheDocument()
  })

  it('should show syncing status', () => {
    const syncingInstance: Instance = {
      ...baseInstance,
      status: 'syncing',
    }

    render(<SyncStatusCard instance={syncingInstance} />)

    expect(screen.getByText('Syncing')).toBeInTheDocument()
  })

  it('should show error status', () => {
    const errorInstance: Instance = {
      ...baseInstance,
      status: 'error',
      lastError: 'Connection timeout',
    }

    render(<SyncStatusCard instance={errorInstance} />)

    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('should display last sync time', () => {
    render(<SyncStatusCard instance={baseInstance} />)

    expect(screen.getByText('Last Sync')).toBeInTheDocument()
    // Should show relative time
    expect(screen.getByText(/ago/)).toBeInTheDocument()
  })

  it('should show "Never" when no last sync', () => {
    const instanceWithoutSync: Instance = {
      ...baseInstance,
      lastSyncAt: undefined,
    }

    render(<SyncStatusCard instance={instanceWithoutSync} />)

    expect(screen.getByText('Never')).toBeInTheDocument()
  })

  it('should show progress bar when syncing', () => {
    const syncingInstance: Instance = {
      ...baseInstance,
      status: 'syncing',
    }

    const syncProgress = {
      current: 50,
      total: 100,
      percentage: 50,
    }

    render(<SyncStatusCard instance={syncingInstance} syncProgress={syncProgress} />)

    expect(screen.getByText('Progress')).toBeInTheDocument()
    expect(screen.getByText('50 / 100')).toBeInTheDocument()
    expect(screen.getByText('50.0% complete')).toBeInTheDocument()
  })

  it('should show error details when status is error', () => {
    const errorInstance: Instance = {
      ...baseInstance,
      status: 'error',
      lastError: 'Connection timeout',
    }

    render(<SyncStatusCard instance={errorInstance} />)

    expect(screen.getByText('Error Details')).toBeInTheDocument()
    expect(screen.getByText('Connection timeout')).toBeInTheDocument()
  })

  it('should show active status', () => {
    render(<SyncStatusCard instance={baseInstance} />)

    expect(screen.getByText('Instance is active')).toBeInTheDocument()
  })

  it('should show inactive status', () => {
    const inactiveInstance: Instance = {
      ...baseInstance,
      isActive: false,
    }

    render(<SyncStatusCard instance={inactiveInstance} />)

    expect(screen.getByText('Instance is inactive')).toBeInTheDocument()
  })

  it('should render status badge with correct variant', () => {
    const { rerender } = render(<SyncStatusCard instance={baseInstance} />)

    // Idle status
    expect(screen.getByText('Idle')).toBeInTheDocument()

    // Syncing status
    const syncingInstance: Instance = { ...baseInstance, status: 'syncing' }
    rerender(<SyncStatusCard instance={syncingInstance} />)
    expect(screen.getByText('Syncing')).toBeInTheDocument()

    // Error status
    const errorInstance: Instance = { ...baseInstance, status: 'error' }
    rerender(<SyncStatusCard instance={errorInstance} />)
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('should handle invalid last sync date', () => {
    const instanceWithInvalidDate: Instance = {
      ...baseInstance,
      lastSyncAt: 'invalid-date',
    }

    render(<SyncStatusCard instance={instanceWithInvalidDate} />)

    expect(screen.getByText('Invalid date')).toBeInTheDocument()
  })

  it('should not show progress when not syncing', () => {
    render(<SyncStatusCard instance={baseInstance} />)

    expect(screen.queryByText('Progress')).not.toBeInTheDocument()
  })

  it('should not show error details when no error', () => {
    render(<SyncStatusCard instance={baseInstance} />)

    expect(screen.queryByText('Error Details')).not.toBeInTheDocument()
  })

  it('should format progress percentage correctly', () => {
    const syncingInstance: Instance = {
      ...baseInstance,
      status: 'syncing',
    }

    const syncProgress = {
      current: 33,
      total: 100,
      percentage: 33.333,
    }

    render(<SyncStatusCard instance={syncingInstance} syncProgress={syncProgress} />)

    expect(screen.getByText('33.3% complete')).toBeInTheDocument()
  })
})

