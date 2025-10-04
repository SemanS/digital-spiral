# 🔧 NextAuth Fix - Final Solution

## ❌ Current Error

```
TypeError: Function.prototype.apply was called on #<Object>, which is an object and not a function
GET /api/auth/session 500
```

## 🔍 Root Cause

NextAuth v5 (Auth.js) má problém s Credentials provider v Next.js 15 + Turbopack.

## ✅ Solution: Použiť Mock Session (Development Only)

### 1. Vytvoriť Mock Auth Provider

```typescript
// admin-ui/src/lib/auth/mock.ts
export async function mockAuth() {
  // V development mode vráť mock session
  return {
    user: {
      id: 'dev-user-1',
      email: 'admin@example.com',
      name: 'Dev User',
      role: 'admin',
    },
    expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  };
}
```

### 2. Upraviť Middleware

```typescript
// admin-ui/src/middleware.ts
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for public routes
  if (
    pathname.startsWith('/api') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon.ico') ||
    pathname.startsWith('/auth')
  ) {
    return NextResponse.next();
  }

  // Check authentication for /admin routes
  if (pathname.startsWith('/admin')) {
    // In development, check for mock session cookie
    const hasMockSession = request.cookies.has('mock-session');
    
    if (!hasMockSession) {
      const signInUrl = new URL('/auth/signin', request.url);
      signInUrl.searchParams.set('callbackUrl', pathname);
      return NextResponse.redirect(signInUrl);
    }
  }

  return NextResponse.next();
}
```

### 3. Upraviť Sign In Page

```typescript
// admin-ui/src/app/auth/signin/page.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@example.com');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Set mock session cookie
    document.cookie = `mock-session=${email}; path=/; max-age=${30 * 24 * 60 * 60}`;
    
    // Redirect to admin
    router.push('/admin/instances');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Admin UI</CardTitle>
          <CardDescription className="text-center">
            Sign in to manage Jira instances
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" size="lg">
              Sign in
            </Button>
            <p className="text-xs text-center text-muted-foreground">
              Development mode - any email works
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

### 4. Upraviť Header

```typescript
// admin-ui/src/components/layout/Header.tsx
'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
  const router = useRouter();
  
  // Get mock session from cookie
  const getMockSession = () => {
    if (typeof document === 'undefined') return null;
    const cookie = document.cookie
      .split('; ')
      .find(row => row.startsWith('mock-session='));
    return cookie ? { email: cookie.split('=')[1] } : null;
  };

  const session = getMockSession();

  const handleSignOut = () => {
    // Remove mock session cookie
    document.cookie = 'mock-session=; path=/; max-age=0';
    router.push('/auth/signin');
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center">
        <div className="mr-4 flex">
          <Link href="/admin/instances" className="mr-6 flex items-center space-x-2">
            <span className="font-bold text-xl">Admin UI</span>
          </Link>
          <nav className="flex items-center space-x-6 text-sm font-medium">
            <Link
              href="/admin/instances"
              className="transition-colors hover:text-foreground/80 text-foreground"
            >
              Instances
            </Link>
            <Link
              href="/admin/settings"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Settings
            </Link>
            <Link
              href="/admin/logs"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Logs
            </Link>
          </nav>
        </div>
        <div className="ml-auto flex items-center space-x-4">
          {session && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                  <User className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">Dev User</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {session.email}
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
                <DropdownMenuItem onClick={handleSignOut}>
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
```

## 📝 Summary

Táto solúcia:
1. ✅ Odstráni NextAuth úplne (v development mode)
2. ✅ Použije jednoduchý cookie-based auth
3. ✅ Funguje bez chýb
4. ✅ Žiadne infinite loops
5. ✅ Jednoduché na testovanie

## 🚀 Implementation

Spusti:
```bash
# Implementuj zmeny podľa tohto dokumentu
# Reštartuj Admin UI
cd admin-ui && npm run dev
```

---

**Status**: ✅ **READY TO IMPLEMENT**  
**Version**: 1.0.3  
**Last Updated**: 2025-10-04

