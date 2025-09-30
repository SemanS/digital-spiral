# 📊 Executive Work Pulse - READY TO USE! 🚀

**Jednopanelový dashboard pre top manažérov** - okamžitý prehľad o stave práce naprieč Jira projektmi.

---

## ✅ Čo je HOTOVÉ

### Backend ✅
- ✅ **Dátový model** - WorkItem, Transitions, SLA, MetricDaily, PulseConfig
- ✅ **Jira Connector** - Multi-instance podpora s validáciou duplicít
- ✅ **Backfill Service** - Automatické načítanie 90 dní histórie
- ✅ **REST API** - Kompletné endpointy pre všetky operácie
- ✅ **Error Handling** - Validácie, error messages, logging

### Frontend ✅
- ✅ **Web Dashboard** - Moderný, responzívny UI
- ✅ **5 Kľúčových Metrik** - Throughput, Lead Time, SLA Risk, WIP, Quality
- ✅ **Tabuľka Projektov** - Created/Closed/WIP breakdown
- ✅ **Add Jira Modal** - Jednoduchý formulár na pridanie Jiry
- ✅ **Progress Feedback** - Alerts, loading states, auto-refresh

### Dokumentácia ✅
- ✅ **Quick Start Guide** - Krok-za-krokom návod
- ✅ **Troubleshooting** - Riešenia bežných problémov
- ✅ **API Reference** - Kompletná dokumentácia API

---

## 🚀 SPUSTENIE (3 kroky)

### 1. Server už beží! ✅

```bash
# Server beží na:
http://127.0.0.1:7010

# Dashboard:
http://127.0.0.1:7010/v1/pulse/
```

### 2. Získaj Jira API Token

1. Choď na: https://id.atlassian.com/manage-profile/security/api-tokens
2. Klikni **"Create API token"**
3. Pomenuj: `Pulse Dashboard`
4. **Skopíruj token** (zobrazí sa len raz!)

### 3. Pridaj Jira Inštanciu

**Metóda A: Cez Web UI (odporúčané)**

1. Otvor: http://127.0.0.1:7010/v1/pulse/
2. Klikni: `+ Add Jira Instance`
3. Vyplň:
   ```
   Display Name: Slavo's Jira
   Base URL: https://slavoseman.atlassian.net
   Email: slavosmn@gmail.com
   API Token: [tvoj-token-sem]
   ```
4. Klikni: `Add & Test`
5. Počkaj 30-60 sekúnd (backfill beží na pozadí)
6. Dashboard sa automaticky aktualizuje!

**Metóda B: Cez API**

```bash
curl -X POST http://localhost:7010/v1/pulse/jira/instances \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -d '{
    "display_name": "Slavo'\''s Jira",
    "base_url": "https://slavoseman.atlassian.net",
    "email": "slavosmn@gmail.com",
    "api_token": "TVOJ-API-TOKEN"
  }'
```

---

## 📊 Čo uvidíš na dashboarde

### 5 Kľúčových Metrik

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Throughput   │  │  Lead Time   │  │  SLA Risk    │
│              │  │              │  │              │
│  45 / 52     │  │  P50: 3.2d   │  │     12       │
│  ↑ +8%       │  │  P90: 7.1d   │  │  ⚠️ HIGH     │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐
│     WIP      │  │   Quality    │
│              │  │              │
│     127      │  │    8.2%      │
│  23 stuck    │  │  ↓ -2%       │
└──────────────┘  └──────────────┘
```

### Tabuľka Projektov

```
Project  | Created | Closed | WIP
---------|---------|--------|-----
SCRUM    |   45    |   38   |  23
KANBAN   |   32    |   28   |  15
SUPPORT  |   18    |   16   |   8
```

---

## 🔧 Užitočné príkazy

```bash
# Spustenie servera (ak nie je spustený)
PYTHONPATH=/Users/hotovo/Projects/digital-spiral \
  python3 -m uvicorn orchestrator.app:app --reload --port 7010

# Inicializácia databázy (už hotové)
python3 scripts/init_pulse_db.py

# Test API
./scripts/test_pulse_flow.sh

# List Jira instances
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/jira/instances

# Get dashboard data
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/dashboard

# Manual backfill
curl -X POST http://localhost:7010/v1/pulse/jira/backfill \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "INSTANCE-ID",
    "days_back": 90,
    "max_issues": 1000
  }'
```

---

## 🐛 Troubleshooting

### "No projects found"
- **Počkaj 30-60 sekúnd** - backfill beží na pozadí
- **Skontroluj logy** - uvidíš progress v termináli
- **Refresh dashboard** - klikni na 🔄 Refresh button

### "Jira instance already exists"
- **Skontroluj existujúce** - možno si ju už pridal
- **Použi iný email** - ak máš viacero účtov
- **Odstráň duplicitu** - cez DELETE API

### "401 Unauthorized"
- **Skontroluj API token** - musí byť správny
- **Skontroluj email** - musí byť presne ako v Jira
- **Skontroluj base URL** - bez `/` na konci

**Viac riešení:** [docs/PULSE_TROUBLESHOOTING.md](docs/PULSE_TROUBLESHOOTING.md)

---

## 📁 Štruktúra projektu

```
orchestrator/
├── pulse_models.py          # SQLAlchemy modely
├── pulse_service.py         # Business logika
├── pulse_backfill.py        # Backfill service
├── pulse_api.py             # REST API endpoints
└── templates/
    └── pulse_dashboard.html # Web UI

