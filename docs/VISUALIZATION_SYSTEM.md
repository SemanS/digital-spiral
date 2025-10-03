# 📊 Visualization System - AI Assistant

## Prehľad

AI Assistant používa **inteligentný vizualizačný systém** ktorý automaticky rozhoduje aký typ vizualizácie použiť na základe typu dát a funkcie.

## Architektúra

```
Tool Result → Visualization Middleware → Visualization Type
                                        ├─ Chart (Chart.js)
                                        ├─ Table (HTML Table)
                                        ├─ Cards (Card Layout)
                                        └─ Default (JSON)
```

## Typy vizualizácií

### 1. 📊 Charts (Grafy)

**Použitie:** Metriky, štatistiky, agregované dáta

**Podporované grafy:**
- **Bar Chart** - Pre project metrics (throughput, WIP, lead time)
- **Doughnut Chart** - Pre user workload (issues podľa statusu)
- **Line Chart** - Pre trendy v čase (TODO)

**Príklad:**
```javascript
// Project metrics → Bar chart
sql_get_project_metrics → Bar chart s metrikami

// User workload → Doughnut chart
sql_get_user_workload → Doughnut chart s issues podľa statusu
```

**Výhody:**
- ✅ Vizuálne prehľadné
- ✅ Ľahko porovnateľné hodnoty
- ✅ Interaktívne (hover tooltips)

---

### 2. 📋 Tables (Tabuľky)

**Použitie:** Zoznamy issues, história, search results

**Podporované tabuľky:**
- **Stuck Issues** - Issues bez updatov
- **Search Results** - Nájdené issues
- **Issue History** - Status transitions

**Príklad:**
```javascript
// Stuck issues → Table
sql_get_stuck_issues → Table s issue key, summary, status, assignee, days stuck

// Search results → Table
sql_search_issues_by_text → Table s issue key, summary, status, priority, assignee
```

**Features:**
- ✅ Sortovateľné stĺpce
- ✅ Farebné badges (status, priority)
- ✅ Hover efekty
- ✅ Responsive design

---

### 3. 🗂️ Cards (Karty)

**Použitie:** Komentáre, detaily, textové dáta

**Podporované cards:**
- **Comments** - Komentáre s autorom a dátumom
- **Issue Details** - Detaily issue

**Príklad:**
```javascript
// Comments → Cards
get_comments → Cards s autorom, dátumom a textom
```

**Features:**
- ✅ Prehľadné rozloženie
- ✅ Autor a timestamp
- ✅ Formátovaný text

---

### 4. 📄 Default (JSON)

**Použitie:** Fallback pre neznáme dáta

**Príklad:**
```javascript
// Unknown data → JSON
unknown_function → JSON output
```

---

## Middleware rozhodovanie

### `determineVisualizationType(functionName, result)`

Rozhoduje aký typ vizualizácie použiť:

```javascript
function determineVisualizationType(functionName, result) {
    // Project metrics → Chart
    if (functionName === 'sql_get_project_metrics') {
        return 'chart';
    }
    
    // Stuck issues → Table
    if (functionName === 'sql_get_stuck_issues' && result.issues?.length > 0) {
        return 'table';
    }
    
    // Search results → Table
    if ((functionName === 'search_issues' || functionName === 'sql_search_issues_by_text') 
        && result.issues?.length > 0) {
        return 'table';
    }
    
    // User workload → Chart
    if (functionName === 'sql_get_user_workload') {
        return 'chart';
    }
    
    // Issue history → Table
    if (functionName === 'sql_get_issue_history' && result.history?.length > 0) {
        return 'table';
    }
    
    // Comments → Cards
    if (functionName === 'get_comments' && result.comments) {
        return 'cards';
    }
    
    // Default → Cards
    return 'cards';
}
```

---

## Implementácia

### 1. Chart Visualization

