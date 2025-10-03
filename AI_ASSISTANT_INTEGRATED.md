# 🤖 AI Assistant - Integrovaný do Admin UI!

## ✅ AI Assistant je teraz súčasťou Next.js Admin UI!

---

## 🎉 Čo bolo urobené

### 1. **Vytvorené nové stránky a komponenty**

#### Stránka AI Assistant
- **Path**: `admin-ui/src/app/(dashboard)/admin/assistant/page.tsx`
- **URL**: http://localhost:3002/admin/assistant
- **Features**:
  - Chat interface s AI
  - Project selector
  - Real-time messaging
  - Tool calls visualization
  - Loading states
  - Error handling

#### Komponenty
1. **ChatMessage** (`admin-ui/src/components/ai-assistant/ChatMessage.tsx`)
   - Zobrazenie user/assistant správ
   - Tool calls visualization
   - Timestamp
   - Avatars (User/Bot icons)

2. **ChatInput** (`admin-ui/src/components/ai-assistant/ChatInput.tsx`)
   - Input field s autocomplete
   - @ pre users
   - / pre issues
   - Keyboard navigation (Arrow keys, Enter, Escape)
   - Send button

### 2. **API Routes (Proxy)**

#### Chat Endpoint
- **Path**: `admin-ui/src/app/api/ai-assistant/chat/route.ts`
- **Method**: POST
- **Proxy to**: http://127.0.0.1:7010/v1/ai-assistant/chat
- **Purpose**: Avoid CORS issues

#### Autocomplete Endpoint
- **Path**: `admin-ui/src/app/api/ai-assistant/autocomplete/route.ts`
- **Method**: POST
- **Proxy to**: http://127.0.0.1:7010/v1/ai-assistant/autocomplete
- **Purpose**: Autocomplete for @users and /issues

### 3. **Sidebar Navigation**

#### Aktualizovaný Sidebar
- **File**: `admin-ui/src/components/layout/Sidebar.tsx`
- **Pridaný**: AI Assistant link s Bot ikonou
- **Order**:
  1. Dashboard
  2. Instances
  3. **AI Assistant** ✨ NEW
  4. Settings
  5. Logs

---

## 🌐 Prístupové URL

### Admin UI
- **Home**: http://localhost:3002
- **Instances**: http://localhost:3002/admin/instances
- **AI Assistant**: http://localhost:3002/admin/assistant ✨ NEW
- **Settings**: http://localhost:3002/admin/settings
- **Logs**: http://localhost:3002/admin/logs

### Backend Services
- **Backend API**: http://localhost:8000
- **Orchestrator**: http://127.0.0.1:7010
- **Old AI Assistant UI**: http://127.0.0.1:7010/v1/ai-assistant/ (deprecated)

---

## 🎯 Ako používať AI Assistant

### 1. Otvorte AI Assistant
```bash
open http://localhost:3002/admin/assistant
```

### 2. Vyberte projekt (optional)
- Kliknite na dropdown "Select project"
- Vyberte projekt (SCRUM, DEV, PROJ1, PROJ2)
- Alebo nechajte "All projects"

### 3. Napíšte správu
```
Vyhľadaj všetky bugs s vysokou prioritou
```

### 4. Použite autocomplete
- **@** - Napíšte `@` a začnite písať meno používateľa
  - Príklad: `@john`
  - Zobrazí sa dropdown so suggestions
  - Použite šípky na navigáciu
  - Enter na výber

