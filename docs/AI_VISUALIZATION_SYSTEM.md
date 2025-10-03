# AI-Driven Visualization System

## Overview

AI asistent automaticky rozhoduje kedy a ako vizualizovať dáta. Namiesto toho aby len vrátil text, AI vie vytvoriť **grafy** alebo **tabuľky** priamo v odpovedi.

---

## Ako to funguje

### 1. **AI rozhoduje o vizualizácii**

AI asistent dostal inštrukcie v system message:
- Keď používateľ žiada **metriky/štatistiky** → vytvor **CHART**
- Keď používateľ žiada **zoznam issues** → vytvor **TABLE**
- Keď používateľ žiada **vysvetlenie** → vráť **TEXT**

### 2. **AI vytvorí štrukturované dáta**

AI odpoveď obsahuje špeciálny blok:

**Pre CHART:**
```
```visualization:chart
{"title": "Metriky projektu SCRUM", "chartType": "bar", "labels": ["Vytvorených", "Uzavretých"], "values": [45, 38]}
```
```

**Pre TABLE:**
```
```visualization:table
{"title": "Stuck issues", "columns": ["Issue", "Summary", "Status"], "rows": [["SCRUM-1", "Bug", "In Progress"], ["SCRUM-2", "Task", "Todo"]]}
```
```

### 3. **Frontend parsuje a vykreslí**

JavaScript funkcia `parseVisualizationBlocks()` nájde tieto bloky a automaticky vytvorí:
- **Chart.js graf** (bar alebo doughnut)
- **HTML tabuľku** s lazy loading

---

## Príklady použitia

### Príklad 1: Metriky projektu (CHART)

**Používateľ:**
```
Aké sú metriky projektu SCRUM za posledných 30 dní?
```

**AI:**
1. Zavolá `sql_get_project_metrics(project_key="SCRUM", days=30)`
2. Dostane dáta: `{total_created: 45, total_closed: 38, avg_wip: 12, avg_lead_time_days: 5.2}`
3. Vytvorí odpoveď:

```
Metriky projektu SCRUM za posledných 30 dní:

```visualization:chart
{"title": "Metriky projektu SCRUM", "chartType": "bar", "labels": ["Vytvorených", "Uzavretých", "WIP", "Lead time (dni)"], "values": [45, 38, 12, 5.2]}
```

Projekt má dobrý throughput, uzavrelo sa 38 z 45 vytvorených issues.
```

**Výsledok v UI:**
- Text: "Metriky projektu SCRUM za posledných 30 dní:"
- **Bar chart** s 4 stĺpcami
- Text: "Projekt má dobrý throughput..."

---

### Príklad 2: Stuck issues (TABLE)

**Používateľ:**
```
Ktoré issues sú stuck viac ako 7 dní?
```

**AI:**
1. Zavolá `sql_get_stuck_issues(project_key="SCRUM", days_threshold=7)`
2. Dostane dáta: `{issues: [{key: "SCRUM-1", summary: "Login bug", status: "In Progress", days_stuck: 10}, ...]}`
3. Vytvorí odpoveď:

```
Našiel som 3 stuck issues:

```visualization:table
{"title": "Stuck issues (7+ dní)", "columns": ["Issue Key", "Summary", "Status", "Days Stuck"], "rows": [["SCRUM-1", "Login bug", "In Progress", "10"], ["SCRUM-2", "API error", "Todo", "8"], ["SCRUM-3", "UI glitch", "In Progress", "7"]]}
```

Odporúčam sa pozrieť na SCRUM-1, je stuck už 10 dní.
```

**Výsledok v UI:**
- Text: "Našiel som 3 stuck issues:"
- **HTML tabuľka** s 3 riadkami
- Text: "Odporúčam sa pozrieť na SCRUM-1..."

---

### Príklad 3: Workload používateľa (DOUGHNUT CHART)

**Používateľ:**
```
Aký je workload používateľa John Doe?
```

**AI:**
1. Zavolá `sql_get_user_workload(assignee="John Doe", project_key="SCRUM")`
2. Dostane dáta: `{issues_by_status: {Done: 5, "In Progress": 3, Todo: 2}}`
3. Vytvorí odpoveď:

```
Workload používateľa John Doe:

```visualization:chart
{"title": "Workload - John Doe", "chartType": "doughnut", "labels": ["Done", "In Progress", "Todo"], "values": [5, 3, 2]}
```

John má celkovo 10 issues, z toho 3 sú aktívne.
```

**Výsledok v UI:**
- Text: "Workload používateľa John Doe:"
- **Doughnut chart** s 3 segmentami
- Text: "John má celkovo 10 issues..."

---

## Technická implementácia

### Backend (orchestrator/ai_assistant_api.py)

