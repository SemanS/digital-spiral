# 🤖 AI Assistant - Quick Start Guide

Tento návod ti ukáže, ako rýchlo spustiť AI Assistant UI na `http://127.0.0.1:7010/v1/ai-assistant/`

---

## ✅ Predpoklady

1. **Python 3.10+** nainštalovaný
2. **Docker** nainštalovaný a spustený
3. **AI API Key** - jeden z nasledujúcich:
   - Google AI API Key (odporúčané, zadarmo): https://aistudio.google.com/app/apikey
   - OpenAI API Key: https://platform.openai.com/api-keys

---

## 🚀 Rýchle Spustenie (3 kroky)

### 1. Nastav AI API Key

Otvor `.env` súbor a nastav jeden z týchto API keys:

```bash
# Pre Google AI (Gemini) - ODPORÚČANÉ
GOOGLE_AI_API_KEY=your-google-ai-api-key-here

# ALEBO pre OpenAI
# OPENAI_API_KEY=sk-your-openai-api-key
```

### 2. Spusti pomocný skript

```bash
./scripts/run_ai_assistant.sh
```

Skript automaticky:
- ✅ Skontroluje AI API key
- ✅ Spustí PostgreSQL (ak nebeží)
- ✅ Nastaví environment variables
- ✅ Spustí orchestrator server

### 3. Otvor AI Assistant

Otvor v prehliadači: **http://127.0.0.1:7010/v1/ai-assistant/**

---

## 📱 Čo môžeš robiť?

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

### Autocomplete

- **@** - Napíš `@` a začni písať meno používateľa
- **/** - Napíš `/` a začni písať kľúč alebo názov issue

---

## 🔧 Manuálne Spustenie (ak nechceš použiť skript)

### 1. Spusti PostgreSQL

```bash
docker compose -f docker/docker-compose.dev.yml up -d postgres
```

### 2. Nastav environment variables

```bash
# Load .env file
export $(grep -v '^#' .env | xargs)

# Set orchestrator-specific variables
export DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator"
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### 3. Spusti orchestrator

```bash
cd orchestrator
PYTHONUNBUFFERED=1 python3 -m uvicorn app:app --host 0.0.0.0 --port 7010 --reload
```

### 4. Otvor AI Assistant

Otvor v prehliadači: http://127.0.0.1:7010/v1/ai-assistant/

---

## 🎯 Dostupné Endpointy

Po spustení máš k dispozícii:

- **AI Assistant UI**: http://127.0.0.1:7010/v1/ai-assistant/
- **Pulse Dashboard**: http://127.0.0.1:7010/v1/pulse/
- **Health Check**: http://127.0.0.1:7010/health
- **API Docs**: http://127.0.0.1:7010/docs

---

## 🔍 Overenie Konfigurácie

### Skontroluj AI Provider

```bash
# Skontroluj ktorý AI provider je nakonfigurovaný
grep -E "GOOGLE_AI_API_KEY|OPENAI_API_KEY" .env
```

### Skontroluj Database

```bash
# Skontroluj či PostgreSQL beží
docker compose -f docker/docker-compose.dev.yml ps postgres
```

### Skontroluj Orchestrator

```bash
# Skontroluj health endpoint
curl http://127.0.0.1:7010/health
```

---

## 🐛 Riešenie Problémov

### ❌ "No AI provider configured"

**Problém**: Nie je nastavený AI API key

**Riešenie**:
```bash
# Nastav v .env súbore
GOOGLE_AI_API_KEY=your-key-here
```

### ❌ "Connection refused" na porte 7010

**Problém**: Orchestrator nebeží

**Riešenie**:
```bash
# Spusti orchestrator
./scripts/run_ai_assistant.sh
```

### ❌ "Database connection failed"

**Problém**: PostgreSQL nebeží

**Riešenie**:
```bash
# Spusti PostgreSQL
docker compose -f docker/docker-compose.dev.yml up -d postgres

# Počkaj 5 sekúnd
sleep 5

# Skús znova
./scripts/run_ai_assistant.sh
```

### ❌ "No Jira instance configured"

**Problém**: Nie je nakonfigurovaná Jira inštancia

**Riešenie**:
1. Otvor Pulse Dashboard: http://127.0.0.1:7010/v1/pulse/
2. Klikni na "Add Jira Instance"
3. Zadaj Jira credentials

Alebo nastav v `.env`:
```bash
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

### ❌ Port 7010 je už obsadený

**Problém**: Iná aplikácia používa port 7010

**Riešenie**:
```bash
# Zmeň port v príkaze
cd orchestrator
uvicorn app:app --host 0.0.0.0 --port 7011 --reload

# Potom otvor: http://127.0.0.1:7011/v1/ai-assistant/
```

---

## 📚 Ďalšie Zdroje

- **Kompletná dokumentácia**: [docs/AI_ASSISTANT_README.md](./AI_ASSISTANT_README.md)
- **API príklady**: [docs/API_EXAMPLES.md](./API_EXAMPLES.md)
- **Pulse Dashboard**: [docs/PULSE_QUICKSTART.md](./PULSE_QUICKSTART.md)

---

## 🎉 Hotovo!

Teraz máš funkčný AI Assistant, ktorý ti pomôže s Jira úlohami! 🚀

**Užívaj si prácu s AI asistentom!** 🤖✨

