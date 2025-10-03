import { NextAuthConfig } from 'next-auth';
import Google from 'next-auth/providers/google';
import { UserRole } from './types';

export const authConfig: NextAuthConfig = {
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: 'consent',
          access_type: 'offline',
          response_type: 'code',
        },
      },
    }),
  ],
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
        token.picture = user.image;
        // In production, fetch role from database
        // For now, assign admin role to all users
        token.role = 'admin' as UserRole;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.email = token.email as string;
        session.user.name = token.name as string;
        session.user.image = token.picture as string;
        session.user.role = (token.role as UserRole) || 'user';
      }
      return session;
    },
    async authorized({ auth, request }) {
      const { pathname } = request.nextUrl;

      // Public routes
      if (pathname.startsWith('/auth')) {
        return true;
      }

      // Protected routes require authentication
      if (pathname.startsWith('/admin')) {
        return !!auth?.user;
      }

      return true;
    },
  },
  debug: process.env.NODE_ENV === 'development',
  trustHost: true,
};

