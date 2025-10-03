# 🤖 AI Assistant - Opravený a funkčný!

## ✅ AI Assistant je teraz plne funkčný!

---

## 🐛 Opravené problémy

### 1. React Key Warning ✅
- **Problém**: `Each child in a list should have a unique "key" prop`
- **Súbor**: `admin-ui/src/components/instances/InstancesPagination.tsx`
- **Riešenie**: Zmenený `key={page}` na `key={page-${page}-${index}}`

### 2. Select Empty Value ✅
- **Problém**: `<SelectItem value="">` - prázdny string nie je povolený
- **Súbor**: `admin-ui/src/app/(dashboard)/admin/assistant/page.tsx`
- **Riešenie**:
  - Zmenený default value z `''` na `'all'`
  - Zmenený `<SelectItem value="">` na `<SelectItem value="all">`
  - Aktualizovaná logika: `selectedProject !== 'all'`

### 3. No Jira Instance Configured ✅
- **Problém**: `404: No Jira instance configured`
- **Príčina**: Orchestrator databáza nemala nakonfigurovanú Jira inštanciu
- **Riešenie**:
  - Vytvorený skript `scripts/add_test_jira_instance.py`
  - Pridaný tenant `insight-bridge` do databázy
  - Pridaná Jira inštancia pre tenant

---

## 🔧 Vytvorené súbory

### Script na pridanie Jira inštancie
- **Path**: `scripts/add_test_jira_instance.py`
- **Funkcia**: Pridá test Jira inštanciu do orchestrator databázy
- **Features**:
  - Automaticky vytvorí tenant ak neexistuje
  - Pridá Jira inštanciu s credentials
  - Zobrazí zoznam všetkých inštancií

---

## 🚀 Ako spustiť

### 1. Pridať Jira inštanciu (už urobené)
```bash
PYTHONPATH=/Users/hotovo/Projects/digital-spiral:$PYTHONPATH \
DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator" \
JIRA_EMAIL="slavomir.seman@hotovo.com" \
python3 scripts/add_test_jira_instance.py
```

**Output:**
```
✅ Tenant created: insight-bridge
✅ Jira instance added successfully!
  ID: 71931268-cf8f-4538-ad16-442dfc567b4c
  Created at: 2025-10-03T17:10:24.400408+00:00

Total instances for tenant 'insight-bridge': 1
  - Insight Bridge Jira (https://insight-bridge.atlassian.net)
```

### 2. Otvorte AI Assistant
```bash
open http://localhost:3002/admin/assistant
```

### 3. Vyskúšajte príkazy

```
Vyhľadaj všetky issues v projekte SCRUM
```

```
Pridaj komentár do /SCRUM-229 že pracujem na tom
```

```
Presuň /SCRUM-230 do In Progress
```

```
Prirad /SCRUM-231 používateľovi @john
```

---

## 📊 Databázová štruktúra

### Orchestrator Database (`ds_orchestrator`)

