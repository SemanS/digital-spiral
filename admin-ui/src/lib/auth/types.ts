import { DefaultSession } from 'next-auth';

export type UserRole = 'admin' | 'user';

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      role: UserRole;
    } & DefaultSession['user'];
  }

  interface User {
    role?: UserRole;
  }
}

declare module '@auth/core/jwt' {
  interface JWT {
    role?: UserRole;
  }
}