```javascript
function createChartVisualization(functionName, result) {
    // Create canvas element
    const canvas = document.createElement('canvas');
    canvas.id = 'chart-' + Date.now();
    
    // Render chart using Chart.js
    new Chart(canvas, {
        type: 'bar', // or 'doughnut', 'line'
        data: {
            labels: [...],
            datasets: [{
                data: [...],
                backgroundColor: [...]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true },
                title: { display: true, text: '...' }
            }
        }
    });
}
```

### 2. Table Visualization

```javascript
function createTableVisualization(functionName, result) {
    const table = document.createElement('table');
    table.innerHTML = `
        <thead>
            <tr>
                <th>Column 1</th>
                <th>Column 2</th>
            </tr>
        </thead>
        <tbody>
            ${result.items.map(item => `
                <tr>
                    <td>${item.field1}</td>
                    <td>${item.field2}</td>
                </tr>
            `).join('')}
        </tbody>
    `;
}
```

### 3. Cards Visualization

```javascript
function createCardsVisualization(functionName, result) {
    result.items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'result-item';
        card.innerHTML = `
            <div class="result-item-header">
                <strong>${item.title}</strong>
                <span>${item.date}</span>
            </div>
            <div class="result-item-body">${item.content}</div>
        `;
    });
}
```

---

## Pridanie novej vizualizácie

### Krok 1: Rozšír middleware

```javascript
function determineVisualizationType(functionName, result) {
    // Add new condition
    if (functionName === 'my_new_function') {
        return 'chart'; // or 'table', 'cards'
    }
}
```

### Krok 2: Implementuj vizualizáciu

```javascript
function createChartVisualization(functionName, result) {
    if (functionName === 'my_new_function') {
        // Create custom chart
        new Chart(canvas, {
            type: 'line',
            data: { ... },
            options: { ... }
        });
    }
}
```

### Krok 3: Pridaj CSS štýly

```css
.my-custom-visualization {
    background: white;
    padding: 16px;
    border-radius: 8px;
}
```

---

## Príklady použitia

### Príklad 1: Project Metrics (Bar Chart)

**Prompt:**
```
"Aké sú metriky projektu SCRUM?"
```

**Výsledok:**
- 📊 Bar chart s metrikami (created, closed, WIP, lead time)
- Interaktívne tooltips
- Farebné stĺpce

---

### Príklad 2: Stuck Issues (Table)

**Prompt:**
```
"Ktoré issues sú stuck viac ako 7 dní?"
```

**Výsledok:**
- 📋 Table s stuck issues
- Stĺpce: Issue Key, Summary, Status, Assignee, Days Stuck
- Farebné badges pre status a days stuck

---

### Príklad 3: Comments (Cards)

**Prompt:**
```
"Zobraz komentáre z SCRUM-229"
```

**Výsledok:**
- 🗂️ Cards s komentármi
- Autor, dátum, text
- Prehľadné rozloženie

---

## Technológie

- **Chart.js 4.4.0** - Grafy
- **HTML Tables** - Tabuľky
- **CSS Grid/Flexbox** - Layout
- **Vanilla JavaScript** - Middleware

---

## Výhody systému

✅ **Automatické rozhodovanie** - Middleware rozhodne aký typ vizualizácie použiť  
✅ **Flexibilné** - Ľahko pridať nové vizualizácie  
✅ **Prehľadné** - Grafy, tabuľky, karty  
✅ **Interaktívne** - Hover tooltips, sortovanie  
✅ **Responsive** - Funguje na mobile aj desktop  

---

## Ďalšie možnosti rozšírenia

1. **Line Charts** - Pre trendy v čase
2. **Pie Charts** - Pre percentuálne rozdelenie
3. **Scatter Plots** - Pre korelácie
4. **Heatmaps** - Pre časové rozloženie
5. **Gantt Charts** - Pre timeline
6. **Network Graphs** - Pre dependencies

---

**Vytvorené:** 2025-10-03  
**Autor:** AI Assistant  
**Verzia:** 1.0

