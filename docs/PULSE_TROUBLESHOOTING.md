# 🔧 Executive Work Pulse - Troubleshooting Guide

Riešenia bežných problémov pri používaní Executive Work Pulse dashboardu.

---

## 🚨 "No projects found" po pridaní Jira inštancie

### Príčina
Backfill proces ešte nedobehol alebo zlyhал.

### Riešenie

#### 1. Počkaj 30-60 sekúnd
Backfill beží na pozadí a môže trvať 30-60 sekúnd v závislosti od počtu ticketov.

#### 2. Skontroluj server logy
```bash
# V termináli kde beží server uvidíš:
🚀 Starting backfill for My Jira from 2025-07-03 to 2025-10-01
Progress: 10 issues fetched, 2 projects
Progress: 20 issues fetched, 3 projects
...
✅ Backfill complete: 234 issues fetched, 5 projects, 0 errors
```

#### 3. Manuálne spusti backfill
```bash
curl -X POST http://localhost:7010/v1/pulse/jira/backfill \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "TVOJ-INSTANCE-ID",
    "days_back": 90,
    "max_issues": 1000
  }'
```

#### 4. Skontroluj databázu
```bash
# Pripoj sa k SQLite databáze
sqlite3 artifacts/orchestrator.db

# Skontroluj work items
SELECT COUNT(*) FROM work_items;
SELECT project_key, COUNT(*) FROM work_items GROUP BY project_key;

# Skontroluj Jira instances
SELECT id, display_name, base_url, active FROM jira_instances;
```

#### 5. Refresh dashboard
Klikni na "🔄 Refresh" button v dashboarde.

---

## 🚫 "Jira instance already exists"

### Príčina
Pokúšaš sa pridať tú istú Jira inštanciu (rovnaký base_url + email) dvakrát.

### Riešenie

#### 1. Skontroluj existujúce inštancie
```bash
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/jira/instances
```

#### 2. Odstráň duplicitnú inštanciu
```bash
curl -X DELETE http://localhost:7010/v1/pulse/jira/instances/INSTANCE-ID
```

#### 3. Alebo použi inú kombináciu
- Použi iný email (ak máš viacero účtov)
- Použi iný display name (názov sa môže opakovať)

---

## 🔐 "401 Unauthorized" pri testovaní pripojenia

### Príčina
Nesprávne Jira credentials (email alebo API token).

### Riešenie

#### 1. Skontroluj email
- Musí byť email účtu, ktorý má prístup k Jira
- Musí byť presne ten istý ako v Jira profile

#### 2. Vygeneruj nový API token
1. Choď na: https://id.atlassian.com/manage-profile/security/api-tokens
2. Klikni "Create API token"
3. Pomenuj token: "Pulse Dashboard"
4. Skopíruj token (zobrazí sa len raz!)
5. Použi nový token v dashboarde

#### 3. Skontroluj base URL
- Musí byť: `https://tvoja-domena.atlassian.net`
- BEZ `/` na konci
- BEZ `/jira` alebo iných path segmentov

#### 4. Test connection cez API
```bash
curl -X POST http://localhost:7010/v1/pulse/jira/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://tvoja-domena.atlassian.net",
    "email": "tvoj-email@company.com",
    "api_token": "tvoj-api-token"
  }'
```

---

## 📊 Dashboard zobrazuje nulové metriky

### Príčina
Backfill ešte nedobehol alebo v Jira nie sú žiadne tickety v posledných 90 dňoch.

### Riešenie

#### 1. Skontroluj počet work items
```bash
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/dashboard | jq .
```

#### 2. Skontroluj databázu
```bash
sqlite3 artifacts/orchestrator.db "SELECT COUNT(*) FROM work_items;"
```

#### 3. Zmeň date range
```bash
# Backfill viac dní
curl -X POST http://localhost:7010/v1/pulse/jira/backfill \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "TVOJ-INSTANCE-ID",
    "days_back": 180,
    "max_issues": 2000
  }'
```

#### 4. Skontroluj Jira JQL
Otvor Jira a spusti JQL:
```
updated >= -90d ORDER BY updated ASC
```

Ak nevidíš žiadne tickety, znamená to, že v Jira naozaj nie sú žiadne tickety v posledných 90 dňoch.

---

## 🐌 Backfill trvá príliš dlho

### Príčina
Veľa ticketov v Jira (>1000) alebo pomalé API.

### Riešenie

#### 1. Zmeň max_issues
```bash
curl -X POST http://localhost:7010/v1/pulse/jira/backfill \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "TVOJ-INSTANCE-ID",
    "days_back": 30,
    "max_issues": 500
  }'
```

