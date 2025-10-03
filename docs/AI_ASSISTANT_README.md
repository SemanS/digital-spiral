# AI Assistant - Jira Helper

Inteligentný AI asistent s Google AI (Gemini) integráciou, hybridný systém MCP + SQL pre Jira akcie.

## 🎯 Funkcie

### 1. **Chat Interface**
- Konverzácia s AI asistentom
- Automatické vykonávanie Jira akcií cez MCP
- Kontextové odpovede založené na aktuálnom projekte/issue

### 2. **Autocomplete**
- **@ pre používateľov** - Napíš `@` a začni písať meno používateľa
- **/ pre issues** - Napíš `/` a začni písať kľúč alebo názov issue

### 3. **Hybridný systém: MCP + SQL**

AI automaticky rozhoduje ktorý nástroj použiť:

**SQL nástroje (RÝCHLE čítanie z databázy):**
- ⚡ **sql_get_issue_history** - História zmien issue (10-50ms)
- ⚡ **sql_get_project_metrics** - Metriky projektu (50-100ms)
- ⚡ **sql_get_stuck_issues** - Stuck issues (20-50ms)
- ⚡ **sql_get_user_workload** - Workload používateľa (20-50ms)
- ⚡ **sql_search_issues_by_text** - Full-text search (30ms)

**MCP nástroje (zápis cez Jira API):**

*Základné operácie:*
- ✅ **add_comment** - Pridať komentár do issue
- ✅ **get_comments** - Získať všetky komentáre z issue
- ✅ **transition_issue** - Zmeniť status issue
- ✅ **search_issues** - Vyhľadať issues pomocou JQL
- ✅ **get_issue** - Získať detaily o issue
- ✅ **assign_issue** - Priradiť issue používateľovi

*Pokročilé operácie:*
- ✅ **add_watcher** - Pridať sledujúceho k issue
- ✅ **get_watchers** - Získať všetkých sledujúcich issue
- ✅ **link_issues** - Linkovať dve issues
- ✅ **get_issue_links** - Získať všetky linky issue
- ✅ **search_users** - Vyhľadať používateľov
- ✅ **update_issue_field** - Aktualizovať pole issue

**Výhody hybridného systému:**
- 🚀 **10-100x rýchlejšie** čítanie dát z databázy
- 🤖 **AI automaticky rozhodne** ktorý nástroj použiť
- 📊 **Predpripravené SQL queries** - optimalizované
- ⚡ **Žiadne rate limity** - databáza je lokálna

## 🚀 Spustenie

### 1. Nastav AI API key

**Google AI (Gemini) - Odporúčané:**
```bash
export GOOGLE_AI_API_KEY="AIzaSy..."
```

