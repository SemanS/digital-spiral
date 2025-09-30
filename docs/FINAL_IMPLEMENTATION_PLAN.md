# 📋 Finálny Implementačný Plán

## Problém:
- Všetky tickety sú priradené Slavomir Seman
- Chýba worklog history
- Chýbajú workflow transitions (To Do → In Progress → Review → Done)
- Chýbajú story points
- Demo UI ukazuje 0 issues (možno kvôli cache)

## Riešenie (rozdelené na menšie úlohy):

### ✅ Úloha 1: Vyčistiť všetko (HOTOVO)
- Vymazať všetky tickety
- Vymazať všetky sprinty

### 🔄 Úloha 2: Získať reálnych používateľov z Jira
- Načítať zoznam používateľov cez API
- Filtrovať len reálnych používateľov (nie boty)
- Vybrať 7-10 používateľov pre team

### 🔄 Úloha 3: Vytvoriť script s PLNOU funkčnosťou
Script musí:
1. Vytvoriť sprinty (6 sprintov)
2. Vytvoriť tickety s:
   - Priradením k reálnym používateľom
   - Story points (3, 5, 8, 13)
   - Realistic descriptions
3. Pridať worklog entries:
   - Každý deň práce na tickete
   - Rôzni ľudia logujú čas
4. Pridať workflow transitions:
   - To Do → In Progress (keď začne práca)
   - In Progress → Review (keď je hotové)
   - Review → Done (po schválení)
5. Pridať komentáre:
   - Pri každom transition
   - Code reviews
   - QA testing
   - Approvals

### 🔄 Úloha 4: Opraviť Demo UI
- Pridať cache-busting
- Otestovať načítanie

## Technické detaily:

### Jira API endpoints:
- `/rest/api/3/users/search` - Získať používateľov
- `/rest/api/3/issue/{issueKey}/worklog` - Pridať worklog
- `/rest/api/3/issue/{issueKey}/transitions` - Zmeniť status
- `/rest/agile/1.0/issue/{issueKey}/estimation` - Nastaviť story points

### Workflow transitions:
1. **To Do** (status ID: 10000)
2. **In Progress** (status ID: 3)
3. **Review** (status ID: 10001)
4. **Done** (status ID: 10002)

### Worklog format:
```json
{
  "timeSpentSeconds": 28800,  // 8 hours
  "started": "2025-01-15T09:00:00.000+0000",
  "comment": "Working on implementation"
}
```

### Story points:
- Fibonacci: 3, 5, 8, 13
- Nastavuje sa cez custom field alebo Agile API

## Časový plán:
- Úloha 2: 5 minút
- Úloha 3: 20 minút (vytvorenie scriptu)
- Úloha 4: 5 minút
- **Celkom: 30 minút**

