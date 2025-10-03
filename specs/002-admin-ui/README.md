# Admin UI for Jira Instance Management

## Overview

Modern, secure Admin UI built with Next.js 15 App Router and TypeScript for managing multiple Jira Cloud instances. Provides a wizard-based interface for adding instances, testing connections, and managing data synchronization.

## Features

### ✅ Instance Management
- **List View**: View all Jira instances with search, filters, and pagination
- **Add Wizard**: Multi-step wizard for adding new instances (Details → Auth → Validate → Save)
- **Detail View**: View instance configuration, sync status, and history
- **Edit**: Update instance configuration
- **Delete**: Soft delete with confirmation

### ✅ Connection Testing
- **Test Connection**: Validate credentials before saving
- **Real-time Feedback**: Display user info, rate limits, and detailed errors
- **Rate Limiting**: Max 3 tests per minute per user

### ✅ Sync Management
- **Backfill**: Full historical data sync with progress tracking
- **Incremental Sync**: Sync only recent changes
- **Status Monitoring**: Real-time sync status with polling
- **Watermark Tracking**: Track last synced issue timestamp

### ✅ Security
- **Google OAuth 2.0**: Secure authentication with NextAuth v5
- **Role-based Access**: Admin role required for write operations
- **Encrypted Secrets**: API tokens encrypted before storage
- **HTTPS Only**: Production deployment requires HTTPS

### ✅ User Experience
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Accessibility**: WCAG 2.1 AA compliant
- **Loading States**: Skeleton loaders for async operations
- **Error Handling**: Detailed error messages with retry options
- **Optimistic Updates**: Instant feedback for user actions

## Technology Stack

### Frontend
- **Next.js 15**: App Router, Server Components, Server Actions
- **React 18**: Hooks, Suspense, Error Boundaries
- **TypeScript 5.3+**: Strict mode, type-safe development
- **Tailwind CSS 3.4+**: Utility-first styling
- **shadcn/ui**: High-quality component library

### Forms & Validation
- **React Hook Form 7.x**: Performant form management
- **Zod 3.x**: Schema validation
- **@hookform/resolvers**: RHF + Zod integration

### Data Fetching
- **TanStack Query v5**: Server state management, caching
- **axios**: HTTP client with interceptors

### Authentication
- **NextAuth v5**: Authentication for Next.js
- **Google OAuth 2.0**: Primary authentication provider
- **JWT**: Session management

## Project Structure

```
admin-ui/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── admin/
│   │   │   ├── instances/
│   │   │   │   ├── page.tsx              # List
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx          # Wizard
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx          # Detail
│   │   │   │       └── edit/
│   │   │   │           └── page.tsx      # Edit
│   │   │   ├── settings/
│   │   │   └── logs/
│   │   └── layout.tsx
│   ├── api/
│   │   ├── auth/
│   │   │   └── [...nextauth]/
│   │   │       └── route.ts
│   │   └── instances/
│   │       ├── route.ts                  # GET, POST
│   │       └── [id]/
│   │           ├── route.ts              # GET, PUT, DELETE
│   │           ├── test/
│   │           │   └── route.ts          # POST
│   │           ├── backfill/
│   │           │   └── route.ts          # POST
│   │           └── status/
│   │               └── route.ts          # GET
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                               # shadcn/ui components
│   ├── instances/
│   │   ├── InstancesTable.tsx
│   │   ├── InstanceFormWizard.tsx
│   │   ├── TestConnectionButton.tsx
│   │   ├── SyncStatusCard.tsx
│   │   └── BackfillProgressModal.tsx
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   └── providers/
│       ├── AuthProvider.tsx
│       └── QueryProvider.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts                     # Axios client
│   │   ├── instances.ts                  # API functions
│   │   └── types.ts                      # DTOs
│   ├── auth/
│   │   ├── config.ts                     # NextAuth config
│   │   └── middleware.ts                 # Auth middleware
│   ├── hooks/
│   │   ├── useInstances.ts
│   │   ├── useCreateInstance.ts
│   │   ├── useTestConnection.ts
│   │   └── useSyncStatus.ts
│   ├── schemas/
│   │   └── instance.ts                   # Zod schemas
│   └── utils/
│       ├── cn.ts                         # Class name utility
│       └── format.ts                     # Date/time formatting
├── public/
├── styles/
│   └── globals.css
├── .env.local
├── .env.example
├── next.config.js
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn
- Google OAuth 2.0 credentials
- Backend API running (FastAPI)

### Installation

1. **Clone repository**:
   ```bash
   cd digital-spiral
   ```

2. **Create Next.js app**:
   ```bash
   npx create-next-app@latest admin-ui --typescript --tailwind --app --src-dir --import-alias "@/*"
   cd admin-ui
   ```

3. **Install dependencies**:
   ```bash
   npm install next-auth@beta @auth/core
   npm install @tanstack/react-query @tanstack/react-query-devtools
   npm install react-hook-form @hookform/resolvers zod
   npm install axios
   npm install lucide-react class-variance-authority clsx tailwind-merge
   npm install date-fns
   ```

4. **Install shadcn/ui**:
   ```bash
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button input label table dialog card badge toast form select tabs progress alert dropdown-menu
   ```

5. **Configure environment variables**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your values
   ```

