# 🚀 Obohatiť Jira dáta

Tento návod ti ukáže, ako obohatiť existujúce Jira dáta o:
- ✅ **Assignees** - priradenie ticketov reálnym používateľom
- ✅ **Worklog entries** - time tracking (5-8 záznamov na ticket)
- ✅ **Workflow transitions** - prechody cez stavy (To Do → In Progress → Done)
- ✅ **Komentáre** - realistická diskusia (8-12 komentárov na ticket)
- ✅ **Sprinty** - rozšírená história projektu (12 sprintov)

---

## 📋 Predpoklady

1. **Jira Cloud účet** s API tokenom
2. **Existujúci projekt** s ticketmi (napr. SCRUM)
3. **Python 3.10+** nainštalovaný

---

## 🔧 Príprava

### 1. Získaj API token

1. Choď na https://id.atlassian.com/manage-profile/security/api-tokens
2. Klikni na **Create API token**
3. Pomenuj ho (napr. "Digital Spiral")
4. Skopíruj token (uložíš si ho niekam bezpečne)

### 2. Nájdi svoj projekt

1. Choď do Jira
2. Otvor projekt (napr. SCRUM)
3. Poznač si **project key** (napr. SCRUM)

---

## 🎯 Krok 1: Priraď tickety používateľom

Tento skript priradí všetky tickety reálnym používateľom z Jira.

```bash
python scripts/assign_tickets_to_users.py \
  --base-url https://insight-bridge.atlassian.net \
  --email slavosmn@gmail.com \
  --token YOUR_API_TOKEN \
  --project SCRUM
```

**Čo sa stane:**
- ✅ Načíta všetkých reálnych používateľov z Jira
- ✅ Priradí tickety používateľom v round-robin štýle
- ✅ Trvá ~30 sekúnd pre 50 ticketov

**Výstup:**
```
✓ Connected as: Slavomir Seman

🎯 Assigning tickets to real users...

1️⃣ Getting real users from Jira...
✓ Found 12 real users
   - Slavomir Seman (5f8a9b1c2d3e4f5g6h7i...)
   - abhinav (6g7h8i9j0k1l2m3n4o5p...)
   ...

2️⃣ Getting all tickets...
✓ Found 50 tickets

3️⃣ Assigning tickets to users...
   ✓ SCRUM-1: Setup PostgreSQL database... → Slavomir Seman
   ✓ SCRUM-2: Create FastAPI backend... → abhinav
   ...

📊 Summary:
   ✓ Assigned: 50
   ❌ Failed: 0
```

---

## 📝 Krok 2: Pridaj worklog a komentáre

Tento skript pridá worklog entries, transitions a komentáre.

```bash
python scripts/add_worklog_and_transitions.py \
  --base-url https://insight-bridge.atlassian.net \
  --email slavosmn@gmail.com \
  --token YOUR_API_TOKEN \
  --project SCRUM
```

**Čo sa stane:**
- ✅ Pridá 5-8 worklog entries na ticket (time tracking)
- ✅ Prevedie tickety cez workflow (To Do → In Progress → Done)
- ✅ Pridá 8-12 komentárov simulujúcich diskusiu
- ✅ Trvá ~15-20 minút pre 50 ticketov

**Výstup:**
```
✓ Connected as: Slavomir Seman

🚀 Adding worklog, transitions, and comments...
   This will take 15-20 minutes...
   - Add worklog entries (time tracking)
   - Transition tickets through workflow
   - Add more realistic comments

1️⃣ Getting all tickets...
✓ Found 50 tickets

2️⃣ Getting sprints...
✓ Found 6 sprints

3️⃣ Updating sprint states...
   ✓ Sprint 1 - Foundation: future → closed
   ✓ Sprint 5 - Dashboard: future → active

4️⃣ Processing tickets...
   [Sprint 1 - Foundation] (closed) - 10 tickets
       ✓ SCRUM-1: Setup PostgreSQL database...
       ✓ SCRUM-2: Create FastAPI backend...
   ...
```

---

## 🏃 Krok 3: Pridaj viac sprintov

Tento skript vytvorí 12 sprintov s realistickou históriou.

```bash
python scripts/add_multiple_sprints.py \
  --base-url https://insight-bridge.atlassian.net \
  --email slavosmn@gmail.com \
  --token YOUR_API_TOKEN \
  --project SCRUM
```

**Čo sa stane:**
- ✅ Vytvorí 12 sprintov (4 closed, 2 active, 6 future)
- ✅ Nastaví realistické dátumy (2-týždňové sprinty)
- ✅ Pridá sprint goals
- ✅ Rozdelí tickety medzi sprinty
- ✅ Trvá ~2-3 minúty

