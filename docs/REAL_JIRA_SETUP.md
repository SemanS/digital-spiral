# 🚀 AI Support Copilot - Real Jira Setup Guide

Tento návod ti ukáže, ako pripojiť AI Support Copilot k tvojej reálnej Jira Cloud inštancii (`insight-bridge.atlassian.net`).

## 📋 Predpoklady

- ✅ Jira Cloud účet: `slavosmn@gmail.com`
- ✅ Jira inštancia: `https://insight-bridge.atlassian.net`
- ✅ Admin prístup k Jira (pre vytvorenie projektov)

---

## 🎯 Fáza 1: Rýchly štart s API Token (5 minút)

### Krok 1: Vytvor API Token

1. **Otvor v prehliadači:**
   ```
   https://id.atlassian.com/manage-profile/security/api-tokens
   ```

2. **Klikni "Create API token"**

3. **Pomenuj ho:** `Digital Spiral Dev`

4. **Skopíruj token** (zobrazí sa len raz!)

5. **Ulož token do `.env` súboru:**
   ```bash
   # Pridaj do .env
   JIRA_API_TOKEN="tvoj_token_tu"
   ```

---

### Krok 2: Načítaj dummy data do Jira

```bash
# 1. Vygeneruj seed data (ak ešte neexistujú)
python scripts/generate_dummy_jira.py \
  --config scripts/seed_profiles/ai_support_copilot.json \
  --out artifacts/ai_support_copilot_seed.json

# 2. Načítaj prvých 10 ticketov do tvojej Jira
python scripts/load_to_real_jira.py \
  --base-url https://insight-bridge.atlassian.net \
  --token "TVOJ_API_TOKEN" \
  --seed artifacts/ai_support_copilot_seed.json \
  --limit 10
```

**Poznámka:** Začíname s 10 ticketmi, aby sme nepreťažili tvoju Jira. Neskôr môžeš zvýšiť `--limit`.

---

### Krok 3: Otvor Demo UI

```bash
# Otvor v prehliadači
open demo-ui/real-jira.html
```

**V UI:**
1. Zadaj svoj **API token**
2. Klikni **"Load Issues"**
3. Uvidíš tickety z tvojej Jira!

---

### Krok 4: Spusti Orchestrator (voliteľné)

```bash
# 1. Uisti sa, že Postgres beží
docker compose up -d postgres

# 2. Spusti orchestrator
export JIRA_BASE_URL="https://insight-bridge.atlassian.net"
export JIRA_TOKEN="TVOJ_API_TOKEN"
export DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator"
export FORGE_SHARED_SECRET="forge-dev-secret"
export DEFAULT_TENANT_ID="insight-bridge"

python -m uvicorn orchestrator.app:app --reload --port 7010
```

**Otestuj orchestrator:**
```bash
# Získaj AI analýzu ticketu
curl -X GET "http://localhost:7010/v1/jira/ingest?issueKey=SUP1-1" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: insight-bridge"
```

---

## 🎯 Fáza 2: OAuth 2.0 Setup (pre MCP)

Ak chceš použiť MCP (Model Context Protocol) s AI agentmi, potrebuješ OAuth 2.0.

### Krok 1: Overenie OAuth credentials

Už máš nastavené v `.env`:
```bash
ATLASSIAN_CLIENT_ID="<client_id>"
ATLASSIAN_CLIENT_SECRET="<client_secret>"
ATLASSIAN_REDIRECT_URI="http://127.0.0.1:8055/oauth/callback"
```

### Krok 2: Spusti MCP Bridge

```bash
export ATLASSIAN_CLIENT_ID="<client_id>"
export ATLASSIAN_CLIENT_SECRET="<client_secret>"
export ATLASSIAN_REDIRECT_URI="http://127.0.0.1:8055/oauth/callback"
export ATLASSIAN_SCOPES="offline_access read:jira-user read:jira-work write:jira-work manage:jira-project"

python -m mcp_jira.http_server --port 8055
```

### Krok 3: Autorizuj v prehliadači

Server vypíše URL, napríklad:
```
=== Atlassian OAuth 2.0 ===
Open the following URL in your browser and authorize access:
https://auth.atlassian.com/authorize?...
```

