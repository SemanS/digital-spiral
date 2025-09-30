#!/bin/bash
# Setup script for AI Support Copilot with Real Jira Cloud
# Usage: ./scripts/setup_real_jira.sh YOUR_API_TOKEN

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Support Copilot - Real Jira Setup${NC}\n"

# Check if API token is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: API token required${NC}"
    echo ""
    echo "Usage: $0 YOUR_API_TOKEN"
    echo ""
    echo "Create API token at:"
    echo "  https://id.atlassian.com/manage-profile/security/api-tokens"
    echo ""
    exit 1
fi

API_TOKEN="$1"
JIRA_URL="https://insight-bridge.atlassian.net"
EMAIL="slavosmn@gmail.com"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Jira URL: $JIRA_URL"
echo "  Email: $EMAIL"
echo "  API Token: ${API_TOKEN:0:10}..."
echo ""

# Step 1: Update .env file
echo -e "${BLUE}Step 1: Updating .env file...${NC}"
if ! grep -q "JIRA_API_TOKEN" .env 2>/dev/null; then
    echo "JIRA_API_TOKEN=\"$API_TOKEN\"" >> .env
    echo -e "${GREEN}✓ Added JIRA_API_TOKEN to .env${NC}"
else
    echo -e "${YELLOW}⚠ JIRA_API_TOKEN already exists in .env${NC}"
fi

# Step 2: Test connection
echo -e "\n${BLUE}Step 2: Testing Jira connection...${NC}"
AUTH=$(echo -n "$EMAIL:$API_TOKEN" | base64)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Basic $AUTH" \
    "$JIRA_URL/rest/api/3/myself")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Connection successful!${NC}"
else
    echo -e "${RED}❌ Connection failed (HTTP $HTTP_CODE)${NC}"
    echo "  Please check your API token and try again"
    exit 1
fi

# Step 3: Generate seed data
echo -e "\n${BLUE}Step 3: Generating seed data...${NC}"
if [ ! -f "artifacts/ai_support_copilot_seed.json" ]; then
    python scripts/generate_dummy_jira.py \
        --config scripts/seed_profiles/ai_support_copilot.json \
        --out artifacts/ai_support_copilot_seed.json
    echo -e "${GREEN}✓ Seed data generated${NC}"
else
    echo -e "${YELLOW}⚠ Seed data already exists, skipping generation${NC}"
fi

# Step 4: Load data to Jira
echo -e "\n${BLUE}Step 4: Loading data to Jira...${NC}"
echo -e "${YELLOW}  Loading first 10 issues (to avoid overwhelming your Jira)${NC}"
python scripts/load_to_real_jira.py \
    --base-url "$JIRA_URL" \
    --token "$API_TOKEN" \
    --seed artifacts/ai_support_copilot_seed.json \
    --limit 10

# Step 5: Start Postgres
echo -e "\n${BLUE}Step 5: Starting Postgres...${NC}"
docker compose up -d postgres
echo -e "${GREEN}✓ Postgres started${NC}"
sleep 5

# Step 6: Export environment variables
echo -e "\n${BLUE}Step 6: Setting up environment...${NC}"
export JIRA_BASE_URL="$JIRA_URL"
export JIRA_TOKEN="$API_TOKEN"
export DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator"
export FORGE_SHARED_SECRET="forge-dev-secret"
export DEFAULT_TENANT_ID="insight-bridge"
export DEFAULT_TENANT_SITE_ID="insight-bridge.atlassian.net"
export DEFAULT_TENANT_SECRET="forge-dev-secret"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo -e "${GREEN}✓ Environment configured${NC}"

# Step 7: Instructions for starting orchestrator
echo -e "\n${GREEN}✅ Setup complete!${NC}\n"
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Start the orchestrator:"
echo -e "   ${YELLOW}export JIRA_BASE_URL=\"$JIRA_URL\"${NC}"
echo -e "   ${YELLOW}export JIRA_TOKEN=\"$API_TOKEN\"${NC}"
echo -e "   ${YELLOW}export DATABASE_URL=\"postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator\"${NC}"
echo -e "   ${YELLOW}export PYTHONPATH=\"$(pwd):\$PYTHONPATH\"${NC}"
echo -e "   ${YELLOW}python -m uvicorn orchestrator.app:app --reload --port 7010${NC}"
echo ""
echo "2. Open the demo UI:"
echo -e "   ${YELLOW}open demo-ui/real-jira.html${NC}"
echo ""
echo "3. In the UI, enter your API token and click 'Load Issues'"
echo ""
echo "4. Check your Jira:"
echo -e "   ${YELLOW}$JIRA_URL/jira/projects${NC}"
echo ""
echo -e "${BLUE}📚 Full documentation:${NC} docs/REAL_JIRA_SETUP.md"
echo ""

