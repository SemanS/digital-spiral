# AI Support Copilot - Development Setup Guide

## 📋 Overview

This guide will help you set up a complete development environment for **AI Support Copilot** with realistic dummy data including:

- **8 Support Team Members** (Sarah Johnson, Mike Chen, Emma Wilson, Alex Rodriguez, Lisa Patel, Tom Brown, Nina Kowalski, Raj Sharma)
- **8 Customer Accounts** (representing different companies)
- **240 Support Tickets** over 6 months (~2 tickets per business day)
- **Realistic Scenarios**: Bug reports, access requests, billing issues, incidents, questions, feature requests
- **Full Ticket Lifecycle**: Creation → Assignment → Comments → Resolution
- **12 Sprints** (2-week duration) for performance tracking
- **Comment Threads** with back-and-forth between customers and support agents

## 🚀 Quick Start

### Option 1: Local Development (Recommended for Development)

```bash
# 1. Generate seed data
python scripts/generate_dummy_jira.py \
  --config scripts/seed_profiles/ai_support_copilot.json \
  --out artifacts/ai_support_copilot_seed.json

# 2. Start mock Jira server
python -c "from mockjira.main import run; run()" --port 9000

# 3. In another terminal, load seed data
curl -X POST http://localhost:9000/_mock/seed/load \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d @artifacts/ai_support_copilot_seed.json

# 4. Verify data loaded
curl -H "Authorization: Bearer support-token" \
  "http://localhost:9000/rest/api/3/search?jql=project=SUP1&maxResults=5"
```

### Option 2: Docker Compose (Full Stack)

```bash
# 1. Set environment variable for AI Support Copilot seed profile
export MOCK_JIRA_SEED_CONFIG=scripts/seed_profiles/ai_support_copilot.json

# 2. Start all services (mock Jira + orchestrator + postgres)
docker compose up -d

# 3. Wait for services to be healthy
docker compose ps

# 4. Access services
# - Mock Jira API: http://localhost:9000
# - Mock Jira Docs: http://localhost:9000/docs
# - Orchestrator API: http://localhost:7010
# - Orchestrator Docs: http://localhost:7010/docs
```

## 📊 Data Structure

### Projects

- **SUP1** (Support 1) - Service Desk project with 240 tickets
- **DEV** (Development 1) - Software project for escalations

### Users

**Support Team:**
- `sarah.johnson` - Support Lead
- `mike.chen` - Senior Support Engineer
- `emma.wilson` - Support Engineer
- `alex.rodriguez` - Support Engineer
- `lisa.patel` - Junior Support Engineer
- `tom.brown` - Junior Support Engineer
- `nina.kowalski` - Support Specialist
- `raj.sharma` - Technical Support

**Customers:**
- `customer.john` - John Smith
- `customer.mary` - Mary Davis
- `customer.robert` - Robert Lee
- `customer.jennifer` - Jennifer Taylor
- `customer.david` - David Martinez
- `customer.susan` - Susan Anderson
- `customer.james` - James Wilson
- `customer.patricia` - Patricia Moore

### Authentication Tokens

- `mock-token` - Default token (maps to first user)
- `support-token` - Support team token (maps to sarah.johnson)

## 🎯 Ticket Scenarios

The seed data includes realistic support scenarios:

### Bug Reports (~30 tickets)
- Login issues
- Mobile UI problems
- Export/data corruption
- Performance issues

Example:
```
SUP1-X: Login page returns 500 error after password reset
Priority: High
Labels: bug, login, p1, blocker
Comments: 6 (customer ↔ support back-and-forth)
Status: Resolved
```

### Access Requests (~25 tickets)
- New employee onboarding
- VPN access issues
- Permission changes

### Billing Issues (~20 tickets)
- Duplicate charges
- Invoice discrepancies
- Refund requests

### Incidents (~15 tickets)
- Service outages
- Performance degradation
- Critical production issues

### Questions (~40 tickets)
- How-to questions
- Configuration help
- Feature inquiries

### Feature Requests (~10 tickets)
- UI improvements
- New functionality requests

## 🔍 Testing the Setup

### 1. List All Projects

```bash
curl -H "Authorization: Bearer support-token" \
  http://localhost:9000/rest/api/3/project | jq
```

Expected output:
```json
{
  "values": [
    {"key": "DEV", "name": "Development 1"},
    {"key": "SUP1", "name": "Support 1"}
  ]
}
```

### 2. Search Support Tickets

```bash
# Get recent tickets
curl -H "Authorization: Bearer support-token" \
  "http://localhost:9000/rest/api/3/search?jql=project=SUP1&maxResults=10" | jq

# Get high priority tickets
curl -H "Authorization: Bearer support-token" \
  "http://localhost:9000/rest/api/3/search?jql=project=SUP1+AND+priority=High" | jq

# Get open tickets
curl -H "Authorization: Bearer support-token" \
  "http://localhost:9000/rest/api/3/search?jql=project=SUP1+AND+status!=Done" | jq
```

