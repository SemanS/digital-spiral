# Admin UI for Jira Instance Management

A modern, secure Admin UI built with Next.js 15 App Router and TypeScript for managing multiple Jira Cloud instances.

## Features

- 🔐 Google OAuth authentication with NextAuth v5
- 📊 Manage multiple Jira Cloud instances
- 🧪 Test Jira connections before saving
- 🔄 Trigger backfill and incremental sync
- 📈 Monitor sync status and progress
- 🎨 Modern UI with shadcn/ui components
- 🌐 Responsive design (mobile, tablet, desktop)

## Tech Stack

- **Next.js 15.5**: App Router, Server Components
- **React 19**: Hooks, Suspense
- **TypeScript 5**: Strict mode
- **Tailwind CSS 4**: Utility-first styling
- **shadcn/ui**: Component library
- **NextAuth v5**: Authentication
- **TanStack Query v5**: Server state management
- **React Hook Form + Zod**: Form validation
- **Axios**: HTTP client

## Prerequisites

- Node.js 20.14+ (or 22.12+)
- npm 10+
- Google OAuth credentials
- Backend API running on http://localhost:8000

## Environment Variables

Create a `.env.local` file in the root directory:

```bash
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000

# Environment
NODE_ENV=development
```

### Generate NEXTAUTH_SECRET

```bash
openssl rand -base64 32
```

### Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:3000/api/auth/callback/google`
6. Copy Client ID and Client Secret

## Getting Started

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

### Build for Production

```bash
npm run build
npm run start
```

## Available Scripts

- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting
- `npm run test` - Run unit tests with Vitest
- `npm run test:ui` - Run tests with UI
- `npm run test:e2e` - Run E2E tests with Playwright

## Project Structure

```
admin-ui/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (dashboard)/        # Dashboard layout group
│   │   │   ├── admin/          # Admin routes
│   │   │   │   └── instances/  # Instances management
│   │   │   └── layout.tsx      # Dashboard layout
│   │   ├── api/                # API routes
│   │   │   └── auth/           # NextAuth routes
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Home page
│   ├── components/             # React components
│   │   ├── layout/             # Layout components
│   │   ├── instances/          # Instance components
│   │   ├── providers/          # Context providers
│   │   └── ui/                 # shadcn/ui components
│   ├── lib/                    # Utilities and configs
│   │   ├── api/                # API client and functions
│   │   ├── auth/               # NextAuth config
│   │   ├── hooks/              # Custom React hooks
│   │   └── schemas/            # Zod validation schemas
│   └── middleware.ts           # Next.js middleware
├── public/                     # Static assets
├── .env.local                  # Environment variables (not committed)
├── .env.example                # Example environment variables
├── next.config.ts              # Next.js configuration
├── tailwind.config.ts          # Tailwind CSS configuration
└── tsconfig.json               # TypeScript configuration
```

## Development Guidelines

### Code Style

- Use TypeScript strict mode
- Follow ESLint and Prettier rules
- Use functional components with hooks
- Prefer named exports over default exports
- Use absolute imports with `@/` alias

### Component Guidelines

- Keep components small and focused
- Use shadcn/ui components when possible
- Implement loading and error states
- Make components responsive (mobile-first)
- Add proper TypeScript types

### API Guidelines

- Use TanStack Query for data fetching
- Handle errors with custom error types
- Implement retry logic with exponential backoff
- Add proper TypeScript types for requests/responses
- Use Zod for validation

## Testing

### Unit Tests

```bash
npm run test
```

### E2E Tests

```bash
npm run test:e2e
```

## Deployment

### Vercel (Recommended)

1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Set environment variables in Vercel dashboard

### Docker

```bash
docker build -t admin-ui .
docker run -p 3000:3000 admin-ui
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [NextAuth.js Documentation](https://next-auth.js.org/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## License

MIT