- **/** - Napíšte `/` a začnite písať kľúč issue
  - Príklad: `/SCRUM-`
  - Zobrazí sa dropdown s issues
  - Použite šípky na navigáciu
  - Enter na výber

### 5. Príklady príkazov

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
Vytvor nový issue v projekte SCRUM s názvom "Test issue"
```

```
Ukáž mi všetky issues v projekte SCRUM
```

---

## 🔧 Architektúra

### Flow Diagram

```
User (Browser)
    ↓
Next.js Admin UI (port 3002)
    ↓
/api/ai-assistant/chat (Next.js API Route)
    ↓
Orchestrator (port 7010)
    ↓
Google AI / OpenAI
    ↓
Jira Cloud Adapter
    ↓
Jira Instance
```

### Komponenty

```
admin-ui/
├── src/
│   ├── app/
│   │   ├── (dashboard)/
│   │   │   └── admin/
│   │   │       └── assistant/
│   │   │           └── page.tsx          # Main AI Assistant page
│   │   └── api/
│   │       └── ai-assistant/
│   │           ├── chat/
│   │           │   └── route.ts          # Chat API proxy
│   │           └── autocomplete/
│   │               └── route.ts          # Autocomplete API proxy
│   └── components/
│       ├── ai-assistant/
│       │   ├── ChatMessage.tsx           # Message component
│       │   └── ChatInput.tsx             # Input with autocomplete
│       └── layout/
│           └── Sidebar.tsx               # Updated with AI Assistant link
```

---

## 📊 Features

### Chat Interface
- ✅ Real-time messaging
- ✅ User/Assistant avatars
- ✅ Timestamps
- ✅ Loading states
- ✅ Error handling
- ✅ Auto-scroll to bottom
- ✅ Welcome message with examples

### Autocomplete
- ✅ @ for users
- ✅ / for issues
- ✅ Dropdown suggestions
- ✅ Keyboard navigation (Arrow keys)
- ✅ Enter to select
- ✅ Escape to close
- ✅ Real-time search

### Tool Calls Visualization
- ✅ Display tool name
- ✅ Display arguments
- ✅ Display results (JSON)
- ✅ Collapsible sections
- ✅ Syntax highlighting

### Project Selector
- ✅ Dropdown with projects
- ✅ "All projects" option
- ✅ Filter messages by project

---

## 🚀 Spustenie

### Predpoklady
1. **PostgreSQL** - Running (port 5433)
2. **Orchestrator** - Running (port 7010)
3. **Admin UI** - Running (port 3002)

### Spustenie služieb

#### 1. Spustite Orchestrator (ak nebeží)
```bash
cd /Users/hotovo/Projects/digital-spiral
PYTHONPATH=/Users/hotovo/Projects/digital-spiral:$PYTHONPATH \
DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator" \
GOOGLE_AI_API_KEY=your-google-api-key \
python3 -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 7010 --reload
```

#### 2. Spustite Admin UI (ak nebeží)
```bash
cd admin-ui
npm run dev
```

#### 3. Otvorte AI Assistant
```bash
open http://localhost:3002/admin/assistant
```

---

## 🧪 Testovanie

### 1. Test Chat
```bash
# Open AI Assistant
open http://localhost:3002/admin/assistant

# Type message
"Ahoj! Ako sa máš?"

# Should receive response from AI
```

### 2. Test Autocomplete (@users)
```bash
# Type in input
"Prirad issue používateľovi @"

# Start typing
"@john"

# Should show dropdown with user suggestions
# Use arrow keys to navigate
# Press Enter to select
```

### 3. Test Autocomplete (/issues)
```bash
# Type in input
"Pridaj komentár do /"

# Start typing
"/SCRUM-"

# Should show dropdown with issue suggestions
# Use arrow keys to navigate
# Press Enter to select
```

### 4. Test Project Selector
```bash
# Select project from dropdown
"SCRUM"

# Type message
"Vyhľadaj všetky issues"

# Should search only in SCRUM project
```

### 5. Test Tool Calls
```bash
# Type message that triggers tool call
"Vyhľadaj všetky bugs"

# Should show:
# - User message
# - Tool call badge (e.g., "jira.search")
# - Tool arguments
# - Tool result (JSON)
# - Assistant response
```

---

## 📁 Súbory

### Vytvorené súbory
1. ✅ `admin-ui/src/app/(dashboard)/admin/assistant/page.tsx`
2. ✅ `admin-ui/src/components/ai-assistant/ChatMessage.tsx`
3. ✅ `admin-ui/src/components/ai-assistant/ChatInput.tsx`
4. ✅ `admin-ui/src/app/api/ai-assistant/chat/route.ts`
5. ✅ `admin-ui/src/app/api/ai-assistant/autocomplete/route.ts`
6. ✅ `AI_ASSISTANT_INTEGRATED.md` (this file)

### Upravené súbory
1. ✅ `admin-ui/src/components/layout/Sidebar.tsx` - Pridaný AI Assistant link

---

## 🎨 UI/UX Features

### Design
- ✅ Clean, modern interface
- ✅ Responsive layout
- ✅ Smooth animations
- ✅ Consistent with Admin UI design
- ✅ shadcn/ui components
- ✅ Tailwind CSS styling

### User Experience
- ✅ Auto-scroll to latest message
- ✅ Loading indicators
- ✅ Error messages
- ✅ Welcome message with examples
- ✅ Keyboard shortcuts
- ✅ Autocomplete suggestions
- ✅ Project filtering

### Accessibility
- ✅ Keyboard navigation
- ✅ ARIA labels
- ✅ Focus management
- ✅ Screen reader friendly

---

## 🔌 API Integration

### Chat API
```typescript
// Request
POST /api/ai-assistant/chat
{
  "messages": [
    { "role": "user", "content": "Vyhľadaj issues" }
  ],
  "project_keys": ["SCRUM"]
}

// Response
{
  "message": "Našiel som 5 issues...",
  "tool_calls": [
    {
      "name": "jira.search",
      "args": { "jql": "project = SCRUM" },
      "result": { "issues": [...] }
    }
  ]
}
```

### Autocomplete API
```typescript
// Request
POST /api/ai-assistant/autocomplete
{
  "type": "user",
  "query": "john"
}

// Response
{
  "suggestions": [
    {
      "id": "user-1",
      "label": "John Doe",
      "value": "@john.doe",
      "type": "user"
    }
  ]
}
```

---

## ✅ Status

```
✅ AI Assistant page - Created
✅ ChatMessage component - Created
✅ ChatInput component - Created
✅ Chat API proxy - Created
✅ Autocomplete API proxy - Created
✅ Sidebar navigation - Updated
✅ Orchestrator - Running (port 7010)
✅ Admin UI - Running (port 3002)
✅ Integration - Complete
```

---

## 🎯 Ďalšie kroky

### 1. Vylepšenia UI
- [ ] Pridať markdown rendering pre AI responses
- [ ] Pridať syntax highlighting pre code blocks
- [ ] Pridať copy button pre code snippets
- [ ] Pridať export chat history

### 2. Features
- [ ] Pridať chat history (save to database)
- [ ] Pridať multiple chat sessions
- [ ] Pridať file upload (screenshots, logs)
- [ ] Pridať voice input

### 3. Integration
- [ ] Pridať AI suggestions do instance detail page
- [ ] Pridať quick actions (create issue, add comment)
- [ ] Pridať AI-powered search
- [ ] Pridať AI-powered analytics

### 4. Performance
- [ ] Implementovať streaming responses
- [ ] Pridať caching
- [ ] Optimalizovať autocomplete queries
- [ ] Pridať rate limiting

---

## 🆘 Troubleshooting

### AI Assistant sa nenačíta
```bash
# Check if Orchestrator is running
curl http://127.0.0.1:7010/health

# Check if Admin UI is running
curl http://localhost:3002

# Check browser console for errors
```

### Chat nefunguje
```bash
# Check API proxy
curl -X POST http://localhost:3002/api/ai-assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'

# Check Orchestrator
curl -X POST http://127.0.0.1:7010/v1/ai-assistant/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: insight-bridge" \
  -d '{"messages":[{"role":"user","content":"test"}]}'
```

### Autocomplete nefunguje
```bash
# Check autocomplete API
curl -X POST http://localhost:3002/api/ai-assistant/autocomplete \
  -H "Content-Type: application/json" \
  -d '{"type":"user","query":"john"}'

# Check Orchestrator
curl -X POST http://127.0.0.1:7010/v1/ai-assistant/autocomplete \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: insight-bridge" \
  -d '{"type":"user","query":"john"}'
```

---

**AI Assistant je teraz plne integrovaný do Admin UI! 🎉**

Môžete začať chatovať s AI priamo z Admin UI bez potreby otvárať samostatnú stránku!

---

## 📚 Dokumentácia

- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[AI_ASSISTANT_RUNNING.md](AI_ASSISTANT_RUNNING.md)** - Standalone AI Assistant
- **[AI_ASSISTANT_INTEGRATED.md](AI_ASSISTANT_INTEGRATED.md)** - This file
- **[docs/AI_ASSISTANT_QUICKSTART.md](docs/AI_ASSISTANT_QUICKSTART.md)** - Original guide

---

**Happy chatting! 🚀**