### 3. Get Specific Ticket with Comments

```bash
curl -H "Authorization: Bearer support-token" \
  http://localhost:9000/rest/api/3/issue/SUP1-1 | jq
```

### 4. Test Orchestrator Integration

```bash
# Ingest a ticket (triggers AI analysis)
curl -X GET "http://localhost:7010/v1/jira/ingest?issueKey=SUP1-1" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" | jq

# Expected: AI-generated proposals (comments, transitions, labels)
```

## 🛠️ Development Workflow

### 1. Start Development Environment

```bash
# Terminal 1: Mock Jira
python -c "from mockjira.main import run; run()" --port 9000

# Terminal 2: Orchestrator (requires postgres)
cd orchestrator
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator"
export JIRA_BASE_URL="http://localhost:9000"
export JIRA_TOKEN="support-token"
uvicorn app:app --reload --port 7010

# Terminal 3: Load seed data
curl -X POST http://localhost:9000/_mock/seed/load \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d @artifacts/ai_support_copilot_seed.json
```

### 2. Test AI Features

```bash
# Test intent classification
curl -X GET "http://localhost:7010/v1/jira/ingest?issueKey=SUP1-5" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" | jq '.analysis.intent'

# Test PII detection
curl -X GET "http://localhost:7010/v1/jira/ingest?issueKey=SUP1-10" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" | jq '.analysis.pii'

# Test complexity estimation
curl -X GET "http://localhost:7010/v1/jira/ingest?issueKey=SUP1-15" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" | jq '.analysis.complexity'
```

### 3. Apply AI Suggestions

```bash
# Get proposals
PROPOSALS=$(curl -s -X GET "http://localhost:7010/v1/jira/ingest?issueKey=SUP1-1" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret")

# Apply first proposal (add comment)
curl -X POST "http://localhost:7010/v1/jira/apply" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "X-DS-Actor: human.sarah.johnson" \
  -d '{
    "issueKey": "SUP1-1",
    "action": {
      "id": "add-comment-1",
      "kind": "comment"
    }
  }' | jq
```

## 📈 Metrics & Analytics

### View Credit Summary

```bash
curl -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" \
  "http://localhost:7010/v1/credit/summary?limit=10" | jq
```

### View Agent Performance

```bash
curl -H "Authorization: Bearer forge-dev-secret" \
  -H "X-Tenant-Id: demo" \
  -H "X-DS-Secret: forge-dev-secret" \
  "http://localhost:7010/v1/credit/agent/ai.summarizer?window=30d" | jq
```

## 🔄 Regenerating Seed Data

If you need to regenerate seed data with different parameters:

```bash
# Edit the config
vim scripts/seed_profiles/ai_support_copilot.json

# Regenerate
python scripts/generate_dummy_jira.py \
  --config scripts/seed_profiles/ai_support_copilot.json \
  --out artifacts/ai_support_copilot_seed.json

# Reload into mock Jira
curl -X POST http://localhost:9000/_mock/seed/load \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d @artifacts/ai_support_copilot_seed.json
```

## 🐛 Troubleshooting

### Issue: "Cannot import name 'UTC' from 'datetime'"

**Solution**: You're using Python 3.10. The codebase has been updated with compatibility shims. Pull latest changes.

### Issue: "No support templates found"

**Solution**: Make sure `use_support_templates: true` is set in your seed profile JSON.

### Issue: "Seed data has old users (alice, bob)"

**Solution**: Regenerate seed data with the updated generator that includes `use_support_templates` flag.

### Issue: "Mock Jira returns 401 Unauthorized"

**Solution**: Use the correct token:
- `mock-token` for general access
- `support-token` for support team member access

## 📚 Next Steps

1. **Explore the API**: Visit http://localhost:9000/docs for interactive API documentation
2. **Test Orchestrator**: Visit http://localhost:7010/docs for orchestrator endpoints
3. **Build UI**: Use the Forge app in `forge-app/` to build Jira Cloud UI
4. **Add AI Models**: Integrate OpenAI/Anthropic for better intent classification
5. **Extend Scenarios**: Add more realistic support scenarios in `mockjira/fixtures/support_templates.py`

## 🎉 Success Criteria

You should now have:
- ✅ Mock Jira running with 240 realistic support tickets
- ✅ 8 support team members + 8 customers
- ✅ Full comment history on tickets
- ✅ 6 months of sprint history
- ✅ Orchestrator analyzing tickets and generating proposals
- ✅ Credit tracking for AI agent performance

Happy coding! 🚀

