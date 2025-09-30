# Forge App Development Guide

## 🎯 Overview

Forge App poskytuje **Jira Cloud UI** pre AI Support Copilot. Zobrazuje sa ako panel v každom Jira tickete a umožňuje:

- Vidieť AI návrhy (komentáre, transitions, labels)
- Aplikovať návrhy jedným klikom
- Sledovať credit tracking (koľko času AI ušetrilo)
- Vidieť contributors a performance metriky

## 🚀 Development Options

### Option 1: Forge Tunnel + Real Jira Cloud (Odporúčané pre produkciu)

**Výhody:**
- Reálne Jira Cloud UI
- Testovanie v produkčnom prostredí
- Webhooks fungujú automaticky

**Nevýhody:**
- Potrebuješ Atlassian účet
- Potrebuješ Jira Cloud site
- Pomalšie (deploy trvá ~30s)

### Option 2: Mock Jira + Custom UI (Rýchlejšie pre development)

**Výhody:**
- Žiadne Atlassian credentials
- Rýchle iterácie
- Plná kontrola nad dátami

**Nevýhody:**
- Nie je to reálne Jira UI
- Musíš si vytvoriť vlastné UI

---

## 📦 Option 1: Forge Tunnel Setup

### Prerequisites

```bash
# 1. Nainštaluj Forge CLI (už máš)
npm install -g @forge/cli

# 2. Prihlás sa do Atlassian
forge login
# Potrebuješ:
# - Email: slavomir.seman@hotovo.com
# - API Token: https://id.atlassian.com/manage/api-tokens
```

### Setup Steps

#### 1. Vytvor Jira Cloud Site (ak nemáš)

Choď na: https://www.atlassian.com/try/cloud/signup?product=jira-software

- Vytvor free Jira site (napr. `hotovo-dev.atlassian.net`)
- Počkaj kým sa site vytvorí (~2 min)

#### 2. Nastav Environment Variables

```bash
cd forge-app

# Nastav orchestrator URL (lokálny)
export ORCH_URL="http://localhost:7010"

# Alebo použij ngrok pre public URL
# ngrok http 7010
# export ORCH_URL="https://your-ngrok-url.ngrok.io"
```

#### 3. Registruj App

```bash
cd forge-app

# Prvýkrát - vytvor novú app
forge register

# Vyber:
# - App name: digital-spiral-dev
# - Category: Issue tracking
```

#### 4. Deploy App

```bash
# Deploy do Atlassian cloud
forge deploy

# Nainštaluj na svoj Jira site
forge install

# Vyber svoj Jira site (napr. hotovo-dev.atlassian.net)
```

#### 5. Spusti Tunnel (Development Mode)

```bash
# Spusti tunnel - zmeny sa aplikujú okamžite
forge tunnel

# Tunnel prepojí lokálny kód s Jira Cloud
# Každá zmena v src/ sa okamžite prejaví v Jira UI
```

#### 6. Nastav Orchestrator URL v Jira

1. Choď do Jira: `https://your-site.atlassian.net`
2. Choď do Project Settings → Apps → Digital Spiral Settings
3. Nastav:
   - **Orchestrator URL**: `http://localhost:7010` (alebo ngrok URL)
   - **Shared Secret**: `forge-dev-secret`
   - **Tenant ID**: `demo`

#### 7. Spusti Orchestrator

```bash
# Terminal 1: Mock Jira
python -c "from mockjira.main import run; run()" --port 9000

# Terminal 2: Load seed data
curl -X POST http://localhost:9000/_mock/seed/load \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d @artifacts/ai_support_copilot_seed.json

# Terminal 3: Orchestrator
cd orchestrator
export DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator"
export JIRA_BASE_URL="http://localhost:9000"
export JIRA_TOKEN="support-token"
export FORGE_SHARED_SECRET="forge-dev-secret"
uvicorn app:app --reload --port 7010

# Terminal 4: Forge tunnel
cd forge-app
forge tunnel
```

#### 8. Test v Jira UI

1. Otvor Jira ticket: `https://your-site.atlassian.net/browse/SUP1-1`
2. Pozri sa na pravý panel → **Digital Spiral**
3. Uvidíš AI návrhy a môžeš ich aplikovať

---

## 🔧 Option 2: Custom UI Development

Ak nechceš používať Forge, môžeš si vytvoriť vlastné UI pomocou React/Vue/Angular.