**OpenAI (alternatíva):**
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_ORGANIZATION="org-..."
```

### 2. Spusti server

```bash
cd /Users/hotovo/Projects/digital-spiral
PYTHONUNBUFFERED=1 python3 -m uvicorn orchestrator.app:app --port 7010 --reload
```

### 3. Otvor AI Assistant

Otvor v prehliadači: http://127.0.0.1:7010/v1/ai-assistant/

## 📝 Príklady použitia

### Pridať komentár
```
Pridaj komentár do /SCRUM-229 že pracujem na tom
```

AI asistent:
1. Rozpozná že chceš pridať komentár
2. Zavolá MCP action `add_comment`
3. Pridá komentár do issue SCRUM-229
4. Potvrdí že akcia bola úspešná

### Zmeniť status
```
Presuň /SCRUM-230 do In Progress
```

AI asistent:
1. Rozpozná že chceš zmeniť status
2. Zavolá MCP action `transition_issue`
3. Zmení status issue SCRUM-230 na "In Progress"
4. Potvrdí že akcia bola úspešná

### Vyhľadať issues
```
Nájdi všetky open issues v projekte SCRUM
```

AI asistent:
1. Rozpozná že chceš vyhľadať issues
2. Zavolá MCP action `search_issues` s JQL: `project = SCRUM AND status = Open`
3. Zobrazí zoznam nájdených issues

### Priradiť issue
```
Prirad /SCRUM-231 používateľovi @john
```

AI asistent:
1. Rozpozná že chceš priradiť issue
2. Zavolá MCP action `assign_issue`
3. Priradí issue SCRUM-231 používateľovi john
4. Potvrdí že akcia bola úspešná

## 🔧 Technické detaily

### AI Providers

Systém podporuje viacero AI providerov:

1. **Google AI (Gemini)** - Primárny provider
   - Model: `gemini-2.5-flash`
   - Rýchly, lacný, výkonný
   - Function calling support

2. **OpenAI** - Alternatívny provider
   - Model: `gpt-4-turbo-preview`
   - Drahší, ale veľmi kvalitný
   - Function calling support

**Automatický výber:**
- Ak je nastavený `GOOGLE_AI_API_KEY` → použije Google AI
- Ak je nastavený `OPENAI_API_KEY` → použije OpenAI
- Ak nie je nastavený žiadny → error

### Backend API

**Endpointy:**
- `GET /v1/ai-assistant/` - HTML stránka s chat interface
- `POST /v1/ai-assistant/chat` - Chat s AI asistentom
- `POST /v1/ai-assistant/autocomplete` - Autocomplete pre @ a /
- `GET /v1/ai-assistant/context/{issue_key}` - Kontext o issue

**Request format (chat):**
```json
{
  "messages": [
    {"role": "user", "content": "Pridaj komentár do SCRUM-229"}
  ],
  "project_key": "SCRUM",
  "issue_key": null
}
```

**Response format:**
```json
{
  "message": "Pridal som komentár do issue SCRUM-229.",
  "tool_calls": [
    {
      "tool_call_id": "call_123",
      "function_name": "add_comment",
      "result": {
        "success": true,
        "result": {...}
      }
    }
  ]
}
```

### Frontend

**Autocomplete:**
- Detekuje `@` a `/` v texte
- Zobrazuje dropdown s návrhmi
- Podporuje navigáciu šípkami (↑↓)
- Výber pomocou Enter alebo Tab

**Chat:**
- Real-time konverzácia s AI
- Zobrazenie tool calls (vykonané akcie)
- Loading indikátor počas spracovania
- Automatické scrollovanie na najnovšiu správu

### MCP Integration

AI asistent používa OpenAI Function Calling pre vykonávanie akcií:

1. **User prompt** → OpenAI GPT-4
2. **GPT-4 rozhodne** ktorú funkciu zavolať
3. **MCP executor** vykoná akciu cez Jira adapter
4. **Výsledok** sa vráti do GPT-4
5. **GPT-4 vygeneruje** finálnu odpoveď pre používateľa

## 🎨 UI Features

- **Gradient design** - Moderný fialový gradient
- **Responsive** - Funguje na desktop aj mobile
- **Dark mode ready** - Pripravené na dark mode
- **Smooth animations** - Plynulé animácie a prechody
- **Keyboard shortcuts** - Enter pre odoslanie, Esc pre zatvorenie autocomplete

## 🔐 Bezpečnosť

- API key sa ukladá len v environment variables
- Tenant isolation - každý tenant má svoje Jira inštancie
- Validácia všetkých vstupov
- Error handling pre všetky MCP akcie

## 📊 Monitoring

Server loguje všetky MCP akcie:
```
INFO: Executing MCP action: add_comment with params: {'issue_key': 'SCRUM-229', 'comment': '...'}
```

## 🐛 Troubleshooting

### AI API key not configured
```
Error: No AI provider configured. Set GOOGLE_AI_API_KEY or OPENAI_API_KEY
```
**Riešenie:** Nastav `GOOGLE_AI_API_KEY` alebo `OPENAI_API_KEY` environment variable

### No Jira instance configured
```
Error: No Jira instance configured
```
**Riešenie:** Pridaj Jira inštanciu cez Pulse Dashboard: http://127.0.0.1:7010/v1/pulse/

### Autocomplete nefunguje
**Riešenie:** Skontroluj že máš vybraný projekt v sidebar

### Tool call failed
**Riešenie:** Skontroluj Jira API token a permissions

## 🚀 Ďalšie možnosti rozšírenia

1. **Viac MCP actions:**
   - Create issue
   - Update issue fields
   - Add attachments
   - Link issues
   - Create subtasks

2. **Lepší autocomplete:**
   - Real-time user search cez Jira API
   - Fuzzy search pre issues
   - Recent items cache

3. **Context awareness:**
   - Automatické načítanie kontextu z aktuálneho issue
   - História konverzácie per issue
   - Suggestions based on issue type

4. **Multi-tenant:**
   - Per-tenant OpenAI API keys
   - Per-tenant MCP configurations
   - Tenant-specific prompts

5. **Analytics:**
   - Track AI usage per user
   - Most used actions
   - Success rate of tool calls

## 📚 Dokumentácia

**Interné dokumenty:**
- **SQL Tools Guide:** [docs/SQL_TOOLS_GUIDE.md](./SQL_TOOLS_GUIDE.md) - Hybridný systém MCP + SQL
- **SQL Tools Examples:** [docs/SQL_TOOLS_EXAMPLES.md](./SQL_TOOLS_EXAMPLES.md) - Praktické príklady
- **MCP Standard Procedure:** [docs/MCP_STANDARD_PROCEDURE.md](./MCP_STANDARD_PROCEDURE.md) - Ako pridať nové MCP akcie
- **AI Chaining Guide:** [docs/AI_CHAINING_GUIDE.md](./AI_CHAINING_GUIDE.md) - Ako reťaziť úlohy s AI

**Externé zdroje:**
- **Google AI (Gemini):** https://ai.google.dev/docs
- **OpenAI Function Calling:** https://platform.openai.com/docs/guides/function-calling
- **Jira Cloud REST API:** https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- **MCP Protocol:** https://modelcontextprotocol.io/

---

**Vytvoril:** AI Assistant  
**Dátum:** 2025-01-03  
**Verzia:** 1.0.0

