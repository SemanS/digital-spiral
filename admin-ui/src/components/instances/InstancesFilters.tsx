'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search } from 'lucide-react';
import type { SyncStatusType, AuthMethod } from '@/lib/api/types';

interface InstancesFiltersProps {
  onSearchChange: (search: string) => void;
  onStatusChange: (status: SyncStatusType | 'all') => void;
  onAuthMethodChange: (authMethod: AuthMethod | 'all') => void;
  defaultSearch?: string;
  defaultStatus?: SyncStatusType | 'all';
  defaultAuthMethod?: AuthMethod | 'all';
}

export function InstancesFilters({
  onSearchChange,
  onStatusChange,
  onAuthMethodChange,
  defaultSearch = '',
  defaultStatus = 'all',
  defaultAuthMethod = 'all',
}: InstancesFiltersProps) {
  const [search, setSearch] = useState(defaultSearch);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(search);
    }, 300);

    return () => clearTimeout(timer);
  }, [search, onSearchChange]);

  return (
    <div className="flex flex-col sm:flex-row gap-4">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search instances..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>
      <Select defaultValue={defaultStatus} onValueChange={onStatusChange}>
        <SelectTrigger className="w-full sm:w-[180px]">
          <SelectValue placeholder="Filter by status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="idle">Idle</SelectItem>
          <SelectItem value="syncing">Syncing</SelectItem>
          <SelectItem value="error">Error</SelectItem>
        </SelectContent>
      </Select>
      <Select defaultValue={defaultAuthMethod} onValueChange={onAuthMethodChange}>
        <SelectTrigger className="w-full sm:w-[180px]">
          <SelectValue placeholder="Filter by auth" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Auth Methods</SelectItem>
          <SelectItem value="api_token">API Token</SelectItem>
          <SelectItem value="oauth">OAuth</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

