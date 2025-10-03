#!/bin/bash

# Digital Spiral - Start Script
# This script starts all services

set -e

echo "🚀 Digital Spiral - Starting All Services"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "📦 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Start Docker services
echo "🐳 Starting Docker services..."
docker compose -f docker/docker-compose.dev.yml up -d
echo -e "${GREEN}✅ Docker services started${NC}"
echo ""

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 3
echo -e "${GREEN}✅ Services ready${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run ./setup.sh first.${NC}"
    exit 1
fi

# Start Backend API in background
echo "🔧 Starting Backend API..."
source venv/bin/activate
nohup uvicorn src.interfaces.rest.main:app --reload --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid
echo -e "${GREEN}✅ Backend API started (PID: $BACKEND_PID)${NC}"
echo ""

# Wait for backend to start
echo "⏳ Waiting for Backend API to be ready..."
sleep 5
echo -e "${GREEN}✅ Backend API ready${NC}"
echo ""

# Start Admin UI in background
if [ -d "admin-ui" ]; then
    echo "🎨 Starting Admin UI..."
    cd admin-ui
    nohup npm run dev > ../logs/admin-ui.log 2>&1 &
    ADMIN_UI_PID=$!
    echo $ADMIN_UI_PID > ../.admin-ui.pid
    cd ..
    echo -e "${GREEN}✅ Admin UI started (PID: $ADMIN_UI_PID)${NC}"
    echo ""
    
    # Wait for Admin UI to start
    echo "⏳ Waiting for Admin UI to be ready..."
    sleep 10
    echo -e "${GREEN}✅ Admin UI ready${NC}"
else
    echo -e "${YELLOW}⚠️  Admin UI directory not found. Skipping...${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "✅ All services started successfully!"
echo "=========================================="
echo ""
echo "📊 Running Services:"
echo "  - PostgreSQL: http://localhost:5433"
echo "  - Redis: http://localhost:6379"
echo "  - Mock Jira: http://localhost:9000"
echo "  - Backend API: http://localhost:8000"
echo "  - Admin UI: http://localhost:3002"
echo ""
echo "📝 Logs:"
echo "  - Backend API: logs/backend.log"
echo "  - Admin UI: logs/admin-ui.log"
echo ""
echo "🛑 To stop all services:"
echo "   ./stop.sh"
echo ""
echo "🌐 Open in browser:"
echo "   - Admin UI: http://localhost:3002"
echo "   - API Docs: http://localhost:8000/docs"
echo ""

