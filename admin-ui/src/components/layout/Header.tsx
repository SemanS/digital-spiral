'use client';

import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { User, LogOut, Settings } from 'lucide-react';

export function Header() {
  const { data: session } = useSession();

  return (
    <header
      data-testid="app-header"
      className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
    >
      <div className="container flex h-16 items-center">
        <div className="mr-4 flex">
          <Link
            href="/admin/instances"
            className="mr-6 flex items-center space-x-2"
            data-testid="header-logo"
            aria-label="Go to instances dashboard"
          >
            <span className="font-bold text-xl">Admin UI</span>
          </Link>
          <nav
            className="flex items-center space-x-6 text-sm font-medium"
            data-testid="header-nav"
            role="navigation"
            aria-label="Main navigation"
          >
            <Link
              href="/admin/instances"
              className="transition-colors hover:text-foreground/80 text-foreground"
              data-testid="header-nav-instances"
              aria-label="Go to instances page"
            >
              Instances
            </Link>
            <Link
              href="/admin/settings"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              data-testid="header-nav-settings"
              aria-label="Go to settings page"
            >
              Settings
            </Link>
            <Link
              href="/admin/logs"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              data-testid="header-nav-logs"
              aria-label="Go to logs page"
            >
              Logs
            </Link>
          </nav>
        </div>
        <div className="ml-auto flex items-center space-x-4">
          {session?.user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="relative h-8 w-8 rounded-full"
                  data-testid="header-user-menu"
                  aria-label="Open user menu"
                >
                  <User className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{session.user.name}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {session.user.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/admin/settings">
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Settings</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => signOut({ callbackUrl: '/auth/signin' })}
                  data-testid="header-user-menu-signout"
                  aria-label="Sign out of your account"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  );
}

