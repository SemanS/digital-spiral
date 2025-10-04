/**
 * Example: Header Component with Test IDs
 * 
 * This is an example of how to add test IDs to the Header component.
 * Compare this with the original file: admin-ui/src/components/layout/Header.tsx
 * 
 * Changes made:
 * 1. Added data-testid to header element
 * 2. Added data-testid to logo link
 * 3. Added data-testid to navigation
 * 4. Added data-testid to each nav link
 * 5. Added data-testid to user menu trigger
 * 6. Added data-testid to dropdown menu items
 * 7. Added aria-label for accessibility
 * 8. Added role="navigation" for semantic HTML
 */

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
            aria-label="Go to Admin UI home"
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
              aria-label="Go to Instances page"
            >
              Instances
            </Link>
            <Link
              href="/admin/settings"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              data-testid="header-nav-settings"
              aria-label="Go to Settings page"
            >
              Settings
            </Link>
            <Link
              href="/admin/logs"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              data-testid="header-nav-logs"
              aria-label="Go to Logs page"
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
              <DropdownMenuContent 
                className="w-56" 
                align="end" 
                forceMount
                data-testid="header-user-menu-content"
              >
                <DropdownMenuLabel 
                  className="font-normal"
                  data-testid="header-user-info"
                >
                  <div className="flex flex-col space-y-1">
                    <p 
                      className="text-sm font-medium leading-none"
                      data-testid="header-user-name"
                    >
                      {session.user.name}
                    </p>
                    <p 
                      className="text-xs leading-none text-muted-foreground"
                      data-testid="header-user-email"
                    >
                      {session.user.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link 
                    href="/admin/settings"
                    data-testid="header-user-menu-settings"
                    aria-label="Go to Settings"
                  >
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Settings</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => signOut({ callbackUrl: '/auth/signin' })}
                  data-testid="header-user-menu-signout"
                  aria-label="Sign out"
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

/**
 * Test IDs Added:
 * 
 * - app-header: Main header element
 * - header-logo: Logo link
 * - header-nav: Navigation container
 * - header-nav-instances: Instances nav link
 * - header-nav-settings: Settings nav link
 * - header-nav-logs: Logs nav link
 * - header-user-menu: User menu trigger button
 * - header-user-menu-content: Dropdown menu content
 * - header-user-info: User info label
 * - header-user-name: User name text
 * - header-user-email: User email text
 * - header-user-menu-settings: Settings menu item
 * - header-user-menu-signout: Sign out menu item
 * 
 * ARIA Labels Added:
 * 
 * - "Go to Admin UI home" on logo
 * - "Main navigation" on nav element
 * - "Go to Instances page" on Instances link
 * - "Go to Settings page" on Settings link
 * - "Go to Logs page" on Logs link
 * - "Open user menu" on user menu button
 * - "Go to Settings" on settings menu item
 * - "Sign out" on sign out menu item
 * 
 * Semantic HTML:
 * 
 * - Added role="navigation" to nav element
 * - Added aria-label to navigation
 * - All interactive elements have descriptive labels
 */

/**
 * Example E2E Test:
 * 
 * test('header displays navigation links', async ({ page }) => {
 *   await page.goto('/admin/instances');
 *   
 *   // Verify header is visible
 *   await expect(page.locator('[data-testid="app-header"]')).toBeVisible();
 *   
 *   // Verify logo
 *   await expect(page.locator('[data-testid="header-logo"]')).toBeVisible();
 *   
 *   // Verify navigation links
 *   await expect(page.locator('[data-testid="header-nav-instances"]')).toBeVisible();
 *   await expect(page.locator('[data-testid="header-nav-settings"]')).toBeVisible();
 *   await expect(page.locator('[data-testid="header-nav-logs"]')).toBeVisible();
 * });
 * 
 * test('user can open user menu', async ({ page }) => {
 *   await page.goto('/admin/instances');
 *   
 *   // Click user menu
 *   await page.click('[data-testid="header-user-menu"]');
 *   
 *   // Verify menu is open
 *   await expect(page.locator('[data-testid="header-user-menu-content"]')).toBeVisible();
 *   
 *   // Verify user info
 *   await expect(page.locator('[data-testid="header-user-name"]')).toContainText('Admin User');
 *   await expect(page.locator('[data-testid="header-user-email"]')).toContainText('admin@example.com');
 * });
 * 
 * test('user can sign out', async ({ page }) => {
 *   await page.goto('/admin/instances');
 *   
 *   // Open user menu
 *   await page.click('[data-testid="header-user-menu"]');
 *   
 *   // Click sign out
 *   await page.click('[data-testid="header-user-menu-signout"]');
 *   
 *   // Verify redirect to sign in page
 *   await page.waitForURL('/auth/signin');
 * });
 */

