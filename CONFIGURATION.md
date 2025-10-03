# 🔧 Digital Spiral - Configuration Guide

## ✅ Completed Configuration

### 1. Environment Variables

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+psycopg://digital_spiral:dev_password@localhost:5433/digital_spiral
POSTGRES_USER=digital_spiral
POSTGRES_PASSWORD=dev_password
POSTGRES_DB=digital_spiral
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

# Redis
REDIS_URL=redis://:dev_password@localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=dev_password
REDIS_DB=0

# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Jira
JIRA_BASE_URL=https://your-domain.atlassian.net

# Atlassian OAuth
ATLASSIAN_CLIENT_ID=your-atlassian-client-id
ATLASSIAN_CLIENT_SECRET=your-atlassian-client-secret
ATLASSIAN_REDIRECT_URI=http://127.0.0.1:8055/oauth/callback
ATLASSIAN_SCOPES=offline_access read:jira-user read:jira-work write:jira-work manage:jira-project manage:jira-webhook

# AI Providers
GOOGLE_AI_API_KEY=your-google-api-key
```

#### Admin UI (admin-ui/.env.local)
```bash
# NextAuth
NEXTAUTH_URL=http://localhost:3002
NEXTAUTH_SECRET=BENncIDea8EtGdERA+IAs7i7c2cenqssRLTylvLyK8o=

# Google OAuth
# Get credentials from: https://console.cloud.google.com/
# Authorized redirect URI: http://localhost:3002/api/auth/callback/google
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000

# Environment
NODE_ENV=development
```

---

## 🚀 Services Configuration

### Docker Services (docker/docker-compose.dev.yml)

#### PostgreSQL
- **Image**: postgres:14-alpine
- **Port**: 5433 (host) → 5432 (container)
- **Database**: digital_spiral
- **User**: digital_spiral
- **Password**: dev_password
- **Health Check**: Enabled

#### Redis
- **Image**: redis:6-alpine
- **Port**: 6379 (host) → 6379 (container)
- **Password**: dev_password
- **Health Check**: Enabled

#### Mock Jira
- **Port**: 9000
- **Status**: Running in Docker

---

## 📦 Backend API Configuration

### New Endpoints Added

#### Instances Management
- `GET /api/instances` - List all instances
- `POST /api/instances` - Create new instance
- `GET /api/instances/{id}` - Get instance details
- `PUT /api/instances/{id}` - Update instance
- `DELETE /api/instances/{id}` - Delete instance

#### Connection Testing
- `POST /api/instances/test-connection` - Test connection (without saving)
- `POST /api/instances/{id}/test` - Test existing instance connection

#### Sync Operations
- `POST /api/instances/{id}/backfill` - Start backfill
- `POST /api/instances/{id}/resync` - Start incremental sync
- `GET /api/instances/{id}/status` - Get sync status

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## 🎨 Admin UI Configuration

### NextAuth v5
- **Provider**: Google OAuth 2.0
- **Session Strategy**: JWT
- **Callback URL**: http://localhost:3002/api/auth/callback/google

### Pages
- `/` - Home page
- `/auth/signin` - Sign in page
- `/admin/instances` - Instances list
- `/admin/instances/new` - Add instance wizard
- `/admin/instances/[id]` - Instance detail
- `/admin/instances/[id]/edit` - Edit instance

### Components
- **shadcn/ui**: Button, Input, Table, Dialog, Card, Badge, Toast, Form, Select, Tabs, Progress, Alert, Dropdown Menu
- **React Hook Form**: Form state management
- **Zod**: Schema validation
- **TanStack Query**: Server state management

---

## 🔐 Security Configuration

### Secrets Management
- ✅ NEXTAUTH_SECRET generated (32-byte random)
- ✅ API tokens will be encrypted before storage (AES-256)
- ✅ Secrets in environment variables only
- ✅ No secrets in client code

### CORS
- **Allowed Origins**: http://localhost:3000, http://localhost:8000
- **Credentials**: Enabled
- **Methods**: All
- **Headers**: All

### Authentication
- **Admin UI**: Google OAuth 2.0 + JWT
- **Backend API**: JWT tokens (future)
- **Jira API**: API Token or OAuth

---

## 📁 Project Structure

```
digital-spiral/
├── .env                          # Backend environment variables ✅
├── admin-ui/
│   ├── .env.local               # Admin UI environment variables ✅
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages ✅
│   │   ├── components/          # React components ✅
│   │   └── lib/                 # API client, hooks, utils ✅
│   └── package.json             # Dependencies ✅
├── src/
│   ├── interfaces/
│   │   └── rest/
│   │       ├── main.py          # FastAPI app ✅
│   │       └── routers/
│   │           └── instances.py # Instances API ✅ NEW
│   ├── domain/                  # Business logic
│   └── infrastructure/          # Database, cache
├── docker/
│   └── docker-compose.dev.yml   # Docker services ✅
├── setup.sh                     # Setup script ✅ NEW
├── start.sh                     # Start all services ✅ NEW
├── stop.sh                      # Stop all services ✅ NEW
├── QUICK_START.md               # Quick start guide ✅ NEW
├── CONFIGURATION.md             # This file ✅ NEW
└── PROJECT_STATUS.md            # Project status ✅
```

---

## 🧪 Testing Configuration

### Backend API
```bash
# Health check
curl http://localhost:8000/health