**System message s inštrukciami:**
```python
system_message = (
    "Si užitočný Jira asistent..."
    "\n\n"
    "**KRITICKY DÔLEŽITÉ - Vizualizácia dát:**\n"
    "\n"
    "Keď používateľ žiada o dáta (metriky, zoznamy, štatistiky), MUSÍŠ ich vizualizovať!\n"
    "\n"
    "**Kedy použiť CHART:**\n"
    "- Metriky projektu (throughput, WIP, lead time)\n"
    "- Workload používateľa (issues podľa statusu)\n"
    "- Štatistiky, porovnania čísel\n"
    "\n"
    "**Kedy použiť TABLE:**\n"
    "- Zoznam issues (stuck issues, search results)\n"
    "- História zmien\n"
    "- Akýkoľvek zoznam položiek\n"
    "\n"
    "**Formát odpovede s vizualizáciou:**\n"
    "\n"
    "Keď chceš vytvoriť CHART, odpoveď MUSÍ obsahovať:\n"
    "```visualization:chart\n"
    '{"title": "Názov", "chartType": "bar|doughnut", "labels": [...], "values": [...]}\n'
    "```\n"
    "\n"
    "Keď chceš vytvoriť TABLE, odpoveď MUSÍ obsahovať:\n"
    "```visualization:table\n"
    '{"title": "Názov", "columns": [...], "rows": [[...], [...]]}\n'
    "```\n"
)
```

### Frontend (orchestrator/templates/static/ai-assistant.js)

**1. Parsing vizualizačných blokov:**
```javascript
function parseVisualizationBlocks(content) {
    const chartRegex = /```visualization:chart\s*\n([\s\S]*?)\n```/;
    const tableRegex = /```visualization:table\s*\n([\s\S]*?)\n```/;
    
    const chartMatch = content.match(chartRegex);
    const tableMatch = content.match(tableRegex);
    
    if (chartMatch) {
        const data = JSON.parse(chartMatch[1]);
        return {
            hasVisualization: true,
            textBefore: content.substring(0, chartMatch.index).trim(),
            textAfter: content.substring(chartMatch.index + chartMatch[0].length).trim(),
            visualization: createChartFromAI(data)
        };
    }
    
    if (tableMatch) {
        const data = JSON.parse(tableMatch[1]);
        return {
            hasVisualization: true,
            textBefore: content.substring(0, tableMatch.index).trim(),
            textAfter: content.substring(tableMatch.index + tableMatch[0].length).trim(),
            visualization: createTableFromAI(data)
        };
    }
    
    return { hasVisualization: false };
}
```

**2. Vytvorenie grafu:**
```javascript
function createChartFromAI(data) {
    const container = document.createElement('div');
    container.className = 'chart-container';
    
    const canvas = document.createElement('canvas');
    const chartId = 'ai-chart-' + Date.now();
    canvas.id = chartId;
    container.appendChild(canvas);
    
    setTimeout(() => {
        new Chart(document.getElementById(chartId), {
            type: data.chartType || 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: ['rgba(102, 126, 234, 0.8)', ...]
                }]
            },
            options: { responsive: true, maintainAspectRatio: true }
        });
    }, 100);
    
    return container;
}
```

**3. Vytvorenie tabuľky:**
```javascript
function createTableFromAI(data) {
    const container = document.createElement('div');
    const tableDiv = document.createElement('div');
    tableDiv.className = 'result-table';
    
    const table = document.createElement('table');
    
    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    data.columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Body with lazy loading (20 rows at a time)
    const tbody = document.createElement('tbody');
    table.appendChild(tbody);
    tableDiv.appendChild(table);
    container.appendChild(tableDiv);
    
    // Lazy loading implementation...
    
    return container;
}
```

---

## Výhody

✅ **AI rozhoduje** - Nemusíš špecifikovať typ vizualizácie  
✅ **Automatické** - AI vie kedy použiť graf vs tabuľku  
✅ **Flexibilné** - Podporuje bar charts, doughnut charts, tabuľky  
✅ **Lazy loading** - Tabuľky sa načítavajú po 20 riadkoch  
✅ **Prehľadné** - Grafy a tabuľky sú krajšie ako text  

---

## Testovanie

### Test 1: Metriky projektu
```
User: "Aké sú metriky projektu SCRUM?"
→ Očakávaný výsledok: Bar chart s metrikami
```

### Test 2: Stuck issues
```
User: "Ktoré issues sú stuck?"
→ Očakávaný výsledok: HTML tabuľka s lazy loading
```

### Test 3: Workload
```
User: "Aký je workload používateľa John Doe?"
→ Očakávaný výsledok: Doughnut chart s issues podľa statusu
```

---

## Rozšírenie

### Pridanie nového typu vizualizácie

1. **Pridaj inštrukcie do system message** (backend)
2. **Pridaj regex pattern** do `parseVisualizationBlocks()` (frontend)
3. **Vytvor render funkciu** (napr. `createLineChartFromAI()`)
4. **Pridaj CSS štýly** do `ai_assistant.html`

---

**Server beží na:** http://127.0.0.1:7010/v1/ai-assistant/

**Vyskúšaj rôzne prompty a sleduj ako AI automaticky vytvára grafy a tabuľky!** 🚀

