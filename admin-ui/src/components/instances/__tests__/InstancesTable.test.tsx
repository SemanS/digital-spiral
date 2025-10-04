import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/utils'
import { InstancesTable } from '../InstancesTable'
import type { Instance } from '@/lib/api/types'

const mockInstances: Instance[] = [
  {
    id: '1',
    name: 'Test Instance 1',
    baseUrl: 'https://test1.atlassian.net',
    authMethod: 'api_token',
    status: 'idle',
    isActive: true,
    lastSyncAt: '2024-01-01T12:00:00Z',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T12:00:00Z',
  },
  {
    id: '2',
    name: 'Test Instance 2',
    baseUrl: 'https://test2.atlassian.net',
    authMethod: 'oauth',
    status: 'syncing',
    isActive: true,
    lastSyncAt: '2024-01-02T12:00:00Z',
    createdAt: '2024-01-02T00:00:00Z',
    updatedAt: '2024-01-02T12:00:00Z',
  },
]

describe('InstancesTable', () => {
  it('should render table headers', () => {
    render(<InstancesTable instances={[]} />)

    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Base URL')).toBeInTheDocument()
    expect(screen.getByText('Auth Method')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Last Sync')).toBeInTheDocument()
    expect(screen.getByText('Actions')).toBeInTheDocument()
  })

  it('should render empty state when no instances', () => {
    render(<InstancesTable instances={[]} />)

    expect(screen.getByText('No instances found')).toBeInTheDocument()
  })

  it('should render instances data', () => {
    render(<InstancesTable instances={mockInstances} />)

    expect(screen.getByText('Test Instance 1')).toBeInTheDocument()
    expect(screen.getByText('Test Instance 2')).toBeInTheDocument()
    expect(screen.getByText('https://test1.atlassian.net')).toBeInTheDocument()
    expect(screen.getByText('https://test2.atlassian.net')).toBeInTheDocument()
  })

  it('should render auth method labels correctly', () => {
    render(<InstancesTable instances={mockInstances} />)

    expect(screen.getByText('API Token')).toBeInTheDocument()
    expect(screen.getByText('OAuth')).toBeInTheDocument()
  })

  it('should render status badges', () => {
    render(<InstancesTable instances={mockInstances} />)

    expect(screen.getByText('Idle')).toBeInTheDocument()
    expect(screen.getByText('Syncing')).toBeInTheDocument()
  })

  it('should render error status badge', () => {
    const errorInstance: Instance = {
      ...mockInstances[0],
      status: 'error',
    }

    render(<InstancesTable instances={[errorInstance]} />)

    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('should format last sync time', () => {
    render(<InstancesTable instances={mockInstances} />)

    // Should show relative time (e.g., "2 days ago")
    const lastSyncCells = screen.getAllByText(/ago/)
    expect(lastSyncCells.length).toBeGreaterThan(0)
  })

  it('should show "Never" for instances without last sync', () => {
    const instanceWithoutSync: Instance = {
      ...mockInstances[0],
      lastSyncAt: undefined,
    }

    render(<InstancesTable instances={[instanceWithoutSync]} />)

    expect(screen.getByText('Never')).toBeInTheDocument()
  })

  it('should call onDelete when delete is clicked', async () => {
    const onDelete = vi.fn()
    const { user } = render(
      <InstancesTable instances={mockInstances} onDelete={onDelete} />
    )

    // Find and click the first actions menu
    const actionButtons = screen.getAllByRole('button', { name: /actions/i })
    await user.click(actionButtons[0])

    // Click delete option
    const deleteButton = screen.getByText('Delete')
    await user.click(deleteButton)

    expect(onDelete).toHaveBeenCalledWith('1')
  })

  it('should call onTestConnection when test is clicked', async () => {
    const onTestConnection = vi.fn()
    const { user } = render(
      <InstancesTable instances={mockInstances} onTestConnection={onTestConnection} />
    )

    // Find and click the first actions menu
    const actionButtons = screen.getAllByRole('button', { name: /actions/i })
    await user.click(actionButtons[0])

    // Click test connection option
    const testButton = screen.getByText('Test Connection')
    await user.click(testButton)

    expect(onTestConnection).toHaveBeenCalledWith('1')
  })

  it('should render links to instance detail pages', () => {
    render(<InstancesTable instances={mockInstances} />)

    const link1 = screen.getByRole('link', { name: 'Test Instance 1' })
    const link2 = screen.getByRole('link', { name: 'Test Instance 2' })

    expect(link1).toHaveAttribute('href', '/admin/instances/1')
    expect(link2).toHaveAttribute('href', '/admin/instances/2')
  })

  it('should render external links to base URLs', () => {
    render(<InstancesTable instances={mockInstances} />)

    const externalLinks = screen.getAllByRole('link', { name: /atlassian\.net/i })
    
    externalLinks.forEach((link) => {
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    })
  })

  it('should render edit links', () => {
    render(<InstancesTable instances={mockInstances} />)

    const editLinks = screen.getAllByRole('link', { name: /edit/i })
    
    expect(editLinks[0]).toHaveAttribute('href', '/admin/instances/1/edit')
    expect(editLinks[1]).toHaveAttribute('href', '/admin/instances/2/edit')
  })
})