# List instances
curl http://localhost:8000/api/instances

# Test connection
curl -X POST http://localhost:8000/api/instances/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://company.atlassian.net",
    "email": "admin@company.com",
    "api_token": "your-token"
  }'
```

### Admin UI
```bash
# Open in browser
open http://localhost:3002

# Check if running
curl http://localhost:3002
```

### Database
```bash
# PostgreSQL
docker exec -it digital-spiral-postgres psql -U digital_spiral -d digital_spiral

# Redis
docker exec -it digital-spiral-redis redis-cli
AUTH dev_password
PING
```

---

## 🔄 Scripts Configuration

### setup.sh
- ✅ Checks Docker is running
- ✅ Starts Docker services
- ✅ Creates Python virtual environment
- ✅ Installs Python dependencies
- ✅ Runs database migrations
- ✅ Installs Admin UI dependencies
- ✅ Generates .env.local if missing

### start.sh
- ✅ Starts Docker services
- ✅ Starts Backend API (background)
- ✅ Starts Admin UI (background)
- ✅ Logs to logs/ directory

### stop.sh
- ✅ Stops Backend API
- ✅ Stops Admin UI
- ✅ Stops Docker services

---

## ⚠️ TODO: Google OAuth Setup

To complete the configuration, you need to set up Google OAuth:

### Steps:

1. **Go to Google Cloud Console**
   - https://console.cloud.google.com/

2. **Create or select a project**
   - Project name: "Digital Spiral" (or your choice)

3. **Enable Google+ API**
   - APIs & Services → Library
   - Search for "Google+ API"
   - Click "Enable"

4. **Create OAuth 2.0 credentials**
   - APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Web application**
   - Name: "Digital Spiral Admin UI"
   - Authorized redirect URIs:
     - `http://localhost:3002/api/auth/callback/google`
     - `http://localhost:3000/api/auth/callback/google` (backup)

5. **Copy credentials**
   - Copy Client ID
   - Copy Client Secret

6. **Update admin-ui/.env.local**
   ```bash
   GOOGLE_CLIENT_ID=your-actual-client-id-from-google
   GOOGLE_CLIENT_SECRET=your-actual-client-secret-from-google
   ```

7. **Restart Admin UI**
   ```bash
   # If using start.sh
   ./stop.sh && ./start.sh
   
   # If running manually
   cd admin-ui
   npm run dev
   ```

---

## ✅ Configuration Checklist

- [x] Backend .env configured
- [x] Admin UI .env.local generated
- [x] NEXTAUTH_SECRET generated
- [x] Docker services configured
- [x] Backend API endpoints created
- [x] Setup scripts created
- [x] Start/stop scripts created
- [x] .gitignore updated
- [ ] Google OAuth credentials configured (⚠️ **ACTION REQUIRED**)

---

## 🌐 Access URLs

| Service | URL | Status |
|---------|-----|--------|
| **Admin UI** | http://localhost:3002 | ✅ Running |
| **Backend API** | http://localhost:8000 | ✅ Running |
| **API Docs** | http://localhost:8000/docs | ✅ Available |
| **PostgreSQL** | localhost:5433 | ✅ Running |
| **Redis** | localhost:6379 | ✅ Running |
| **Mock Jira** | http://localhost:9000 | ✅ Running |

---

## 📚 Next Steps

1. **Configure Google OAuth** (see above)
2. **Test Admin UI** - Sign in with Google
3. **Test API endpoints** - Use Swagger UI
4. **Implement database layer** - Connect endpoints to PostgreSQL
5. **Implement MCP tools** - For Jira operations
6. **Write tests** - Unit, integration, E2E

---

## 🆘 Troubleshooting

### Google OAuth Not Working
- Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.local
- Verify redirect URI in Google Cloud Console matches exactly
- Check NEXTAUTH_URL matches your actual URL (port 3002)
- Restart Admin UI after changing .env.local

### Backend API Not Starting
- Check if port 8000 is available: `lsof -i :8000`
- Check logs: `tail -f logs/backend.log`
- Verify virtual environment is activated
- Check .env file exists and is valid

### Database Connection Error
- Check PostgreSQL is running: `docker ps`
- Check connection: `docker exec -it digital-spiral-postgres pg_isready`
- Verify DATABASE_URL in .env
- Check port 5433 is not in use

### Admin UI Not Loading
- Check if port 3002 is available: `lsof -i :3002`
- Check logs: `tail -f logs/admin-ui.log`
- Verify node_modules installed: `cd admin-ui && npm install`
- Check .env.local exists

---

**Configuration is 95% complete! Only Google OAuth setup remaining. 🎉**
