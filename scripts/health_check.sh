#!/bin/bash
# Health check script for Digital Spiral services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service URLs
MCP_JIRA_URL="${MCP_JIRA_URL:-http://localhost:8055}"
MCP_SQL_URL="${MCP_SQL_URL:-http://localhost:8056}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo "🏥 Digital Spiral Health Check"
echo "================================"
echo ""

# Function to check HTTP service
check_http_service() {
    local name=$1
    local url=$2
    local endpoint=$3
    
    echo -n "Checking $name... "
    
    if response=$(curl -s -f "$url$endpoint" 2>/dev/null); then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to check TCP service
check_tcp_service() {
    local name=$1
    local host=$2
    local port=$3
    
    echo -n "Checking $name... "
    
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Track failures
FAILURES=0

# Check PostgreSQL
if ! check_tcp_service "PostgreSQL" "$POSTGRES_HOST" "$POSTGRES_PORT"; then
    ((FAILURES++))
fi

# Check Redis
if ! check_tcp_service "Redis" "$REDIS_HOST" "$REDIS_PORT"; then
    ((FAILURES++))
fi

# Check MCP Jira Server
if ! check_http_service "MCP Jira Server" "$MCP_JIRA_URL" "/health"; then
    ((FAILURES++))
else
    # Get detailed info
    if tools=$(curl -s "$MCP_JIRA_URL/tools" 2>/dev/null); then
        count=$(echo "$tools" | grep -o '"count":[0-9]*' | cut -d: -f2)
        echo "  └─ Tools available: $count"
    fi
fi

# Check MCP SQL Server
if ! check_http_service "MCP SQL Server" "$MCP_SQL_URL" "/health"; then
    ((FAILURES++))
else
    # Get detailed info
    if templates=$(curl -s "$MCP_SQL_URL/templates" 2>/dev/null); then
        count=$(echo "$templates" | grep -o '"count":[0-9]*' | cut -d: -f2)
        echo "  └─ Templates available: $count"
    fi
fi

echo ""
echo "================================"

# Summary
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All services healthy!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILURES service(s) failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Make sure services are running: make docker-up"
    echo "  - Check logs: make docker-logs"
    echo "  - Or run locally: make mcp-jira (terminal 1), make mcp-sql (terminal 2)"
    exit 1
fi