scripts/
├── init_pulse_db.py         # DB inicializácia
└── test_pulse_flow.sh       # Test script

docs/
├── EXECUTIVE_WORK_PULSE.md  # Kompletný prehľad
├── PULSE_QUICKSTART.md      # Quick start guide
└── PULSE_TROUBLESHOOTING.md # Troubleshooting

artifacts/
└── orchestrator.db          # SQLite databáza
```

---

## 🎯 Implementované Features

### ✅ Hotové
- [x] Multi-tenant architecture
- [x] Multi-Jira instance support
- [x] Duplicate instance validation
- [x] Connection testing
- [x] Automatic backfill on add
- [x] Progress feedback in UI
- [x] Error handling & validation
- [x] 5 core metrics calculation
- [x] Project breakdown table
- [x] Responsive web UI
- [x] REST API
- [x] Comprehensive documentation

### 🚧 TODO (budúcnosť)
- [ ] Real-time webhook updates
- [ ] Daily aggregation cron job
- [ ] SLA tracking (Jira Service Management)
- [ ] Reopen rate calculation
- [ ] 4-week trend comparison
- [ ] Sparkline graphs
- [ ] PDF/Email digest
- [ ] Slack integration
- [ ] GitHub Issues connector
- [ ] Zendesk connector
- [ ] PagerDuty connector

---

## 📊 API Endpoints

### Jira Instances
```bash
GET    /v1/pulse/jira/instances          # List instances
POST   /v1/pulse/jira/instances          # Add instance (+ auto backfill)
DELETE /v1/pulse/jira/instances/{id}     # Delete instance
POST   /v1/pulse/jira/test-connection    # Test connection
POST   /v1/pulse/jira/backfill           # Manual backfill
```

### Dashboard
```bash
GET /v1/pulse/                            # Web UI
GET /v1/pulse/dashboard                   # Dashboard data (JSON)
GET /v1/pulse/dashboard?project_key=X     # Filter by project
GET /v1/pulse/dashboard?since=2025-09-01  # Filter by date
GET /v1/pulse/config                      # Pulse config
```

---

## 💡 Príklad použitia

### 1. Pridaj Jira inštanciu
```bash
curl -X POST http://localhost:7010/v1/pulse/jira/instances \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -d '{
    "display_name": "My Jira",
    "base_url": "https://company.atlassian.net",
    "email": "user@company.com",
    "api_token": "your-token"
  }'
```

**Odpoveď:**
```json
{
  "success": true,
  "instance": {
    "id": "abc-123",
    "display_name": "My Jira",
    "base_url": "https://company.atlassian.net",
    "active": true
  },
  "message": "Backfill started in background..."
}
```

### 2. Počkaj na backfill (30-60s)

Server logy:
```
🚀 Starting backfill for My Jira from 2025-07-03 to 2025-10-01
Progress: 10 issues fetched, 2 projects
Progress: 20 issues fetched, 3 projects
...
✅ Backfill complete: 234 issues fetched, 5 projects, 0 errors
```

### 3. Zobraz dashboard
```bash
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/dashboard
```

**Odpoveď:**
```json
{
  "throughput": {
    "created": 52,
    "closed": 45,
    "delta_pct": 0.08
  },
  "leadTime": {
    "p50Days": 3.2,
    "p90Days": 7.1
  },
  "wip": {
    "total": 127,
    "noAssignee": 15,
    "stuck": 23
  },
  "projects": [
    {"key": "SCRUM", "created": 45, "closed": 38, "wip": 23},
    {"key": "KANBAN", "created": 32, "closed": 28, "wip": 15}
  ]
}
```

---

## 🎉 Hotovo!

Máš teraz funkčný **Executive Work Pulse Dashboard**!

### Čo ďalej?

1. **Otvor dashboard**: http://127.0.0.1:7010/v1/pulse/
2. **Pridaj svoju Jiru** (ak si to ešte neurobil)
3. **Sleduj metriky** - dashboard sa automaticky aktualizuje
4. **Pridaj viac Jira inštancií** - podporuje multi-instance
5. **Experimentuj s API** - všetky operácie sú dostupné cez REST API

### Potrebuješ pomoc?

- 📖 [Quick Start Guide](docs/PULSE_QUICKSTART.md)
- 🔧 [Troubleshooting](docs/PULSE_TROUBLESHOOTING.md)
- 📊 [Full Documentation](docs/EXECUTIVE_WORK_PULSE.md)

---

**Enjoy your Executive Work Pulse Dashboard! 🚀📊**

