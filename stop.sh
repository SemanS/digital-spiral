#!/bin/bash

# Digital Spiral - Stop Script
# This script stops all services

echo "🛑 Digital Spiral - Stopping All Services"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop Backend API
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "🔧 Stopping Backend API (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || echo -e "${YELLOW}⚠️  Backend API already stopped${NC}"
    rm .backend.pid
    echo -e "${GREEN}✅ Backend API stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Backend API PID file not found${NC}"
fi
echo ""

# Stop Admin UI
if [ -f ".admin-ui.pid" ]; then
    ADMIN_UI_PID=$(cat .admin-ui.pid)
    echo "🎨 Stopping Admin UI (PID: $ADMIN_UI_PID)..."
    kill $ADMIN_UI_PID 2>/dev/null || echo -e "${YELLOW}⚠️  Admin UI already stopped${NC}"
    rm .admin-ui.pid
    echo -e "${GREEN}✅ Admin UI stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Admin UI PID file not found${NC}"
fi
echo ""

# Stop Docker services
echo "🐳 Stopping Docker services..."
docker compose -f docker/docker-compose.dev.yml down
echo -e "${GREEN}✅ Docker services stopped${NC}"
echo ""

echo "=========================================="
echo "✅ All services stopped successfully!"
echo "=========================================="
echo ""

