#!/bin/bash

# Script to run AI Assistant orchestrator with proper environment setup

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AI Assistant Orchestrator${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure your API keys"
    exit 1
fi

# Load environment variables from .env
export $(grep -v '^#' .env | xargs)

# Check if AI API key is set
if [ -z "$GOOGLE_AI_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ No AI API key configured!${NC}"
    echo ""
    echo "Please set one of the following in your .env file:"
    echo "  - GOOGLE_AI_API_KEY (get it from: https://aistudio.google.com/app/apikey)"
    echo "  - OPENAI_API_KEY (get it from: https://platform.openai.com/api-keys)"
    echo ""
    exit 1
fi

# Check which AI provider is configured
if [ ! -z "$GOOGLE_AI_API_KEY" ]; then
    echo -e "${GREEN}✅ Using Google AI (Gemini)${NC}"
elif [ ! -z "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}✅ Using OpenAI${NC}"
fi

# Check if Jira is configured
if [ -z "$JIRA_BASE_URL" ]; then
    echo -e "${YELLOW}⚠️  JIRA_BASE_URL not set, using default${NC}"
    export JIRA_BASE_URL="https://insight-bridge.atlassian.net"
fi

# Check if database is running
echo -e "${YELLOW}🔍 Checking database connection...${NC}"
if ! docker compose -f docker/docker-compose.dev.yml ps postgres | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not running. Starting it...${NC}"
    docker compose -f docker/docker-compose.dev.yml up -d postgres
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Set orchestrator-specific environment variables
export DATABASE_URL="postgresql+psycopg://ds:ds@localhost:5432/ds_orchestrator"
export JIRA_TOKEN="${JIRA_TOKEN:-mock-token}"
export WEBHOOK_SECRET="${WEBHOOK_SECRET:-dev-secret}"
export DEFAULT_TENANT_ID="${DEFAULT_TENANT_ID:-insight-bridge}"
export DEFAULT_TENANT_SITE_ID="${DEFAULT_TENANT_SITE_ID:-insight-bridge.atlassian.net}"
export DEFAULT_TENANT_SECRET="${DEFAULT_TENANT_SECRET:-forge-dev-secret}"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo ""
echo -e "${GREEN}📊 Configuration:${NC}"
echo "  - Database: $DATABASE_URL"
echo "  - Jira: $JIRA_BASE_URL"
echo "  - Tenant: $DEFAULT_TENANT_ID"
echo ""

echo -e "${GREEN}🚀 Starting orchestrator on http://127.0.0.1:7010${NC}"
echo -e "${GREEN}📱 AI Assistant UI: http://127.0.0.1:7010/v1/ai-assistant/${NC}"
echo -e "${GREEN}📊 Pulse Dashboard: http://127.0.0.1:7010/v1/pulse/${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run orchestrator
cd orchestrator
PYTHONUNBUFFERED=1 python3 -m uvicorn app:app --host 0.0.0.0 --port 7010 --reload