1. **Otvor URL v prehliadači**
2. **Prihlás sa** ako `slavosmn@gmail.com`
3. **Autorizuj prístup** pre aplikáciu
4. **Presmeruje ťa** na `http://127.0.0.1:8055/oauth/callback`
5. **MCP Bridge** automaticky získa tokeny

---

## 📊 Čo teraz máš k dispozícii

### 1. **Demo UI** (`demo-ui/real-jira.html`)
- ✅ Zobrazuje tickety z tvojej Jira
- ✅ Filtre a vyhľadávanie
- ✅ Kliknutím otvoríš ticket v Jira

### 2. **Orchestrator API** (`http://localhost:7010`)
- ✅ AI analýza ticketov
- ✅ Intent classification
- ✅ PII detection
- ✅ Automated responses

### 3. **MCP Bridge** (`http://localhost:8055`)
- ✅ MCP tools pre AI agentov
- ✅ OAuth 2.0 autentifikácia
- ✅ Automatické refresh tokeny

---

## 🔧 Vývoj AI Support Copilot

### Typický workflow:

```bash
# 1. Spusti všetky služby
docker compose up -d postgres
python -m uvicorn orchestrator.app:app --reload --port 7010

# 2. Otvor demo UI
open demo-ui/real-jira.html

# 3. Testuj API
curl -X GET "http://localhost:7010/v1/jira/ingest?issueKey=SUP1-1" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: insight-bridge"

# 4. Sleduj logy
tail -f orchestrator/logs/*.log
```

### Pridanie nových features:

1. **Upraviť orchestrator** (`orchestrator/app.py`)
2. **Pridať AI logiku** (`orchestrator/analysis.py`)
3. **Aktualizovať UI** (`demo-ui/real-jira.html`)
4. **Otestovať** na reálnych ticketoch

---

## 🐛 Troubleshooting

### Problém: "401 Unauthorized"
**Riešenie:** Skontroluj API token:
```bash
curl -u "slavosmn@gmail.com:TVOJ_TOKEN" \
  https://insight-bridge.atlassian.net/rest/api/3/myself
```

### Problém: "403 Forbidden" pri OAuth
**Riešenie:** Skontroluj, či máš správne scopes v Atlassian Console:
- `offline_access`
- `read:jira-user`
- `read:jira-work`
- `write:jira-work`
- `manage:jira-project`

### Problém: Postgres connection error
**Riešenie:**
```bash
# Reštartuj Postgres
docker compose down postgres
docker compose up -d postgres

# Počkaj 10 sekúnd
sleep 10

# Spusti orchestrator znova
```

### Problém: "Project not found"
**Riešenie:** Vytvor projekt manuálne v Jira:
1. Choď na https://insight-bridge.atlassian.net/jira/projects
2. Klikni "Create project"
3. Vyber "Service management"
4. Pomenuj ho "SUP1" alebo "Support 1"

---

## 📚 Ďalšie kroky

1. **Forge App** - Nainštaluj Forge aplikáciu do Jira UI
   ```bash
   cd forge-app
   forge login
   forge deploy
   forge install --site insight-bridge.atlassian.net
   ```

2. **AI Models** - Integruj OpenAI/Anthropic pre lepšiu analýzu
   ```bash
   export OPENAI_API_KEY="sk-..."
   # Upraviť orchestrator/analysis.py
   ```

3. **Webhooks** - Automatická reakcia na nové tickety
   ```bash
   # Registruj webhook v Jira
   curl -X POST https://insight-bridge.atlassian.net/rest/api/3/webhook \
     -H "Authorization: Basic ..." \
     -d '{"url": "http://your-server.com/webhook", ...}'
   ```

---

## 💡 Tipy pre vývoj

- **Používaj `--limit 10`** pri načítavaní dát, aby si nepreťažil Jira
- **Testuj na staging projekte** pred produkciou
- **Sleduj rate limity** Jira API (max 10 req/s)
- **Používaj OAuth** pre produkciu, API token len pre dev
- **Backup dát** pred veľkými zmenami

---

**Máš otázky? Potrebuješ pomoc?** Napíš mi! 🚀
