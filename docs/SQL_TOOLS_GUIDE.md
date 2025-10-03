# SQL Tools Guide - Hybridný systém MCP + SQL

Tento dokument vysvetľuje hybridný systém kde AI môže rozhodnúť či použije MCP (Jira API) alebo SQL (databáza).

## 🎯 Prečo hybridný systém?

### Problém:
- **Jira API** je pomalé pre read operácie (komentáre, história, metriky)
- **Databáza** je rýchla ale nemôže robiť write operácie

### Riešenie:
- **SQL nástroje** - Pre READ operácie (rýchle!)
- **MCP nástroje** - Pre WRITE operácie (Jira API)

### Výhody:
✅ **10-100x rýchlejšie** čítanie dát z databázy  
✅ **AI automaticky rozhodne** ktorý nástroj použiť  
✅ **Predpripravené SQL queries** - optimalizované  
✅ **Žiadne rate limity** - databáza je lokálna

---

## 📊 Porovnanie: SQL vs MCP

| Operácia | MCP (Jira API) | SQL (Database) | Odporúčanie |
|----------|----------------|----------------|-------------|
| Získať komentáre | 500-1000ms | 10-50ms | ✅ SQL |
| Získať históriu | 500-1000ms | 10-50ms | ✅ SQL |
| Metriky projektu | 2000-5000ms | 50-100ms | ✅ SQL |
| Stuck issues | 1000-2000ms | 20-50ms | ✅ SQL |
| User workload | 1000-2000ms | 20-50ms | ✅ SQL |
| **Pridať komentár** | 300-500ms | ❌ Nie je možné | ✅ MCP |
| **Zmeniť status** | 300-500ms | ❌ Nie je možné | ✅ MCP |
| **Priradiť issue** | 300-500ms | ❌ Nie je možné | ✅ MCP |

---

## 🔧 Dostupné SQL nástroje

### 1. **sql_get_issue_history**
Získať históriu zmien issue (všetky status transitions).

**Použitie:**
```
User: "Zobraz históriu SCRUM-229"
AI: Zavolá sql_get_issue_history → Vráti všetky transitions
```

**Výsledok:**
```json
{
  "history": [
    {
      "from_status": "To Do",
      "to_status": "In Progress",
      "transitioned_at": "2025-01-01T10:00:00",
      "transitioned_by": "john@example.com"
    },
    {
      "from_status": "In Progress",
      "to_status": "Done",
      "transitioned_at": "2025-01-02T15:30:00",
      "transitioned_by": "jane@example.com"
    }
  ],
  "total": 2
}
```

---

### 2. **sql_get_project_metrics**
Získať agregované metriky projektu (throughput, WIP, lead time).

**Použitie:**
```
User: "Aké sú metriky projektu SCRUM za posledných 30 dní?"
AI: Zavolá sql_get_project_metrics → Vráti metriky
```

**Výsledok:**
```json
{
  "project_key": "SCRUM",
  "days": 30,
  "total_created": 45,
  "total_closed": 38,
  "avg_wip": 12.5,
  "avg_lead_time_days": 5.2,
  "throughput_per_day": 1.3
}
```

---

### 3. **sql_get_stuck_issues**
Získať issues ktoré sú stuck (žiadne updaty X dní).

**Použitie:**
```
User: "Ktoré issues sú stuck viac ako 7 dní?"
AI: Zavolá sql_get_stuck_issues → Vráti stuck issues
```

**Výsledok:**
```json
{
  "issues": [
    {
      "key": "SCRUM-123",
      "summary": "Fix login bug",
      "status": "In Progress",
      "assignee": "john@example.com",
      "days_stuck": 14,
      "last_updated": "2024-12-20T10:00:00"
    }
  ],
  "total": 1
}
```

---

### 4. **sql_get_user_workload**
Získať workload používateľa (koľko issues má assigned).

**Použitie:**
```
User: "Koľko issues má John?"
AI: Zavolá sql_get_user_workload → Vráti workload
```

**Výsledok:**
```json
{
  "assignee": "john@example.com",
  "total_open": 8,
  "by_status": {
    "To Do": [
      {"key": "SCRUM-1", "summary": "Task 1", "priority": "High"}
    ],
    "In Progress": [
      {"key": "SCRUM-2", "summary": "Task 2", "priority": "Medium"}
    ]
  }
}
```

---

### 5. **sql_search_issues_by_text**
Full-text search v názvoch issues.

**Použitie:**
```
User: "Nájdi issues s textom 'login'"
AI: Zavolá sql_search_issues_by_text → Vráti issues
```

**Výsledok:**
```json
{
  "issues": [
    {
      "key": "SCRUM-123",
      "summary": "Fix login bug",
      "status": "In Progress",
      "assignee": "john@example.com",
      "priority": "High"
    }
  ],
  "total": 1
}
```

---

## 🤖 Ako AI rozhoduje?

AI dostane v system message jasné inštrukcie:

```
**DÔLEŽITÉ - Výber nástroja:**
- Pre READ operácie (čítanie dát): VŽDY použi SQL nástroje (sql_*) - sú RÝCHLEJŠIE!
  Príklady: história issue, metriky projektu, stuck issues, workload používateľa
- Pre WRITE operácie (zmeny): Použi MCP nástroje (add_comment, transition_issue, atď.)
  Príklady: pridať komentár, zmeniť status, priradiť issue
```

**Príklady rozhodnutí:**

