# 🚀 AI Support Copilot - Quick Start Guide

**Všetko je pripravené! Tento návod ti ukáže, ako používať AI Support Copilot s tvojou reálnou Jira Cloud inštanciou.**

---

## ✅ **Čo už beží:**

```
✅ Jira Proxy Server:  http://localhost:8080
✅ Demo UI:            demo-ui/real-jira.html (otvorené v prehliadači)
✅ Jira Cloud:         https://insight-bridge.atlassian.net
✅ Projekt SCRUM:      15 support ticketov načítaných
```

---

## 🎯 **Ako používať Demo UI:**

### **1. Otvor Demo UI** (ak nie je otvorené)

```bash
open demo-ui/real-jira.html
```

### **2. Zadaj credentials:**

V Demo UI zadaj:

- **Proxy URL:** `http://localhost:8080/proxy`
- **Jira URL:** `https://insight-bridge.atlassian.net`
- **API Token:** `YOUR_API_TOKEN`
- **Email:** `slavosmn@gmail.com`

### **3. Klikni "Load Issues"**

Uvidíš všetky tickety z tvojej Jira!

---

## 📊 **Čo vidíš v Demo UI:**

- **15 support ticketov** z projektu SCRUM
- **Summary, Status, Priority, Assignee** pre každý ticket
- **Kliknutím na ticket** sa otvorí v Jira Cloud

---

## 🔧 **Príkazy pre vývoj:**

### **Načítať viac ticketov do Jira:**

```bash
python scripts/load_to_real_jira.py \
  --base-url https://insight-bridge.atlassian.net \
  --email slavosmn@gmail.com \
  --token "YOUR_API_TOKEN" \
  --seed artifacts/ai_support_copilot_seed.json \
  --project SCRUM \
  --limit 20
```

### **Reštartovať Proxy Server:**

```bash
# Zastaviť
pkill -f jira_proxy.py

# Spustiť znova
python scripts/jira_proxy.py
```

### **Otestovať API priamo:**

```bash
curl -s "http://localhost:8080/proxy?jira_url=https://insight-bridge.atlassian.net&path=/rest/api/3/search/jql&jql=project=SCRUM&maxResults=5&fields=summary,status,priority" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "X-Jira-Email: slavosmn@gmail.com"
```

---

## 🎓 **Typický development workflow:**

```bash
# 1. Ráno - Uisti sa, že proxy beží
python scripts/jira_proxy.py

# 2. Otvor Demo UI
open demo-ui/real-jira.html

# 3. Načítaj tickety v UI
# - Zadaj credentials
# - Klikni "Load Issues"

# 4. Vyvíjaj features
# - Upravuj orchestrator/app.py
# - Testuj v Demo UI

# 5. Načítaj viac dummy dát podľa potreby
python scripts/load_to_real_jira.py --limit 30
```

---

## 📚 **Štruktúra projektu:**

```
digital-spiral/
├── demo-ui/
│   └── real-jira.html          # ✅ Demo UI pre reálnu Jira
├── scripts/
│   ├── jira_proxy.py           # ✅ CORS proxy server
│   ├── load_to_real_jira.py    # ✅ Načíta data do Jira
│   └── generate_dummy_jira.py  # Generuje seed data
├── clients/python/
│   └── jira_cloud_adapter.py   # ✅ Jira Cloud API adapter
├── orchestrator/               # AI orchestrator (ďalší krok)
├── mcp_jira/                   # MCP bridge (ďalší krok)
└── artifacts/
    └── ai_support_copilot_seed.json  # 240 dummy ticketov
```

---

## 🚀 **Ďalšie kroky:**

### **1. Spustiť Orchestrator (AI features)**

```bash
# Spusti Postgres
docker compose up -d postgres

# Nastav environment
export JIRA_BASE_URL="https://insight-bridge.atlassian.net"
export JIRA_TOKEN="YOUR_API_TOKEN"
export DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator"
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Spusti orchestrator
python -m uvicorn orchestrator.app:app --reload --port 7010
```

### **2. Integrovať AI analýzu do Demo UI**

- Pridať tlačidlo "Analyze with AI"
- Volať orchestrator API
- Zobraziť AI návrhy odpovedí

### **3. Pridať viac features:**

- **Automatická kategorizácia** ticketov
- **Sentiment analysis** komentárov
- **Návrhy odpovedí** pre support team
- **Performance metrics** a dashboardy

---

## 💡 **Tipy:**

- **API Token** je uložený v localStorage prehliadača
- **Proxy server** musí bežať, aby Demo UI fungovalo
- **Seed data** obsahujú 240 realistic ticketov - môžeš načítať viac
- **Jira Cloud API** používa nový `/rest/api/3/search/jql` endpoint

---

## 🐛 **Troubleshooting:**

### **Problém: "Failed to fetch" v Demo UI**

**Riešenie:**
```bash
# Skontroluj, či proxy beží
curl http://localhost:8080/health

# Ak nebeží, spusti ho
python scripts/jira_proxy.py
```

### **Problém: "401 Unauthorized"**

**Riešenie:**
- Skontroluj, či API token je správny
- Vytvor nový token na: https://id.atlassian.com/manage-profile/security/api-tokens

### **Problém: Žiadne tickety v Jira**

**Riešenie:**
```bash
# Načítaj dummy data
python scripts/load_to_real_jira.py \
  --base-url https://insight-bridge.atlassian.net \
  --email slavosmn@gmail.com \
  --token "YOUR_TOKEN" \
  --project SCRUM \
  --limit 15
```

---

## 📖 **Ďalšia dokumentácia:**

- **[REAL_JIRA_SETUP.md](REAL_JIRA_SETUP.md)** - Kompletný setup guide
- **[AI_SUPPORT_COPILOT_PRODUCT.md](AI_SUPPORT_COPILOT_PRODUCT.md)** - Product vision
- **[AI_SUPPORT_COPILOT_SETUP.md](AI_SUPPORT_COPILOT_SETUP.md)** - Development setup

---

**Máš otázky? Potrebuješ pomoc?** Napíš mi! 🚀