#### 2. Backfill po projektoch
```bash
# TODO: Implementovať project filter v backfill
```

#### 3. Sleduj progress v logoch
```bash
# Server logy ukazujú progress každých 10 ticketov
Progress: 10 issues fetched, 2 projects
Progress: 20 issues fetched, 3 projects
...
```

---

## 🔄 Server sa nespustí

### Príčina
Chýbajúce dependencies alebo port už používaný.

### Riešenie

#### 1. Nainštaluj dependencies
```bash
pip3 install rapidfuzz uvicorn fastapi pydantic sqlalchemy psycopg prometheus-client
```

#### 2. Skontroluj port
```bash
# Zisti, či port 7010 je voľný
lsof -i :7010

# Ak je obsadený, použi iný port
PYTHONPATH=/Users/hotovo/Projects/digital-spiral python3 -m uvicorn orchestrator.app:app --reload --port 7011
```

#### 3. Skontroluj PYTHONPATH
```bash
# Musí byť nastavený na root projektu
export PYTHONPATH=/Users/hotovo/Projects/digital-spiral
python3 -m uvicorn orchestrator.app:app --reload --port 7010
```

---

## 🗄️ Databáza sa nevytvorí

### Príčina
Chýbajúce permissions alebo nesprávny DATABASE_URL.

### Riešenie

#### 1. Skontroluj permissions
```bash
# Skontroluj, či môžeš zapisovať do artifacts/
ls -la artifacts/
mkdir -p artifacts
```

#### 2. Manuálne vytvor databázu
```bash
python3 scripts/init_pulse_db.py
```

#### 3. Skontroluj DATABASE_URL
```bash
# Default je SQLite v artifacts/
echo $DATABASE_URL

# Ak chceš PostgreSQL:
export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/dbname"
```

---

## 📱 Dashboard sa nenačíta v prehliadači

### Príčina
Server nebeží alebo nesprávna URL.

### Riešenie

#### 1. Skontroluj, či server beží
```bash
curl http://localhost:7010/health
```

#### 2. Skontroluj URL
- Správna URL: `http://127.0.0.1:7010/v1/pulse/`
- NIE: `http://localhost:7010/pulse/` (chýba `/v1/`)

#### 3. Skontroluj browser console
- Otvor Developer Tools (F12)
- Pozri Console tab
- Hľadaj chyby (červené)

#### 4. Skontroluj CORS
```bash
# Ak používaš iný port, môže byť problém s CORS
# TODO: Pridať CORS middleware
```

---

## 🔍 Debugging Tips

### 1. Zapni verbose logging
```bash
# V orchestrator/pulse_backfill.py zmeň:
logging.basicConfig(level=logging.DEBUG)
```

### 2. Skontroluj server logy
```bash
# Server logy ukazujú všetky requesty
INFO:     127.0.0.1:52345 - "GET /v1/pulse/dashboard HTTP/1.1" 200 OK
```

### 3. Použi curl na testovanie API
```bash
# Test connection
curl -X POST http://localhost:7010/v1/pulse/jira/test-connection \
  -H "Content-Type: application/json" \
  -d '{"base_url": "...", "email": "...", "api_token": "..."}'

# List instances
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/jira/instances

# Get dashboard
curl -H "X-Tenant-Id: demo" http://localhost:7010/v1/pulse/dashboard
```

### 4. Skontroluj databázu priamo
```bash
sqlite3 artifacts/orchestrator.db

# Užitočné queries:
SELECT * FROM jira_instances;
SELECT COUNT(*) FROM work_items;
SELECT project_key, COUNT(*) FROM work_items GROUP BY project_key;
SELECT * FROM work_items LIMIT 5;
```

---

## 📞 Ďalšia pomoc

Ak problém pretrváva:

1. **Skontroluj logy** - server logy obsahujú detailné error messages
2. **Skontroluj databázu** - SQLite databáza v `artifacts/orchestrator.db`
3. **Spusti test script** - `./scripts/test_pulse_flow.sh`
4. **Vytvor issue** - s logmi a error messages

---

## ✅ Checklist pre úspešné spustenie

- [ ] Server beží na `http://localhost:7010`
- [ ] Databáza vytvorená (`artifacts/orchestrator.db` existuje)
- [ ] Jira API token vygenerovaný
- [ ] Jira inštancia pridaná cez UI
- [ ] Backfill dokončený (vidíš v logoch "✅ Backfill complete")
- [ ] Dashboard zobrazuje projekty
- [ ] Metriky nie sú nulové

Ak všetko funguje, uvidíš:
- ✅ Zoznam Jira inštancií
- ✅ 5 metrik s číslami
- ✅ Tabuľku projektov s dátami

**Enjoy! 🚀**

