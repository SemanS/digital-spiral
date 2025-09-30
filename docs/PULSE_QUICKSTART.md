# 🚀 Executive Work Pulse - Quick Start Guide

Tento návod ti ukáže, ako spustiť Executive Work Pulse dashboard a pripojiť tvoju Jira inštanciu.

---

## ✅ Čo je hotové

- ✅ **Dátový model** - WorkItem, Transitions, SLA, MetricDaily
- ✅ **Jira Connector** - Multi-instance podpora
- ✅ **Backfill Service** - Načítanie historických dát
- ✅ **Dashboard UI** - Web rozhranie s 5 metrikami
- ✅ **REST API** - Endpointy pre všetky operácie

---

## 📋 Predpoklady

1. **Python 3.9+** nainštalovaný
2. **Jira Cloud** účet s API tokenom
3. **Dependencies** nainštalované:
   ```bash
   pip3 install rapidfuzz uvicorn fastapi pydantic sqlalchemy psycopg prometheus-client
   ```

---

## 🚀 Spustenie

### 1. Inicializácia databázy

```bash
cd /Users/hotovo/Projects/digital-spiral
python3 scripts/init_pulse_db.py
```

**Výstup:**
```
Initializing Executive Work Pulse database tables...
✅ Database tables created successfully!

Created tables:
  - tenants
  - agents
  - credit_events
  - apply_actions
  - jira_instances
  - work_items
  - work_item_transitions
  - work_item_slas
  - work_item_metrics_daily
  - pulse_configs
```

### 2. Spustenie servera

```bash
PYTHONPATH=/Users/hotovo/Projects/digital-spiral python3 -m uvicorn orchestrator.app:app --reload --port 7010
```

**Výstup:**
```
INFO:     Uvicorn running on http://127.0.0.1:7010 (Press CTRL+C to quit)
INFO:     Started server process
INFO:     Application startup complete.
```

### 3. Otvorenie dashboardu

Otvor v prehliadači:
```
http://127.0.0.1:7010/v1/pulse/
```

---

## 🔗 Pripojenie Jira inštancie

### Krok 1: Získaj Jira API token

1. Choď na: https://id.atlassian.com/manage-profile/security/api-tokens
2. Klikni na **"Create API token"**
3. Pomenuj token (napr. "Pulse Dashboard")
4. Skopíruj token (uloží sa len raz!)

### Krok 2: Pridaj Jira inštanciu cez UI

1. V dashboarde klikni na **"+ Add Jira Instance"**
2. Vyplň formulár:
   - **Display Name**: Názov pre tvoju Jiru (napr. "My Company Jira")
   - **Base URL**: `https://tvoja-domena.atlassian.net`
   - **Email**: Tvoj Jira email
   - **API Token**: Token z kroku 1
3. Klikni **"Add & Test"**

Dashboard automaticky:
- ✅ Otestuje pripojenie
- ✅ Spustí backfill (načíta posledných 90 dní histórie)
- ✅ Zobrazí metriky

---

## 📊 Čo uvidíš na dashboarde

### 5 Kľúčových Metrik

1. **Throughput** - Vytvorené / Uzavreté tickety
2. **Lead Time** - P50/P90 čas dokončenia (dni)
3. **SLA Risk** - Počet ticketov blízko porušenia SLA
4. **Work in Progress** - Rozpracované tickety (celkom / bez assignee / stuck)
5. **Quality** - Reopen rate (%)

### Tabuľka Projektov

- Zoznam všetkých projektov
- Created / Closed / WIP počty pre každý projekt

---

## 🔧 API Endpointy

### Jira Instance Management

```bash
# List instances
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/jira/instances

# Add instance
curl -X POST http://localhost:7010/v1/pulse/jira/instances \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -d '{
    "display_name": "My Jira",
    "base_url": "https://company.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "your-api-token"
  }'

# Test connection
curl -X POST http://localhost:7010/v1/pulse/jira/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://company.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "your-api-token"
  }'

# Backfill data
curl -X POST http://localhost:7010/v1/pulse/jira/backfill \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "your-instance-id",
    "days_back": 90,
    "max_issues": 1000
  }'
```

