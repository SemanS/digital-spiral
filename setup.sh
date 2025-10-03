#!/bin/bash

# Digital Spiral - Setup Script
# This script sets up the entire project

set -e

echo "🚀 Digital Spiral - Setup Script"
echo "================================"
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
echo "🐳 Starting Docker services (PostgreSQL, Redis, Mock Jira)..."
docker compose -f docker/docker-compose.dev.yml up -d
echo -e "${GREEN}✅ Docker services started${NC}"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec digital-spiral-postgres pg_isready -U digital_spiral > /dev/null 2>&1; do
    sleep 1
done
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
echo ""

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
until docker exec digital-spiral-redis redis-cli ping > /dev/null 2>&1; do
    sleep 1
done
echo -e "${GREEN}✅ Redis is ready${NC}"
echo ""

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head
echo -e "${GREEN}✅ Database migrations completed${NC}"
echo ""

# Check if Admin UI exists
if [ -d "admin-ui" ]; then
    echo "📦 Installing Admin UI dependencies..."
    cd admin-ui
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        npm install
        echo -e "${GREEN}✅ Admin UI dependencies installed${NC}"
    else
        echo -e "${GREEN}✅ Admin UI dependencies already installed${NC}"
    fi
    
    cd ..
else
    echo -e "${YELLOW}⚠️  Admin UI directory not found. Skipping...${NC}"
fi
echo ""

# Generate .env.local if it doesn't exist
if [ ! -f "admin-ui/.env.local" ]; then
    echo "🔧 Generating Admin UI .env.local..."
    cat > admin-ui/.env.local << EOF
# NextAuth
NEXTAUTH_URL=http://localhost:3002
NEXTAUTH_SECRET=$(openssl rand -base64 32)

# Google OAuth
# Get credentials from: https://console.cloud.google.com/
# Authorized redirect URI: http://localhost:3002/api/auth/callback/google
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000

# Environment
NODE_ENV=development
EOF
    echo -e "${GREEN}✅ Admin UI .env.local generated${NC}"
    echo -e "${YELLOW}⚠️  Please update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in admin-ui/.env.local${NC}"
else
    echo -e "${GREEN}✅ Admin UI .env.local already exists${NC}"
fi
echo ""

# Summary
echo "================================"
echo "✅ Setup completed successfully!"
echo "================================"
echo ""
echo "📊 Services Status:"
echo "  - PostgreSQL: Running on port 5433"
echo "  - Redis: Running on port 6379"
echo "  - Mock Jira: Running on port 9000"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start Backend API:"
echo "   source venv/bin/activate"
echo "   uvicorn src.interfaces.rest.main:app --reload --port 8000"
echo ""
echo "2. Start Admin UI (in another terminal):"
echo "   cd admin-ui"
echo "   npm run dev"
echo ""
echo "3. Configure Google OAuth:"
echo "   - Go to: https://console.cloud.google.com/"
echo "   - Create OAuth 2.0 credentials"
echo "   - Add redirect URI: http://localhost:3002/api/auth/callback/google"
echo "   - Update admin-ui/.env.local with credentials"
echo ""
echo "📚 Documentation:"
echo "   - PROJECT_STATUS.md - Current project status"
echo "   - README.md - Project overview"
echo ""
echo "🌐 Access URLs:"
echo "   - Backend API: http://localhost:8000"
echo "   - Admin UI: http://localhost:3002"
echo "   - Mock Jira: http://localhost:9000"
echo ""

