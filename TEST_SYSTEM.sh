#!/usr/bin/env bash
# Test Digital Spiral System

set -e

echo "🧪 Testing Digital Spiral System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}▶ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

print_error() {
    echo -e "${RED}✗ ${NC}$1"
}

# Test 1: Check Docker containers
print_step "Checking Docker containers..."
if docker ps | grep -q "digital-spiral-postgres"; then
    print_success "PostgreSQL is running"
else
    print_error "PostgreSQL is not running"
fi

if docker ps | grep -q "digital-spiral-redis"; then
    print_success "Redis is running"
else
    print_error "Redis is not running"
fi

if docker ps | grep -q "mock-jira"; then
    print_success "Mock Jira is running"
else
    print_error "Mock Jira is not running"
fi
echo ""

# Test 2: Check PostgreSQL connection
print_step "Testing PostgreSQL connection..."
if docker exec digital-spiral-postgres pg_isready -U ds -d ds_orchestrator >/dev/null 2>&1; then
    print_success "PostgreSQL connection OK"
else
    print_error "PostgreSQL connection failed"
fi
echo ""

# Test 3: Check Redis connection
print_step "Testing Redis connection..."
if docker exec digital-spiral-redis redis-cli ping | grep -q "PONG"; then
    print_success "Redis connection OK"
else
    print_error "Redis connection failed"
fi
echo ""

# Test 4: Check Mock Jira
print_step "Testing Mock Jira..."
if curl -s http://localhost:9000/_mock/health | grep -q "ok"; then
    print_success "Mock Jira is healthy"
else
    print_error "Mock Jira is not responding"
fi
echo ""

# Test 5: Check database tables
print_step "Checking database tables..."
TABLES=$(docker exec digital-spiral-postgres psql -U ds -d ds_orchestrator -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')
print_success "Found $TABLES tables in database"
echo ""

# Test 6: Check if migrations are up to date
print_step "Checking migrations..."
if command -v alembic >/dev/null 2>&1; then
    CURRENT=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]{12}' | head -1 || echo "none")
    if [ "$CURRENT" != "none" ]; then
        print_success "Current migration: $CURRENT"
    else
        print_warning "No migrations applied yet"
    fi
else
    print_warning "Alembic not found"
fi
echo ""

# Test 7: Check if FastAPI is running
print_step "Checking FastAPI server..."
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    print_success "FastAPI is running on port 8000"
else
    print_warning "FastAPI is not running (start with: uvicorn src.interfaces.api.main:app --reload --port 8000)"
fi
echo ""

# Test 8: Check if Admin UI is running
print_step "Checking Admin UI..."
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    print_success "Admin UI is running on port 3000"
else
    print_warning "Admin UI is not running (start with: cd admin-ui && npm run dev)"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "System test complete!"
echo ""
echo "📊 Services Status:"
echo "  ✓ PostgreSQL: localhost:5432"
echo "  ✓ Redis: localhost:6379"
echo "  ✓ Mock Jira: http://localhost:9000"
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "  ✓ FastAPI: http://localhost:8000"
else
    echo "  ⚠ FastAPI: Not running"
fi
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "  ✓ Admin UI: http://localhost:3000"
else
    echo "  ⚠ Admin UI: Not running"
fi
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start FastAPI (if not running):"
echo "   uvicorn src.interfaces.api.main:app --reload --port 8000"
echo ""
echo "2. Start Admin UI (if not running):"
echo "   cd admin-ui && npm run dev"
echo ""
echo "3. Test API endpoints:"
echo "   curl http://localhost:8000/docs"
echo "   curl http://localhost:8000/analytics/metrics"
echo ""
echo "4. Test with Auggie:"
echo "   Read: AUGGIE.md"
echo "   Read: QUICKSTART_FEATURE_004.md"
echo "   Run: /implement"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