6. **Run development server**:
   ```bash
   npm run dev
   ```

7. **Open browser**:
   ```
   http://localhost:3000
   ```

### Environment Variables

Create `.env.local`:

```bash
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-generated-secret-change-in-production

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000

# Environment
NODE_ENV=development
```

**Generate NEXTAUTH_SECRET**:
```bash
openssl rand -base64 32
```

**Get Google OAuth credentials**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:3000/api/auth/callback/google`

## Development

### Run Development Server

```bash
npm run dev
```

### Run Tests

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

### Lint and Format

```bash
# Lint
npm run lint

# Format
npm run format

# Type check
npm run type-check
```

### Build for Production

```bash
npm run build
npm run start
```

## Deployment

### Vercel (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   vercel
   ```

3. **Set environment variables** in Vercel dashboard:
   - `NEXTAUTH_URL`
   - `NEXTAUTH_SECRET`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `NEXT_PUBLIC_API_URL`
   - `API_URL`

4. **Update Google OAuth redirect URI**:
   - Add: `https://your-domain.vercel.app/api/auth/callback/google`

### Docker

```bash
# Build image
docker build -t admin-ui .

# Run container
docker run -p 3000:3000 --env-file .env.local admin-ui
```

## Usage

### Add New Jira Instance

1. Navigate to `/admin/instances`
2. Click "Add Instance" button
3. Follow wizard steps:
   - **Step 1 (Details)**: Enter name, base URL, project filter
   - **Step 2 (Auth)**: Select auth method, enter email and API token
   - **Step 3 (Validate)**: Test connection
   - **Step 4 (Save)**: Review and save
4. Instance added successfully

### Test Connection

1. Navigate to instance detail page
2. Click "Test Connection" button
3. View results (user info, rate limits, errors)

### Start Backfill

1. Navigate to instance detail page
2. Go to "Sync" tab
3. Click "Start Backfill" button
4. Confirm in dialog
5. Monitor progress in modal

### Edit Instance

1. Navigate to instance detail page
2. Click "Edit" button
3. Update fields
4. Click "Save"

### Delete Instance

1. Navigate to instance detail page
2. Click "Delete" button
3. Type instance name to confirm
4. Click "Delete"

## API Endpoints

### Instances

- `GET /api/instances` - List instances
- `POST /api/instances` - Create instance
- `GET /api/instances/:id` - Get instance details
- `PUT /api/instances/:id` - Update instance
- `DELETE /api/instances/:id` - Delete instance

### Connection & Sync

- `POST /api/instances/:id/test` - Test connection
- `POST /api/instances/:id/backfill` - Start backfill
- `POST /api/instances/:id/resync` - Start resync
- `GET /api/instances/:id/status` - Get sync status

## Testing

### Unit Tests (Vitest)

```bash
npm run test
```

Tests:
- API client functions
- Zod schemas
- Utility functions
- Custom hooks

### Component Tests (React Testing Library)

```bash
npm run test
```

Tests:
- InstancesTable
- InstanceFormWizard
- TestConnectionButton
- SyncStatusCard

### E2E Tests (Playwright)

```bash
npm run test:e2e
```

Tests:
- Add instance flow
- Edit instance flow
- Delete instance flow
- Error scenarios

## Troubleshooting

### NextAuth Error: "Invalid callback URL"

**Solution**: Update Google OAuth redirect URI in Google Cloud Console:
- Dev: `http://localhost:3000/api/auth/callback/google`
- Prod: `https://your-domain.com/api/auth/callback/google`

### API Connection Error

**Solution**: Check backend API is running and `NEXT_PUBLIC_API_URL` is correct.

### Build Error: "Module not found"

**Solution**: Run `npm install` to install missing dependencies.

## Contributing

1. Create feature branch: `git checkout -b feature/admin-ui-instances`
2. Make changes
3. Write tests
4. Run linter: `npm run lint`
5. Commit: `git commit -m "feat: add instances list page"`
6. Push: `git push origin feature/admin-ui-instances`
7. Create pull request

## License

MIT

## Support

For issues or questions:
- GitHub Issues: [digital-spiral/issues](https://github.com/SemanS/digital-spiral/issues)
- Email: slavomir.seman@hotovo.com

## Documentation

- [Constitution](./constitution.md) - Project principles and standards
- [Specification](./spec.md) - Detailed requirements
- [Implementation Plan](./plan.md) - Technical implementation plan
- [Tasks](./tasks.md) - Detailed task breakdown
- [Auggie Guide](./AUGGIE_GUIDE.md) - Guide for using Auggie to implement

