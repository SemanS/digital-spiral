# 🤖 AI Assistant - SPUSTENÝ!

## ✅ AI Assistant je teraz spustený a funkčný!

---

## 🌐 Prístupové URL

### AI Assistant
- **UI**: http://127.0.0.1:7010/v1/ai-assistant/
- **Chat API**: http://127.0.0.1:7010/v1/ai-assistant/chat
- **Autocomplete**: http://127.0.0.1:7010/v1/ai-assistant/autocomplete

### Pulse Dashboard
- **Dashboard**: http://127.0.0.1:7010/v1/pulse/

### Admin UI (Next.js)
- **Home**: http://localhost:3002
- **Instances**: http://localhost:3002/admin/instances

### Backend API (FastAPI)
- **API Root**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

---

## 🎯 Čo môžeš robiť s AI Assistantom?

### Základné príkazy

```
Pridaj komentár do /SCRUM-229 že pracujem na tom
```

```
Presuň /SCRUM-230 do In Progress
```

```
Prirad /SCRUM-231 používateľovi @john
```

```
Vyhľadaj všetky bugs s vysokou prioritou
```

```
Ukáž mi všetky issues v projekte SCRUM
```

```
Vytvor nový issue v projekte SCRUM s názvom "Test issue"
```

### Autocomplete