**Výstup:**
```
✓ Connected as: Slavomir Seman

🏃 Adding 12 sprints to SCRUM...
   - 4 closed sprints (past)
   - 2 active sprints (current)
   - 6 future sprints (planned)

1️⃣ Finding board...
✓ Found board: SCRUM board (ID: 1)

2️⃣ Creating sprints...
   ✓ Sprint 1 - Foundation
   ✓ Sprint 2 - Jira Integration
   ...
   ✓ Sprint 12 - Launch Prep

3️⃣ Updating sprint states...
   ✓ Sprint 1 - Foundation: closed
   ✓ Sprint 5 - Dashboard UI: active
   ...

4️⃣ Distributing tickets across sprints...
   Found 50 tickets
   ✓ Sprint 1 - Foundation: 4 tickets
   ✓ Sprint 2 - Jira Integration: 4 tickets
   ...
```

---

## 🎉 Výsledok

Po dokončení všetkých krokov budeš mať:

### ✅ Realistické assignees
- Tickety priradené reálnym používateľom
- Round-robin distribúcia

### ✅ Time tracking
- 5-8 worklog entries na ticket
- Rôzne časy (1-8 hodín)
- Realistické komentáre (research, implementation, testing, ...)

### ✅ Workflow transitions
- Closed sprints: všetky tickety Done
- Active sprints: mix In Progress, Review, Done
- Future sprints: všetky To Do

### ✅ Bohatá diskusia
- 8-12 komentárov na ticket
- Simuluje code review, QA feedback, product approval
- Realistické mená (Tech Lead, QA, Product)

### ✅ Rozšírená história
- 12 sprintov (4 closed, 2 active, 6 future)
- Realistické dátumy (2-týždňové sprinty)
- Sprint goals pre každý sprint

---

## 🔍 Overenie

### 1. Skontroluj assignees
```bash
# Otvor Jira
https://insight-bridge.atlassian.net/jira/software/c/projects/SCRUM/boards/1

# Skontroluj, že tickety majú assignees
```

### 2. Skontroluj worklog
```bash
# Otvor ticket (napr. SCRUM-1)
# Klikni na "Log work" v pravom paneli
# Uvidíš 5-8 worklog entries
```

### 3. Skontroluj komentáre
```bash
# Otvor ticket (napr. SCRUM-1)
# Scroll dole na komentáre
# Uvidíš 8-12 komentárov
```

### 4. Skontroluj sprinty
```bash
# Otvor board
https://insight-bridge.atlassian.net/jira/software/c/projects/SCRUM/boards/1

# Klikni na "Backlog"
# Uvidíš 12 sprintov
```

---

## ⚠️ Poznámky

### Rate limiting
- Jira Cloud má rate limit ~100 requests/min
- Skripty majú built-in delays (0.3-0.5s medzi requestmi)
- Ak dostaneš 429 error, počkaj 1 minútu a skús znova

### Permissions
- Potrebuješ **admin** alebo **project admin** práva
- Assignees fungujú len pre používateľov s prístupom k projektu

### Bezpečnosť
- **NIKDY** nezdieľaj API token
- Token má rovnaké práva ako tvoj účet
- Môžeš ho kedykoľvek zrušiť na https://id.atlassian.com/manage-profile/security/api-tokens

---

## 🐛 Troubleshooting

### "Failed to assign" error
```
❌ SCRUM-1: Failed to assign - User does not have permission
```

**Riešenie:** Používateľ nemá prístup k projektu. Pridaj ho do projektu v Jira.

### "Rate limited" error
```
❌ 429 Too Many Requests
```

**Riešenie:** Počkaj 1 minútu a skús znova.

### "Sprint not found" error
```
❌ No board found for project SCRUM
```

**Riešenie:** Vytvor board pre projekt v Jira (Project settings → Boards → Create board).

---

## 📚 Ďalšie kroky

Ak chceš ešte viac realistických dát:

1. **Pridaj attachments** - screenshoty, logy, dokumenty
2. **Pridaj issue links** - "blocks", "relates to", "duplicates"
3. **Pridaj custom fields** - story points, labels, components
4. **Pridaj watchers** - kto sleduje ticket

Pozri `scripts/create_realistic_project_with_real_users.py` pre inšpiráciu.

---

## 🎯 Zhrnutie

```bash
# 1. Priraď tickety používateľom (~30s)
python scripts/assign_tickets_to_users.py \
  --base-url https://insight-bridge.atlassian.net \
  --email slavosmn@gmail.com \
  --token YOUR_API_TOKEN \
  --project SCRUM

# 2. Pridaj worklog a komentáre (~15-20 min)
python scripts/add_worklog_and_transitions.py \
  --base-url https://insight-bridge.atlassian.net \
  --email slavosmn@gmail.com \
  --token YOUR_API_TOKEN \
  --project SCRUM

# 3. Pridaj viac sprintov (~2-3 min)
python scripts/add_multiple_sprints.py \
  --base-url https://insight-bridge.atlassian.net \
  --email slavosmn@gmail.com \
  --token YOUR_API_TOKEN \
  --project SCRUM
```

**Celkový čas:** ~20-25 minút

**Výsledok:** Plne realistický Jira projekt s bohatou históriou! 🎉

