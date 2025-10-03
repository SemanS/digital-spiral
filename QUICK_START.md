# 🚀 Digital Spiral - Quick Start Guide

## Prerequisites

- **Docker Desktop** - Running
- **Python 3.11+** - Installed
- **Node.js 18+** - Installed
- **npm** - Installed

---

## 🎯 Quick Start (3 Steps)

### 1. Setup (First Time Only)

```bash
./setup.sh
```

This will:
- ✅ Start Docker services (PostgreSQL, Redis, Mock Jira)
- ✅ Create Python virtual environment
- ✅ Install Python dependencies
- ✅ Run database migrations
- ✅ Install Admin UI dependencies
- ✅ Generate `.env.local` for Admin UI

### 2. Configure Google OAuth

Edit `admin-ui/.env.local`:

```bash
# Get credentials from: https://console.cloud.google.com/
GOOGLE_CLIENT_ID=your-actual-client-id
GOOGLE_CLIENT_SECRET=your-actual-client-secret
```

**How to get Google OAuth credentials:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:3002/api/auth/callback/google`
5. Copy Client ID and Client Secret to `.env.local`

### 3. Start All Services

```bash
./start.sh
```

This will start:
- ✅ PostgreSQL (port 5433)
- ✅ Redis (port 6379)
- ✅ Mock Jira (port 9000)
- ✅ Backend API (port 8000)
- ✅ Admin UI (port 3002)

---

## 🌐 Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Admin UI** | http://localhost:3002 | Main application |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Mock Jira** | http://localhost:9000 | Mock Jira server |

---

## 🛑 Stop All Services

```bash
./stop.sh
```

---

## 📝 Manual Start (Alternative)

If you prefer to start services manually:

### Terminal 1: Backend API
```bash
source venv/bin/activate
uvicorn src.interfaces.rest.main:app --reload --port 8000
```

### Terminal 2: Admin UI
```bash
cd admin-ui
npm run dev
```

### Terminal 3: Docker Services
```bash
docker compose -f docker/docker-compose.dev.yml up
```

---

## 🧪 Testing

### Backend API
```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"digital-spiral-api","version":"1.0.0"}
```

### Admin UI
```bash
# Open in browser
open http://localhost:3002
```

### Database
```bash
# PostgreSQL
docker exec -it digital-spiral-postgres psql -U digital_spiral -d digital_spiral -c "SELECT version();"

# Redis
docker exec -it digital-spiral-redis redis-cli ping
# Expected: PONG
```

---

## 📊 Project Structure

```
digital-spiral/
├── admin-ui/              # Next.js Admin UI
│   ├── src/
│   │   ├── app/          # App Router pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities, hooks, API client
│   └── .env.local        # Environment variables
├── src/                   # Backend (FastAPI)
│   ├── interfaces/       # REST API
│   ├── domain/           # Business logic
│   └── infrastructure/   # Database, cache
├── mockjira/             # Mock Jira server
├── docker/               # Docker Compose files
├── setup.sh              # Setup script
├── start.sh              # Start all services
└── stop.sh               # Stop all services
```

---

## 🔧 Configuration Files

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+psycopg://digital_spiral:dev_password@localhost:5433/digital_spiral

# Redis
REDIS_URL=redis://:dev_password@localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
```

### Admin UI (admin-ui/.env.local)
```bash
# NextAuth
NEXTAUTH_URL=http://localhost:3002
NEXTAUTH_SECRET=<generated-secret>

# Google OAuth
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000
```

---

## 🐛 Troubleshooting

### Port Already in Use

If you see "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8000  # Backend API
lsof -i :3002  # Admin UI
lsof -i :5433  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9000  # Mock Jira

# Kill the process
kill -9 <PID>
```

### Docker Services Not Starting

```bash
# Check Docker status
docker ps

# Restart Docker services
docker compose -f docker/docker-compose.dev.yml down
docker compose -f docker/docker-compose.dev.yml up -d

# Check logs
docker compose -f docker/docker-compose.dev.yml logs
```

### Admin UI Not Loading

1. Check if Google OAuth is configured in `.env.local`
2. Check if Backend API is running: `curl http://localhost:8000/health`
3. Check Admin UI logs: `tail -f logs/admin-ui.log`

### Database Connection Error

```bash
# Check PostgreSQL is running
docker exec -it digital-spiral-postgres pg_isready -U digital_spiral

# Check connection
psql postgresql://digital_spiral:dev_password@localhost:5433/digital_spiral
```

---

## 📚 Next Steps

### 1. Explore Admin UI
- Navigate to http://localhost:3002
- Sign in with Google
- Explore the interface

### 2. Test API Endpoints
- Open http://localhost:8000/docs
- Try the interactive API documentation

### 3. Add Jira Instance
- Go to http://localhost:3002/admin/instances/new
- Fill in the form
- Test connection

### 4. Development
- Backend code: `src/`
- Frontend code: `admin-ui/src/`
- Make changes and see hot reload in action

---

## 📖 Documentation

- **PROJECT_STATUS.md** - Current project status
- **README.md** - Full project documentation
- **.specify/features/** - Spec-Kit documentation

---

## 🆘 Getting Help

### Check Logs
```bash
# Backend API
tail -f logs/backend.log

# Admin UI
tail -f logs/admin-ui.log

# Docker services
docker compose -f docker/docker-compose.dev.yml logs -f
```

### Common Commands
```bash
# Restart everything
./stop.sh && ./start.sh

# Check service status
docker compose -f docker/docker-compose.dev.yml ps

# View running processes
ps aux | grep uvicorn
ps aux | grep node
```

---

## ✅ Success Checklist

- [ ] Docker Desktop is running
- [ ] `./setup.sh` completed successfully
- [ ] Google OAuth credentials configured in `admin-ui/.env.local`
- [ ] `./start.sh` completed successfully
- [ ] http://localhost:8000/health returns healthy status
- [ ] http://localhost:3002 loads successfully
- [ ] Can sign in with Google

---

**You're all set! 🎉**

Start building with Digital Spiral!