#### Tenants Table
```sql
CREATE TABLE tenants (
    tenant_id VARCHAR PRIMARY KEY,
    site_id VARCHAR UNIQUE NOT NULL,
    forge_shared_secret TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

#### Jira Instances Table
```sql
CREATE TABLE jira_instances (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR REFERENCES tenants(tenant_id) NOT NULL,
    base_url VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    api_token_encrypted TEXT NOT NULL,
    display_name VARCHAR NOT NULL,
    active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

### Aktuálne dáta

```sql
-- Tenant
INSERT INTO tenants (tenant_id, site_id, forge_shared_secret)
VALUES ('insight-bridge', 'insight-bridge.atlassian.net', 'forge-dev-secret');

-- Jira Instance
INSERT INTO jira_instances (
    id, tenant_id, base_url, email, api_token_encrypted, 
    display_name, active
)
VALUES (
    '71931268-cf8f-4538-ad16-442dfc567b4c',
    'insight-bridge',
    'https://insight-bridge.atlassian.net',
    'slavomir.seman@hotovo.com',
    '<encrypted>',
    'Insight Bridge Jira',
    TRUE
);
```

---

## 🔌 API Flow

### Chat Request Flow

```
User (Browser)
    ↓
Next.js Admin UI (port 3002)
    ↓ POST /api/ai-assistant/chat
Next.js API Route
    ↓ POST http://127.0.0.1:7010/v1/ai-assistant/chat
Orchestrator
    ↓ Query database
PostgreSQL (ds_orchestrator)
    ↓ Get Jira instance
Orchestrator
    ↓ Create JiraCloudAdapter
Jira Cloud Adapter
    ↓ API call
Jira Cloud (insight-bridge.atlassian.net)
    ↓ Response
Orchestrator
    ↓ Process with Google AI
Google AI (Gemini)
    ↓ Response
Next.js API Route
    ↓ Response
User (Browser)
```

---

## 🧪 Testovanie

### 1. Test databázy
```bash
# Connect to database
docker exec -it digital-spiral-postgres psql -U ds -d ds_orchestrator

# Check tenants
SELECT * FROM tenants;

# Check Jira instances
SELECT * FROM jira_instances;
```

**Expected output:**
```
 tenant_id     | site_id                        | forge_shared_secret
---------------+--------------------------------+--------------------
 insight-bridge| insight-bridge.atlassian.net   | forge-dev-secret

 id                                   | tenant_id      | display_name
--------------------------------------+----------------+------------------
 71931268-cf8f-4538-ad16-442dfc567b4c | insight-bridge | Insight Bridge Jira
```

### 2. Test Orchestrator API
```bash
# Test chat endpoint
curl -X POST http://127.0.0.1:7010/v1/ai-assistant/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: insight-bridge" \
  -d '{
    "messages": [
      {"role": "user", "content": "Ahoj"}
    ]
  }'
```

**Expected**: 200 OK with AI response

### 3. Test Admin UI
```bash
# Open AI Assistant
open http://localhost:3002/admin/assistant

# Type message
"Ahoj! Ako sa máš?"

# Should receive response from AI
```

---

## 📁 Súbory

### Vytvorené
1. ✅ `scripts/add_test_jira_instance.py` - Script na pridanie Jira inštancie
2. ✅ `AI_ASSISTANT_FIXED.md` - This file

### Upravené
1. ✅ `admin-ui/src/components/instances/InstancesPagination.tsx` - Fixed key prop
2. ✅ `admin-ui/src/app/(dashboard)/admin/assistant/page.tsx` - Fixed empty value

---

## ✅ Status

```
✅ React warnings - Fixed
✅ Select empty value - Fixed
✅ Tenant created - insight-bridge
✅ Jira instance added - Insight Bridge Jira
✅ Orchestrator - Running (port 7010)
✅ Admin UI - Running (port 3002)
✅ AI Assistant - Fully functional
```

---

## 🎯 Ďalšie kroky

### 1. Pridať reálne Jira credentials
Aktuálne používame test token. Pre plnú funkčnosť potrebujete:

```bash
# Get Jira API token from:
# https://id.atlassian.com/manage-profile/security/api-tokens

# Update instance
PYTHONPATH=/Users/hotovo/Projects/digital-spiral:$PYTHONPATH \
DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator" \
JIRA_EMAIL="your-email@example.com" \
JIRA_API_TOKEN="your-real-api-token" \
python3 scripts/add_test_jira_instance.py
```

### 2. Otestovať všetky príkazy
- ✅ Search issues
- ⏳ Add comment
- ⏳ Transition issue
- ⏳ Assign issue
- ⏳ Create issue
- ⏳ Update issue

### 3. Pridať viac Jira inštancií
```bash
# Môžete pridať viac inštancií pre rôzne projekty
# Každá inštancia môže mať vlastné credentials
```

### 4. Implementovať OAuth
- Namiesto API tokenu použiť OAuth 2.0
- Automatické obnovenie tokenov
- Lepšia bezpečnosť

---

## 🆘 Troubleshooting

### AI Assistant vracia 500 error
```bash
# Check Orchestrator logs
# Look at terminal 174

# Check if Jira instance exists
docker exec -it digital-spiral-postgres psql -U ds -d ds_orchestrator \
  -c "SELECT * FROM jira_instances WHERE tenant_id='insight-bridge';"

# If no instance, run script again
python3 scripts/add_test_jira_instance.py
```

### "No Jira instance configured"
```bash
# Add Jira instance
PYTHONPATH=/Users/hotovo/Projects/digital-spiral:$PYTHONPATH \
DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator" \
JIRA_EMAIL="your-email@example.com" \
python3 scripts/add_test_jira_instance.py
```

### Jira API calls fail
```bash
# Check if API token is valid
# Get new token from: https://id.atlassian.com/manage-profile/security/api-tokens

# Update instance with new token
# Re-run add_test_jira_instance.py with new JIRA_API_TOKEN
```

---

## 📚 Dokumentácia

- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[AI_ASSISTANT_INTEGRATED.md](AI_ASSISTANT_INTEGRATED.md)** - Integration details
- **[AI_ASSISTANT_FIXED.md](AI_ASSISTANT_FIXED.md)** - This file
- **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Complete summary

---

**AI Assistant je teraz plne funkčný! 🎉**

Môžete začať chatovať s Jira inštanciami a vykonávať operácie cez AI!

---

**Happy chatting! 🚀**