### Quick React Example

```bash
# Vytvor React app
npx create-react-app digital-spiral-ui
cd digital-spiral-ui

# Nainštaluj dependencies
npm install axios @atlaskit/button @atlaskit/section-message
```

### Example Component

```tsx
// src/IssuePanel.tsx
import React, { useEffect, useState } from 'react';
import Button from '@atlaskit/button';
import SectionMessage from '@atlaskit/section-message';

interface Proposal {
  id: string;
  kind: string;
  explain?: string;
}

export const IssuePanel: React.FC<{ issueKey: string }> = ({ issueKey }) => {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:7010/v1/jira/ingest?issueKey=${issueKey}`, {
      headers: {
        'Authorization': 'Bearer forge-dev-secret',
        'X-Tenant-Id': 'demo',
        'X-DS-Secret': 'forge-dev-secret',
      },
    })
      .then(res => res.json())
      .then(data => {
        setProposals(data.proposals || []);
        setLoading(false);
      });
  }, [issueKey]);

  const applyProposal = async (proposal: Proposal) => {
    await fetch('http://localhost:7010/v1/jira/apply', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer forge-dev-secret',
        'X-Tenant-Id': 'demo',
        'X-DS-Secret': 'forge-dev-secret',
      },
      body: JSON.stringify({
        issueKey,
        action: { id: proposal.id, kind: proposal.kind },
      }),
    });
    alert('Applied!');
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>AI Support Copilot</h2>
      {proposals.map(proposal => (
        <SectionMessage key={proposal.id} title={proposal.kind}>
          <p>{proposal.explain}</p>
          <Button onClick={() => applyProposal(proposal)}>Apply</Button>
        </SectionMessage>
      ))}
    </div>
  );
};
```

---

## 🧪 Testing

### Test Orchestrator API Directly

```bash
# Get proposals for ticket
curl -X GET "http://localhost:7010/v1/jira/ingest?issueKey=SUP1-1" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" | jq

# Apply proposal
curl -X POST "http://localhost:7010/v1/jira/apply" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" \
  -d '{
    "issueKey": "SUP1-1",
    "action": {
      "id": "add-comment-1",
      "kind": "comment"
    }
  }' | jq
```

### Test in Browser

```bash
# Open Swagger UI
open http://localhost:7010/docs

# Test endpoints interactively
```

---

## 🐛 Troubleshooting

### Issue: "forge: command not found"

```bash
npm install -g @forge/cli
```

### Issue: "Orchestrator URL not reachable from Jira Cloud"

**Problem**: Jira Cloud nemôže pristúpiť k `localhost:7010`

**Solution**: Použij ngrok alebo podobný tunnel:

```bash
# Nainštaluj ngrok
brew install ngrok

# Spusti tunnel
ngrok http 7010

# Použij ngrok URL v Forge app settings
# Napr: https://abc123.ngrok.io
```

### Issue: "No proposals available"

**Možné príčiny:**
1. Orchestrator nebeží
2. Mock Jira nebeží
3. Seed data nie sú načítané
4. Nesprávne credentials

**Debug:**
```bash
# Check orchestrator
curl http://localhost:7010/health

# Check mock Jira
curl http://localhost:9000/_mock/health

# Check proposals directly
curl -H "Authorization: Bearer support-token" \
  "http://localhost:9000/rest/api/3/issue/SUP1-1"
```

### Issue: "Forge tunnel disconnects"

**Solution**: Forge tunnel sa niekedy odpojí. Reštartuj ho:

```bash
# Ctrl+C to stop
# Then restart
forge tunnel
```

---

## 📚 Resources

- **Forge Documentation**: https://developer.atlassian.com/platform/forge/
- **Forge UI Kit**: https://developer.atlassian.com/platform/forge/ui-kit/
- **Atlassian Design System**: https://atlassian.design/
- **Mock Jira API Docs**: http://localhost:9000/docs
- **Orchestrator API Docs**: http://localhost:7010/docs

---

## 🎯 Next Steps

1. **Customize UI**: Upraviť `forge-app/src/panel.tsx`
2. **Add Features**: Pridať sentiment analysis, auto-resolution
3. **Improve AI**: Integrovať OpenAI/Anthropic
4. **Deploy to Production**: `forge deploy --environment production`

Happy coding! 🚀