### Dashboard Data

```bash
# Get dashboard data
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/dashboard

# Get dashboard for specific project
curl -H "X-Tenant-Id: demo" "http://localhost:7010/v1/pulse/dashboard?project_key=SCRUM"

# Get dashboard for date range
curl -H "X-Tenant-Id: demo" "http://localhost:7010/v1/pulse/dashboard?since=2025-09-01"
```

### Configuration

```bash
# Get pulse config
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/config
```

---

## 📝 Príklad: Pripojenie tvojej Jiry

### Tvoje údaje (nahraď vlastnými):

```bash
BASE_URL="https://slavoseman.atlassian.net"
EMAIL="slavosmn@gmail.com"
API_TOKEN="tvoj-api-token-sem"
```

### Pridanie cez API:

```bash
curl -X POST http://localhost:7010/v1/pulse/jira/instances \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -d "{
    \"display_name\": \"Slavo's Jira\",
    \"base_url\": \"$BASE_URL\",
    \"email\": \"$EMAIL\",
    \"api_token\": \"$API_TOKEN\"
  }"
```

**Odpoveď:**
```json
{
  "success": true,
  "instance": {
    "id": "abc-123-def",
    "tenant_id": "demo",
    "base_url": "https://slavoseman.atlassian.net",
    "email": "slavosmn@gmail.com",
    "display_name": "Slavo's Jira",
    "active": true,
    "created_at": "2025-10-01T19:45:00Z"
  }
}
```

### Spustenie backfillu:

```bash
curl -X POST http://localhost:7010/v1/pulse/jira/backfill \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "abc-123-def",
    "days_back": 90,
    "max_issues": 1000
  }'
```

**Odpoveď:**
```json
{
  "success": true,
  "stats": {
    "instance_id": "abc-123-def",
    "instance_name": "Slavo's Jira",
    "start_date": "2025-07-03T00:00:00Z",
    "end_date": "2025-10-01T19:45:00Z",
    "issues_fetched": 234,
    "issues_created": 234,
    "issues_updated": 0,
    "errors": 0
  }
}
```

---

## 🎯 Čo ďalej?

### Hotové ✅
- [x] Dátový model
- [x] Jira Connector
- [x] Backfill service
- [x] Dashboard UI
- [x] REST API

### TODO 🚧
- [ ] Webhook processor (real-time updates)
- [ ] Denné agregácie (cron job)
- [ ] SLA tracking
- [ ] Reopen rate calculation
- [ ] 4-week trend comparison
- [ ] PDF/Email digest
- [ ] Slack integration

---

## 🐛 Troubleshooting

### Server sa nespustí

**Problém:** `ModuleNotFoundError`

**Riešenie:**
```bash
pip3 install rapidfuzz uvicorn fastapi pydantic sqlalchemy psycopg prometheus-client
```

### Databáza sa nevytvorí

**Problém:** `ARRAY type not supported`

**Riešenie:** Už opravené - používame JSON namiesto ARRAY pre SQLite kompatibilitu

### Jira connection test fails

**Problém:** `401 Unauthorized`

**Riešenie:**
1. Skontroluj, že API token je správny
2. Skontroluj, že email je správny
3. Skontroluj, že base URL je správne (bez `/` na konci)

---

## 📚 Ďalšie dokumentácie

- [Executive Work Pulse Overview](./EXECUTIVE_WORK_PULSE.md)
- [Data Model](./PULSE_DATA_MODEL.md)
- [API Reference](./PULSE_API.md)

---

## 🎉 Hotovo!

Teraz máš funkčný Executive Work Pulse dashboard pripojený na tvoju Jiru!

Dashboard sa automaticky aktualizuje pri každom refreshi. V budúcnosti pridáme:
- Real-time updates cez webhooks
- Automatické denné agregácie
- Email/Slack digesty
- PDF exporty

**Enjoy! 🚀**