- **@** - Napíš `@` a začni písať meno používateľa
- **/** - Napíš `/` a začni písať kľúč alebo názov issue

---

## 🔧 Konfigurácia

### Environment Variables

```bash
# AI Provider
GOOGLE_AI_API_KEY=your-google-api-key ✅

# Database
DATABASE_URL=postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator ✅

# Jira
JIRA_BASE_URL=https://your-domain.atlassian.net ✅
ATLASSIAN_CLIENT_ID=your-atlassian-client-id ✅
ATLASSIAN_CLIENT_SECRET=your-atlassian-client-secret ✅
```

---

## 📊 Bežiace služby

| Service | URL | Port | Status |
|---------|-----|------|--------|
| **AI Assistant** | http://127.0.0.1:7010/v1/ai-assistant/ | 7010 | ✅ Running |
| **Pulse Dashboard** | http://127.0.0.1:7010/v1/pulse/ | 7010 | ✅ Running |
| **Admin UI** | http://localhost:3002 | 3002 | ✅ Running |
| **Backend API** | http://localhost:8000 | 8000 | ✅ Running |
| **PostgreSQL** | localhost:5433 | 5433 | ✅ Running |
| **Redis** | localhost:6379 | 6379 | ✅ Running |
| **Mock Jira** | http://localhost:9000 | 9000 | ✅ Running |

---

## 🚀 Ako spustiť AI Assistant (v budúcnosti)

### Metóda 1: Automatický skript (odporúčané)

Vytvorte nový skript `start-ai-assistant.sh`:

```bash
#!/bin/bash

# Start AI Assistant
PYTHONPATH=/Users/hotovo/Projects/digital-spiral:$PYTHONPATH \
DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator" \
GOOGLE_AI_API_KEY=your-google-api-key \
python3 -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 7010 --reload
```

Potom:
```bash
chmod +x start-ai-assistant.sh
./start-ai-assistant.sh
```

### Metóda 2: Manuálne

```bash
# 1. Ensure PostgreSQL is running
docker compose -f docker/docker-compose.dev.yml up -d postgres

# 2. Start AI Assistant
cd /Users/hotovo/Projects/digital-spiral
PYTHONPATH=/Users/hotovo/Projects/digital-spiral:$PYTHONPATH \
DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator" \
GOOGLE_AI_API_KEY=your-google-api-key \
python3 -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 7010 --reload
```

---

## 🧪 Testovanie

### 1. Otvorte AI Assistant UI
```bash
open http://127.0.0.1:7010/v1/ai-assistant/
```

### 2. Vyskúšajte základný príkaz
```
Ahoj! Ako sa máš?
```

### 3. Vyskúšajte Jira príkaz
```
Vyhľadaj všetky issues v projekte SCRUM
```

### 4. Vyskúšajte autocomplete
- Napíšte `@` a začnite písať meno používateľa
- Napíšte `/` a začnite písať kľúč issue

---

## 🔌 API Endpoints

### Chat
```bash
curl -X POST http://127.0.0.1:7010/v1/ai-assistant/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: insight-bridge" \
  -d '{
    "messages": [
      {"role": "user", "content": "Vyhľadaj všetky issues"}
    ],
    "project_keys": ["SCRUM"]
  }'
```

### Autocomplete
```bash
curl -X POST http://127.0.0.1:7010/v1/ai-assistant/autocomplete \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: insight-bridge" \
  -d '{
    "query": "john",
    "type": "user"
  }'
```

---

## 🎨 Features

### AI Assistant UI
- ✅ Chat interface
- ✅ Autocomplete (@users, /issues)
- ✅ Project selector
- ✅ Issue context
- ✅ Tool calls visualization
- ✅ Real-time responses

### Supported Actions
- ✅ Search issues (JQL)
- ✅ Get issue details
- ✅ Add comment
- ✅ Transition issue
- ✅ Assign issue
- ✅ Create issue
- ✅ Update issue
- ✅ List projects
- ✅ Get project details

### AI Providers
- ✅ Google AI (Gemini) - Currently active
- ✅ OpenAI (GPT-4) - Available

---

## 📁 Architektúra

```
orchestrator/
├── app.py                    # Main FastAPI app
├── ai_assistant_api.py       # AI Assistant endpoints
├── ai_providers.py           # Google AI & OpenAI providers
├── pulse_api.py              # Pulse dashboard endpoints
├── pulse_service.py          # Jira instance management
├── sql_tools.py              # SQL query tools
├── checkpoint_service.py     # Rollback functionality
└── templates/
    ├── ai_assistant.html     # AI Assistant UI
    ├── pulse_dashboard.html  # Pulse Dashboard UI
    └── static/
        └── ai-assistant.js   # AI Assistant JS
```

---

## 🔧 Databáza

### Orchestrator Database
- **Name**: `ds_orchestrator`
- **User**: `ds` / `ds`
- **Port**: 5433 (mapped from 5432)
- **Tables**:
  - `jira_instances` - Jira instance configurations
  - `sync_watermarks` - Sync progress tracking
  - `audit_log` - Audit trail
  - `checkpoints` - Rollback points

### Queries
```bash
# Connect to database
docker exec -it digital-spiral-postgres psql -U ds -d ds_orchestrator

# List tables
\dt

# View instances
SELECT * FROM jira_instances;

# View sync status
SELECT * FROM sync_watermarks;
```

---

## 🛑 Zastavenie služieb

### Zastaviť AI Assistant
```bash
# Find process
ps aux | grep "uvicorn orchestrator.app"

# Kill process
kill <PID>

# Or use Ctrl+C in terminal
```

### Zastaviť všetky služby
```bash
./stop.sh
```

---

## 📚 Dokumentácia

### Quick Start
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[docs/AI_ASSISTANT_QUICKSTART.md](docs/AI_ASSISTANT_QUICKSTART.md)** - AI Assistant guide

### Configuration
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration details
- **[OAUTH_FIX.md](OAUTH_FIX.md)** - OAuth fix details
- **[FINAL_FIX.md](FINAL_FIX.md)** - Complete fix summary

### AI Assistant
- **[AI_ASSISTANT_RUNNING.md](AI_ASSISTANT_RUNNING.md)** - This file

---

## 🎯 Ďalšie kroky

### 1. Otestujte AI Assistant
```bash
open http://127.0.0.1:7010/v1/ai-assistant/
```

### 2. Pridajte Jira inštanciu cez Admin UI
```bash
open http://localhost:3002/admin/instances/new
```

### 3. Otestujte Pulse Dashboard
```bash
open http://127.0.0.1:7010/v1/pulse/
```

### 4. Integrujte AI Assistant s Admin UI
- Pridajte link na AI Assistant do Admin UI
- Vytvorte embedded chat widget
- Pridajte AI suggestions do instance detail page

---

## ✅ Status

```
✅ AI Assistant - Running (port 7010)
✅ Pulse Dashboard - Running (port 7010)
✅ Admin UI - Running (port 3002)
✅ Backend API - Running (port 8000)
✅ PostgreSQL - Running (port 5433)
✅ Redis - Running (port 6379)
✅ Mock Jira - Running (port 9000)
✅ Google AI - Configured
✅ Jira OAuth - Configured
✅ Database - Configured
```

---

**AI Assistant je pripravený na použitie! 🤖**

Môžete začať chatovať s Jira inštanciami cez AI Assistant UI!

---

## 🆘 Troubleshooting

### AI Assistant sa nespustí
```bash
# Check database
docker exec -it digital-spiral-postgres psql -U ds -d ds_orchestrator

# Check environment variables
echo $GOOGLE_AI_API_KEY
echo $DATABASE_URL

# Check logs
# Look for errors in terminal output
```

### Chat nefunguje
```bash
# Check if Jira instance is configured
curl http://127.0.0.1:7010/v1/pulse/instances

# Check AI provider
curl http://127.0.0.1:7010/v1/ai-assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'
```

### Autocomplete nefunguje
```bash
# Check if projects are loaded
curl http://127.0.0.1:7010/v1/pulse/projects

# Check autocomplete endpoint
curl http://127.0.0.1:7010/v1/ai-assistant/autocomplete \
  -H "Content-Type: application/json" \
  -d '{"query":"test","type":"user"}'
```

---

**Happy chatting! 🚀**