| User prompt | AI rozhodnutie | Dôvod |
|-------------|----------------|-------|
| "Zobraz históriu SCRUM-229" | ✅ SQL | READ operácia |
| "Pridaj komentár do SCRUM-229" | ✅ MCP | WRITE operácia |
| "Aké sú metriky projektu?" | ✅ SQL | READ operácia |
| "Zmeň status na Done" | ✅ MCP | WRITE operácia |
| "Ktoré issues sú stuck?" | ✅ SQL | READ operácia |
| "Prirad issue Johnovi" | ✅ MCP | WRITE operácia |

---

## 📝 Príklady použitia

### Príklad 1: Analýza projektu (SQL)

```
User: "Urob analýzu projektu SCRUM za posledných 30 dní"

AI:
1. Zavolá sql_get_project_metrics(project_key="SCRUM", days=30)
2. Zavolá sql_get_stuck_issues(project_key="SCRUM")
3. Vráti súhrn:

"Projekt SCRUM za posledných 30 dní:
- Vytvorených: 45 issues
- Uzavretých: 38 issues
- Priemerný WIP: 12.5
- Priemerný lead time: 5.2 dní
- Throughput: 1.3 issues/deň

Stuck issues (>7 dní): 3
- SCRUM-123: Fix login bug (14 dní)
- SCRUM-124: Update docs (10 dní)
- SCRUM-125: Refactor code (8 dní)"
```

### Príklad 2: User workload (SQL)

```
User: "Koľko issues má John a v akom sú stave?"

AI:
1. Zavolá sql_get_user_workload(assignee="john@example.com")
2. Vráti:

"John má 8 open issues:
- To Do: 3 issues
- In Progress: 4 issues
- In Review: 1 issue

Najvyššia priorita:
- SCRUM-1: Fix critical bug (High)
- SCRUM-2: Deploy to prod (High)"
```

### Príklad 3: Kombinácia SQL + MCP

```
User: "Nájdi stuck issues v SCRUM a prirad ich Johnovi"

AI:
1. Zavolá sql_get_stuck_issues(project_key="SCRUM") → SQL (READ)
2. Pre každé issue zavolá assign_issue(issue_key, assignee="john") → MCP (WRITE)
3. Vráti:

"Našiel som 3 stuck issues a priradil som ich Johnovi:
- SCRUM-123: Fix login bug
- SCRUM-124: Update docs
- SCRUM-125: Refactor code"
```

---

## 🚀 Výhody hybridného systému

### 1. **Rýchlosť**
- SQL queries sú 10-100x rýchlejšie ako Jira API
- Žiadne rate limity
- Lokálna databáza

### 2. **Flexibilita**
- AI automaticky rozhodne ktorý nástroj použiť
- Kombinácia SQL + MCP pre komplexné operácie
- Predpripravené queries pre bežné use cases

### 3. **Škálovateľnosť**
- Databáza zvládne tisíce queries/sec
- Jira API má rate limity (10-100 req/sec)
- Lepšie pre veľké projekty

### 4. **Offline režim**
- SQL funguje aj keď Jira API je nedostupné
- Dáta sú cached v databáze
- Backfill job synchronizuje dáta

---

## 📊 Architektúra

```
User Prompt
    ↓
AI Provider (Gemini/OpenAI)
    ↓
    ├─→ SQL Tools (READ) → Database → Fast response
    │   - get_issue_history
    │   - get_project_metrics
    │   - get_stuck_issues
    │   - get_user_workload
    │   - search_issues_by_text
    │
    └─→ MCP Tools (WRITE) → Jira API → Slower but necessary
        - add_comment
        - transition_issue
        - assign_issue
        - update_issue_field
        - ...
```

---

## 🔧 Implementácia

### 1. SQL Query Library
**Súbor:** `orchestrator/sql_tools.py`

Obsahuje predpripravené SQL queries:
- `get_issue_history()` - História transitions
- `get_project_metrics()` - Agregované metriky
- `get_stuck_issues()` - Stuck issues
- `get_user_workload()` - Workload používateľa
- `search_issues_by_text()` - Full-text search

### 2. SQL Tool Definitions
**Súbor:** `orchestrator/ai_assistant_api.py`

Pridané do `MCP_TOOLS`:
- `sql_get_issue_history`
- `sql_get_project_metrics`
- `sql_get_stuck_issues`
- `sql_get_user_workload`
- `sql_search_issues_by_text`

### 3. SQL Executors
**Súbor:** `orchestrator/ai_assistant_api.py`

Pridané do `execute_mcp_action()`:
```python
elif action_name == "sql_get_issue_history":
    result = await execute_sql_query("get_issue_history", params, tenant_id)
    return result
```

---

## 📚 Ďalšie možnosti rozšírenia

1. **Viac SQL queries:**
   - `sql_get_sprint_burndown` - Burndown chart dáta
   - `sql_get_team_velocity` - Team velocity
   - `sql_get_sla_breaches` - SLA breaches
   - `sql_get_reopened_issues` - Reopened issues

2. **Caching:**
   - Cache SQL results pre 1-5 minút
   - Invalidate cache pri write operáciách

3. **Materialized views:**
   - Pre komplexné agregácie
   - Refresh každých 5-10 minút

4. **Real-time updates:**
   - WebSocket pre live updates
   - Refresh UI pri zmene dát

---

**Vytvoril:** AI Assistant  
**Dátum:** 2025-01-03  
**Verzia:** 1.0.0

