'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Database, Settings, FileText, LayoutDashboard, Bot } from 'lucide-react';

const navigation = [
  {
    name: 'Dashboard',
    href: '/admin',
    icon: LayoutDashboard,
  },
  {
    name: 'Instances',
    href: '/admin/instances',
    icon: Database,
  },
  {
    name: 'Assistant',
    href: '/admin/assistant',
    icon: Bot,
  },
  {
    name: 'Settings',
    href: '/admin/settings',
    icon: Settings,
  },
  {
    name: 'Logs',
    href: '/admin/logs',
    icon: FileText,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 md:pt-16"
      data-testid="app-sidebar"
      aria-label="Sidebar navigation"
    >
      <div className="flex-1 flex flex-col min-h-0 border-r bg-background">
        <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
          <nav
            className="mt-5 flex-1 px-2 space-y-1"
            data-testid="sidebar-nav"
            role="navigation"
            aria-label="Main sidebar navigation"
          >
            {navigation.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
              const testId = `sidebar-nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                  data-testid={testId}
                  data-active={isActive}
                  aria-label={`Go to ${item.name}`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <item.icon
                    className={cn('mr-3 flex-shrink-0 h-5 w-5', isActive ? '' : 'opacity-75')}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </aside>
  );
}

